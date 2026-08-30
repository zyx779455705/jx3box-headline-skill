[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"
$SkillRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

try {
    $RuntimePython = (Get-Command python -ErrorAction Stop).Source
    $ScriptPath = Join-Path $SkillRoot "scripts\headline_brief.py"
    & $RuntimePython $ScriptPath @RemainingArgs
    exit $LASTEXITCODE
}
catch {
    $Payload = [ordered]@{
        error = $_.Exception.Message
        error_type = "runtime"
        hint = "Install Python 3.10+ and verify that it is available on PATH."
    }
    [Console]::Error.WriteLine(($Payload | ConvertTo-Json -Compress))
    exit 1
}
