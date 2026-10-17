param([string]$PackagesPath)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'install-common.ps1')
$packages=Resolve-PackagesPath $PackagesPath
$target=Join-Path $packages 'RichMarkdownPreview'
Assert-PackagePath $target $packages
Assert-HostStopped $target
if(Test-Path -LiteralPath $target){Remove-Item -LiteralPath $target -Recurse -Force}
Write-Output 'RichMarkdownPreview removed. User documents, keybindings and settings were not changed.'
