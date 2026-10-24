$ws = New-Object -ComObject WScript.Shell
$activated = $ws.AppActivate(30304)
if (-not $activated) {
    $activated = $ws.AppActivate("Autodesk Revit")
}
if (-not $activated) {
    $activated = $ws.AppActivate("Revit")
}

if ($activated) {
    Start-Sleep -Milliseconds 200
    $ws.SendKeys("{ESC}")
    Start-Sleep -Milliseconds 100
    $ws.SendKeys("{ESC}")
    Write-Output "Successfully sent ESC to Revit"
} else {
    Write-Output "Could not activate Revit window"
}
