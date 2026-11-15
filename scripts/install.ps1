# One-line install (PowerShell):
#   irm https://raw.githubusercontent.com/lumacoder/myasi/main/scripts/install.ps1 | iex
# Downloads only myasi.py + myasi.cmd into ~\.myasi\bin and adds it to the user PATH. Private repo: set $env:GITHUB_TOKEN first.
# myasi.cmd (not a .ps1) so it runs under any PowerShell execution policy. $env:MYASI_RAW_URL overrides the download base.
$ErrorActionPreference = 'Stop'
$repo = if ($env:MYASI_REPO) { $env:MYASI_REPO } else { 'lumacoder/myasi' }
$ref  = if ($env:MYASI_REF)  { $env:MYASI_REF }  else { 'main' }
$root = if ($env:MYASI_HOME) { $env:MYASI_HOME } else { Join-Path $HOME '.myasi' }
$bin  = Join-Path $root 'bin'
New-Item -ItemType Directory -Force -Path $bin | Out-Null
$tok = if ($env:GITHUB_TOKEN) { $env:GITHUB_TOKEN } else { $env:GH_TOKEN }
$base = if ($env:MYASI_RAW_URL) { $env:MYASI_RAW_URL.TrimEnd('/') } else { "https://raw.githubusercontent.com/$repo/$ref" }
foreach ($f in 'scripts/myasi.py', 'bin/myasi.cmd') {
  $out = Join-Path $bin (Split-Path $f -Leaf)
  if ($tok -and -not $env:MYASI_RAW_URL) {
    Invoke-WebRequest -UseBasicParsing -Headers @{ Authorization = "Bearer $tok"; Accept = 'application/vnd.github.raw' } `
      -Uri "https://api.github.com/repos/$repo/contents/$f`?ref=$ref" -OutFile $out
  } else {
    Invoke-WebRequest -UseBasicParsing -Uri "$base/$f" -OutFile $out
  }
}
Remove-Item -ErrorAction SilentlyContinue (Join-Path $bin 'myasi.ps1')  # older installs shipped a .ps1 that shadows myasi.cmd
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (($userPath -split ';') -notcontains $bin) {
  [Environment]::SetEnvironmentVariable('Path', "$bin;$userPath", 'User')
  $env:Path = "$bin;$env:Path"
  Write-Host "added $bin to user PATH (new terminals pick it up)"
}
& (Join-Path $bin 'myasi.cmd') --version
