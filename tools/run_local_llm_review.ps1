# PowerShell 7: run blinded reviews using only a LOCAL Ollama server.
# Requires existing models. No model downloads, remote calls or GitHub writes.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Models,
    [string]$CasePath = ".\results\interventions\CONCEPT_AUDIT_CASE.json",
    [string]$OutputPath = ".\results\interventions\review_ollama",
    [string]$OllamaUrl = "http://127.0.0.1:11434"
)
$ErrorActionPreference = "Stop"
$endpoint = [Uri]$OllamaUrl
if ($endpoint.Host -notin @("localhost", "127.0.0.1") -or $endpoint.Scheme -ne "http") {
    throw "Only local HTTP Ollama endpoints are accepted"
}
if (Test-Path $OutputPath) { throw "Output directory already exists; choose a new path" }
$cfg = Get-Content -LiteralPath $Models -Raw | ConvertFrom-Json -AsHashtable
$case = Get-Content -LiteralPath $CasePath -Raw | ConvertFrom-Json -AsHashtable
$roles = @("proposer", "skeptic", "experimenter")
foreach ($role in $roles) {
    if (-not $cfg.ContainsKey($role) -or -not $cfg[$role].model -or -not $cfg[$role].family) {
        throw "Provide model and family for role $role"
    }
}
if ($cfg.proposer.family -eq $cfg.skeptic.family) {
    throw "Proposer and skeptic must use different model families"
}
python .\research_interventions.py prepare --case $CasePath --dir $OutputPath
if ($LASTEXITCODE -ne 0) { throw "Prompt preparation failed" }
foreach ($role in $roles) {
    $model = [string]$cfg[$role].model
    $family = [string]$cfg[$role].family
    $prompt = Get-Content -LiteralPath (Join-Path $OutputPath "$role.prompt.txt") -Raw
    $payload = @{
        model = $model
        stream = $false
        format = "json"
        options = @{ temperature = 0 }
        messages = @(@{ role = "user"; content = $prompt })
    } | ConvertTo-Json -Depth 10
    Write-Host "Reviewing $role with $model"
    $response = Invoke-RestMethod -Method Post -Uri "$($OllamaUrl.TrimEnd('/'))/api/chat" -ContentType "application/json" -Body ([Text.Encoding]::UTF8.GetBytes($payload)) -TimeoutSec 240
    $review = $response.message.content | ConvertFrom-Json -AsHashtable
    if ($review -isnot [System.Collections.IDictionary] -or
        $review.case_id -ne $case.case_id -or $review.role -ne $role) {
        throw "Invalid model response from $model for role $role"
    }
    # Model and family identity come from our configuration, not the model's claim.
    $review.model_id = "ollama/$model"
    $review.model_family = $family
    $review | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $OutputPath "$role.json") -Encoding utf8
}
python .\research_interventions.py evaluate --case $CasePath --dir $OutputPath |
    Set-Content -LiteralPath (Join-Path $OutputPath "gate.json") -Encoding utf8
if ($LASTEXITCODE -ne 0) { throw "Evidence gate failed. See saved reviews." }
Get-Content -LiteralPath (Join-Path $OutputPath "gate.json")
