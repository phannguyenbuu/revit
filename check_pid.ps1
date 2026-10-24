$p = Get-Process -Id 30304
Write-Host "Process Name: $($p.ProcessName)"
Write-Host "Main Window Title: '$($p.MainWindowTitle)'"
Write-Host "Main Window Handle: $($p.MainWindowHandle)"
