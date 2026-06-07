# publish-frontend.ps1
# Lokaler Hands-on-Schritt (Lab 7.0): liest die Stack-Outputs, schreibt config.js,
# zippt das Frontend und pusht es zu Amplify. In Lab 7.1 macht das die Pipeline.
# Voraussetzung: sam deploy ist gelaufen.  Aufruf:  .\publish-frontend.ps1

$ErrorActionPreference = "Stop"
$stack       = "netlab-scheduler"
$region      = "us-east-1"
$frontendDir = "frontend"

$outputs = aws cloudformation describe-stacks --stack-name $stack --region $region --query "Stacks[0].Outputs" | ConvertFrom-Json
function Get-Out($key) { ($outputs | Where-Object { $_.OutputKey -eq $key }).OutputValue }
$appId = Get-Out "AmplifyAppId"

$config = @"
window.APP_CONFIG = {
  apiEndpoint: "$(Get-Out 'ApiEndpoint')",
  userPoolId: "$(Get-Out 'UserPoolId')",
  userPoolClientId: "$(Get-Out 'UserPoolClientId')",
  cognitoDomain: "$(Get-Out 'CognitoDomain')"
};
"@
Set-Content -Path "$frontendDir/config.js" -Value $config -Encoding utf8NoBOM

$zip = "frontend.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path "$frontendDir/index.html","$frontendDir/config.js" -DestinationPath $zip

$dep = aws amplify create-deployment --app-id $appId --branch-name main --region $region | ConvertFrom-Json
Invoke-RestMethod -Uri $dep.zipUploadUrl -Method Put -InFile $zip -ContentType "application/zip"
aws amplify start-deployment --app-id $appId --branch-name main --job-id $dep.jobId --region $region

Write-Host ""
Write-Host "Frontend live unter: https://main.$appId.amplifyapp.com"
