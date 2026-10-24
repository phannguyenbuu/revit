$res = Invoke-RestMethod -Uri 'http://127.0.0.1:8092/api/execute' -Method Post -ContentType 'application/json; charset=utf-8' -Body (@{action='execute_dynamic'; dllPath='D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll'; typeName='RevitScript.InspectWestAndEastDetails'; methodName='Run'} | ConvertTo-Json)

Write-Host "=== WEST ELEMENTS ALONG Y ==="
$res.westElements | Format-Table id, cat, name, minY, maxY, minX, maxX

Write-Host "=== EAST ELEMENTS ALONG Y ==="
$res.eastElements | Format-Table id, cat, name, minY, maxY, minX, maxX
