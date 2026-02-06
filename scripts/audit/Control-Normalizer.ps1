[CmdletBinding()]
param(
    [string]$RepoRoot = ""
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path $PSScriptRoot\..\..).Path
}

Write-Host "--- AGENT 4: CONTROL NORMALIZER ---" -ForegroundColor Cyan
Write-Host "Applying document governance headers..." -ForegroundColor Gray

$TargetDocuments = @(
    @{ 
        Path = "CONSTITUTION.md"; 
        DocId = "SOV-DOC-001"; 
        Authority = "Sovereign Authority"; 
        Revision = "1.2" 
    }
    @{ 
        Path = "SOP_DAILY.md"; 
        DocId = "SOV-SOP-001"; 
        Authority = "Ops Command"; 
        Revision = "1.1" 
    }
    @{ 
        Path = "governance/THE_DIAMOND_DOCTRINE.md"; 
        DocId = "SOV-DOC-002"; 
        Authority = "Sovereign Authority"; 
        Revision = "1.0" 
    }
)

foreach ($doc in $TargetDocuments) {
    $absPath = Join-Path $RepoRoot $doc.Path
    if (Test-Path $absPath) {
        $content = Get-Content -Path $absPath -Raw
        
        # Check if already normalized
        if ($content -match "DOCUMENT_ID: " + $doc.DocId) {
            Write-Host "Skipping $($doc.Path) - Already normalized." -ForegroundColor Gray
            continue
        }

        $header = @"
---
DOCUMENT_ID: $($doc.DocId)
AUTHORITY: $($doc.Authority)
REVISION: $($doc.Revision)
LAST_AUDIT: $((Get-Date).ToUniversalTime().ToString("yyyy-MM-dd"))
STATUS: AUDITED
---

"@
        
        $newContent = $header + $content
        $newContent | Set-Content -Path $absPath -Encoding UTF8
        Write-Host "Normalized: $($doc.Path)" -ForegroundColor Green
    } else {
        Write-Host "Warning: Document not found: $($doc.Path)" -ForegroundColor Yellow
    }
}
