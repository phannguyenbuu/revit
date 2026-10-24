Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Collections.Generic;
using System.Diagnostics;

public class ThreadWindowFinder {
    public delegate bool EnumThreadDelegate(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool EnumThreadWindows(int dwThreadId, EnumThreadDelegate lpfn, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    public const uint WM_KEYDOWN = 0x0100;
    public const uint WM_KEYUP = 0x0101;
    public const int VK_ESCAPE = 0x1B;

    public static List<string> FindAndSendEsc(int pid) {
        var list = new List<string>();
        var proc = Process.GetProcessById(pid);
        foreach (ProcessThread th in proc.Threads) {
            EnumThreadWindows(th.Id, (hWnd, lParam) => {
                var sb = new StringBuilder(512);
                GetWindowText(hWnd, sb, 512);
                string title = sb.ToString();
                var cb = new StringBuilder(512);
                GetClassName(hWnd, cb, 512);
                string cls = cb.ToString();
                bool vis = IsWindowVisible(hWnd);
                if (vis || !string.IsNullOrEmpty(title)) {
                    list.Add(string.Format("HWND: {0} | Cls: {1} | Vis: {2} | Title: '{3}'", hWnd, cls, vis, title));
                    PostMessage(hWnd, WM_KEYDOWN, (IntPtr)VK_ESCAPE, IntPtr.Zero);
                    PostMessage(hWnd, WM_KEYUP, (IntPtr)VK_ESCAPE, IntPtr.Zero);
                }
                return true;
            }, IntPtr.Zero);
        }
        return list;
    }
}
"@

$res = [ThreadWindowFinder]::FindAndSendEsc(30304)
$res | ForEach-Object { Write-Host $_ }
