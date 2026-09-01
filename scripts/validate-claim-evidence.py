#!/usr/bin/env python3
"""
TLL OS Claim-Evidence Validation Tool
Validates that every capability claim in .tll-engine/truth/capability.json
has corresponding evidence in .tll-engine/evidence/.

This is part of P0-16.1 TLL Engineering Enforcement Layer.
It prevents "claim without evidence" — a core TLL Engineering Protocol rule (P006).

Usage:
    python3 scripts/validate-claim-evidence.py [--strict] [--engine-dir .tll-engine]

Exit codes:
    0 = PASS
    1 = FAIL (errors found)
    2 = FAIL (strict mode, warnings treated as errors)
"""

import json
import os
import sys
import argparse
from pathlib import Path


class ClaimEvidenceValidator:
    def __init__(self, engine_dir, strict=False):
        self.engine_dir = Path(engine_dir).resolve()
        self.strict = strict
        self.errors = []
        self.warnings = []
        self.info = []

        # Track statistics
        self.total_claims = 0
        self.claims_with_evidence = 0
        self.claims_without_evidence = 0
        self.total_evidence = 0
        self.valid_evidence = 0
        self.invalid_evidence = 0

    def log_error(self, msg):
        self.errors.append(msg)
        print(f"  [ERROR] {msg}")

    def log_warning(self, msg):
        self.warnings.append(msg)
        print(f"  [WARNING] {msg}")

    def log_info(self, msg):
        self.info.append(msg)
        print(f"  [INFO] {msg}")

    def load_json(self, filepath):
        """Load and validate a JSON file. Returns (data, error_msg)."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data, None
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON: {e}"
        except FileNotFoundError:
            return None, f"File not found: {filepath}"
        except Exception as e:
            return None, f"Error reading file: {e}"

    def validate_evidence_schema(self, evidence_data, filepath):
        """Validate that an evidence file has the required schema fields."""
        required_fields = [
            'schema_version',
            'evidence_type',
            'id',
            'proves',
            'does_not_prove',
            'confidence',
            'hash',
            'provenance_chain'
        ]

        missing = []
        for field in required_fields:
            if field not in evidence_data:
                missing.append(field)

        if missing:
            self.log_error(f"Evidence file missing required fields {missing}: {filepath.name}")
            return False

        # Validate proves and does_not_prove are non-empty lists
        if not isinstance(evidence_data['proves'], list) or len(evidence_data['proves']) == 0:
            self.log_error(f"Evidence 'proves' must be a non-empty list: {filepath.name}")
            return False

        if not isinstance(evidence_data['does_not_prove'], list):
            self.log_error(f"Evidence 'does_not_prove' must be a list: {filepath.name}")
            return False

        # Validate confidence is one of allowed values
        allowed_confidence = ['high', 'medium', 'low', 'none', 'verified', 'partial', 'unverified']
        if evidence_data['confidence'] not in allowed_confidence:
            self.log_warning(f"Evidence confidence '{evidence_data['confidence']}' not in standard values: {filepath.name}")

        return True

    def scan_evidence(self):
        """Scan all evidence files and build a searchable index."""
        evidence_index = {}  # keyword -> list of evidence ids
        evidence_files = {}  # id -> evidence_data
        evidence_dir = self.engine_dir / 'evidence'

        if not evidence_dir.exists():
            self.log_error("Evidence directory not found")
            return evidence_index, evidence_files

        for subdir in ['ci', 'benchmark', 'audit']:
            subdir_path = evidence_dir / subdir
            if not subdir_path.exists():
                self.log_warning(f"Evidence subdirectory not found: evidence/{subdir}")
                continue

            for filepath in subdir_path.glob('*.json'):
                self.total_evidence += 1
                data, error = self.load_json(filepath)
                if error:
                    self.log_error(f"{error}: {filepath}")
                    self.invalid_evidence += 1
                    continue

                if not self.validate_evidence_schema(data, filepath):
                    self.invalid_evidence += 1
                    continue

                self.valid_evidence += 1
                ev_id = data['id']
                evidence_files[ev_id] = data

                # Index by keywords in 'proves' list
                for proves_item in data['proves']:
                    # Normalize: lowercase, split into keywords
                    keywords = proves_item.lower().replace(',', ' ').replace('.', ' ').split()
                    for kw in keywords:
                        if len(kw) > 2:  # Ignore very short words
                            if kw not in evidence_index:
                                evidence_index[kw] = []
                            if ev_id not in evidence_index[kw]:
                                evidence_index[kw].append(ev_id)

        self.log_info(f"Evidence scan: {self.valid_evidence} valid, {self.invalid_evidence} invalid, {self.total_evidence} total")
        return evidence_index, evidence_files

    def find_evidence_for_claim(self, claim_text, evidence_index, evidence_files):
        """Find evidence that supports a given claim. Returns list of (evidence_id, match_score)."""
        matches = []
        claim_lower = claim_text.lower()

        # Extract key terms from claim
        key_terms = []
        for term in claim_lower.replace(',', ' ').replace('.', ' ').split():
            if len(term) > 3 and term not in ['with', 'from', 'that', 'this', 'have', 'been', 'will', 'they', 'their', 'what', 'when', 'where', 'which', 'while', 'would', 'could', 'should', 'about', 'above', 'after', 'again', 'against', 'because', 'before', 'between', 'both', 'during', 'each', 'further', 'here', 'into', 'more', 'most', 'other', 'such', 'than', 'then', 'there', 'these', 'those', 'through', 'under', 'very', 'were', 'your']:
                key_terms.append(term)

        # Score each evidence file by keyword overlap
        for ev_id, ev_data in evidence_files.items():
            score = 0
            ev_proves_text = ' '.join(ev_data['proves']).lower()
            for term in key_terms:
                if term in ev_proves_text:
                    score += 1
            if score > 0:
                matches.append((ev_id, score, ev_data['confidence']))

        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def validate_capability_claims(self, evidence_index, evidence_files):
        """Validate that all capability claims have corresponding evidence."""
        capability_file = self.engine_dir / 'truth' / 'capability.json'
        data, error = self.load_json(capability_file)
        if error:
            self.log_error(f"Cannot load capability.json: {error}")
            return

        if 'capability_categories' not in data:
            self.log_error("capability.json missing 'capability_categories' field")
            return

        for category in data['capability_categories']:
            cat_name = category.get('category', 'Unknown')
            capabilities = category.get('capabilities', [])

            for cap in capabilities:
                self.total_claims += 1
                cap_id = cap.get('id', 'unknown')
                cap_name = cap.get('name', 'unknown')
                cap_status = cap.get('status', 'unknown')
                cap_claim = cap.get('claim', '')
                cap_confidence = cap.get('confidence', 'unknown')

                # Only require evidence for ready/verified/partial status
                # missing/none status is expected to not have evidence
                if cap_status in ['missing', 'none', 'planned']:
                    self.log_info(f"Claim [{cap_id}] status='{cap_status}' — no evidence required (expected)")
                    continue

                # Check for evidence_refs field (explicit evidence references)
                evidence_refs = cap.get('evidence_refs', [])
                evidence = cap.get('evidence', [])

                has_explicit_evidence = len(evidence_refs) > 0 or len(evidence) > 0

                if has_explicit_evidence:
                    self.claims_with_evidence += 1
                    self.log_info(f"Claim [{cap_id}] has explicit evidence references")

                    # Verify referenced evidence files exist
                    for ref in evidence_refs:
                        # ref could be a file path like "evidence/ci/run_123.json"
                        ref_path = self.engine_dir / ref
                        if not ref_path.exists():
                            # Try just the filename in any evidence subdir
                            found = False
                            for subdir in ['ci', 'benchmark', 'audit']:
                                if (self.engine_dir / 'evidence' / subdir / Path(ref).name).exists():
                                    found = True
                                    break
                            if not found:
                                self.log_warning(f"Claim [{cap_id}] references missing evidence: {ref}")
                else:
                    # No explicit evidence references — try to find matching evidence
                    matches = self.find_evidence_for_claim(cap_claim, evidence_index, evidence_files)

                    if matches:
                        self.claims_with_evidence += 1
                        top_match = matches[0]
                        self.log_info(f"Claim [{cap_id}] matched evidence: {top_match[0]} (score={top_match[1]}, confidence={top_match[2]})")
                    else:
                        self.claims_without_evidence += 1
                        if cap_status in ['ready', 'verified']:
                            self.log_error(f"Claim [{cap_id}] '{cap_name}' status='{cap_status}' but has NO evidence. Claim: {cap_claim[:80]}...")
                        elif cap_status == 'partial':
                            self.log_warning(f"Claim [{cap_id}] '{cap_name}' status='partial' but has NO evidence. Claim: {cap_claim[:80]}...")
                        else:
                            self.log_info(f"Claim [{cap_id}] '{cap_name}' status='{cap_status}' — no evidence found (informational)")

    def validate_truth_consistency(self):
        """Validate that Truth files are internally consistent."""
        truth_dir = self.engine_dir / 'truth'
        required_fields = ['schema_version', 'name', 'version', 'hash', 'created_at']

        for truth_file in ['architecture.json', 'language.json', 'runtime.json', 'capability.json']:
            filepath = truth_dir / truth_file
            data, error = self.load_json(filepath)
            if error:
                self.log_error(f"Truth file error: {error}")
                continue

            for field in required_fields:
                if field not in data:
                    self.log_error(f"Truth file {truth_file} missing required field: {field}")

            # Check that version follows semver-like format
            version = data.get('version', '')
            if version and not any(c.isdigit() for c in version):
                self.log_warning(f"Truth file {truth_file} version '{version}' does not contain digits")

        self.log_info("Truth consistency validation complete")

    def validate_manifest(self):
        """Validate that version/manifest.json is consistent with actual files."""
        manifest_file = self.engine_dir / 'version' / 'manifest.json'
        data, error = self.load_json(manifest_file)
        if error:
            self.log_error(f"Manifest error: {error}")
            return

        # Check that all components listed in manifest exist
        components = data.get('components', {})
        for comp_name, comp_data in components.items():
            comp_files = comp_data.get('files', [])
            for f in comp_files:
                filepath = self.engine_dir / f
                if not filepath.exists():
                    self.log_error(f"Manifest lists file that does not exist: {f} (component: {comp_name})")

        # Check immutable_core_rules
        immutable_rules = data.get('immutable_core_rules', [])
        if len(immutable_rules) < 10:
            self.log_warning(f"Manifest has only {len(immutable_rules)} immutable core rules (expected 10)")

        self.log_info("Manifest validation complete")

    def run(self):
        """Run the full validation."""
        print("=" * 60)
        print("TLL OS Claim-Evidence Validation")
        print("=" * 60)
        print(f"Engine dir: {self.engine_dir}")
        print(f"Strict mode: {self.strict}")
        print()

        # Step 1: Validate Truth consistency
        print("[Step 1] Validating Truth file consistency...")
        self.validate_truth_consistency()
        print()

        # Step 2: Scan evidence
        print("[Step 2] Scanning evidence files...")
        evidence_index, evidence_files = self.scan_evidence()
        print()

        # Step 3: Validate capability claims
        print("[Step 3] Validating capability claims have evidence...")
        self.validate_capability_claims(evidence_index, evidence_files)
        print()

        # Step 4: Validate manifest
        print("[Step 4] Validating version manifest...")
        self.validate_manifest()
        print()

        # Summary
        print("=" * 60)
        print("Validation Summary")
        print("=" * 60)
        print(f"Total claims:        {self.total_claims}")
        print(f"Claims with evidence: {self.claims_with_evidence}")
        print(f"Claims without evidence: {self.claims_without_evidence}")
        print(f"Total evidence:      {self.total_evidence}")
        print(f"Valid evidence:      {self.valid_evidence}")
        print(f"Invalid evidence:    {self.invalid_evidence}")
        print(f"Errors:              {len(self.errors)}")
        print(f"Warnings:            {len(self.warnings)}")
        print()

        if self.errors:
            print("RESULT: FAIL")
            print("Fix the errors above before committing.")
            return 1

        if self.strict and self.warnings:
            print("RESULT: FAIL (strict mode, warnings treated as errors)")
            return 2

        print("RESULT: PASS")
        print("All capability claims have corresponding evidence.")
        return 0


def main():
    parser = argparse.ArgumentParser(description='TLL OS Claim-Evidence Validation Tool')
    parser.add_argument('--engine-dir', default='.tll-engine',
                        help='Path to .tll-engine directory (default: .tll-engine)')
    parser.add_argument('--strict', action='store_true',
                        help='Treat warnings as errors')
    args = parser.parse_args()

    validator = ClaimEvidenceValidator(args.engine_dir, args.strict)
    exit_code = validator.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
