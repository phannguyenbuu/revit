$maxCode = @"
(
    local obj = selection[1]
    if obj == undefined then (
        "ERROR|No selection"
    ) else (
        local shiftVec = [0,0,0]
        if (matchPattern obj.name pattern:"*0725 CAX_obj005*" or matchPattern obj.name pattern:"*Mat_Tien*") then (
            shiftVec = [19973.3, 0.0, 0.0]
        ) else (
            shiftVec = -obj.pivot
        )
        move obj shiftVec
        local tempDir = getDir #temp
        local dwgPath = tempDir + "\\Sync_3dsMax_To_Revit.dwg"
        if doesFileExist dwgPath do deleteFile dwgPath
        select #(obj)
        local res = exportFile dwgPath #noPrompt selectedOnly:true
        move obj (-shiftVec)
        select #(obj)
        if res then (
            "SUCCESS|" + obj.name + "|" + dwgPath
        ) else (
            "ERROR|Export failed"
        )
    )
)
"@

$body = @{ code = $maxCode } | ConvertTo-Json
$res = Invoke-RestMethod -Uri "http://127.0.0.1:8096/api/execute" -Method Post -ContentType "application/json" -Body $body
$res | ConvertTo-Json
