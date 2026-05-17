# =========================
# CONFIG (patterns to remove)
# =========================
$patterns = @(
    'msys',          # C:\msys64\...
    'mingw',         # C:\msys64\mingw64\..., C:\MinGW\...
    'git\\usr\\bin'  # C:\Program Files\Git\usr\bin
)

# =========================
# Helpers
# =========================
function Split-PathList($p) {
    ($p -split ';') | Where-Object { $_ -and $_.Trim() -ne '' } | ForEach-Object { $_.Trim() }
}

function Join-PathList($arr) {
    ($arr | Where-Object { $_ -and $_.Trim() -ne '' }) -join ';'
}

function Dedup-CaseInsensitive($arr) {
    $seen = @{}
    foreach ($e in $arr) {
        $key = $e.ToLowerInvariant()
        if (-not $seen.ContainsKey($key)) {
            $seen[$key] = $true
            $e
        }
    }
}

function Filter-Entries($entries, $patterns) {
    $removed = @()
    $kept = @()

    foreach ($e in $entries) {
        $lower = $e.ToLowerInvariant()
        $match = $false
        foreach ($p in $patterns) {
            if ($lower -match $p) { $match = $true; break }
        }
        if ($match) { $removed += $e } else { $kept += $e }
    }

    [pscustomobject]@{
        Kept    = $kept
        Removed = $removed
    }
}

function Backup-Env($name, $value) {
    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    $file = "$env:USERPROFILE\Desktop\PATH_backup_${name}_$ts.txt"
    $value | Out-File -FilePath $file -Encoding utf8
    Write-Host "Backed up $name PATH to $file"
}

# =========================
# Process one scope
# =========================
function Clean-PathScope($scopeName) {
    Write-Host "`n=== Processing $scopeName PATH ===" -ForegroundColor Cyan

    $current = [Environment]::GetEnvironmentVariable('Path', $scopeName)
    if (-not $current) { $current = "" }

    Backup-Env $scopeName $current

    $entries = Split-PathList $current
    $filtered = Filter-Entries $entries $patterns

    $deduped = Dedup-CaseInsensitive $filtered.Kept
    $newPath = Join-PathList $deduped

    # Show diff
    if ($filtered.Removed.Count -gt 0) {
        Write-Host "Will REMOVE:" -ForegroundColor Yellow
        $filtered.Removed | ForEach-Object { Write-Host "  - $_" }
    } else {
        Write-Host "No matching entries to remove."
    }

    Write-Host "`nResulting PATH entries count: $($deduped.Count)"

    # Apply
    [Environment]::SetEnvironmentVariable('Path', $newPath, $scopeName)
    Write-Host "Updated $scopeName PATH."
}

# =========================
# Run
# =========================
# User PATH (no admin needed)
Clean-PathScope 'User'

# System PATH (needs Admin)
try {
    Clean-PathScope 'Machine'
} catch {
    Write-Warning "Could not update Machine PATH (run PowerShell as Administrator to modify System PATH)."
}

Write-Host "`nDone. Restart your terminal (and VS) to pick up changes." -ForegroundColor Green