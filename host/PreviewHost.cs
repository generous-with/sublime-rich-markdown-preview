using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;

internal static class Native {
    [DllImport("user32.dll")] internal static extern bool IsWindow(IntPtr h);
    [DllImport("user32.dll")] internal static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] internal static extern IntPtr GetParent(IntPtr h);
    [DllImport("user32.dll")] internal static extern uint GetDpiForWindow(IntPtr h);
    [DllImport("user32.dll")] internal static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int width, int height, uint flags);
    [DllImport("user32.dll")] internal static extern bool ShowWindow(IntPtr h, int command);
    [DllImport("user32.dll")] internal static extern bool SetProcessDpiAwarenessContext(IntPtr context);
}

internal sealed class NativeChild : Control {
    readonly IntPtr parent;
    internal NativeChild(IntPtr hwnd) { parent = hwnd; SetStyle(ControlStyles.Opaque, true); }
    protected override CreateParams CreateParams {
        get { var cp = base.CreateParams; cp.Parent = parent; cp.Style = unchecked((int)0x46000000); cp.ExStyle = 0; cp.Caption = "Sublime Rich Markdown Preview"; return cp; }
    }
}

internal sealed class Host : ApplicationContext {
    readonly string statePath, statusPath, shellPath, profilePath;
    readonly IntPtr parent;
    readonly NativeChild child;
    readonly bool diagnostics;
    readonly Timer timer = new Timer();
    readonly JavaScriptSerializer json = new JavaScriptSerializer { MaxJsonLength = 16777216 };
    readonly Dictionary<string, object> status = new Dictionary<string, object>();
    CoreWebView2Environment environment;
    CoreWebView2Controller controller;
    bool busy, loaded;
    long lastGeneration = -1, lastEvaluation = -1;
    DateTime lastStateSeen = DateTime.UtcNow;
    DateTime lastStateWrite = DateTime.MinValue;
    Dictionary<string, object> cachedState;
    string lastStatus;

    internal Host(string state, long hwnd, string shell, string profile, bool allowDiagnostics) {
        statePath = state; statusPath = state + ".status.json"; shellPath = shell; profilePath = profile;
        parent = new IntPtr(hwnd);
        diagnostics = allowDiagnostics;
        child = new NativeChild(parent);
        var handle = child.Handle;
        status["pid"] = Process.GetCurrentProcess().Id;
        status["child_hwnd"] = handle.ToInt64();
        status["parent_hwnd"] = Native.GetParent(handle).ToInt64();
        status["expected_parent"] = hwnd;
        timer.Interval = 80;
        timer.Tick += async (sender, args) => await Tick();
        timer.Start();
        Initialize();
    }

    async void Initialize() {
        try {
            Directory.CreateDirectory(profilePath);
            environment = await CoreWebView2Environment.CreateAsync(null, profilePath);
            controller = await environment.CreateCoreWebView2ControllerAsync(child.Handle);
            controller.CoreWebView2.Settings.AreDevToolsEnabled = false;
            controller.CoreWebView2.Settings.IsStatusBarEnabled = false;
            controller.CoreWebView2.Settings.AreDefaultContextMenusEnabled = true;
            controller.CoreWebView2.Settings.IsZoomControlEnabled = true;
            controller.CoreWebView2.Settings.AreBrowserAcceleratorKeysEnabled = true;
            controller.CoreWebView2.NewWindowRequested += (sender, e) => {
                e.Handled = true;
                OpenLink(e.Uri);
            };
            controller.CoreWebView2.NavigationStarting += (sender, e) => {
                Uri destination;
                if (Uri.TryCreate(e.Uri, UriKind.Absolute, out destination) && destination.Scheme == "file" &&
                    !String.Equals(destination.LocalPath, shellPath, StringComparison.OrdinalIgnoreCase)) {
                    e.Cancel = true; return;
                }
                if (Uri.TryCreate(e.Uri, UriKind.Absolute, out destination) && destination.Scheme != "file" && destination.Scheme != "about") {
                    e.Cancel = true; OpenLink(e.Uri);
                }
            };
            controller.CoreWebView2.NavigationCompleted += async (sender, e) => {
                loaded = e.IsSuccess;
                status["loaded"] = loaded;
                status["navigation_error"] = e.WebErrorStatus.ToString();
                if (loaded) await controller.CoreWebView2.ExecuteScriptAsync("document.documentElement.dataset.embedded='true'");
                SaveStatus();
            };
            controller.CoreWebView2.Navigate(new Uri(shellPath).AbsoluteUri);
            status["runtime"] = environment.BrowserVersionString;
            status["initialized"] = true;
            SaveStatus();
        } catch (Exception error) { status["error"] = error.ToString(); SaveStatus(); }
    }

    static void OpenLink(string link) {
        Uri uri;
        if (Uri.TryCreate(link, UriKind.Absolute, out uri) && (uri.Scheme == "https" || uri.Scheme == "http"))
            Process.Start(new ProcessStartInfo(link) { UseShellExecute = true });
    }

    async Task Tick() {
        if (busy) return;
        busy = true;
        try {
            if (!Native.IsWindow(parent)) { ExitThread(); return; }
            if (!File.Exists(statePath)) {
                if ((DateTime.UtcNow - lastStateSeen).TotalSeconds > 10) ExitThread();
                return;
            }
            DateTime changed = File.GetLastWriteTimeUtc(statePath);
            if (cachedState == null || changed != lastStateWrite) {
                try { cachedState = json.Deserialize<Dictionary<string, object>>(File.ReadAllText(statePath, Encoding.UTF8)); lastStateWrite = changed; }
                catch (IOException) { return; }
            }
            Dictionary<string, object> state = cachedState;
            lastStateSeen = DateTime.UtcNow;
            if (state.ContainsKey("closed") && Convert.ToBoolean(state["closed"])) { ExitThread(); return; }
            if (state.ContainsKey("owner_pid")) {
                try { using (var owner = Process.GetProcessById(Convert.ToInt32(state["owner_pid"]))) { if (owner.HasExited) { ExitThread(); return; } } }
                catch (ArgumentException) { ExitThread(); return; }
            }
            var rect = (Dictionary<string, object>)state["rect"];
            double scale = Native.GetDpiForWindow(parent) / 96.0;
            int x = (int)Math.Round(Convert.ToDouble(rect["x"]) * scale);
            int y = (int)Math.Round(Convert.ToDouble(rect["y"]) * scale);
            int width = Math.Max(1, (int)Math.Round(Convert.ToDouble(rect["width"]) * scale));
            int height = Math.Max(1, (int)Math.Round(Convert.ToDouble(rect["height"]) * scale));
            Native.SetWindowPos(child.Handle, IntPtr.Zero, x, y, width, height, 0x0014);
            bool visible = Convert.ToBoolean(state["visible"]) && !Native.IsIconic(parent);
            Native.ShowWindow(child.Handle, visible ? 5 : 0);
            if (controller == null) return;
            controller.Bounds = new Rectangle(0, 0, width, height);
            controller.IsVisible = visible;
            controller.NotifyParentWindowPositionChanged();
            status["visible"] = visible;
            status["bounds"] = new Dictionary<string, object> { {"x", x}, {"y", y}, {"width", width}, {"height", height} };
            status["dpi_scale"] = scale;
            long generation = Convert.ToInt64(state["generation"]);
            if (loaded && generation != lastGeneration) {
                var payload = new Dictionary<string, object> { {"markdown", state["markdown"]}, {"baseUri", state["base_uri"]} };
                string response = await controller.CoreWebView2.ExecuteScriptAsync("window.updatePreview(" + json.Serialize(payload) + ")");
                status["render_result"] = response;
                lastGeneration = generation;
                status["generation"] = generation;
            }
            if (diagnostics && loaded && state.ContainsKey("evaluate")) {
                var evaluation = (Dictionary<string, object>)state["evaluate"];
                long id = Convert.ToInt64(evaluation["id"]);
                if (id != lastEvaluation) {
                    status["evaluation"] = await controller.CoreWebView2.ExecuteScriptAsync(Convert.ToString(evaluation["script"]));
                    status["evaluation_id"] = id;
                    lastEvaluation = id;
                }
            }
            if (diagnostics && loaded && state.ContainsKey("capture")) {
                string capture = Convert.ToString(state["capture"]);
                if (!File.Exists(capture)) using (var output = File.Create(capture))
                    await controller.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, output);
            }
            SaveStatus();
        } catch (Exception error) { status["error"] = error.ToString(); SaveStatus(); }
        finally { busy = false; }
    }

    void SaveStatus() {
        try { string value = json.Serialize(status); if (value != lastStatus) { File.WriteAllText(statusPath, value, new UTF8Encoding(false)); lastStatus = value; } } catch (IOException) { }
    }

    protected override void ExitThreadCore() {
        timer.Stop();
        if (controller != null) controller.Close();
        child.Dispose();
        base.ExitThreadCore();
    }
}

internal static class Program {
    [STAThread] static void Main(string[] args) {
        if (args.Length != 4 && args.Length != 5) return;
        Native.SetProcessDpiAwarenessContext(new IntPtr(-4));
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new Host(args[0], long.Parse(args[1]), args[2], args[3], args.Length == 5 && args[4] == "--diagnostics"));
    }
}
