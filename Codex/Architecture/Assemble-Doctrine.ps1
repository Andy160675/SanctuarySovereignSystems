<#
.SYNOPSIS
    Doctrine Assembler v0.1 — Codex Sovereign Systems
    
.DESCRIPTION
    Assembles doctrine documents from tagged evidence blocks.
    The one invariant: doctrine is assembled, not rewritten.

.PARAMETER EvidencePath
    Directory containing tagged evidence fragment files.

.PARAMETER TemplatePath
    Path to the assembly template file.

.PARAMETER OutputPath
    Directory for assembled output.

.EXAMPLE
    .\Assemble-Doctrine.ps1 -EvidencePath "S:\doctrine\evidence" -TemplatePath "S:\doctrine\templates\CSS-ARCH-DOC-001.template" -OutputPath "S:\doctrine\builds"
#>

param(
    [Parameter(Mandatory)]
    [string]$EvidencePath,
    
    [Parameter(Mandatory)]
    [string]$TemplatePath,
    
    [Parameter(Mandatory)]
    [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Layer 1: Parse Evidence Fragments ---

function Get-EvidenceFragments {
    param([string]$Path)
    
    $fragments = @{}
    $blockPattern = '(?s)@block\s+(.+?)\n(.+?)@end'
    $metaPattern = '(\w+)=(\S+)'
    
    Get-ChildItem -Path $Path -Recurse -File | ForEach-Object {
        $filePath = $_.FullName
        try {
            $content = Get-Content $filePath -Raw -Encoding UTF8
        } catch {
            Write-Warning "Skipping unreadable file: $filePath"
            return
        }
        
        [regex]::Matches($content, $blockPattern) | ForEach-Object {
            $header = $_.Groups[1].Value.Trim()
            $body = $_.Groups[2].Value.Trim()
            
            $meta = @{}
            [regex]::Matches($header, $metaPattern) | ForEach-Object {
                $meta[$_.Groups[1].Value] = $_.Groups[2].Value
            }
            
            $blockId = $meta['id']
            if (-not $blockId) { return }
            
            $hash = [System.BitConverter]::ToString(
                [System.Security.Cryptography.SHA256]::Create().ComputeHash(
                    [System.Text.Encoding]::UTF8.GetBytes($body)
                )
            ).Replace('-','').Substring(0,16).ToLower()
            
            $fragments[$blockId] = @{
                id          = $blockId
                domain      = if ($meta['domain']) { $meta['domain'] } else { 'UNKNOWN' }
                type        = if ($meta['type']) { $meta['type'] } else { 'unknown' }
                weight      = if ($meta['weight']) { $meta['weight'] } else { 'provisional' }
                content     = $body
                source_file = $filePath
                content_hash = $hash
            }
        }
    }
    
    # Fix: source_file needs the file path, re-parse with file tracking
    # The above closure captures the pipeline variable correctly in PS5.1+
    
    return $fragments
}

# --- Layer 2: Deterministic Assembly ---

function Invoke-DoctrineAssembly {
    param(
        [string]$TemplatePath,
        [hashtable]$Fragments
    )
    
    $template = Get-Content $TemplatePath -Raw -Encoding UTF8
    
    # Extract metadata
    $docMeta = @{}
    foreach ($line in ($template -split "`n")) {
        if ($line -match '^title:\s*(.+)') { $docMeta['title'] = $Matches[1].Trim() }
        if ($line -match '^doc_id:\s*(.+)') { $docMeta['doc_id'] = $Matches[1].Trim() }
        if ($line -match '^version:\s*(.+)') { $docMeta['version'] = $Matches[1].Trim() }
    }
    
    # Strip header (before ---)
    $body = if ($template -match '(?s)---(.+)') { $Matches[1] } else { $template }
    
    # Replace [block.id] references
    $used = [System.Collections.ArrayList]::new()
    $missing = [System.Collections.ArrayList]::new()
    
    $assembled = [regex]::Replace($body, '\[([a-zA-Z0-9_.]+)\]', {
        param($match)
        $blockId = $match.Groups[1].Value
        if ($Fragments.ContainsKey($blockId)) {
            [void]$used.Add($blockId)
            return $Fragments[$blockId].content
        } else {
            [void]$missing.Add($blockId)
            return "**[MISSING: $blockId]**"
        }
    })
    
    return @{
        assembled = $assembled
        doc_meta  = $docMeta
        used      = $used
        missing   = $missing
    }
}

# --- Layer 3: Output ---

function New-DoctrineHeader {
    param([hashtable]$Meta)
    
    $title = if ($Meta['title']) { $Meta['title'] } else { 'Untitled Doctrine Document' }
    $docId = if ($Meta['doc_id']) { $Meta['doc_id'] } else { '' }
    $version = if ($Meta['version']) { $Meta['version'] } else { '' }
    $now = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm UTC')
    
    return @"
# $title

**Document:** $docId | **Version:** $version | **Assembled:** $now

*This document is mechanically assembled from tagged evidence blocks. Do not edit directly. Edit source fragments and reassemble.*

---
"@
}

function New-BuildManifest {
    param(
        [hashtable]$DocMeta,
        [hashtable]$Fragments,
        [array]$Used,
        [array]$Missing,
        [string]$TemplatePath
    )
    
    $now = (Get-Date).ToUniversalTime().ToString('o')
    $docId = if ($DocMeta['doc_id']) { $DocMeta['doc_id'] } else { 'UNKNOWN' }
    $version = if ($DocMeta['version']) { $DocMeta['version'] } else { '0.0.0' }
    
    $lines = @(
        "# Build Manifest: $docId"
        "**Version:** $version"
        "**Built:** $now"
        "**Template:** $TemplatePath"
        "**Fragments used:** $($Used.Count)"
        "**Fragments missing:** $($Missing.Count)"
        ""
        "## Fragment Provenance"
        ""
        "| Block ID | Domain | Type | Weight | Source File | Content Hash |"
        "|----------|--------|------|--------|------------|-------------|"
    )
    
    foreach ($blockId in $Used) {
        $f = $Fragments[$blockId]
        $srcFile = Split-Path $f.source_file -Leaf
        $lines += "| ``$($f.id)`` | $($f.domain) | $($f.type) | $($f.weight) | ``$srcFile`` | ``$($f.content_hash)`` |"
    }
    
    if ($Missing.Count -gt 0) {
        $lines += ""
        $lines += "## Missing Fragments"
        $lines += ""
        foreach ($m in $Missing) {
            $lines += "- ``$m`` - **NOT FOUND** in evidence"
        }
    }
    
    return $lines -join "`n"
}

# --- Main ---

if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

Write-Host "Scanning evidence: $EvidencePath"
$fragments = Get-EvidenceFragments -Path $EvidencePath
Write-Host "  Found $($fragments.Count) tagged fragments"

Write-Host "Assembling from: $TemplatePath"
$result = Invoke-DoctrineAssembly -TemplatePath $TemplatePath -Fragments $fragments
Write-Host "  Used $($result.used.Count) fragments, $($result.missing.Count) missing"

$docId = if ($result.doc_meta['doc_id']) { $result.doc_meta['doc_id'] } else { 'output' }

# Write document
$header = New-DoctrineHeader -Meta $result.doc_meta
$fullDoc = $header + $result.assembled
$docPath = Join-Path $OutputPath "$docId.md"
$fullDoc | Out-File $docPath -Encoding UTF8
Write-Host "  Document: $docPath"

# Write manifest
$manifest = New-BuildManifest -DocMeta $result.doc_meta -Fragments $fragments `
    -Used $result.used -Missing $result.missing -TemplatePath $TemplatePath
$manifestPath = Join-Path $OutputPath "$docId.manifest.md"
$manifest | Out-File $manifestPath -Encoding UTF8
Write-Host "  Manifest: $manifestPath"

# Document hash
$docHash = [System.BitConverter]::ToString(
    [System.Security.Cryptography.SHA256]::Create().ComputeHash(
        [System.Text.Encoding]::UTF8.GetBytes($fullDoc)
    )
).Replace('-','').Substring(0,16).ToLower()
Write-Host "  Document hash: $docHash"

if ($result.missing.Count -gt 0) {
    Write-Host ""
    Write-Warning "$($result.missing.Count) missing fragments:"
    foreach ($m in $result.missing) {
        Write-Host "    - $m" -ForegroundColor Yellow
    }
}

Write-Host "`nAssembly complete."
