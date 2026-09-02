# RFC 8032 Test 1 reference values
$seedHex = "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
$seedBytes = [byte[]]::new(32)
for ($i = 0; $i -lt 32; $i++) {
    $seedBytes[$i] = [Convert]::ToByte($seedHex.Substring($i*2, 2), 16)
}

Write-Host "seed[0..3]: $($seedBytes[0]) $($seedBytes[1]) $($seedBytes[2]) $($seedBytes[3])"
Write-Host "seed[31]: $($seedBytes[31])"

# SHA-512(seed)
$sha512 = [System.Security.Cryptography.SHA512]::Create()
$h = $sha512.ComputeHash($seedBytes)
$hHex = [BitConverter]::ToString($h) -replace '-',''
Write-Host ""
Write-Host "SHA-512(seed) = $hHex"
Write-Host "h[0..7]: $($h[0]) $($h[1]) $($h[2]) $($h[3]) $($h[4]) $($h[5]) $($h[6]) $($h[7])"

# a = clamp(h[0:32])
$aBytes = [byte[]]::new(32)
[Array]::Copy($h, 0, $aBytes, 0, 32)
$aBytes[0] = $aBytes[0] -band 0xF8
$aBytes[31] = $aBytes[31] -band 0x7F
$aBytes[31] = $aBytes[31] -bor 0x40
$aHex = [BitConverter]::ToString($aBytes) -replace '-',''
Write-Host ""
Write-Host "a (clamped) = $aHex"
Write-Host "a[0]: $($aBytes[0]) (expected h[0] & 0xF8)"
Write-Host "a[31]: $($aBytes[31])"

# prefix = h[32:64]
$prefix = [byte[]]::new(32)
[Array]::Copy($h, 32, $prefix, 0, 32)
$prefixHex = [BitConverter]::ToString($prefix) -replace '-',''
Write-Host ""
Write-Host "prefix = $prefixHex"
Write-Host "prefix[0]: $($prefix[0])"

# rHash = SHA-512(prefix + empty message) = SHA-512(prefix)
$rHash = $sha512.ComputeHash($prefix)
$rHashHex = [BitConverter]::ToString($rHash) -replace '-',''
Write-Host ""
Write-Host "rHash = SHA-512(prefix) = $rHashHex"
Write-Host "rHash[0]: $($rHash[0])"

# public key (from RFC)
$pubKeyHex = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
$pubKey = [byte[]]::new(32)
for ($i = 0; $i -lt 32; $i++) {
    $pubKey[$i] = [Convert]::ToByte($pubKeyHex.Substring($i*2, 2), 16)
}

# Expected R (first 32 bytes of signature)
$expectedSigHex = "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
$expectedR = [byte[]]::new(32)
for ($i = 0; $i -lt 32; $i++) {
    $expectedR[$i] = [Convert]::ToByte($expectedSigHex.Substring($i*2, 2), 16)
}
$expectedRHex = [BitConverter]::ToString($expectedR) -replace '-',''
Write-Host ""
Write-Host "Expected R = $expectedRHex"
Write-Host "Expected R[0]: $($expectedR[0])"

# kHash = SHA-512(R + pubKey + empty message) = SHA-512(R + pubKey)
$kInput = [byte[]]::new(64)
[Array]::Copy($expectedR, 0, $kInput, 0, 32)
[Array]::Copy($pubKey, 0, $kInput, 32, 32)
$kHash = $sha512.ComputeHash($kInput)
$kHashHex = [BitConverter]::ToString($kHash) -replace '-',''
Write-Host ""
Write-Host "kHash = SHA-512(R + pubKey) = $kHashHex"
Write-Host "kHash[0]: $($kHash[0])"

# Expected S (last 32 bytes of signature)
$expectedS = [byte[]]::new(32)
for ($i = 0; $i -lt 32; $i++) {
    $expectedS[$i] = [Convert]::ToByte($expectedSigHex.Substring(64 + $i*2, 2), 16)
}
$expectedSHex = [BitConverter]::ToString($expectedS) -replace '-',''
Write-Host ""
Write-Host "Expected S = $expectedSHex"
Write-Host "Expected S[0]: $($expectedS[0])"
