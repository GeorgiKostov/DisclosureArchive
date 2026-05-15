param(
  [string]$Url = $(if ($env:DISCLOSURE_SITE_URL) { $env:DISCLOSURE_SITE_URL } else { "https://disclosurearchive.org/" })
)

$ErrorActionPreference = "Stop"

function HeaderValue($Headers, [string]$Name) {
  foreach ($key in $Headers.Keys) {
    if ($key -ieq $Name) {
      $value = $Headers[$key]
      if ($value -is [array]) {
        return ($value -join ", ")
      }
      return [string]$value
    }
  }
  return ""
}

function CheckHeader($Headers, [string]$Name, [string]$ExpectedPattern = "") {
  $value = HeaderValue $Headers $Name
  if (-not $value) {
    return [pscustomobject]@{ Header = $Name; Status = "missing"; Value = "" }
  }
  if ($ExpectedPattern -and ($value -notmatch $ExpectedPattern)) {
    return [pscustomobject]@{ Header = $Name; Status = "weak"; Value = $value }
  }
  return [pscustomobject]@{ Header = $Name; Status = "ok"; Value = $value }
}

Write-Host "Checking security headers for $Url"
$response = Invoke-WebRequest -UseBasicParsing -Method Head $Url -TimeoutSec 20
$headers = $response.Headers

$checks = @(
  (CheckHeader $headers "Content-Security-Policy" "default-src.+object-src\s+'none'.+base-uri\s+'self'"),
  (CheckHeader $headers "Referrer-Policy" "strict-origin-when-cross-origin|no-referrer|same-origin"),
  (CheckHeader $headers "X-Content-Type-Options" "^nosniff$"),
  (CheckHeader $headers "X-Frame-Options" "^(DENY|SAMEORIGIN)$"),
  (CheckHeader $headers "Permissions-Policy" "camera=\(\).+microphone=\(\)")
)

$checks | Format-Table -AutoSize

$failed = @($checks | Where-Object { $_.Status -ne "ok" })
if ($failed.Count -gt 0) {
  Write-Error "Missing or weak HTTP security headers: $($failed.Header -join ', '). GitHub Pages does not apply _headers; deploy through Cloudflare Pages, Netlify, Vercel, or a proxy that injects these headers."
  exit 1
}

Write-Host "Security headers are present."
