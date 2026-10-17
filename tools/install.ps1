param([string]$PackagesPath,[string]$PayloadPath)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'install-common.ps1')
$root=Split-Path $PSScriptRoot -Parent
if(-not $PayloadPath){
 $PayloadPath=Join-Path $root 'RichMarkdownPreview'
 if(-not(Test-Path -LiteralPath $PayloadPath)){$PayloadPath=Join-Path $root 'dist\unpacked\RichMarkdownPreview'}
}
$PayloadPath=[IO.Path]::GetFullPath($PayloadPath)
Assert-Payload $PayloadPath
$packages=Resolve-PackagesPath $PackagesPath
$target=Join-Path $packages 'RichMarkdownPreview'
Assert-PackagePath $target $packages
Assert-HostStopped $target
New-Item -ItemType Directory -Path $packages -Force | Out-Null
$backup=$null
if(Test-Path -LiteralPath $target){
 $backupRoot=Join-Path (Split-Path $packages -Parent) 'RichMarkdownPreview-Backups'
 $backup=Join-Path $backupRoot ((Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N'))
 if(-not([IO.Path]::GetFullPath($backup).StartsWith(([IO.Path]::GetFullPath($backupRoot)+'\'),[StringComparison]::OrdinalIgnoreCase))){throw 'Unexpected backup target'}
 New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
 Move-Item -LiteralPath $target -Destination $backup
}
try {Copy-Item -LiteralPath $PayloadPath -Destination $target -Recurse}
catch {
 Assert-PackagePath $target $packages
 if(Test-Path -LiteralPath $target){Remove-Item -LiteralPath $target -Recurse -Force}
 if($backup){Move-Item -LiteralPath $backup -Destination $target}
 throw
}
Write-Output ('Installed: '+$target)
if($backup){Write-Output ('Previous version: '+$backup)}
Write-Output 'Open Markdown and use Rich Markdown: Preview in Current Window from the command palette. Default shortcut: Alt+M.'
