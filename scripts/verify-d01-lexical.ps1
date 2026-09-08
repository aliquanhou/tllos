# ============================================================
# TPC-D01 Lexical Capability Verification Entry
# 可重复执行的 D01 词法能力验证入口
# Usage: scripts\verify-d01-lexical.ps1
# ============================================================
$ErrorActionPreference = "Continue"

$REPO_ROOT = Split-Path -Parent $PSScriptRoot
$HOST_C = Join-Path $REPO_ROOT "host\c"
$TLLVM = Join-Path $HOST_C "tllvm.exe"
$TLLC_BC = Join-Path $REPO_ROOT "tools\TLLC\tllc.tllbc"
$TEST_DIR = Join-Path $REPO_ROOT "tests\d01-lexical"

Write-Output "=== TPC-D01 Lexical Capability Verification ==="
Write-Output ""

# Step 1: Ensure tllvm.exe exists
if (-not (Test-Path $TLLVM)) {
    Write-Output "[1/4] tllvm.exe not found, building with MSVC..."
    $vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
    # P2-01-B.6: Shared TLL Runtime Core replaces old host/c/value.c
    $srcs = "main.c vm.c ..\..\runtime\value.c ..\..\runtime\arithmetic.c ..\..\runtime\io.c json.c builtin.c ffi_builtin.c sqlite_builtin.c crypto_builtin.c password_builtin.c hmac_builtin.c http_client_builtin.c sqlite3.c"
    $cmd = "`"$vcvars`" >nul 2>&1 && cd /d `"$HOST_C`" && cl /O2 /std:c11 /D_WIN32 /D_CRT_SECURE_NO_WARNINGS /I..\..\runtime /Fe:tllvm.exe $srcs /link winhttp.lib ws2_32.lib bcrypt.lib >nul 2>&1"
    cmd /c $cmd
    if (-not (Test-Path $TLLVM)) {
        Write-Output "ERROR: Failed to build tllvm.exe"
        exit 1
    }
    Write-Output "  tllvm.exe built successfully"
} else {
    Write-Output "[1/4] tllvm.exe already available"
}

# Step 2: Positive test - compile and run
Write-Output "[2/4] Running positive capability verification..."
$pos_tll = Join-Path $TEST_DIR "d01_positive.tll"
$pos_bc = Join-Path $TEST_DIR "d01_positive.tllbc"
$compile_out = & $TLLVM $TLLC_BC compile $pos_tll -o $pos_bc 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Output "  FAIL: positive test compile error"
    Write-Output $compile_out
    exit 1
}
$run_out = & $TLLVM $pos_bc 2>&1
if ($run_out -contains "D01-POSITIVE-ALL-PASS") {
    Write-Output "  PASS: all positive lexical capabilities verified (compile + run + assertion)"
} else {
    Write-Output "  FAIL: positive test did not pass"
    Write-Output $run_out
    exit 1
}

# Step 3: Negative tests - verify they fail as expected
Write-Output "[3/4] Running negative/missing capability verification..."
$negative_tests = @(
    @{ name="block_comment /* */"; file="d01_block_comment.tll"; expect="Lexer error|Parse error" },
    @{ name="single_quote '...'"; file="d01_single_quote.tll"; expect="Lexer error" },
    @{ name="unicode_identifier"; file="d01_unicode_ident.tll"; expect="Lexer error" },
    @{ name="unicode_escape \u"; file="d01_unicode_escape.tll"; expect="compile_ok_but_semantic_wrong" },
    @{ name="unclosed_string"; file="d01_unclosed_string.tll"; expect="Parse error|EOF" },
    @{ name="number_suffix"; file="d01_number_suffix.tll"; expect="undefined identifier" },
    @{ name="annotation @"; file="d01_annotation.tll"; expect="Parse error|AT" },
    @{ name="invalid_char $"; file="d01_invalid_char.tll"; expect="Lexer error" }
)

$neg_pass = 0
$neg_fail = 0
foreach ($t in $negative_tests) {
    $tll = Join-Path $TEST_DIR $t.file
    $bc = Join-Path $TEST_DIR ($t.file -replace '\.tll$', '.tllbc')
    $out = & $TLLVM $TLLC_BC compile $tll -o $bc 2>&1
    $combined = ($out | Out-String)
    if ($t.expect -eq "compile_ok_but_semantic_wrong") {
        # \u escape: compiles but outputs literal u
        if ($LASTEXITCODE -eq 0) {
            $run = & $TLLVM $bc 2>&1
            if ($run -contains "u4e2du6587") {
                Write-Output "  CONFIRMED MISSING: $($t.name) (compiles but \u is literal, not unicode)"
                $neg_pass++
            } else {
                Write-Output "  UNEXPECTED: $($t.name)"
                $neg_fail++
            }
        } else {
            Write-Output "  UNEXPECTED: $($t.name) (compile failed)"
            $neg_fail++
        }
    } elseif ($combined -match $t.expect) {
        Write-Output "  CONFIRMED MISSING/ERROR: $($t.name)"
        $neg_pass++
    } else {
        Write-Output "  UNEXPECTED: $($t.name) (did not match expected error)"
        $neg_fail++
    }
}

# Step 4: Summary
Write-Output ""
Write-Output "[4/4] Verification Summary"
Write-Output "  Positive capabilities: ALL PASS"
Write-Output "  Negative confirmations: $neg_pass passed, $neg_fail unexpected"
Write-Output ""
Write-Output "=== D01 Verification Complete ==="
Write-Output "Test artifacts: $TEST_DIR"
