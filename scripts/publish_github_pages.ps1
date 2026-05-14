param(
  [string]$Db = "indexes/uap_release.sqlite",
  [string]$Out = "public_site",
  [string]$Remote = "origin",
  [string]$Branch = "gh-pages",
  [string]$CustomDomain = $(if ($env:DISCLOSURE_CUSTOM_DOMAIN) { $env:DISCLOSURE_CUSTOM_DOMAIN } else { "disclosurearchive.org" }),
  [string]$AnalyticsDomain = $env:DISCLOSURE_ANALYTICS_DOMAIN,
  [string]$AnalyticsScriptUrl = $(if ($env:DISCLOSURE_ANALYTICS_SCRIPT_URL) { $env:DISCLOSURE_ANALYTICS_SCRIPT_URL } else { "https://plausible.io/js/script.js" })
)

$ErrorActionPreference = "Stop"

function Step($Message) {
  Write-Host "==> $Message"
}

$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  $python = "python"
}

Step "Regenerating static public site"
Push-Location $repo
try {
  $env:PYTHONPATH = "src"
  $exportArgs = @("-m", "ufo_indexer.export_site", "--db", $Db, "--out", $Out)
  if ($AnalyticsDomain) {
    $exportArgs += @("--analytics-domain", $AnalyticsDomain, "--analytics-script-url", $AnalyticsScriptUrl)
  }
  & $python @exportArgs
  if ($LASTEXITCODE -ne 0) {
    throw "Static export failed."
  }

  $site = Resolve-Path $Out
  $html = Join-Path $site "index.html"
  $json = Join-Path $site "data\documents.json"
  if (-not (Test-Path $html) -or -not (Test-Path $json)) {
    throw "Static export is missing index.html or data/documents.json."
  }

  $payload = Get-Content $json -Raw
  $forbidden = @("Z:\", "C:\Users", "DisclosureArchivePackage", "derived/", "derived\", "indexes/uap_release.sqlite", "indexes\uap_release.sqlite")
  foreach ($needle in $forbidden) {
    if ($payload.Contains($needle)) {
      throw "Public JSON contains a forbidden local/private marker: $needle"
    }
  }

  Step "Preparing temporary $Branch checkout"
  $publishRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("DisclosureArchivePages-" + [guid]::NewGuid().ToString("N"))
  New-Item -ItemType Directory -Path $publishRoot | Out-Null
  git -C $publishRoot init
  git -C $publishRoot remote add $Remote (git -C $repo remote get-url $Remote)

  $hasBranch = $false
  git -C $publishRoot ls-remote --exit-code --heads $Remote $Branch *> $null
  if ($LASTEXITCODE -eq 0) {
    $hasBranch = $true
  }

  if ($hasBranch) {
    git -C $publishRoot fetch --depth 1 $Remote $Branch
    git -C $publishRoot checkout -B $Branch FETCH_HEAD
    Get-ChildItem -LiteralPath $publishRoot -Force |
      Where-Object { $_.Name -ne ".git" } |
      Remove-Item -Recurse -Force
  } else {
    git -C $publishRoot checkout --orphan $Branch
  }

  Step "Copying public site files"
  Copy-Item -Path (Join-Path $site "*") -Destination $publishRoot -Recurse -Force
  New-Item -ItemType File -Path (Join-Path $publishRoot ".nojekyll") -Force | Out-Null
  if ($CustomDomain) {
    Set-Content -Path (Join-Path $publishRoot "CNAME") -Value $CustomDomain.Trim() -NoNewline
  }

  git -C $publishRoot add -A
  git -C $publishRoot diff --cached --quiet
  if ($LASTEXITCODE -eq 0) {
    Step "No Pages changes to publish"
    return
  }
  if ($LASTEXITCODE -ne 1) {
    throw "Failed to check staged Pages changes."
  }
  git -C $publishRoot commit -m "deploy: update public archive site"

  Step "Pushing $Branch to $Remote"
  git -C $publishRoot push $Remote "HEAD:$Branch"

  Step "Published branch $Branch"
  Write-Host "Next: in GitHub repository settings, set Pages source to '$Branch' branch / root if it is not already enabled."
} finally {
  Pop-Location
}
