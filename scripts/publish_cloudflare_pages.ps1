param(
  [string]$Db = "indexes/uap_release.sqlite",
  [string]$Out = "public_site",
  [string]$ProjectName = $(if ($env:DISCLOSURE_CLOUDFLARE_PROJECT) { $env:DISCLOSURE_CLOUDFLARE_PROJECT } else { "disclosurearchive" }),
  [string]$Branch = $(if ($env:DISCLOSURE_CLOUDFLARE_BRANCH) { $env:DISCLOSURE_CLOUDFLARE_BRANCH } else { "main" }),
  [string]$SiteUrl = $(if ($env:DISCLOSURE_SITE_URL) { $env:DISCLOSURE_SITE_URL } else { "https://disclosurearchive.org" }),
  [string]$AnalyticsDomain = $env:DISCLOSURE_ANALYTICS_DOMAIN,
  [string]$AnalyticsScriptUrl = $(if ($env:DISCLOSURE_ANALYTICS_SCRIPT_URL) { $env:DISCLOSURE_ANALYTICS_SCRIPT_URL } else { "https://plausible.io/js/script.js" }),
  [string]$GaMeasurementId = $(if ($env:DISCLOSURE_GA_MEASUREMENT_ID) { $env:DISCLOSURE_GA_MEASUREMENT_ID } else { "G-NNXB9F00V6" })
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

Push-Location $repo
try {
  $env:PYTHONPATH = "src"

  Step "Regenerating static public site"
  $exportArgs = @("-m", "ufo_indexer.export_site", "--db", $Db, "--out", $Out, "--site-url", $SiteUrl)
  if ($AnalyticsDomain) {
    $exportArgs += @("--analytics-domain", $AnalyticsDomain, "--analytics-script-url", $AnalyticsScriptUrl)
  }
  if ($GaMeasurementId) {
    $exportArgs += @("--ga-measurement-id", $GaMeasurementId)
  }
  & $python @exportArgs
  if ($LASTEXITCODE -ne 0) {
    throw "Static export failed."
  }

  $site = Resolve-Path $Out
  $json = Join-Path $site "data\documents.json"
  if (-not (Test-Path (Join-Path $site "index.html")) -or -not (Test-Path $json)) {
    throw "Static export is missing index.html or data/documents.json."
  }
  if (-not (Test-Path (Join-Path $site "_headers"))) {
    throw "Static export is missing _headers; Cloudflare Pages will not apply the expected security headers."
  }

  $payload = Get-Content $json -Raw
  $forbidden = @("Z:\", "C:\Users", "DisclosureArchivePackage", "derived/", "derived\", "indexes/uap_release.sqlite", "indexes\uap_release.sqlite")
  foreach ($needle in $forbidden) {
    if ($payload.Contains($needle)) {
      throw "Public JSON contains a forbidden local/private marker: $needle"
    }
  }

  Step "Deploying to Cloudflare Pages project '$ProjectName'"
  npx wrangler pages deploy $site --project-name $ProjectName --branch $Branch
  if ($LASTEXITCODE -ne 0) {
    throw "Cloudflare Pages deploy failed. Run 'npx wrangler login' first if this machine is not authenticated."
  }

  Write-Host "Next: attach disclosurearchive.org to the Cloudflare Pages project and enable DNS/proxying there."
  Write-Host "Then verify live headers with:"
  Write-Host "  powershell -ExecutionPolicy Bypass -File scripts/check_public_security_headers.ps1 -Url $SiteUrl"
} finally {
  Pop-Location
}
