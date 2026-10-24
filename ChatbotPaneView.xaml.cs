using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using RevitScript;

namespace RevitMcpBridge
{
    public class ChatMessageItem
    {
        public string Message { get; set; } = string.Empty;
        public string Timestamp { get; set; } = DateTime.Now.ToString("HH:mm");
        public bool IsUser { get; set; }
        public bool IsAssistant => !IsUser;
    }

    public partial class ChatbotPaneView : Page
    {
        public ObservableCollection<ChatMessageItem> Messages { get; } = new();

        public ChatbotPaneView()
        {
            InitializeComponent();
            ChatItemsControl.ItemsSource = Messages;

            AddAssistantMessage(
                "Xin chào! Tôi là Revit AI Copilot.\n\n" +
                "Tôi hỗ trợ bạn thao tác trực tiếp với mô hình và Family đang mở:\n" +
                "• 🎨 Đổi màu các đối tượng theo chuẩn bản vẽ FK2025\n" +
                "• 🔍 Soát các chi tiết hình học (Solid) và vật liệu\n" +
                "• 📊 Thống kê Levels, Grids, Sheets\n" +
                "• 💾 Lưu tài liệu tự động\n\n" +
                "Hãy chọn các nút tác vụ nhanh ở trên hoặc gõ yêu cầu trực tiếp vào khung chat!"
            );

            UpdateStatusText();
        }

        public void UpdateStatusText()
        {
            int port = App.Instance?.Server?.Port ?? 8090;
            bool running = App.Instance?.Server?.IsRunning ?? false;
            TxtStatus.Text = running ? $"🟢 MCP Server: Online (Port {port})" : "⚪ MCP Server: Offline";
        }

        public void AddUserMessage(string text)
        {
            Dispatcher.Invoke(() =>
            {
                Messages.Add(new ChatMessageItem { Message = text, IsUser = true });
                ScrollToBottom();
            });
        }

        public void AddAssistantMessage(string text)
        {
            Dispatcher.Invoke(() =>
            {
                Messages.Add(new ChatMessageItem { Message = text, IsUser = false });
                ScrollToBottom();
            });
        }

        private void ScrollToBottom()
        {
            ChatScrollViewer?.ScrollToBottom();
        }

        private async void BtnSend_Click(object sender, RoutedEventArgs e)
        {
            await SubmitMessageAsync();
        }

        private async void TxtInput_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter && !Keyboard.IsKeyDown(Key.LeftShift) && !Keyboard.IsKeyDown(Key.RightShift))
            {
                e.Handled = true;
                await SubmitMessageAsync();
            }
        }

        private async Task SubmitMessageAsync()
        {
            string prompt = TxtInput.Text.Trim();
            if (string.IsNullOrEmpty(prompt)) return;

            TxtInput.Text = string.Empty;
            AddUserMessage(prompt);

            await ProcessUserPromptAsync(prompt);
        }

        private async Task ProcessUserPromptAsync(string prompt)
        {
            var handler = App.Instance?.Handler;
            if (handler == null)
            {
                AddAssistantMessage("⚠️ RevitBridgeHandler chưa sẵn sàng.");
                return;
            }

            string pLower = prompt.ToLowerInvariant();

            try
            {
                if (pLower.Contains("đổi màu") || pLower.Contains("màu") || pLower.Contains("color") || pLower.Contains("fk2025"))
                {
                    AddAssistantMessage("⏳ Đang phân tích các đối tượng và áp dụng bộ màu chuẩn FK2025...");
                    var res = await handler.EnqueueAsync(app => ColorChanger.ApplyPdfColors(app, default));
                    AddAssistantMessage($"✅ Kết quả đổi màu:\n{FormatResult(res)}");
                }
                else if (pLower.Contains("soát") || pLower.Contains("kiểm tra") || pLower.Contains("inspect") || pLower.Contains("family") || pLower.Contains("vật liệu"))
                {
                    AddAssistantMessage("⏳ Đang quét chi tiết hình học Solid và vật liệu trong Family...");
                    var res = await handler.EnqueueAsync(app => GeometryInspector.InspectDetails(app, default));
                    AddAssistantMessage($"🔍 Thông tin kiểm tra Family:\n{FormatResult(res)}");
                }
                else if (pLower.Contains("ẩn") && (pLower.Contains("sàn") || pLower.Contains("floor")))
                {
                    AddAssistantMessage("⏳ Đang ẩn toàn bộ đối tượng Sàn (Floors) trong khung nhìn...");
                    var res = await handler.EnqueueAsync(app => FloorHider.HideFloors(app, default));
                    AddAssistantMessage($"✅ Đã ẩn toàn bộ đối tượng Sàn:\n{FormatResult(res)}");
                }
                else if ((pLower.Contains("hiện") || pLower.Contains("bỏ ẩn")) && (pLower.Contains("sàn") || pLower.Contains("floor")))
                {
                    AddAssistantMessage("⏳ Đang hiển thị lại toàn bộ đối tượng Sàn (Floors)...");
                    var res = await handler.EnqueueAsync(app => FloorHider.UnhideFloors(app, default));
                    AddAssistantMessage($"✅ Đã bỏ ẩn các đối tượng Sàn:\n{FormatResult(res)}");
                }
                else if (pLower.Contains("thống kê") || pLower.Contains("summary") || pLower.Contains("level") || pLower.Contains("grid") || pLower.Contains("sheet") || pLower.Contains("mô hình"))
                {
                    AddAssistantMessage("⏳ Đang truy xuất thông tin mô hình...");
                    var res = await handler.EnqueueAsync(app => RevitCommandDispatcher.GetModelSummary(app));
                    AddAssistantMessage($"📊 Tổng quan mô hình:\n{FormatResult(res)}");
                }
                else if (pLower.Contains("lưu") || pLower.Contains("save"))
                {
                    AddAssistantMessage("⏳ Đang lưu tài liệu...");
                    var res = await handler.EnqueueAsync(app =>
                    {
                        var doc = app.ActiveUIDocument?.Document;
                        if (doc == null) return "Không có tài liệu đang mở.";
                        doc.Save();
                        return $"Đã lưu tài liệu thành công: {doc.Title}";
                    });
                    AddAssistantMessage($"💾 {FormatResult(res)}");
                }
                else if (pLower.Contains("trạng thái") || pLower.Contains("status") || pLower.Contains("info"))
                {
                    var res = await handler.EnqueueAsync(app => RevitCommandDispatcher.GetDocumentInfo(app));
                    AddAssistantMessage($"ℹ️ Trạng thái dự án:\n{FormatResult(res)}");
                }
                else
                {
                    // General query: provide contextual BIM response
                    var docInfo = await handler.EnqueueAsync(app =>
                    {
                        var doc = app.ActiveUIDocument?.Document;
                        return doc != null ? $"Tài liệu '{doc.Title}' ({(doc.IsFamilyDocument ? "Family RFA" : "Dự án RVT")})" : "Chưa mở tài liệu";
                    });

                    AddAssistantMessage(
                        $"🤖 Nhận yêu cầu: \"{prompt}\"\n\n" +
                        $"• Mô hình hiện tại: {docInfo}\n" +
                        "• Cổng MCP Server: Port " + (App.Instance?.Server?.Port ?? 8090) + "\n\n" +
                        "💡 Gợi ý lệnh nhanh:\n" +
                        "- Bấm 'Đổi màu FK2025' để tô màu các khối Solid theo tài liệu kỹ thuật\n" +
                        "- Bấm 'Soát Family' để xem vật liệu và thể tích các đối tượng\n" +
                        "- Bấm 'Thống kê' để xem số tầng (Level), trục (Grid), bản vẽ (Sheet)\n" +
                        "- Bấm 'Lưu file' để lưu công việc hiện tại."
                    );
                }
            }
            catch (Exception ex)
            {
                AddAssistantMessage($"❌ Lỗi xử lý lệnh: {ex.Message}");
            }
        }

        private string FormatResult(object? obj)
        {
            if (obj == null) return "Trống";
            if (obj is string s) return s;

            try
            {
                return JsonSerializer.Serialize(obj, new JsonSerializerOptions { WriteIndented = true });
            }
            catch
            {
                return obj.ToString() ?? "Trống";
            }
        }

        private async void BtnColor_Click(object sender, RoutedEventArgs e)
        {
            AddUserMessage("Đổi màu các đối tượng theo chuẩn FK2025");
            await ProcessUserPromptAsync("đổi màu");
        }

        private async void BtnInspect_Click(object sender, RoutedEventArgs e)
        {
            AddUserMessage("Soát các đối tượng và vật liệu trong Family");
            await ProcessUserPromptAsync("soát family");
        }

        private async void BtnModel_Click(object sender, RoutedEventArgs e)
        {
            AddUserMessage("Thống kê tổng quan mô hình");
            await ProcessUserPromptAsync("thống kê mô hình");
        }

        private async void BtnSave_Click(object sender, RoutedEventArgs e)
        {
            AddUserMessage("Lưu tài liệu hiện tại");
            await ProcessUserPromptAsync("lưu file");
        }

        private void BtnClearHistory_Click(object sender, RoutedEventArgs e)
        {
            Messages.Clear();
            AddAssistantMessage("Lịch sử chat đã được làm sạch. Bạn có thể bắt đầu phiên làm việc mới!");
        }
    }
}
