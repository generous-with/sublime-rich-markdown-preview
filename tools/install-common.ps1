function Resolve-PackagesPath([string]$Path) {
 if($Path){return [IO.Path]::GetFullPath($Path)}
 $candidates=@(@((Join-Path $env:APPDATA 'Sublime Text\Packages'),(Join-Path $env:APPDATA 'Sublime Text 3\Packages')) | Where-Object {Test-Path -LiteralPath $_})
 if(@($candidates).Count -ne 1){throw 'Specify -PackagesPath with the Packages folder shown by Preferences > Browse Packages'}
 return [IO.Path]::GetFullPath($candidates[0])
}
function Assert-PackagePath([string]$Path,[string]$PackagesPath) {
 $expected=[IO.Path]::GetFullPath((Join-Path $PackagesPath 'RichMarkdownPreview'))
 if([IO.Path]::GetFullPath($Path) -ne $expected){throw 'Unexpected package target'}
 if(Test-Path -LiteralPath $Path){
  $entries=@(Get-Item -LiteralPath $Path;Get-ChildItem -LiteralPath $Path -Recurse -Force)
  if(@($entries | Where-Object {($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0}).Count){throw 'Package contains reparse points; refusing to modify it'}
 }
}
function Assert-HostStopped([string]$PackagePath) {
 $exe=Join-Path $PackagePath 'bin\PreviewHost.exe'
 if(@(Get-Process PreviewHost -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $exe}).Count){throw 'Close Rich Markdown previews before installing or uninstalling'}
}
function Assert-Payload([string]$Payload) {
 $manifest=Join-Path $Payload 'files.sha256.json'
 if(-not(Test-Path -LiteralPath $manifest)){throw 'Build the release with tools/package.ps1 before installing'}
 $entries=@(Get-Item -LiteralPath $Payload;Get-ChildItem -LiteralPath $Payload -Recurse -Force)
 if(@($entries | Where-Object {($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0}).Count){throw 'Payload contains reparse points'}
 $verified=@($manifest)
 foreach($item in (Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 | ConvertFrom-Json)){
  $file=[IO.Path]::GetFullPath((Join-Path $Payload $item.path))
  if(-not $file.StartsWith(([IO.Path]::GetFullPath($Payload)+'\'),[StringComparison]::OrdinalIgnoreCase)){throw 'Manifest path escapes payload'}
  if((Get-FileHash -LiteralPath $file).Hash -ne $item.sha256){throw ('Payload checksum mismatch: '+$item.path)}
  $verified+=$file
 }
 foreach($file in ($entries | Where-Object {-not $_.PSIsContainer})){
  if($file.FullName -notin $verified){throw ('Unlisted payload file: '+$file.Name)}
 }
 if(-not(Test-Path -LiteralPath (Join-Path $Payload 'bin\PreviewHost.exe'))){throw 'Host executable missing'}
}
