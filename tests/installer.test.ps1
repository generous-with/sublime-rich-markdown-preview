$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$testRoot=Join-Path $root ('build\installer-test-'+[Guid]::NewGuid().ToString('N'))
$packages=Join-Path $testRoot 'Packages'
$payload=Join-Path $root 'dist\unpacked\RichMarkdownPreview'
if(Test-Path -LiteralPath (Join-Path $payload 'package-metadata.json')){throw 'Unmanaged release must not carry Package Control managed metadata'}
if(-not(Test-Path -LiteralPath (Join-Path $payload 'rich-markdown-version.json'))){throw 'Plugin version information missing'}
New-Item -ItemType Directory -Path (Join-Path $packages 'User') -Force | Out-Null
$sentinel=Join-Path $packages 'User\Default (Windows).sublime-keymap'
[IO.File]::WriteAllText($sentinel,'user settings sentinel')
$before=(Get-FileHash -LiteralPath $sentinel).Hash
& (Join-Path $root 'tools\install.ps1') -PackagesPath $packages -PayloadPath $payload
if(-not(Test-Path -LiteralPath (Join-Path $packages 'RichMarkdownPreview\bin\PreviewHost.exe'))){throw 'Fresh install failed'}
$legacyMarker=Join-Path $packages 'RichMarkdownPreview\package-metadata.json'
[IO.File]::WriteAllText($legacyMarker,'{"name":"RichMarkdownPreview","version":"0.2.0"}')
& (Join-Path $root 'tools\install.ps1') -PackagesPath $packages -PayloadPath $payload
if(Test-Path -LiteralPath $legacyMarker){throw 'Upgrade retained the Package Control managed marker'}
if(@(Get-ChildItem -LiteralPath (Join-Path $testRoot 'RichMarkdownPreview-Backups') -Directory).Count -ne 1){throw 'Upgrade backup missing'}
if((Get-FileHash -LiteralPath $sentinel).Hash -ne $before){throw 'User settings modified'}
. (Join-Path $root 'tools\install-common.ps1')
$bad=Join-Path $testRoot 'corrupt-payload'
Copy-Item -LiteralPath $payload -Destination $bad -Recurse
[IO.File]::AppendAllText((Join-Path $bad 'rich_markdown.py'),'tampered')
$rejected=$false
try {Assert-Payload $bad} catch {if($_ -match 'checksum mismatch'){$rejected=$true}else{throw}}
if(-not $rejected){throw 'Corrupt payload was accepted'}
$rejected=$false
try {Assert-PackagePath $packages $packages} catch {$rejected=$true}
if(-not $rejected){throw 'Unsafe target was accepted'}
& (Join-Path $root 'tools\uninstall.ps1') -PackagesPath $packages
if(Test-Path -LiteralPath (Join-Path $packages 'RichMarkdownPreview')){throw 'Uninstall failed'}
if((Get-FileHash -LiteralPath $sentinel).Hash -ne $before){throw 'Uninstall damaged User settings'}
Write-Output 'Installer: release layout, fresh install, legacy metadata removal, upgrade backup, settings preservation, checksum rejection, target guard and uninstall passed.'
