param([string]$NTopExe = "C:\Program Files\nTopology\nTopology\ntop.exe", [ValidateSet("installed","exploded","panels")][string]$View = "installed")
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$models = @{installed='rev-o-installed-skins.ntop'; exploded='rev-o-exploded-skins.ntop'; panels='rev-n-skin-layout.ntop'}
if (-not (Test-Path -LiteralPath $NTopExe)) { throw 'Pass -NTopExe with the path to your licensed compatible nTop build.' }
# This is an explicitly user-run interactive launcher.
Start-Process -FilePath $NTopExe -ArgumentList ('"' + (Join-Path $PSScriptRoot $models[$View]) + '"') -WorkingDirectory $PSScriptRoot
