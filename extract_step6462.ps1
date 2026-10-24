$line = Get-Content 'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\.system_generated\logs\transcript_full.jsonl' | Select-Object -Skip 6462 -First 1 | ConvertFrom-Json
$code = $line.tool_calls[0].args.CodeContent
[System.IO.File]::WriteAllText('D:\Dropbox\_Documents\RevitAI\step6462_code.cs', $code)
Write-Host "Code written, length = " $code.Length
