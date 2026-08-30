[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"
$SkillRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

try {
    $RuntimePython = $null
    $RuntimePrefix = @()
    $Candidates = @(
        @{ Name = "python"; Prefix = @() },
        @{ Name = "py"; Prefix = @("-3") }
    )
    foreach ($Candidate in $Candidates) {
        $Command = Get-Command $Candidate.Name -ErrorAction SilentlyContinue
        if (-not $Command) { continue }
        $Version = & $Command.Source @($Candidate.Prefix) -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}'); raise SystemExit(sys.version_info < (3, 10))" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $RuntimePython = $Command.Source
            $RuntimePrefix = @($Candidate.Prefix)
            break
        }
    }
    if (-not $RuntimePython) {
        throw "Python 3.10+ was not found (checked 'python' and 'py -3')."
    }
    $ScriptPath = Join-Path $SkillRoot "scripts\headline_brief.py"
    & $RuntimePython @RuntimePrefix $ScriptPath @RemainingArgs
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
