# TLL Scalar Reduction Independent Oracle
# Uses PowerShell BigInteger - completely independent of TLL implementation
# L = 2^252 + 27742317777372353535851937790883648493

$L = [System.Numerics.BigInteger]::Parse("7237005577332262213973186563042994240857116359379907606001950938285454250989")

function Get-BytesLE {
    param([System.Numerics.BigInteger]$n, [int]$len=32)
    $bytes = $n.ToByteArray()
    if ($bytes.Length -lt $len) {
        $padded = New-Object byte[] $len
        [Array]::Copy($bytes, $padded, $bytes.Length)
        return $padded
    }
    return $bytes[0..($len-1)]
}

function Test-Reduction {
    param([string]$name, [System.Numerics.BigInteger]$input)
    $result = $input % $L
    if ($result -lt 0) { $result += $L }
    $bytes = Get-BytesLE $result
    Write-Host "[$name]"
    Write-Host "  input (decimal): $input"
    Write-Host "  result (decimal): $result"
    Write-Host "  result bytes (LE hex): $(($bytes | ForEach-Object { $_.ToString('x2') }) -join '')"
    Write-Host ""
    return $bytes
}

Write-Host "=== TLL Scalar Reduction Independent Oracle ==="
Write-Host "L = $L"
Write-Host ""

# 1. Minimal Reduction Gate
$zero = [System.Numerics.BigInteger]::Zero
$one = [System.Numerics.BigInteger]::One
$Lminus1 = $L - 1
$Lplus1 = $L + 1
$twoL = $L * 2
$twoLplus1 = $twoL + 1
$pow256 = [System.Numerics.BigInteger]::Pow(2, 256)

Test-Reduction "0 mod L" $zero
Test-Reduction "1 mod L" $one
Test-Reduction "L-1 mod L" $Lminus1
Test-Reduction "L mod L" $L
Test-Reduction "L+1 mod L" $Lplus1
Test-Reduction "2L mod L" $twoL
Test-Reduction "2L+1 mod L" $twoLplus1
Test-Reduction "2^256 mod L" $pow256

# 2. RFC8032 Test Vector #1
Write-Host "=== RFC8032 Test Vector #1 ==="
$seedHex = "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
$seedBytes = ($seedHex -split '(..)' | Where-Object { $_ }) | ForEach-Object { [Convert]::ToByte($_, 16) }

# SHA-512(seed)
$sha512 = [System.Security.Cryptography.SHA512]::Create()
$hBytes = $sha512.ComputeHash($seedBytes)
$hHex = ($hBytes | ForEach-Object { $_.ToString('x2') }) -join ''
Write-Host "h = SHA512(seed): $hHex"

# a = clamp(h[0:32])
$aBytes = $hBytes[0..31]
$aBytes[0] = $aBytes[0] -band 0xF8
$aBytes[31] = ($aBytes[31] -band 0x7F) -bor 0x40
$aHex = ($aBytes | ForEach-Object { $_.ToString('x2') }) -join ''
Write-Host "a = clamp(h[0:32]): $aHex"

# prefix = h[32:64]
$prefixBytes = $hBytes[32..63]
$prefixHex = ($prefixBytes | ForEach-Object { $_.ToString('x2') }) -join ''
Write-Host "prefix = h[32:64]: $prefixHex"

# rHash = SHA512(prefix)
$rHashBytes = $sha512.ComputeHash($prefixBytes)
$rHashHex = ($rHashBytes | ForEach-Object { $_.ToString('x2') }) -join ''
Write-Host "rHash = SHA512(prefix): $rHashHex"

# rOracle = BigInteger(rHash) mod L
$rHashInt = [System.Numerics.BigInteger]::new($rHashBytes)
if ($rHashInt -lt 0) { $rHashInt += [System.Numerics.BigInteger]::Pow(2, 512) }
$rOracle = $rHashInt % $L
if ($rOracle -lt 0) { $rOracle += $L }
$rOracleBytes = Get-BytesLE $rOracle
$rOracleHex = ($rOracleBytes | ForEach-Object { $_.ToString('x2') }) -join ''
Write-Host "rOracle = rHash mod L: $rOracleHex"
Write-Host "rOracle[0] = $($rOracleBytes[0]) (decimal)"
Write-Host ""

# Expected RFC8032 signature
$expectedSigHex = "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
$expectedR = $expectedSigHex.Substring(0, 64)
$expectedS = $expectedSigHex.Substring(64, 64)
Write-Host "Expected R: $expectedR"
Write-Host "Expected S: $expectedS"
Write-Host ""

# kHash = SHA512(R || A || M) where M is empty
# A = public key from RFC8032
$pubKeyHex = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
$pubKeyBytes = ($pubKeyHex -split '(..)' | Where-Object { $_ }) | ForEach-Object { [Convert]::ToByte($_, 16) }

# R from expected signature
$expectedRBytes = ($expectedR -split '(..)' | Where-Object { $_ }) | ForEach-Object { [Convert]::ToByte($_, 16) }

# kHash = SHA512(R || A || empty message)
$kInput = $expectedRBytes + $pubKeyBytes
$kHashBytes = $sha512.ComputeHash($kInput)
$kHashHex = ($kHashBytes | ForEach-Object { $_.ToString('x2') }) -join ''
Write-Host "kHash = SHA512(R || A || M): $kHashHex"

# kOracle = kHash mod L
$kHashInt = [System.Numerics.BigInteger]::new($kHashBytes)
if ($kHashInt -lt 0) { $kHashInt += [System.Numerics.BigInteger]::Pow(2, 512) }
$kOracle = $kHashInt % $L
if ($kOracle -lt 0) { $kOracle += $L }
$kOracleBytes = Get-BytesLE $kOracle
$kOracleHex = ($kOracleBytes | ForEach-Object { $_.ToString('x2') }) -join ''
Write-Host "kOracle = kHash mod L: $kOracleHex"
Write-Host ""

# S = (r + k*a) mod L
$aInt = [System.Numerics.BigInteger]::new($aBytes)
if ($aInt -lt 0) { $aInt += [System.Numerics.BigInteger]::Pow(2, 256) }
$SOracle = ($rOracle + $kOracle * $aInt) % $L
if ($SOracle -lt 0) { $SOracle += $L }
$SOracleBytes = Get-BytesLE $SOracle
$SOracleHex = ($SOracleBytes | ForEach-Object { $_.ToString('x2') }) -join ''
Write-Host "SOracle = (r + k*a) mod L: $SOracleHex"
Write-Host "Expected S:               $expectedS"
if ($SOracleHex -eq $expectedS) {
    Write-Host "S MATCHES RFC8032!"
} else {
    Write-Host "S DOES NOT MATCH"
}
Write-Host ""

Write-Host "=== Oracle Summary ==="
Write-Host "rOracle: $rOracleHex"
Write-Host "kOracle: $kOracleHex"
Write-Host "SOracle: $SOracleHex"
