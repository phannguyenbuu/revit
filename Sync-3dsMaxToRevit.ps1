# Sync-3dsMaxToRevit.ps1
$py = "C:\Python314\python.exe"
if (Test-Path "C:\Python314\pythonw.exe") {
    $py = "C:\Python314\pythonw.exe"
}
$script = "D:\Dropbox\_Documents\RevitAI\sync_max_to_revit.py"
& $py $script
