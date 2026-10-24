Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Collections.Generic;

public class WinLister {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);
    [DllImport("user32.dll", CharSet = CharSet.Auto)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);

    public static List<string> ListAll() {
        var list = new List<string>();
        EnumWindows((hWnd, lParam) => {
            if (IsWindowVisible(hWnd)) {
                var sb = new StringBuilder(512);
                GetWindowText(hWnd, sb, 512);
                string title = sb.ToString();
                if (!string.IsNullOrEmpty(title)) {
                    uint pid;
                    GetWindowThreadProcessId(hWnd, out pid);
                    list.Add(string.Format("PID: {0} | HWND: {1} | Title: {2}", pid, hWnd, title));
                }
            }
            return true;
        }, IntPtr.Zero);
        return list;
    }
}
"@

$list = [WinLister]::ListAll()
Write-Host "Total windows: $($list.Count)"
$list | Select-Object -First 20 | ForEach-Object { Write-Host $_ }
