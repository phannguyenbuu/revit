using System;
using System.IO;
using System.Net;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using System.Linq;

namespace RevitMcpBridge
{
    public class HttpServer
    {
        private HttpListener _listener = new();
        private readonly RevitBridgeHandler _handler;
        private int _port;
        private CancellationTokenSource? _cts;
        private Task? _listenTask;

        public bool IsRunning => _listener?.IsListening ?? false;
        public int Port => _port;

        public HttpServer(RevitBridgeHandler handler, int port = 8088)
        {
            _handler = handler;
            _port = port;
        }

        public void Start()
        {
            if (IsRunning) return;

            int[] candidatePorts = [_port, 8090, 8092, 8094, 8088];
            var ports = candidatePorts.Distinct().ToArray();

            foreach (var p in ports)
            {
                try
                {
                    var listener = new HttpListener();
                    listener.Prefixes.Add($"http://127.0.0.1:{p}/");
                    listener.Prefixes.Add($"http://localhost:{p}/");
                    listener.Start();

                    _listener = listener;
                    _port = p;
                    _cts = new CancellationTokenSource();
                    _listenTask = Task.Run(() => ListenLoopAsync(_cts.Token));

                    SavePortInfo(_port);
                    break;
                }
                catch
                {
                    // Port unavailable, try next
                }
            }
        }

        private static void SavePortInfo(int port)
        {
            try
            {
                string text = port.ToString();
                File.WriteAllText(Path.Combine(Path.GetTempPath(), "revit_bridge_port.txt"), text);
                string repoPortFile = @"D:\Dropbox\_Documents\RevitAI\bridge_port.txt";
                File.WriteAllText(repoPortFile, text);
            }
            catch { }
        }

        public void Stop()
        {
            if (!IsRunning) return;

            _cts?.Cancel();
            try { _listener.Stop(); } catch { }
        }

        private async Task ListenLoopAsync(CancellationToken token)
        {
            while (!token.IsCancellationRequested && _listener.IsListening)
            {
                try
                {
                    var context = await _listener.GetContextAsync();
                    _ = Task.Run(() => HandleRequestAsync(context));
                }
                catch (HttpListenerException) when (token.IsCancellationRequested)
                {
                    break;
                }
                catch (ObjectDisposedException)
                {
                    break;
                }
                catch (Exception)
                {
                    // Ignore background listen errors
                }
            }
        }

        private async Task HandleRequestAsync(HttpListenerContext context)
        {
            var req = context.Request;
            var res = context.Response;

            // Add CORS
            res.Headers.Add("Access-Control-Allow-Origin", "*");
            res.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
            res.Headers.Add("Access-Control-Allow-Headers", "Content-Type, Authorization");

            if (req.HttpMethod == "OPTIONS")
            {
                res.StatusCode = 200;
                res.Close();
                return;
            }

            try
            {
                string path = req.Url?.AbsolutePath.ToLowerInvariant() ?? "";

                if (req.HttpMethod == "GET" && (path == "/api/status" || path == "/"))
                {
                    var info = await _handler.EnqueueAsync(app => RevitCommandDispatcher.GetDocumentInfo(app));
                    await SendJsonAsync(res, new { status = "online", revit = info });
                }
                else if (req.HttpMethod == "GET" && path == "/api/model")
                {
                    var summary = await _handler.EnqueueAsync(app => RevitCommandDispatcher.GetModelSummary(app));
                    await SendJsonAsync(res, summary);
                }
                else if (req.HttpMethod == "POST" && path == "/api/execute")
                {
                    using var reader = new StreamReader(req.InputStream, Encoding.UTF8);
                    string body = await reader.ReadToEndAsync();
                    using var doc = JsonDocument.Parse(body);
                    var root = doc.RootElement;

                    string action = root.GetProperty("action").GetString() ?? "";

                    object? result = action.ToLowerInvariant() switch
                    {
                        "query" => await _handler.EnqueueAsync(app =>
                        {
                            string category = root.TryGetProperty("category", out var c) ? c.GetString() ?? "" : "";
                            int limit = root.TryGetProperty("limit", out var l) ? l.GetInt32() : 50;
                            return RevitCommandDispatcher.QueryElements(app, category, limit);
                        }),
                        "create_level" => await _handler.EnqueueAsync(app =>
                        {
                            string name = root.TryGetProperty("name", out var n) ? n.GetString() ?? "" : "";
                            double elev = root.TryGetProperty("elevation", out var e) ? e.GetDouble() : 0.0;
                            return RevitCommandDispatcher.CreateLevel(app, name, elev);
                        }),
                        "create_grid" => await _handler.EnqueueAsync(app =>
                        {
                            string name = root.TryGetProperty("name", out var n) ? n.GetString() ?? "" : "";
                            double x1 = root.TryGetProperty("startX", out var sx) ? sx.GetDouble() : 0.0;
                            double y1 = root.TryGetProperty("startY", out var sy) ? sy.GetDouble() : 0.0;
                            double x2 = root.TryGetProperty("endX", out var ex) ? ex.GetDouble() : 10.0;
                            double y2 = root.TryGetProperty("endY", out var ey) ? ey.GetDouble() : 0.0;
                            return RevitCommandDispatcher.CreateGrid(app, name, x1, y1, x2, y2);
                        }),
                        "link_cad" => await _handler.EnqueueAsync(app =>
                        {
                            string dwg = root.TryGetProperty("dwgPath", out var d) ? d.GetString() ?? "" : "";
                            bool viewOnly = root.TryGetProperty("currentViewOnly", out var v) && v.GetBoolean();
                            return RevitCommandDispatcher.LinkCadDwg(app, dwg, viewOnly);
                        }),
                        "isolate_floors_3d" => await _handler.EnqueueAsync(app =>
                        {
                            return RevitCommandDispatcher.IsolateFloors3D(app, root);
                        }),
                        "save_document" => await _handler.EnqueueAsync(app =>
                        {
                            return RevitCommandDispatcher.SaveDocument(app);
                        }),
                        "execute_dynamic" => await _handler.EnqueueAsync(app =>
                        {
                            return RevitCommandDispatcher.ExecuteDynamic(app, root);
                        }),
                        "convert_ifc_to_rfa" => await _handler.EnqueueAsync(app =>
                        {
                            string ifcDir = root.TryGetProperty("ifcDir", out var id) ? id.GetString() ?? "" : "";
                            string? outputDir = root.TryGetProperty("outputDir", out var od) ? od.GetString() : null;
                            string? templatePath = root.TryGetProperty("templatePath", out var tp) ? tp.GetString() : null;
                            return IfcToRfaConverter.ConvertIfcDirectoryToRfa(app, ifcDir, outputDir, templatePath);
                        }),
                        _ => new { error = $"Unknown action: {action}" }
                    };

                    await SendJsonAsync(res, result);
                }
                else if (req.HttpMethod == "POST" && path == "/mcp")
                {
                    using var reader = new StreamReader(req.InputStream, Encoding.UTF8);
                    string body = await reader.ReadToEndAsync();
                    using var doc = JsonDocument.Parse(body);
                    var root = doc.RootElement;

                    string method = root.TryGetProperty("method", out var m) ? m.GetString() ?? "" : "";
                    object? id = root.TryGetProperty("id", out var idProp) ? idProp.Clone() : 1;

                    if (method == "tools/list")
                    {
                        var tools = new[]
                        {
                            new { name = "revit_get_status", description = "Get status of active Revit document and view" },
                            new { name = "revit_get_model_summary", description = "Get summary of levels, grids, category counts, and sheets" },
                            new { name = "revit_query_elements", description = "Query BIM elements by category (walls, doors, rooms, etc.)" },
                            new { name = "revit_create_level", description = "Create a new Level with elevation in meters" },
                            new { name = "revit_create_grid", description = "Create a new Grid with start/end coordinates in meters" },
                            new { name = "revit_link_cad", description = "Link a DWG CAD file into current active view" },
                            new { name = "revit_isolate_floors_3d", description = "Isolate each floor with Section Box and export colored 3D PCCC views" },
                            new { name = "revit_save_document", description = "Save the active Revit document" }
                        };
                        await SendJsonAsync(res, new { jsonrpc = "2.0", id, result = new { tools } });
                    }
                    else if (method == "tools/call")
                    {
                        string toolName = root.GetProperty("params").GetProperty("name").GetString() ?? "";
                        var args = root.GetProperty("params").TryGetProperty("arguments", out var a) ? a : default;

                        object? toolResult = toolName switch
                        {
                            "revit_get_status" => await _handler.EnqueueAsync(app => RevitCommandDispatcher.GetDocumentInfo(app)),
                            "revit_get_model_summary" => await _handler.EnqueueAsync(app => RevitCommandDispatcher.GetModelSummary(app)),
                            "revit_query_elements" => await _handler.EnqueueAsync(app =>
                            {
                                string cat = args.TryGetProperty("category", out var c) ? c.GetString() ?? "" : "";
                                int lim = args.TryGetProperty("limit", out var l) ? l.GetInt32() : 50;
                                return RevitCommandDispatcher.QueryElements(app, cat, lim);
                            }),
                            "revit_create_level" => await _handler.EnqueueAsync(app =>
                            {
                                string name = args.TryGetProperty("name", out var n) ? n.GetString() ?? "" : "";
                                double elev = args.TryGetProperty("elevation", out var e) ? e.GetDouble() : 0.0;
                                return RevitCommandDispatcher.CreateLevel(app, name, elev);
                            }),
                            "revit_create_grid" => await _handler.EnqueueAsync(app =>
                            {
                                string name = args.TryGetProperty("name", out var n) ? n.GetString() ?? "" : "";
                                double x1 = args.TryGetProperty("startX", out var sx) ? sx.GetDouble() : 0.0;
                                double y1 = args.TryGetProperty("startY", out var sy) ? sy.GetDouble() : 0.0;
                                double x2 = args.TryGetProperty("endX", out var ex) ? ex.GetDouble() : 10.0;
                                double y2 = args.TryGetProperty("endY", out var ey) ? ey.GetDouble() : 0.0;
                                return RevitCommandDispatcher.CreateGrid(app, name, x1, y1, x2, y2);
                            }),
                            "revit_link_cad" => await _handler.EnqueueAsync(app =>
                            {
                                string dwg = args.TryGetProperty("dwgPath", out var d) ? d.GetString() ?? "" : "";
                                bool vo = args.TryGetProperty("currentViewOnly", out var v) && v.GetBoolean();
                                return RevitCommandDispatcher.LinkCadDwg(app, dwg, vo);
                            }),
                            "revit_isolate_floors_3d" => await _handler.EnqueueAsync(app => RevitCommandDispatcher.IsolateFloors3D(app, args)),
                            "revit_save_document" => await _handler.EnqueueAsync(app => RevitCommandDispatcher.SaveDocument(app)),
                            _ => new { error = $"Unknown tool: {toolName}" }
                        };

                        await SendJsonAsync(res, new { jsonrpc = "2.0", id, result = new { content = new[] { new { type = "text", text = JsonSerializer.Serialize(toolResult) } } } });
                    }
                    else
                    {
                        await SendJsonAsync(res, new { jsonrpc = "2.0", id, error = new { code = -32601, message = "Method not found" } });
                    }
                }
                else
                {
                    res.StatusCode = 404;
                    res.Close();
                }
            }
            catch (Exception ex)
            {
                res.StatusCode = 500;
                await SendJsonAsync(res, new { error = ex.Message });
            }
        }

        private static async Task SendJsonAsync(HttpListenerResponse res, object? data)
        {
            byte[] bytes = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(data, new JsonSerializerOptions { WriteIndented = true }));
            res.ContentType = "application/json; charset=utf-8";
            res.ContentLength64 = bytes.Length;
            await res.OutputStream.WriteAsync(bytes, 0, bytes.Length);
            res.OutputStream.Close();
        }
    }
}
