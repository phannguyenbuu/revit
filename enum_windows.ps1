Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;

public class Win32Helper {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);
}
'@

[Win32Helper]::EnumWindows({
    param($hWnd, $lParam)
    $procId = 0
    [Win32Helper]::GetWindowThreadProcessId($hWnd, [ref]$procId)
    if ($procId -eq 30304) {
        $sb = New-Object System.Text.StringBuilder 512
        [Win32Helper]::GetWindowText($hWnd, $sb, 512)
        $title = $sb.ToString()
        $cb = New-Object System.Text.StringBuilder 512
        [Win32Helper]::GetClassName($hWnd, $cb, 512)
        $cls = $cb.ToString()
        $vis = [Win32Helper]::IsWindowVisible($hWnd)
        if ($title -ne "" -or $vis) {
            Write-Output "HWND: $hWnd | Class: $cls | Vis: $vis | Title: '$title'"
        }
    }
    return $true
}, [IntPtr]::Zero)
