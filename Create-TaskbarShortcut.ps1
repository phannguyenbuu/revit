$wsh = New-Object -ComObject WScript.Shell

$scriptPath = "D:\Dropbox\_Documents\RevitAI\sync_max_to_revit.py"
$targetExe = "C:\Python314\pythonw.exe"
$arguments = "`"$scriptPath`""
$iconPath = "C:\Program Files\Autodesk\Revit 2025\Revit.exe"

$desktop = [System.Environment]::GetFolderPath('Desktop')
$programs = [System.Environment]::GetFolderPath('Programs')

$locations = @(
    "D:\Dropbox\_Documents\RevitAI\Sync 3dsMax to Revit.lnk",
    (Join-Path $desktop "Sync 3dsMax to Revit.lnk"),
    (Join-Path $programs "Sync 3dsMax to Revit.lnk")
)

foreach ($loc in $locations) {
    try {
        $shortcut = $wsh.CreateShortcut($loc)
        $shortcut.TargetPath = $targetExe
        $shortcut.Arguments = $arguments
        $shortcut.WorkingDirectory = "D:\Dropbox\_Documents\RevitAI"
        $shortcut.Description = "Dong bo vat the dang chon tu 3ds Max sang Revit Family"
        $shortcut.IconLocation = "$iconPath,0"
        $shortcut.Save()
        Write-Host "Created shortcut: $loc"
    } catch {
        Write-Host "Failed to create shortcut at $loc : $_"
    }
}

try {
    $desktopLnk = Join-Path $desktop "Sync 3dsMax to Revit.lnk"
    $shell = New-Object -ComObject Shell.Application
    $folder = $shell.Namespace($desktop)
    $item = $folder.ParseName("Sync 3dsMax to Revit.lnk")
    $verbs = $item.Verbs()
    $pinned = $false
    foreach ($v in $verbs) {
        if ($v.Name -match "taskbar|thanh tác vụ|Pin to taskbar") {
            $v.DoIt()
            $pinned = $true
            Write-Host "Triggered taskbar pin verb: $($v.Name)"
            break
        }
    }
    if (-not $pinned) {
        Write-Host "Shortcut created on Desktop. Right-click it and select 'Pin to taskbar' if needed."
    }
} catch {
    Write-Host "Taskbar pin note: $_"
}
