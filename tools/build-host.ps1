$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'bin'
$compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$core=Join-Path $out 'Microsoft.Web.WebView2.Core.dll'
if(-not(Test-Path -LiteralPath $compiler)){throw 'Install .NET Framework 4.8 developer tools or use the prebuilt release'}
if(-not(Test-Path -LiteralPath $core)){throw 'Run python tools/fetch_dependencies.py first'}
$signature=Get-AuthenticodeSignature -LiteralPath $core
if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Microsoft Corporation'){throw 'WebView2 SDK signature is not valid'}
$arguments=@('/noconfig','/nologo','/target:winexe','/platform:x64','/optimize+',('/out:'+(Join-Path $out 'PreviewHost.exe')),
 ('/reference:'+$core),'/reference:System.dll','/reference:System.Core.dll','/reference:System.Windows.Forms.dll',
 '/reference:System.Drawing.dll','/reference:System.Web.Extensions.dll',(Join-Path $root 'host\PreviewHost.cs'))
& $compiler @arguments
if($LASTEXITCODE -ne 0){throw 'Host compilation failed'}
Write-Output ('Built '+(Join-Path $out 'PreviewHost.exe'))
