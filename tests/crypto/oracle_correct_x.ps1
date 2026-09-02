# Compute correct Ed25519 base point x from y and d
Add-Type -AssemblyName System.Numerics

$p = [System.Numerics.BigInteger]::Pow(2, 255) - 19

# y = 4/5 mod p
$y = (4 * [System.Numerics.BigInteger]::ModPow(5, $p - 2, $p)) % $p
Write-Host "y = $y"
$yBytes = $y.ToByteArray()
if ($yBytes.Length -lt 32) { $yBytes = $yBytes + @(0) * (32 - $yBytes.Length) }
Write-Host "y (LE hex): $(($yBytes | ForEach-Object { $_.ToString('x2') }) -join '')"

# d = -121665/121666 mod p
$d = ((-121665) * [System.Numerics.BigInteger]::ModPow(121666, $p - 2, $p)) % $p
if ($d -lt 0) { $d += $p }
Write-Host "d = $d"
$dBytes = $d.ToByteArray()
if ($dBytes.Length -lt 32) { $dBytes = $dBytes + @(0) * (32 - $dBytes.Length) }
Write-Host "d (LE hex): $(($dBytes | ForEach-Object { $_.ToString('x2') }) -join '')"

# Verify 5*y == 4
Write-Host "5*y mod p = $((5 * $y) % $p) (expected 4)"

# Verify 121666*d + 121665 == 0
Write-Host "121666*d + 121665 mod p = $(((121666 * $d + 121665) % $p + $p) % $p) (expected 0)"

# Compute x^2 = (y^2 - 1) / (1 + d*y^2) mod p
$y2 = ($y * $y) % $p
$y2minus1 = ($y2 - 1) % $p
if ($y2minus1 -lt 0) { $y2minus1 += $p }
$dy2 = ($d * $y2) % $p
$onePlusdy2 = (1 + $dy2) % $p
$invOnePlusdy2 = [System.Numerics.BigInteger]::ModPow($onePlusdy2, $p - 2, $p)
$x2 = ($y2minus1 * $invOnePlusdy2) % $p

Write-Host ""
Write-Host "x^2 = (y^2-1)/(1+d*y^2) mod p"
Write-Host "x^2 = $x2"
$x2Bytes = $x2.ToByteArray()
if ($x2Bytes.Length -lt 32) { $x2Bytes = $x2Bytes + @(0) * (32 - $x2Bytes.Length) }
elseif ($x2Bytes.Length -gt 32) { $x2Bytes = $x2Bytes[0..31] }
Write-Host "x^2 (LE hex): $(($x2Bytes | ForEach-Object { $_.ToString('x2') }) -join '')"

# Compute x = sqrt(x^2) mod p
# For Ed25519, sqrt can be computed via x = x2^((p+3)/8) then adjust
$exp = ($p + 3) / 8
$x = [System.Numerics.BigInteger]::ModPow($x2, $exp, $p)

# Check if x^2 == x2, if not multiply by sqrt(-1)
$xCheck = ($x * $x) % $p
if ($xCheck -ne $x2) {
    # sqrt(-1) = 2^((p-1)/4) mod p
    $sqrtMinus1 = [System.Numerics.BigInteger]::ModPow(2, ($p - 1) / 4, $p)
    $x = ($x * $sqrtMinus1) % $p
}

# Choose positive x (even? Ed25519 chooses x with even sign bit)
# Ed25519 convention: x is positive means x mod 2 == 0? Actually sign bit is x & 1
# RFC 8032: "x is the positive square root" - positive means x < p/2
if ($x -gt $p / 2) { $x = $p - $x }

Write-Host ""
Write-Host "x = sqrt(x^2) mod p (positive root)"
Write-Host "x = $x"
$xBytes = $x.ToByteArray()
if ($xBytes.Length -lt 32) { $xBytes = $xBytes + @(0) * (32 - $xBytes.Length) }
elseif ($xBytes.Length -gt 32) { $xBytes = $xBytes[0..31] }
Write-Host "x (LE hex): $(($xBytes | ForEach-Object { $_.ToString('x2') }) -join '')"
Write-Host "x (LE decimal): $(($xBytes | ForEach-Object { $_.ToString() }) -join ',')"

# Verify curve equation with computed x
$lhs = (-$x2 + $y2) % $p
if ($lhs -lt 0) { $lhs += $p }
$rhs = (1 + $d * $x2 * $y2) % $p
Write-Host ""
Write-Host "Curve equation with computed x:"
Write-Host "lhs = $lhs"
Write-Host "rhs = $rhs"
Write-Host "lhs == rhs: $($lhs -eq $rhs)"

# Compare with hardcoded x
$hardcodedXBytes = @(
    0xD5, 0x25, 0x8F, 0x60, 0x2D, 0x56, 0xC9, 0xB2,
    0x7B, 0x5A, 0x52, 0x09, 0x76, 0xCC, 0x92, 0xC6,
    0xC5, 0xDC, 0xD6, 0xFD, 0x31, 0xE2, 0xA4, 0xC0,
    0xFE, 0x53, 0x6E, 0xCD, 0xD3, 0x36, 0x69, 0x21
)
$hardcodedX = [System.Numerics.BigInteger]::new($hardcodedXBytes + @(0))
Write-Host ""
Write-Host "Hardcoded x = $hardcodedX"
Write-Host "Computed  x = $x"
Write-Host "Match: $($hardcodedX -eq $x)"
