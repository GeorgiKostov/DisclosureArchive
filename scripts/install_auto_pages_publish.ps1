$ErrorActionPreference = "Stop"

$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$hook = Join-Path $repo ".githooks\pre-push"

if (-not (Test-Path $hook)) {
  throw "Missing tracked hook: $hook"
}

git -C $repo config core.hooksPath .githooks
if ($LASTEXITCODE -ne 0) {
  throw "Failed to configure core.hooksPath."
}

Write-Host "Enabled DisclosureArchive auto Pages publish."
Write-Host "Before pushing origin/main, Git will run scripts/publish_github_pages.ps1."
Write-Host "For a one-off skip, set DISCLOSURE_SKIP_PAGES_PUBLISH=1 before pushing."
