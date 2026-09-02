# Independent Oracle: compute x*x mod p using System.Numerics.BigInteger
# p = 2^255 - 19
# x = Ed25519 base point x (little-endian bytes)

Add-Type -AssemblyName System.Numerics

# p = 2^255 - 19
$p = [System.Numerics.BigInteger]::Pow(2, 255) - 19
Write-Host "p = $p"

# x little-endian bytes (RFC 8032 base point x)
$xBytesLE = @(
    0xD5, 0x25, 0x8F, 0x60, 0x2D, 0x56, 0xC9, 0xB2,
    0x7B, 0x5A, 0x52, 0x09, 0x76, 0xCC, 0x92, 0xC6,
    0xC5, 0xDC, 0xD6, 0xFD, 0x31, 0xE2, 0xA4, 0xC0,
    0xFE, 0x53, 0x6E, 0xCD, 0xD3, 0x36, 0x69, 0x21
)

# Convert little-endian bytes to BigInteger (need to prepend 0 to ensure positive)
$xBytesLEWithZero = $xBytesLE + @(0)
$x = [System.Numerics.BigInteger]::new($xBytesLEWithZero)
Write-Host "x = $x"

# Compute x*x mod p
$x2 = ($x * $x) % $p
Write-Host "x^2 mod p = $x2"

# Convert result to little-endian 32 bytes
$x2Bytes = $x2.ToByteArray()
# Ensure exactly 32 bytes
if ($x2Bytes.Length -lt 32) {
    $x2Bytes = $x2Bytes + @(0) * (32 - $x2Bytes.Length)
} elseif ($x2Bytes.Length -gt 32) {
    $x2Bytes = $x2Bytes[0..31]
}

Write-Host ""
Write-Host "x^2 mod p (little-endian hex):"
$hex = ($x2Bytes | ForEach-Object { $_.ToString("x2") }) -join ""
Write-Host $hex

Write-Host ""
Write-Host "x^2 mod p (decimal bytes):"
($x2Bytes | ForEach-Object { $_.ToString() }) -join ","

# Also compute y for reference
$yBytesLE = @(
    0x58, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66,
    0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66,
    0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66,
    0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66
)
$yBytesLEWithZero = $yBytesLE + @(0)
$y = [System.Numerics.BigInteger]::new($yBytesLEWithZero)
$y2 = ($y * $y) % $p
Write-Host ""
Write-Host "y^2 mod p (little-endian hex):"
$y2Bytes = $y2.ToByteArray()
if ($y2Bytes.Length -lt 32) { $y2Bytes = $y2Bytes + @(0) * (32 - $y2Bytes.Length) }
elseif ($y2Bytes.Length -gt 32) { $y2Bytes = $y2Bytes[0..31] }
(($y2Bytes | ForEach-Object { $_.ToString("x2") }) -join "")

# Compute d = -121665/121666 mod p
$d = ((-121665) * [System.Numerics.BigInteger]::ModPow(121666, $p - 2, $p)) % $p
if ($d -lt 0) { $d += $p }
Write-Host ""
Write-Host "d mod p (little-endian hex):"
$dBytes = $d.ToByteArray()
if ($dBytes.Length -lt 32) { $dBytes = $dBytes + @(0) * (32 - $dBytes.Length) }
elseif ($dBytes.Length -gt 32) { $dBytes = $dBytes[0..31] }
(($dBytes | ForEach-Object { $_.ToString("x2") }) -join "")

# Verify curve equation: -x^2 + y^2 == 1 + d*x^2*y^2 mod p
$lhs = (-$x2 + $y2) % $p
if ($lhs -lt 0) { $lhs += $p }
$rhs = (1 + $d * $x2 * $y2) % $p
Write-Host ""
Write-Host "Curve equation check:"
Write-Host "lhs = -x^2 + y^2 = $lhs"
Write-Host "rhs = 1 + d*x^2*y^2 = $rhs"
Write-Host "lhs == rhs: $($lhs -eq $rhs)"
