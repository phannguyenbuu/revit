using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Collections.Generic;

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

    public static List<string> FindWindowsForPid(uint targetPid) {
        var list = new List<string>();
        EnumWindows((hWnd, lParam) => {
            uint procId;
            GetWindowThreadProcessId(hWnd, out procId);
            if (procId == targetPid) {
                var sb = new StringBuilder(512);
                GetWindowText(hWnd, sb, 512);
                string title = sb.ToString();
                var cb = new StringBuilder(512);
                GetClassName(hWnd, cb, 512);
                string cls = cb.ToString();
                bool vis = IsWindowVisible(hWnd);
                if (!string.IsNullOrEmpty(title) || vis) {
                    list.Add(string.Format("HWND: {0} | Class: {1} | Vis: {2} | Title: '{3}'", hWnd, cls, vis, title));
                }
            }
            return true;
        }, IntPtr.Zero);
        return list;
    }
}
