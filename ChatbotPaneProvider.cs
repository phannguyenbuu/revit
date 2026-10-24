using System;
using Autodesk.Revit.UI;

namespace RevitMcpBridge
{
    public class ChatbotPaneProvider : IDockablePaneProvider
    {
        private readonly ChatbotPaneView _view;

        public ChatbotPaneProvider(ChatbotPaneView view)
        {
            _view = view;
        }

        public void SetupDockablePane(DockablePaneProviderData data)
        {
            data.FrameworkElement = _view;
            data.InitialState = new DockablePaneState
            {
                DockPosition = DockPosition.Right,
                MinimumWidth = 320
            };
            data.VisibleByDefault = true;
        }
    }
}
