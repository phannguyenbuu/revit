using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectBimModelFolder
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            string dir = @"D:\Dropbox\_Documents\_KIEN TRUC 2026\CM Fire Protect\Coolermaster 2 - BIM model";
            
            var rvtFiles = Directory.GetFiles(dir, "*.rvt", SearchOption.AllDirectories).ToList();
            
            // Also check parent folder for rvt files
            string parentDir = @"D:\Dropbox\_Documents\_KIEN TRUC 2026\CM Fire Protect";
            var parentRvts = Directory.GetFiles(parentDir, "*.rvt", SearchOption.TopDirectoryOnly).ToList();

            var results = new List<object>();

            foreach (var file in rvtFiles.Concat(parentRvts).Distinct())
            {
                var fi = new FileInfo(file);
                object basicInfoObj = null;
                object linksObj = null;

                try
                {
                    var bfi = BasicFileInfo.Extract(file);
                    basicInfoObj = new
                    {
                        Format = bfi.Format,
                        IsWorkshared = bfi.IsWorkshared,
                        IsCentral = bfi.IsCentral,
                        CentralPath = bfi.CentralPath,
                        Username = bfi.Username
                    };
                }
                catch (Exception ex)
                {
                    basicInfoObj = new { error = ex.Message };
                }

                try
                {
                    var modelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(file);
                    var transData = TransmissionData.ReadTransmissionData(modelPath);
                    if (transData != null)
                    {
                        var externalFileRefs = transData.GetAllExternalFileReferenceIds();
                        var links = new List<object>();
                        foreach (var id in externalFileRefs)
                        {
                            var extRef = transData.GetLastSavedReferenceData(id);
                            links.Add(new
                            {
                                ExtType = extRef.ExternalFileReferenceType.ToString(),
                                Path = ModelPathUtils.ConvertModelPathToUserVisiblePath(extRef.GetPath())
                            });
                        }
                        linksObj = links;
                    }
                }
                catch (Exception ex)
                {
                    linksObj = new { error = ex.Message };
                }

                results.Add(new
                {
                    fileName = fi.Name,
                    fullPath = fi.FullName,
                    directory = fi.DirectoryName,
                    sizeMB = Math.Round((double)fi.Length / (1024 * 1024), 2),
                    lastModified = fi.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"),
                    basicInfo = basicInfoObj,
                    externalLinks = linksObj
                });
            }

            return new { count = results.Count, files = results };
        }
    }
}
