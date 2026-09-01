#!/usr/bin/env python3
"""
TLL OS Engineering Cognition Query Engine
Part of P0-16.2 TLL Engineering Cognition Query API.

Provides 8 core queries that let any Agent understand the TLL engineering world
without reading 500+ Markdown files. All data comes from .tll-engine/ — the
machine-readable engineering truth layer.

Usage:
    python3 scripts/query-engine.py what <id>
    python3 scripts/query-engine.py why <id>
    python3 scripts/query-engine.py depends <id> [--direction forward|backward|both]
    python3 scripts/query-engine.py proves <id>
    python3 scripts/query-engine.py constrains <id>
    python3 scripts/query-engine.py changed <id>
    python3 scripts/query-engine.py safely-change <id>
    python3 scripts/query-engine.py must-verify <id>
    python3 scripts/query-engine.py list [nodes|capabilities|decisions|evidence]

Output formats: --format json (default) | text
Engine directory: --engine-dir .tll-engine (default)
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime


class EngineeringCognitionEngine:
    def __init__(self, engine_dir):
        self.engine_dir = Path(engine_dir).resolve()
        self._cache = {}

    def _load_json(self, rel_path):
        """Load and cache a JSON file from .tll-engine/."""
        if rel_path in self._cache:
            return self._cache[rel_path]
        filepath = self.engine_dir / rel_path
        if not filepath.exists():
            return None
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._cache[rel_path] = data
            return data
        except Exception:
            return None

    def _load_all_evidence(self):
        """Load all evidence files from evidence/ subdirectories."""
        evidence = []
        evidence_dir = self.engine_dir / 'evidence'
        if not evidence_dir.exists():
            return evidence
        for subdir in ['ci', 'benchmark', 'audit']:
            subdir_path = evidence_dir / subdir
            if not subdir_path.exists():
                continue
            for filepath in subdir_path.glob('*.json'):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    data['_source_file'] = str(filepath.relative_to(self.engine_dir))
                    evidence.append(data)
                except Exception:
                    pass
        return evidence

    def _load_audit_logs(self):
        """Load all audit logs from audit/ directory."""
        logs = []
        audit_dir = self.engine_dir / 'audit'
        if not audit_dir.exists():
            return logs
        for filepath in sorted(audit_dir.glob('audit-*.json')):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logs.append(data)
            except Exception:
                pass
        return logs

    def _find_node(self, node_id):
        """Find a node in cognition graph by ID (exact or partial match)."""
        graph = self._load_json('cognition/graph.json')
        if not graph or 'nodes' not in graph:
            return None
        # Exact match first
        for node in graph['nodes']:
            if node['id'] == node_id:
                return node
        # Partial match (contains)
        for node in graph['nodes']:
            if node_id.lower() in node['id'].lower() or node_id.lower() in node.get('name', '').lower():
                return node
        return None

    def _find_capability(self, cap_id):
        """Find a capability by ID (exact or partial match)."""
        caps = self._load_json('truth/capability.json')
        if not caps or 'capability_categories' not in caps:
            return None
        for category in caps['capability_categories']:
            for cap in category.get('capabilities', []):
                if cap['id'] == cap_id:
                    return {**cap, '_category': category.get('category')}
        for category in caps['capability_categories']:
            for cap in category.get('capabilities', []):
                if cap_id.lower() in cap['id'].lower() or cap_id.lower() in cap.get('name', '').lower():
                    return {**cap, '_category': category.get('category')}
        return None

    def _get_edges_for_node(self, node_id, direction='both'):
        """Get edges connected to a node."""
        graph = self._load_json('cognition/graph.json')
        if not graph or 'edges' not in graph:
            return []
        edges = []
        for edge in graph['edges']:
            if direction in ('forward', 'both') and edge['from'] == node_id:
                edges.append(edge)
            if direction in ('backward', 'both') and edge['to'] == node_id:
                edges.append(edge)
        return edges

    # ============================================================
    # Query 1: WHAT — definition of a node/capability/module
    # ============================================================
    def query_what(self, identifier):
        """What is this? Returns definition, type, status, confidence."""
        result = {
            'query': 'what',
            'identifier': identifier,
            'found': False,
            'results': []
        }

        # Search in cognition graph nodes
        node = self._find_node(identifier)
        if node:
            result['found'] = True
            result['results'].append({
                'source': 'cognition_graph',
                'id': node['id'],
                'type': node.get('type'),
                'name': node.get('name'),
                'description': node.get('description'),
                'status': node.get('status'),
                'confidence': node.get('confidence'),
                'last_verified': node.get('last_verified')
            })

        # Search in capabilities
        cap = self._find_capability(identifier)
        if cap:
            result['found'] = True
            result['results'].append({
                'source': 'capability_truth',
                'id': cap['id'],
                'category': cap.get('_category'),
                'name': cap.get('name'),
                'claim': cap.get('claim'),
                'status': cap.get('status'),
                'confidence': cap.get('confidence'),
                'last_verified': cap.get('last_verified')
            })

        # Search in runtime components
        runtime = self._load_json('truth/runtime.json')
        if runtime and 'runtime_components' in runtime:
            for comp in runtime['runtime_components']:
                if identifier.lower() in comp.get('name', '').lower() or identifier.lower() in comp.get('id', '').lower():
                    result['found'] = True
                    result['results'].append({
                        'source': 'runtime_truth',
                        'id': comp.get('id'),
                        'name': comp.get('name'),
                        'description': comp.get('description'),
                        'status': comp.get('status')
                    })

        # Search in language features
        language = self._load_json('truth/language.json')
        if language and 'language_features' in language:
            for feat in language['language_features']:
                if identifier.lower() in feat.get('name', '').lower() or identifier.lower() in feat.get('id', '').lower():
                    result['found'] = True
                    result['results'].append({
                        'source': 'language_truth',
                        'id': feat.get('id'),
                        'name': feat.get('name'),
                        'description': feat.get('description'),
                        'status': feat.get('status')
                    })

        if not result['found']:
            result['message'] = f"No entity found matching '{identifier}'. Try 'list nodes' or 'list capabilities'."

        return result

    # ============================================================
    # Query 2: WHY — design motivation and historical decisions
    # ============================================================
    def query_why(self, identifier):
        """Why does this exist? Returns design rationale, decisions, context."""
        result = {
            'query': 'why',
            'identifier': identifier,
            'found': False,
            'decisions': [],
            'architecture_principles': [],
            'rationale': []
        }

        # Search in decisions log
        decisions = self._load_json('cognition/decisions.json')
        if decisions and 'decisions' in decisions:
            for dec in decisions['decisions']:
                text = json.dumps(dec, ensure_ascii=False).lower()
                if identifier.lower() in text:
                    result['found'] = True
                    result['decisions'].append({
                        'id': dec.get('id'),
                        'title': dec.get('title'),
                        'date': dec.get('date'),
                        'status': dec.get('status'),
                        'context': dec.get('context'),
                        'decision': dec.get('decision'),
                        'rationale': dec.get('rationale'),
                        'alternatives_considered': dec.get('alternatives_considered'),
                        'impact': dec.get('impact')
                    })

        # Search in architecture key principles
        arch = self._load_json('truth/architecture.json')
        if arch and 'key_principles' in arch:
            for principle in arch['key_principles']:
                text = json.dumps(principle, ensure_ascii=False).lower()
                if identifier.lower() in text:
                    result['found'] = True
                    result['architecture_principles'].append(principle)

        # Search in node description for rationale hints
        node = self._find_node(identifier)
        if node and node.get('description'):
            result['found'] = True
            result['rationale'].append({
                'source': 'node_description',
                'node_id': node['id'],
                'description': node['description']
            })

        if not result['found']:
            result['message'] = f"No design rationale found for '{identifier}'. Try 'list decisions'."

        return result

    # ============================================================
    # Query 3: DEPENDS — dependency graph and impact scope
    # ============================================================
    def query_depends(self, identifier, direction='both'):
        """What depends on this / what does this depend on? Returns dependency graph."""
        result = {
            'query': 'depends',
            'identifier': identifier,
            'direction': direction,
            'found': False,
            'forward_dependencies': [],   # this -> depends_on
            'backward_dependencies': [],  # depends_on -> this
            'module_dependencies': [],
            'test_dependencies': [],
            'capability_dependencies': []
        }

        # Get graph edges
        node = self._find_node(identifier)
        if node:
            result['found'] = True
            node_id = node['id']

            forward_edges = self._get_edges_for_node(node_id, 'forward')
            backward_edges = self._get_edges_for_node(node_id, 'backward')

            for edge in forward_edges:
                target = self._find_node(edge['to'])
                result['forward_dependencies'].append({
                    'edge_type': edge.get('type'),
                    'weight': edge.get('weight'),
                    'target_id': edge['to'],
                    'target_name': target.get('name') if target else edge['to']
                })

            for edge in backward_edges:
                source = self._find_node(edge['from'])
                result['backward_dependencies'].append({
                    'edge_type': edge.get('type'),
                    'weight': edge.get('weight'),
                    'source_id': edge['from'],
                    'source_name': source.get('name') if source else edge['from']
                })

        # Get module dependencies from dependency.json
        deps = self._load_json('cognition/dependency.json')
        if deps:
            if 'module_dependencies' in deps:
                for mod_dep in deps['module_dependencies']:
                    text = json.dumps(mod_dep, ensure_ascii=False).lower()
                    if identifier.lower() in text:
                        result['found'] = True
                        result['module_dependencies'].append(mod_dep)

            if 'test_dependencies' in deps:
                for test_dep in deps['test_dependencies']:
                    text = json.dumps(test_dep, ensure_ascii=False).lower()
                    if identifier.lower() in text:
                        result['found'] = True
                        result['test_dependencies'].append(test_dep)

            if 'capability_dependencies' in deps:
                for cap_dep in deps['capability_dependencies']:
                    text = json.dumps(cap_dep, ensure_ascii=False).lower()
                    if identifier.lower() in text:
                        result['found'] = True
                        result['capability_dependencies'].append(cap_dep)

        if not result['found']:
            result['message'] = f"No dependencies found for '{identifier}'. Try 'list nodes'."

        return result

    # ============================================================
    # Query 4: PROVES — evidence, CI runs, tests
    # ============================================================
    def query_proves(self, identifier):
        """What proves this? Returns evidence files, CI runs, test references."""
        result = {
            'query': 'proves',
            'identifier': identifier,
            'found': False,
            'capability_evidence': [],
            'evidence_files': [],
            'ci_runs': []
        }

        # Get capability's explicit evidence references
        cap = self._find_capability(identifier)
        if cap:
            result['found'] = True
            result['capability_evidence'] = {
                'capability_id': cap['id'],
                'capability_name': cap.get('name'),
                'status': cap.get('status'),
                'confidence': cap.get('confidence'),
                'evidence_refs': cap.get('evidence_refs', []),
                'evidence': cap.get('evidence', [])
            }

        # Search all evidence files for mentions
        all_evidence = self._load_all_evidence()
        for ev in all_evidence:
            text = json.dumps(ev, ensure_ascii=False).lower()
            if identifier.lower() in text:
                result['found'] = True
                result['evidence_files'].append({
                    'id': ev.get('id'),
                    'type': ev.get('evidence_type'),
                    'source_file': ev.get('_source_file'),
                    'confidence': ev.get('confidence'),
                    'proves': ev.get('proves', []),
                    'does_not_prove': ev.get('does_not_prove', []),
                    'run_id': ev.get('run_id'),
                    'commit_sha': ev.get('commit_sha'),
                    'platform': ev.get('platform')
                })
                if ev.get('run_id'):
                    result['ci_runs'].append({
                        'run_id': ev.get('run_id'),
                        'commit_sha': ev.get('commit_sha'),
                        'platform': ev.get('platform'),
                        'status': ev.get('conclusion'),
                        'run_url': ev.get('run_url')
                    })

        if not result['found']:
            result['message'] = f"No evidence found for '{identifier}'. Try 'list evidence'."

        return result

    # ============================================================
    # Query 5: CONSTRAINS — invariants, protocol rules, boundaries
    # ============================================================
    def query_constrains(self, identifier):
        """What constrains this? Returns invariants, protocol rules, boundaries."""
        result = {
            'query': 'constrains',
            'identifier': identifier,
            'found': False,
            'runtime_invariants': [],
            'immutable_core_rules': [],
            'protocol_rules': [],
            'known_limitations': [],
            'scope_model': None
        }

        # Runtime invariants
        runtime = self._load_json('truth/runtime.json')
        if runtime and 'runtime_invariants' in runtime:
            for inv in runtime['runtime_invariants']:
                text = json.dumps(inv, ensure_ascii=False).lower()
                if identifier.lower() in text:
                    result['found'] = True
                    result['runtime_invariants'].append(inv)

        # Immutable core rules from manifest
        manifest = self._load_json('version/manifest.json')
        if manifest and 'immutable_core_rules' in manifest:
            for rule in manifest['immutable_core_rules']:
                text = json.dumps(rule, ensure_ascii=False).lower()
                if identifier.lower() in text:
                    result['found'] = True
                    result['immutable_core_rules'].append(rule)

        # Protocol rules (forbidden behaviors)
        dev_protocol = self._load_json('protocol/development.yaml')
        if dev_protocol:
            # YAML is not natively JSON, but we stored it as structured data
            # Search in the raw text
            try:
                protocol_text = json.dumps(dev_protocol, ensure_ascii=False).lower()
                if identifier.lower() in protocol_text:
                    result['found'] = True
                    result['protocol_rules'].append({'source': 'development.yaml', 'matched': True})
            except Exception:
                pass

        # Known limitations
        if manifest and 'known_limitations' in manifest:
            for lim in manifest['known_limitations']:
                text = json.dumps(lim, ensure_ascii=False).lower()
                if identifier.lower() in text:
                    result['found'] = True
                    result['known_limitations'].append(lim)

        language = self._load_json('truth/language.json')
        if language and 'known_limitations' in language:
            for lim in language['known_limitations']:
                text = json.dumps(lim, ensure_ascii=False).lower()
                if identifier.lower() in text:
                    result['found'] = True
                    result['known_limitations'].append(lim)

        # Scope model (for scope-related queries)
        if 'scope' in identifier.lower() or 'variable' in identifier.lower() or 'shadow' in identifier.lower():
            if language and 'scope_model' in language:
                result['found'] = True
                result['scope_model'] = language['scope_model']

        if not result['found']:
            result['message'] = f"No constraints found for '{identifier}'."

        return result

    # ============================================================
    # Query 6: CHANGED — history of modifications, audit logs
    # ============================================================
    def query_changed(self, identifier):
        """What changed this? Returns audit logs, decision history, version chain."""
        result = {
            'query': 'changed',
            'identifier': identifier,
            'found': False,
            'audit_logs': [],
            'decisions': [],
            'version_chain': []
        }

        # Audit logs
        audit_logs = self._load_audit_logs()
        for log in audit_logs:
            text = json.dumps(log, ensure_ascii=False).lower()
            if identifier.lower() in text:
                result['found'] = True
                result['audit_logs'].append({
                    'audit_id': log.get('audit_id'),
                    'timestamp': log.get('timestamp'),
                    'agent_id': log.get('agent_id'),
                    'agent_name': log.get('agent_name'),
                    'operation_type': log.get('operation_type'),
                    'phase': log.get('phase'),
                    'title': log.get('title'),
                    'commit_sha': log.get('commit_sha'),
                    'files_modified_count': len(log.get('files_modified', [])),
                    'claims_made': log.get('claims_made', []),
                    'known_limitations': log.get('known_limitations', [])
                })

        # Decisions that mention the identifier
        decisions = self._load_json('cognition/decisions.json')
        if decisions and 'decisions' in decisions:
            for dec in decisions['decisions']:
                text = json.dumps(dec, ensure_ascii=False).lower()
                if identifier.lower() in text:
                    result['found'] = True
                    result['decisions'].append({
                        'id': dec.get('id'),
                        'title': dec.get('title'),
                        'date': dec.get('date'),
                        'status': dec.get('status'),
                        'decision': dec.get('decision')
                    })

        # Version chain
        manifest = self._load_json('version/manifest.json')
        if manifest and 'version_chain' in manifest:
            result['version_chain'] = manifest['version_chain']

        if not result['found']:
            result['message'] = f"No change history found for '{identifier}'. Try 'list decisions'."

        return result

    # ============================================================
    # Query 7: SAFELY-CHANGE — modification boundaries and risk
    # ============================================================
    def query_safely_change(self, identifier):
        """What can I safely change? Returns modification boundaries, risk assessment."""
        result = {
            'query': 'safely-change',
            'identifier': identifier,
            'found': False,
            'entity': None,
            'risk_level': 'unknown',
            'safe_to_change': [],
            'requires_care': [],
            'do_not_change': [],
            'impact_scope': {},
            'related_bugs': []
        }

        # Get entity info
        node = self._find_node(identifier)
        cap = self._find_capability(identifier)

        if node:
            result['found'] = True
            result['entity'] = {'type': 'node', 'id': node['id'], 'name': node.get('name')}
        elif cap:
            result['found'] = True
            result['entity'] = {'type': 'capability', 'id': cap['id'], 'name': cap.get('name')}

        if not result['found']:
            result['message'] = f"No entity found matching '{identifier}'. Try 'list nodes'."
            return result

        # Get dependencies to assess impact
        deps = self.query_depends(identifier)
        result['impact_scope'] = {
            'forward_dependencies_count': len(deps.get('forward_dependencies', [])),
            'backward_dependencies_count': len(deps.get('backward_dependencies', [])),
            'module_dependencies_count': len(deps.get('module_dependencies', [])),
            'test_dependencies_count': len(deps.get('test_dependencies', []))
        }

        # Risk assessment based on entity type and dependencies
        entity_id = (node or cap)['id']
        total_deps = (result['impact_scope']['forward_dependencies_count'] +
                      result['impact_scope']['backward_dependencies_count'])

        if 'compiler' in entity_id.lower() or 'vm' in entity_id.lower() or 'runtime' in entity_id.lower():
            result['risk_level'] = 'high'
            result['do_not_change'] = [
                'Core VM opcode semantics (requires full regression)',
                'ABI contracts (breaks binary compatibility)',
                'Garbage collection / memory management (requires ASAN)',
                'Coroutine scheduler (requires 100K stress test)'
            ]
            result['requires_care'] = [
                'Any change requires full test suite + blockchain network tests',
                'Must run scope tests (95 assertions) to verify variable resolution',
                'Must run 100K coroutine stress test',
                'Must run 4-node blockchain network tests (15 CI gates)'
            ]
        elif 'blockchain' in entity_id.lower() or 'p2p' in entity_id.lower():
            result['risk_level'] = 'medium'
            result['requires_care'] = [
                'Must run bc_node, bc_multi, bc_sync, bc_reconnect, bc_invalid tests',
                'Must run bc_stress (120 tx high-message test)',
                'Must run fault injection tests (fi_duptx, fi_dupblock, fi_ooo, fi_kill9, fi_multi)'
            ]
        elif 'truth' in entity_id.lower() or 'protocol' in entity_id.lower() or 'cognition' in entity_id.lower():
            result['risk_level'] = 'low'
            result['safe_to_change'] = [
                'Adding new capabilities to capability.json (with evidence)',
                'Adding new nodes/edges to cognition graph',
                'Adding new decisions to decisions log',
                'Updating evidence files (auto-generated preferred)'
            ]
            result['requires_care'] = [
                'Modifying immutable_core_rules requires human approval',
                'Modifying protocol rules requires audit log entry',
                'Changing capability status requires corresponding evidence'
            ]
        else:
            result['risk_level'] = 'medium' if total_deps > 3 else 'low'

        result['safe_to_change'].extend([
            'Test files (tests/) — always safe, improves coverage',
            'Documentation (docs/) — safe',
            'CI workflow (.github/workflows/) — safe if not removing existing gates',
            'Evidence files (.tll-engine/evidence/) — safe, auto-generated preferred'
        ])

        return result

    # ============================================================
    # Query 8: MUST-VERIFY — required tests and CI gates after change
    # ============================================================
    def query_must_verify(self, identifier):
        """What must I verify after changing this? Returns required tests, CI gates."""
        result = {
            'query': 'must-verify',
            'identifier': identifier,
            'found': False,
            'entity': None,
            'required_tests': [],
            'required_ci_gates': [],
            'required_evidence': [],
            'estimated_time': 'unknown'
        }

        node = self._find_node(identifier)
        cap = self._find_capability(identifier)

        if node:
            result['found'] = True
            result['entity'] = {'type': 'node', 'id': node['id'], 'name': node.get('name')}
        elif cap:
            result['found'] = True
            result['entity'] = {'type': 'capability', 'id': cap['id'], 'name': cap.get('name')}

        if not result['found']:
            result['message'] = f"No entity found matching '{identifier}'. Try 'list nodes'."
            return result

        entity_id = (node or cap)['id']

        # Base tests always required
        base_tests = [
            {'name': 'Core test suite (28/38 tests)', 'command': 'scripts/run-tests.sh', 'platform': 'all'},
            {'name': 'Scope semantics (10 tests, 95 assertions)', 'command': 'tests/scope/scope_*.tll', 'platform': 'all'},
            {'name': '.tll-engine/ validation', 'command': 'scripts/validate-tll-engine.sh', 'platform': 'all'},
            {'name': 'Claim-Evidence matching', 'command': 'scripts/validate-claim-evidence.py', 'platform': 'all'}
        ]

        # Entity-specific tests
        if 'compiler' in entity_id.lower() or 'codegen' in entity_id.lower():
            result['required_tests'] = base_tests + [
                {'name': 'Self-host bootstrap', 'command': 'compiler/compiler.tllbc', 'platform': 'all'},
                {'name': 'ABI consistency', 'command': 'scripts/check-abi.sh', 'platform': 'all'},
                {'name': 'End-to-end tllc compile+run', 'command': 'tllc compile hello.tll', 'platform': 'all'}
            ]
            result['required_ci_gates'] = ['native-build-test (all 3 platforms)']
            result['estimated_time'] = '10-15 minutes'
        elif 'vm' in entity_id.lower() or 'runtime' in entity_id.lower() or 'coroutine' in entity_id.lower():
            result['required_tests'] = base_tests + [
                {'name': '100K Coroutine Stress', 'command': 'tests/coroutine_stress_test.tll', 'platform': 'all'},
                {'name': 'TCP FD Boundary (64 limit)', 'command': 'tests/tcp_fd_boundary.tll', 'platform': 'all'},
                {'name': '4-Node Blockchain Network (5 tests)', 'command': 'scripts/run-bc-network-test.sh', 'platform': 'all'},
                {'name': 'Blockchain High-Message Stress (120 tx)', 'command': 'bc_stress', 'platform': 'all'}
            ]
            result['required_ci_gates'] = ['native-build-test (all 3 platforms)', 'Coroutine 100K Stress', 'TCP FD Boundary']
            result['estimated_time'] = '15-20 minutes'
        elif 'blockchain' in entity_id.lower() or 'p2p' in entity_id.lower() or 'mempool' in entity_id.lower():
            result['required_tests'] = base_tests + [
                {'name': 'Blockchain basic unit test', 'command': 'tests/blockchain_basic.tll', 'platform': 'all'},
                {'name': '4-Node Network (bc_node)', 'command': 'bc_node', 'platform': 'all'},
                {'name': '5-Block Multi-Node Sync (bc_multi)', 'command': 'bc_multi', 'platform': 'all'},
                {'name': 'Auto-Sync (bc_sync)', 'command': 'bc_sync', 'platform': 'all'},
                {'name': 'Reconnect + Auto-Sync (bc_reconnect)', 'command': 'bc_reconnect', 'platform': 'all'},
                {'name': 'Invalid Block + Fork Detection (bc_invalid)', 'command': 'bc_invalid', 'platform': 'all'},
                {'name': 'High-Message Stress (bc_stress, 120 tx)', 'command': 'bc_stress', 'platform': 'all'},
                {'name': 'Fault Injection (5 tests)', 'command': 'fi_duptx, fi_dupblock, fi_ooo, fi_kill9, fi_multi', 'platform': 'all'}
            ]
            result['required_ci_gates'] = ['native-build-test (all 3 platforms)', 'Blockchain Network (15 gates)', 'Fault Injection (15 gates)']
            result['estimated_time'] = '20-30 minutes'
        elif 'truth' in entity_id.lower() or 'protocol' in entity_id.lower() or 'cognition' in entity_id.lower():
            result['required_tests'] = base_tests
            result['required_ci_gates'] = ['.tll-engine/ validation', 'Claim-Evidence matching']
            result['estimated_time'] = '2-5 minutes'
        else:
            result['required_tests'] = base_tests
            result['required_ci_gates'] = ['native-build-test (all 3 platforms)']
            result['estimated_time'] = '5-10 minutes'

        # Required evidence after change
        result['required_evidence'] = [
            {'type': 'ci_run', 'description': 'GitHub Actions Run ID for all 3 platforms'},
            {'type': 'test_output', 'description': 'Full test output logs (saved on failure)'},
            {'type': 'audit_log', 'description': 'Agent operation audit log entry'}
        ]

        return result

    # ============================================================
    # LIST — list all entities of a given type
    # ============================================================
    def query_list(self, entity_type='all'):
        """List all nodes, capabilities, decisions, or evidence."""
        result = {
            'query': 'list',
            'entity_type': entity_type,
            'results': {}
        }

        if entity_type in ('all', 'nodes'):
            graph = self._load_json('cognition/graph.json')
            if graph and 'nodes' in graph:
                result['results']['nodes'] = [
                    {'id': n['id'], 'type': n.get('type'), 'name': n.get('name'), 'status': n.get('status')}
                    for n in graph['nodes']
                ]

        if entity_type in ('all', 'capabilities'):
            caps = self._load_json('truth/capability.json')
            if caps and 'capability_categories' in caps:
                result['results']['capabilities'] = []
                for category in caps['capability_categories']:
                    for cap in category.get('capabilities', []):
                        result['results']['capabilities'].append({
                            'id': cap['id'],
                            'category': category.get('category'),
                            'name': cap.get('name'),
                            'status': cap.get('status'),
                            'confidence': cap.get('confidence')
                        })

        if entity_type in ('all', 'decisions'):
            decisions = self._load_json('cognition/decisions.json')
            if decisions and 'decisions' in decisions:
                result['results']['decisions'] = [
                    {'id': d['id'], 'title': d.get('title'), 'date': d.get('date'), 'status': d.get('status')}
                    for d in decisions['decisions']
                ]

        if entity_type in ('all', 'evidence'):
            all_evidence = self._load_all_evidence()
            result['results']['evidence'] = [
                {'id': ev.get('id'), 'type': ev.get('evidence_type'), 'confidence': ev.get('confidence'), 'source': ev.get('_source_file')}
                for ev in all_evidence
            ]

        if entity_type in ('all', 'audit'):
            audit_logs = self._load_audit_logs()
            result['results']['audit_logs'] = [
                {'id': log.get('audit_id'), 'phase': log.get('phase'), 'title': log.get('title'), 'timestamp': log.get('timestamp')}
                for log in audit_logs
            ]

        return result


def format_text(result):
    """Format query result as human-readable text."""
    lines = []
    query = result.get('query', 'unknown')

    if query == 'list':
        for entity_type, items in result.get('results', {}).items():
            lines.append(f"\n=== {entity_type.upper()} ({len(items)}) ===")
            for item in items:
                if 'name' in item:
                    lines.append(f"  {item['id']} — {item['name']} [{item.get('status', '?')}]")
                elif 'title' in item:
                    lines.append(f"  {item['id']} — {item['title']} [{item.get('status', '?')}]")
                else:
                    lines.append(f"  {item.get('id', '?')} — {json.dumps(item, ensure_ascii=False)[:80]}")
        return '\n'.join(lines)

    if not result.get('found'):
        return f"[NOT FOUND] {result.get('message', 'No results.')}"

    lines.append(f"\n=== Query: {query} ===")
    lines.append(f"Identifier: {result.get('identifier')}")

    if query == 'what':
        for r in result.get('results', []):
            lines.append(f"\n  [{r['source']}] {r.get('id')}")
            lines.append(f"    Name: {r.get('name')}")
            lines.append(f"    Type: {r.get('type', r.get('category', '?'))}")
            lines.append(f"    Status: {r.get('status')}")
            lines.append(f"    Confidence: {r.get('confidence')}")
            if r.get('description'):
                lines.append(f"    Description: {r['description'][:120]}")
            if r.get('claim'):
                lines.append(f"    Claim: {r['claim'][:120]}")

    elif query == 'why':
        for d in result.get('decisions', []):
            lines.append(f"\n  [Decision] {d['id']} — {d['title']}")
            lines.append(f"    Date: {d.get('date')} | Status: {d.get('status')}")
            if d.get('rationale'):
                lines.append(f"    Rationale: {str(d['rationale'])[:150]}")
        for p in result.get('architecture_principles', []):
            lines.append(f"\n  [Principle] {json.dumps(p, ensure_ascii=False)[:150]}")

    elif query == 'depends':
        lines.append(f"\n  Forward dependencies (this -> depends_on): {len(result.get('forward_dependencies', []))}")
        for d in result.get('forward_dependencies', []):
            lines.append(f"    -> {d['target_id']} ({d.get('target_name')}) [{d.get('edge_type')}]")
        lines.append(f"\n  Backward dependencies (depends_on -> this): {len(result.get('backward_dependencies', []))}")
        for d in result.get('backward_dependencies', []):
            lines.append(f"    <- {d['source_id']} ({d.get('source_name')}) [{d.get('edge_type')}]")

    elif query == 'proves':
        for ev in result.get('evidence_files', []):
            lines.append(f"\n  [Evidence] {ev['id']}")
            lines.append(f"    Type: {ev.get('type')} | Confidence: {ev.get('confidence')}")
            lines.append(f"    Source: {ev.get('source_file')}")
            if ev.get('run_id'):
                lines.append(f"    CI Run: #{ev['run_id']} ({ev.get('platform')}) — {ev.get('status')}")

    elif query == 'constrains':
        for inv in result.get('runtime_invariants', []):
            lines.append(f"\n  [Invariant] {json.dumps(inv, ensure_ascii=False)[:150]}")
        for rule in result.get('immutable_core_rules', []):
            lines.append(f"\n  [Immutable Rule] {json.dumps(rule, ensure_ascii=False)[:150]}")
        for lim in result.get('known_limitations', []):
            lines.append(f"\n  [Limitation] {json.dumps(lim, ensure_ascii=False)[:150]}")

    elif query == 'changed':
        for log in result.get('audit_logs', []):
            lines.append(f"\n  [Audit] {log['audit_id']}")
            lines.append(f"    Phase: {log.get('phase')} | Title: {log.get('title')}")
            lines.append(f"    Agent: {log.get('agent_name')} | Commit: {str(log.get('commit_sha', ''))[:8]}")
            lines.append(f"    Files changed: {log.get('files_modified_count')}")

    elif query == 'safely-change':
        lines.append(f"\n  Risk level: {result.get('risk_level')}")
        lines.append(f"  Impact: {json.dumps(result.get('impact_scope', {}))}")
        if result.get('safe_to_change'):
            lines.append(f"\n  SAFE TO CHANGE:")
            for item in result['safe_to_change']:
                lines.append(f"    + {item}")
        if result.get('requires_care'):
            lines.append(f"\n  REQUIRES CARE:")
            for item in result['requires_care']:
                lines.append(f"    ! {item}")
        if result.get('do_not_change'):
            lines.append(f"\n  DO NOT CHANGE:")
            for item in result['do_not_change']:
                lines.append(f"    X {item}")

    elif query == 'must-verify':
        lines.append(f"\n  Estimated time: {result.get('estimated_time')}")
        lines.append(f"\n  REQUIRED TESTS ({len(result.get('required_tests', []))}):")
        for t in result.get('required_tests', []):
            lines.append(f"    - {t['name']} [{t.get('platform', 'all')}]")
        if result.get('required_ci_gates'):
            lines.append(f"\n  REQUIRED CI GATES:")
            for g in result['required_ci_gates']:
                lines.append(f"    - {g}")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='TLL OS Engineering Cognition Query Engine (P0-16.2)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/query-engine.py what compiler
  python3 scripts/query-engine.py why coroutine
  python3 scripts/query-engine.py depends vm --direction backward
  python3 scripts/query-engine.py proves coroutine
  python3 scripts/query-engine.py constrains scope
  python3 scripts/query-engine.py changed codegen
  python3 scripts/query-engine.py safely-change compiler
  python3 scripts/query-engine.py must-verify blockchain
  python3 scripts/query-engine.py list capabilities
        """
    )
    parser.add_argument('query', choices=['what', 'why', 'depends', 'proves', 'constrains', 'changed', 'safely-change', 'must-verify', 'list'],
                        help='Query type')
    parser.add_argument('identifier', nargs='?', default='',
                        help='Entity identifier (node ID, capability ID, or partial match)')
    parser.add_argument('--direction', choices=['forward', 'backward', 'both'], default='both',
                        help='Dependency direction (for depends query)')
    parser.add_argument('--format', choices=['json', 'text'], default='json',
                        help='Output format (default: json)')
    parser.add_argument('--engine-dir', default='.tll-engine',
                        help='Path to .tll-engine directory (default: .tll-engine)')
    args = parser.parse_args()

    engine = EngineeringCognitionEngine(args.engine_dir)

    # Dispatch query
    if args.query == 'what':
        result = engine.query_what(args.identifier)
    elif args.query == 'why':
        result = engine.query_why(args.identifier)
    elif args.query == 'depends':
        result = engine.query_depends(args.identifier, args.direction)
    elif args.query == 'proves':
        result = engine.query_proves(args.identifier)
    elif args.query == 'constrains':
        result = engine.query_constrains(args.identifier)
    elif args.query == 'changed':
        result = engine.query_changed(args.identifier)
    elif args.query == 'safely-change':
        result = engine.query_safely_change(args.identifier)
    elif args.query == 'must-verify':
        result = engine.query_must_verify(args.identifier)
    elif args.query == 'list':
        result = engine.query_list(args.identifier or 'all')
    else:
        result = {'error': f'Unknown query: {args.query}'}

    # Output
    if args.format == 'text':
        print(format_text(result))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit code: 0 if found, 1 if not found
    if not result.get('found', True) and args.query != 'list':
        sys.exit(1)


if __name__ == '__main__':
    main()
