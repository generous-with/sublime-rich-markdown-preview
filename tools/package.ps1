$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$version=(Get-Content (Join-Path $root 'package\package-metadata.json') -Raw -Encoding UTF8 | ConvertFrom-Json).version
$stage=Join-Path $root 'dist\unpacked'
$payload=Join-Path $stage 'RichMarkdownPreview'
if(Test-Path -LiteralPath $stage){throw 'dist/unpacked already exists; use a fresh build directory'}
New-Item -ItemType Directory -Path $payload -Force | Out-Null
Get-ChildItem -LiteralPath (Join-Path $root 'package') -File -Force | ForEach-Object {Copy-Item -LiteralPath $_.FullName -Destination $payload}
foreach($name in @('bin','web','licenses','docs')){Copy-Item -LiteralPath (Join-Path $root $name) -Destination $payload -Recurse}
foreach($name in @('README.md','README.zh-CN.md','LICENSE','THIRD_PARTY_NOTICES.md')){Copy-Item -LiteralPath (Join-Path $root $name) -Destination $payload}
$items=@()
Get-ChildItem -LiteralPath $payload -File -Recurse -Force | ForEach-Object {$items+=@{path=$_.FullName.Substring($payload.Length+1).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName).Hash.ToLowerInvariant()}}
$utf8=New-Object Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $payload 'files.sha256.json'),(ConvertTo-Json -InputObject $items -Depth 4),$utf8)
New-Item -ItemType Directory -Path (Join-Path $stage 'tools') | Out-Null
foreach($name in @('install.ps1','uninstall.ps1','install-common.ps1')){Copy-Item -LiteralPath (Join-Path $root ('tools\'+$name)) -Destination (Join-Path $stage 'tools')}
Copy-Item -LiteralPath (Join-Path $root 'README.md') -Destination $stage
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=Join-Path $root ('dist\RichMarkdownPreview-'+$version+'-windows-x64.zip')
[IO.Compression.ZipFile]::CreateFromDirectory($stage,$zip)
$sum=(Get-FileHash -LiteralPath $zip).Hash.ToLowerInvariant()+'  '+[IO.Path]::GetFileName($zip)
[IO.File]::WriteAllText((Join-Path $root 'dist\SHA256SUMS.txt'),$sum+"`n",$utf8)
Write-Output $zip
