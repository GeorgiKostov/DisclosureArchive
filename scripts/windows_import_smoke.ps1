param(
  [string]$Repo = "C:\DisclosureArchive\repo",
  [string]$Package = "E:\DisclosureArchivePackage",
  [string]$RawTarget = "C:\DisclosureArchive\ufo_war_release"
)

$ErrorActionPreference = "Stop"

function Invoke-RobocopyChecked {
  param(
    [string]$Source,
    [string]$Destination
  )

  if (!(Test-Path $Source)) {
    throw "Missing source path: $Source"
  }

  New-Item -ItemType Directory -Force -Path $Destination | Out-Null
  robocopy $Source $Destination /E

  if ($LASTEXITCODE -gt 7) {
    throw "robocopy failed from $Source to $Destination with exit code $LASTEXITCODE"
  }
}

if (!(Test-Path $Package)) {
  throw "Missing transfer package: $Package"
}

if (!(Test-Path $Repo)) {
  New-Item -ItemType Directory -Force -Path (Split-Path $Repo) | Out-Null
  git clone https://github.com/GeorgiKostov/DisclosureArchive.git $Repo
}

Invoke-RobocopyChecked "$Package\ufo_war_release" $RawTarget
Invoke-RobocopyChecked "$Package\indexes" "$Repo\indexes"
Invoke-RobocopyChecked "$Package\derived" "$Repo\derived"

Set-Location $Repo

if (!(Test-Path ".venv")) {
  py -3 -m venv .venv
}

.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .

python -m ufo_indexer.search `
  --db indexes\uap_release.sqlite `
  --mode hybrid `
  --q "lunar surface flash Grimaldi"

python -m ufo_indexer.search `
  --db indexes\uap_release.sqlite `
  --mode hybrid `
  --q "nasa moon"

python -m ufo_indexer.search `
  --db indexes\uap_release.sqlite `
  --mode vector `
  --q "helicopter crew saw hot orange orbs split and flare in formation"

Write-Host ""
Write-Host "Import smoke tests finished."
Write-Host "If result paths still point to /Users/georgikostov, rebuild with:"
Write-Host "python -m ufo_indexer.index --source-root $RawTarget --db indexes\uap_release.sqlite --rebuild"
