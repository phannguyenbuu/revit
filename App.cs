using System;
using System.Reflection;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitMcpBridge
{
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class App : IExternalApplication
    {
        public static App? Instance { get; private set; }
        public RevitBridgeHandler? Handler { get; private set; }
        public ExternalEvent? ExtEvent { get; private set; }
        public HttpServer? Server { get; private set; }
        public ChatbotPaneView? ChatbotView { get; private set; }

        public static readonly DockablePaneId ChatbotPaneId = new DockablePaneId(new Guid("D3B89E21-78A1-4F23-9021-9988C7F00125"));

        public Result OnStartup(UIControlledApplication application)
        {
            Instance = this;

            try
            {
                // 1. Initialize ExternalEvent and Handler
                Handler = new RevitBridgeHandler();
                ExtEvent = ExternalEvent.Create(Handler);
                Handler.SetExternalEvent(ExtEvent);

                // 2. Start HTTP Server on port 8088 / 8090
                Server = new HttpServer(Handler, 8088);
                Server.Start();

                // 3. Register Dockable Chatbot Pane (Sidebar like Revit 2027 Autodesk Assistant)
                ChatbotView = new ChatbotPaneView();
                var paneProvider = new ChatbotPaneProvider(ChatbotView);
                application.RegisterDockablePane(ChatbotPaneId, "Revit AI Chatbot", paneProvider);

                // 4. Create Ribbon UI
                string tabName = "AI Copilot";
                try
                {
                    application.CreateRibbonTab(tabName);
                }
                catch
                {
                    // Tab may already exist
                }

                var panel = application.CreateRibbonPanel(tabName, "AI Assistant");
                string thisAssemblyPath = Assembly.GetExecutingAssembly().Location;

                // Button 1: Open AI Chatbot Pane
                var chatButtonData = new PushButtonData(
                    "AiChatbotButton",
                    "AI Chatbot\n(Sidebar)",
                    thisAssemblyPath,
                    "RevitMcpBridge.ToggleChatbotCommand"
                )
                {
                    ToolTip = "Mở khung chat AI Chatbot bên phải màn hình (Dockable Pane giống Revit 2027)"
                };
                panel.AddItem(chatButtonData);

                // Button 2: Status check
                int port = Server?.Port ?? 8090;
                var statusButtonData = new PushButtonData(
                    "AiBridgeStatus",
                    $"Server Status\n(Port {port})",
                    thisAssemblyPath,
                    "RevitMcpBridge.ShowStatusCommand"
                )
                {
                    ToolTip = $"Kiểm tra trạng thái server AI Copilot Bridge (Port {port})"
                };
                panel.AddItem(statusButtonData);

                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                TaskDialog.Show("AI Bridge Startup Error", ex.ToString());
                return Result.Failed;
            }
        }

        public Result OnShutdown(UIControlledApplication application)
        {
            try
            {
                Server?.Stop();
                ExtEvent?.Dispose();
            }
            catch
            {
            }

            return Result.Succeeded;
        }
    }

    [Transaction(TransactionMode.ReadOnly)]
    public class ToggleChatbotCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                var pane = commandData.Application.GetDockablePane(App.ChatbotPaneId);
                if (pane != null)
                {
                    if (pane.IsShown())
                    {
                        pane.Hide();
                    }
                    else
                    {
                        pane.Show();
                    }
                }
                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                TaskDialog.Show("AI Chatbot Error", ex.Message);
                return Result.Failed;
            }
        }
    }

    [Transaction(TransactionMode.ReadOnly)]
    public class ShowStatusCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            bool isRunning = App.Instance?.Server?.IsRunning ?? false;
            string docTitle = commandData.Application.ActiveUIDocument?.Document?.Title ?? "None";

            int port = App.Instance?.Server?.Port ?? 8090;
            TaskDialog.Show(
                "AI Copilot Bridge",
                $"Status: {(isRunning ? "ONLINE (Active)" : "OFFLINE")}\n" +
                $"Port: {port} (http://127.0.0.1:{port}/)\n" +
                $"Active Project: {docTitle}\n\n" +
                "The AI assistant can directly interact with this model via chat prompts."
            );

            return Result.Succeeded;
        }
    }
}
