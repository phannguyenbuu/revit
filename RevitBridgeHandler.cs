using System;
using System.Collections.Concurrent;
using System.Threading.Tasks;
using Autodesk.Revit.UI;

namespace RevitMcpBridge
{
    public class RevitTask
    {
        public Func<UIApplication, object?> Action { get; }
        public TaskCompletionSource<object?> Tcs { get; }

        public RevitTask(Func<UIApplication, object?> action)
        {
            Action = action;
            Tcs = new TaskCompletionSource<object?>(TaskCreationOptions.RunContinuationsAsynchronously);
        }
    }

    public class RevitBridgeHandler : IExternalEventHandler
    {
        private readonly ConcurrentQueue<RevitTask> _taskQueue = new();
        private ExternalEvent? _externalEvent;

        public void SetExternalEvent(ExternalEvent externalEvent)
        {
            _externalEvent = externalEvent;
        }

        public Task<object?> EnqueueAsync(Func<UIApplication, object?> action)
        {
            var task = new RevitTask(action);
            _taskQueue.Enqueue(task);
            _externalEvent?.Raise();
            return task.Tcs.Task;
        }

        public void Execute(UIApplication app)
        {
            while (_taskQueue.TryDequeue(out var task))
            {
                try
                {
                    var result = task.Action(app);
                    task.Tcs.TrySetResult(result);
                }
                catch (Exception ex)
                {
                    task.Tcs.TrySetException(ex);
                }
            }
        }

        public string GetName() => "RevitMcpBridgeExternalEventHandler";
    }
}
