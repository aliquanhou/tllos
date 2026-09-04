# TLL Mall Route Statistics Script
$ErrorActionPreference = "Stop"
$baseDir = "C:\Users\Administrator\Doubao\chats\2026-09-04\new-chat\tllos\mall"

Write-Host "========================================"
Write-Host "  TLL Mall Route Statistics"
Write-Host "========================================"
Write-Host ""

$tllFiles = Get-ChildItem -Path $baseDir -Filter "*.tll" -Recurse | Where-Object { $_.Name -notlike "test_*" }
Write-Host "Source files scanned: $($tllFiles.Count)"
Write-Host ""

$allRoutes = @()
$methodCount = @{ GET = 0; POST = 0; PUT = 0; DELETE = 0 }

foreach ($file in $tllFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    $module = $file.BaseName

    $patterns = @(
        @{ method = "GET";    regex = 'router_get\s*\(\s*\w+\s*,\s*"([^"]+)"' },
        @{ method = "POST";   regex = 'router_post\s*\(\s*\w+\s*,\s*"([^"]+)"' },
        @{ method = "PUT";    regex = 'router_put\s*\(\s*\w+\s*,\s*"([^"]+)"' },
        @{ method = "DELETE"; regex = 'router_delete\s*\(\s*\w+\s*,\s*"([^"]+)"' }
    )

    foreach ($p in $patterns) {
        $matches = [regex]::Matches($content, $p.regex)
        foreach ($m in $matches) {
            $path = $m.Groups[1].Value
            $allRoutes += [PSCustomObject]@{
                Module = $module
                Method = $p.method
                Path   = $path
                File   = $file.Name
            }
            $methodCount[$p.method]++
        }
    }
}

Write-Host "Total routes found: $($allRoutes.Count)"
Write-Host ""

Write-Host "=== Routes by Module ==="
$byModule = $allRoutes | Group-Object Module | Sort-Object Count -Descending
foreach ($g in $byModule) {
    $getCount = ($g.Group | Where-Object { $_.Method -eq "GET" }).Count
    $postCount = ($g.Group | Where-Object { $_.Method -eq "POST" }).Count
    Write-Host ("  {0,-15} {1,3} routes  (GET:{2} POST:{3})" -f $g.Name, $g.Count, $getCount, $postCount)
}
Write-Host ""

Write-Host "=== Routes by HTTP Method ==="
foreach ($m in @("GET", "POST", "PUT", "DELETE")) {
    $count = $methodCount[$m]
    $pct = if ($allRoutes.Count -gt 0) { [math]::Round($count / $allRoutes.Count * 100, 1) } else { 0 }
    Write-Host ("  {0,-8} {1,3} routes  ({2}%)" -f $m, $count, $pct)
}
Write-Host ""

Write-Host "=== Routes by Business Domain ==="
$domains = @(
    @{ Name = "Frontend Home";    Filter = { $_.Path -match "^/$|^/category|^/product|^/search" } },
    @{ Name = "Cart";              Filter = { $_.Path -match "^/cart" } },
    @{ Name = "Order/Checkout";    Filter = { $_.Path -match "^/checkout|^/order" } },
    @{ Name = "Auth";              Filter = { $_.Path -match "^/login|^/register|^/logout" } },
    @{ Name = "User Center";       Filter = { $_.Path -match "^/user" } },
    @{ Name = "Admin Dashboard";   Filter = { $_.Path -match "^/admin$" } },
    @{ Name = "Admin Products";    Filter = { $_.Path -match "^/admin/product" } },
    @{ Name = "Admin Orders";      Filter = { $_.Path -match "^/admin/order" } },
    @{ Name = "Admin Users";       Filter = { $_.Path -match "^/admin/users" } },
    @{ Name = "Admin Categories";  Filter = { $_.Path -match "^/admin/categories" } }
)

$categorized = @()
foreach ($d in $domains) {
    $routes = $allRoutes | Where-Object $d.Filter
    $categorized += $routes
    if ($routes.Count -gt 0) {
        Write-Host ("  {0,-20} {1,3} routes" -f $d.Name, $routes.Count)
    }
}
$uncategorized = $allRoutes | Where-Object { $categorized -notcontains $_ }
if ($uncategorized.Count -gt 0) {
    Write-Host ("  {0,-20} {1,3} routes" -f "Other", $uncategorized.Count)
}
Write-Host ""

Write-Host "=== Complete Route Listing ==="
$sorted = $allRoutes | Sort-Object Module, Path
$currentModule = ""
foreach ($r in $sorted) {
    if ($r.Module -ne $currentModule) {
        $currentModule = $r.Module
        Write-Host ""
        Write-Host "[$currentModule]"
    }
    $methodPad = $r.Method.PadRight(6)
    Write-Host "  $methodPad $($r.Path)"
}
Write-Host ""

Write-Host "=== Database Tables ==="
$schemaFile = Join-Path $baseDir "core\schema.tll"
$tables = @()
if (Test-Path $schemaFile) {
    $schemaContent = Get-Content $schemaFile -Raw -Encoding UTF8
    $tableMatches = [regex]::Matches($schemaContent, 'CREATE TABLE (?:IF NOT EXISTS )?(\w+)')
    $tables = $tableMatches | ForEach-Object { $_.Groups[1].Value } | Sort-Object
    Write-Host "Total tables: $($tables.Count)"
    Write-Host ""
    $i = 1
    foreach ($t in $tables) {
        Write-Host ("  {0,2}. {1}" -f $i, $t)
        $i++
    }
}
Write-Host ""

Write-Host "========================================"
Write-Host "  Summary"
Write-Host "========================================"
Write-Host "  Total routes:  $($allRoutes.Count)"
Write-Host "  Total tables:  $($tables.Count)"
Write-Host "  Source files:  $($tllFiles.Count)"
Write-Host "  HTTP methods:  GET=$($methodCount.GET) POST=$($methodCount.POST) PUT=$($methodCount.PUT) DELETE=$($methodCount.DELETE)"
Write-Host "========================================"
