param(
    [string]$typeName,
    [string]$methodName = "Run",
    [string]$extraJson = "{}",
    [string]$AssemblyPath = "D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_InspectLines.dll"
)

$payload = @{
    action = "execute_dynamic"
    dllPath = $AssemblyPath
    typeName = $typeName
    methodName = $methodName
}

$json = $payload | ConvertTo-Json -Compress
$res = Invoke-RestMethod -Uri "http://127.0.0.1:8092/api/execute" -Method Post -ContentType "application/json; charset=utf-8" -Body $json -TimeoutSec 600
$res | ConvertTo-Json -Depth 6
