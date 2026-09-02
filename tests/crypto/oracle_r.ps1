# Compute rHash mod L reference value
$rHashHex = "b6b19cd8e0426f5983fa112d89a143aa97dab8bc5deb8d5b6253c928b65272f4044098c2a990039cde5b6a4818df0bfb6e40dc5dee54248032962323e701352d"

# Convert to bytes (little-endian)
$rHashBytes = [byte[]]::new(64)
for ($i = 0; $i -lt 64; $i++) {
    $rHashBytes[$i] = [Convert]::ToByte($rHashHex.Substring($i*2, 2), 16)
}

# Convert to BigInteger (little-endian)
$rHash = [System.Numerics.BigInteger]::new($rHashBytes)
Write-Host "rHash (first 32 bytes as int): $($rHash % [System.Numerics.BigInteger]::Pow(2,256))"

# L = 2^252 + 27742317777372353535851937790883648493
$L = [System.Numerics.BigInteger]::Pow(2, 252) + [System.Numerics.BigInteger]::Parse("27742317777372353535851937790883648493")
Write-Host "L = $L"

# r = rHash mod L
$r = $rHash % $L
Write-Host ""
Write-Host "r = $r"

# Convert r to little-endian bytes
$rBytes = $r.ToByteArray()
# Ensure 32 bytes
if ($rBytes.Length -lt 32) {
    $padded = [byte[]]::new(32)
    [Array]::Copy($rBytes, $padded, $rBytes.Length)
    $rBytes = $padded
}
$rHex = [BitConverter]::ToString($rBytes[0..31]) -replace '-',''
Write-Host "r hex (LE): $rHex"
Write-Host "r[0]: $($rBytes[0])"

# Expected R from RFC signature (first 32 bytes)
$expectedSigHex = "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
$expectedRHex = $expectedSigHex.Substring(0, 64)
Write-Host ""
Write-Host "Expected R hex: $expectedRHex"
Write-Host "Expected R[0]: $([Convert]::ToByte($expectedRHex.Substring(0,2),16))"

# TLL r hex
$tllRhex = "0c6e1f28dfac8e62a131fa633bece8bd4682bf4dc0dad8f2b5daf4f352660503"
Write-Host ""
Write-Host "TLL r hex: $tllRhex"
Write-Host "Match: $($rHex.ToLower() -eq $tllRhex.ToLower())"
