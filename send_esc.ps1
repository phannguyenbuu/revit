Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Collections.Generic;

public class Win32 {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);

    public const uint WM_KEYDOWN = 0x0100;
    public const uint WM_KEYUP = 0x0101;
    public const int VK_ESCAPE = 0x1B;

    public static void SendEscToProcess(uint pid) {
        EnumWindows((hWnd, lParam) => {
            uint procId;
            GetWindowThreadProcessId(hWnd, out procId);
            if (procId == pid) {
                PostMessage(hWnd, WM_KEYDOWN, (IntPtr)VK_ESCAPE, IntPtr.Zero);
                PostMessage(hWnd, WM_KEYUP, (IntPtr)VK_ESCAPE, IntPtr.Zero);
            }
            return true;
        }, IntPtr.Zero);
    }
}
"@

$proc = Get-Process -Name Revit -ErrorAction SilentlyContinue
if ($proc) {
    [Win32]::SendEscToProcess($proc.Id)
    Write-Host "Sent ESC to Revit PID $($proc.Id)"
}
