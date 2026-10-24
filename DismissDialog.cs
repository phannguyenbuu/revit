using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Diagnostics;

public class Program
{
    [DllImport("user32.dll")]
    static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    static extern int GetClassName(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [DllImport("user32.dll")]
    static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll")]
    static extern bool SetForegroundWindow(IntPtr hWnd);

    delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    const uint WM_KEYDOWN = 0x0100;
    const uint WM_KEYUP = 0x0101;
    const uint VK_RETURN = 0x0D;
    const uint VK_SPACE = 0x20;
    const uint WM_COMMAND = 0x0111;

    public static void Main()
    {
        EnumWindows((hWnd, lParam) =>
        {
            uint pid;
            GetWindowThreadProcessId(hWnd, out pid);
            if (!IsWindowVisible(hWnd)) return true;

            var sbTitle = new StringBuilder(256);
            GetWindowText(hWnd, sbTitle, 256);
            string title = sbTitle.ToString();
            if (string.IsNullOrEmpty(title)) return true;

            var sbClass = new StringBuilder(256);
            GetClassName(hWnd, sbClass, 256);
            string cls = sbClass.ToString();

            if (title.ToLower().Contains("revit") || title.ToLower().Contains("autodesk") || cls == "#32770")
            {
                Console.WriteLine("HWND: " + hWnd + ", PID: " + pid + ", Class: " + cls + ", Title: '" + title + "'");
            }
            return true;
        }, IntPtr.Zero);
    }
}
