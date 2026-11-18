# Runtime launcher: Windows PowerShell is included with Windows 10 and 11.
$ErrorActionPreference = 'Stop'
try {
    $appPath = $env:PHV_APP_PATH
    if (-not $appPath) { $appPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'app\index.html' }
    $resolved = (Resolve-Path -LiteralPath $appPath).Path
    $fileUri = [Uri]::new($resolved).AbsoluteUri
    $candidates = @(
        (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\Application\msedge.exe')
    )
    $edge = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($edge) {
        # The visible app window is the user-requested launcher output.
        Start-Process -FilePath $edge -ArgumentList @("--app=$fileUri", '--no-first-run')
    } else {
        Start-Process -FilePath $resolved
    }
    exit 0
} catch {
    Write-Error $_
    exit 1
}
