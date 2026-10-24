$res = Invoke-RestMethod -Uri 'http://127.0.0.1:8092/api/execute' -Method Post -ContentType 'application/json; charset=utf-8' -Body (@{action='execute_dynamic'; dllPath='D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll'; typeName='RevitScript.InspectDetailedPerimeter'; methodName='Run'} | ConvertTo-Json)

Write-Host "=== SOUTH DOORS ==="
$res.southDoors | Format-Table id, name, x, minX, maxX
Write-Host "=== SOUTH WINDOWS ==="
$res.southWindows | Format-Table id, name, x, minX, maxX
Write-Host "=== NORTH DOORS & WINDOWS ==="
$res.northDoors | Format-Table id, name, x, minX, maxX
$res.northWindows | Format-Table id, name, x, minX, maxX
Write-Host "=== WEST ELEMENTS ==="
$res.westElements | Format-Table id, cat, name, minY, maxY, minX, maxX
