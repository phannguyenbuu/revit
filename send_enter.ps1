$wshell = New-Object -ComObject wscript.shell
if ($wshell.AppActivate(30304)) {
    Start-Sleep -Milliseconds 300
    $wshell.SendKeys("{ENTER}")
    Start-Sleep -Milliseconds 300
    $wshell.SendKeys("{ESC}")
    Write-Host "Sent ENTER and ESC to Revit"
} else {
    Write-Host "Could not activate Revit"
}
