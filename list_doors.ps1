$res = & "d:\Dropbox\_Documents\RevitAI\call_revit.ps1" -typeName "RevitScript.InspectDoorsInRevit" | ConvertFrom-Json
$res.doorSymbols | Format-Table familyName, typeName, widthMm, heightMm -AutoSize
