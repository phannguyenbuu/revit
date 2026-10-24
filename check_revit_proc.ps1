Get-Process Revit | Select-Object Id, ProcessName, SessionId, Responding, @{Name="MainWindowTitle";Expression={$_.MainWindowTitle}} | Format-List
