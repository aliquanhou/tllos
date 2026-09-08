$bytes = [System.Text.Encoding]::UTF8.GetBytes("abc")
$hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
$result = [BitConverter]::ToString($hash) -replace '-', ''
Write-Output $result.ToLower()
