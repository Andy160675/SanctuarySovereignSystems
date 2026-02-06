# scripts/ops/Verify-Autonomy-Boundaries.ps1
$limitsFile = "AUTONOMY_LIMITS.md"
$content = Get-Content $limitsFile -Raw
$forbiddenMatches = [regex]::Matches($content, '(?s)forbidden:\s*(.*?)(?:\n\n|\n#|\n---|$)')
$forbiddenList = $forbiddenMatches[0].Groups[1].Value -split "\n" | Where-Object { $_ -match "^\s*-\s+" } | ForEach-Object { $_.Replace("-", "").Trim() }
Write-Host "Found $($forbiddenList.Count) forbidden actions."
$pyCode = "import sys, os, json; sys.path.insert(0, os.path.abspath('.')); from jarus.core.constitutional_runtime import ConstitutionalRuntime, DecisionType; runtime = ConstitutionalRuntime(); forbidden_actions = json.loads(sys.argv[1]); results = {'passed': 0, 'failed': 0, 'violations': []}; [ (results.update({'passed': results['passed'] + 1}) if runtime.evaluate({'action': a, 'autonomous': True}).decision_type in [DecisionType.DENY, DecisionType.HALT, DecisionType.ESCALATE] else (results.update({'failed': results['failed'] + 1}), results['violations'].append(a))) for a in forbidden_actions ]; print(json.dumps(results))"
$forbiddenJson = $forbiddenList | ConvertTo-Json -Compress
# Escape quotes for shell execution
$forbiddenJsonEscaped = $forbiddenJson -replace '"', '\"'
$resultJson = python -c "$pyCode" "$forbiddenJsonEscaped"
$result = $resultJson | ConvertFrom-Json
if ($result.failed -eq 0) {
    Write-Host "SUCCESS: All $($result.passed) forbidden actions correctly blocked/escalated."
} else {
    Write-Host "FAILURE: $($result.failed) forbidden actions were PERMITTED!"
    exit 1
}
