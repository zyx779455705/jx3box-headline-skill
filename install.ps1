[CmdletBinding()]
param(
    [ValidateSet("universal", "codex", "claude-code", "copilot", "gemini", "cursor")]
    [string]$Platform = "universal",
    [switch]$Project,
    [string]$Path = "",
    [switch]$DryRun,
    [switch]$Force,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$SkillName = "jx3box-headline-skill"
$Version = "1.1.0"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Help) {
    Write-Host @"
Install $SkillName $Version

Usage:
  .\install.ps1 [-Platform universal|codex|claude-code|copilot|gemini|cursor]
                 [-Project] [-Path <exact-destination>] [-DryRun] [-Force]

The default destination is ~/.agents/skills/$SkillName.
-Project selects the current project's native skill directory.
-Force replaces only the resolved $SkillName destination.
"@
    exit 0
}

function Resolve-TargetPath {
    if ($Path) {
        return [System.IO.Path]::GetFullPath($Path)
    }
    $base = if ($Project) {
        switch ($Platform) {
            "claude-code" { ".claude\skills" }
            "copilot" { ".github\skills" }
            "gemini" { ".gemini\skills" }
            "cursor" { ".cursor\skills" }
            default { ".agents\skills" }
        }
    }
    else {
        switch ($Platform) {
            "claude-code" { Join-Path $env:USERPROFILE ".claude\skills" }
            "copilot" { Join-Path $env:USERPROFILE ".copilot\skills" }
            "gemini" { Join-Path $env:USERPROFILE ".gemini\skills" }
            "cursor" { throw "Cursor has no supported global destination; use -Project or -Path." }
            default { Join-Path $env:USERPROFILE ".agents\skills" }
        }
    }
    return [System.IO.Path]::GetFullPath((Join-Path $base $SkillName))
}

function Assert-SafeTarget([string]$Target) {
    $root = [System.IO.Path]::GetPathRoot($Target)
    $UserHomePath = [System.IO.Path]::GetFullPath($env:USERPROFILE).TrimEnd('\')
    $normalized = [System.IO.Path]::GetFullPath($Target).TrimEnd('\')
    if (-not $normalized -or $normalized -eq $root.TrimEnd('\') -or $normalized -eq $UserHomePath) {
        throw "Refusing unsafe install destination: $Target"
    }
    if ((Split-Path $normalized -Leaf) -ne $SkillName) {
        throw "Destination must end with '$SkillName': $Target"
    }
}

if (-not (Test-Path -LiteralPath (Join-Path $ScriptDir "SKILL.md"))) {
    throw "SKILL.md is missing from $ScriptDir"
}

$Target = Resolve-TargetPath
Assert-SafeTarget $Target
$sourceFull = [System.IO.Path]::GetFullPath($ScriptDir).TrimEnd('\')
$targetFull = [System.IO.Path]::GetFullPath($Target).TrimEnd('\')

if ($sourceFull -eq $targetFull) {
    Write-Host "Already installed at $Target"
    exit 0
}

if ($DryRun) {
    Write-Host "[dry-run] $ScriptDir -> $Target"
    exit 0
}

if (Test-Path -LiteralPath $Target) {
    if (-not $Force) {
        throw "Destination already exists. Re-run with -Force to replace only: $Target"
    }
    Remove-Item -LiteralPath $Target -Recurse -Force
}

$SourceItems = Get-ChildItem -LiteralPath $ScriptDir -Force | Where-Object {
    if ($_.Name -in @(".git", "__pycache__", ".pytest_cache")) { return $false }
    $ItemPath = [System.IO.Path]::GetFullPath($_.FullName).TrimEnd('\') + '\'
    return -not $targetFull.StartsWith(
        $ItemPath,
        [System.StringComparison]::OrdinalIgnoreCase
    )
}

New-Item -ItemType Directory -Path $Target -Force | Out-Null
foreach ($SourceItem in $SourceItems) {
    Copy-Item -LiteralPath $SourceItem.FullName -Destination $Target -Recurse -Force
}

Write-Host "Installed $SkillName $Version to $Target"
Write-Host "Open a new agent session and invoke /$SkillName"
