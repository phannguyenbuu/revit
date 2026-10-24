using System;
using System.IO;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class InspectModelVersions
    {
        public static object Run(UIApplication uiapp, dynamic args)
        {
            string baseDir = @"D:\Dropbox\_Documents\_KIEN TRUC 2026\CM Fire Protect\Coolermaster 2 - BIM model";
            var files = new List<string>
            {
                Path.Combine(baseDir, "CMF 2 - CO - Nha Xuong.rvt"),
                Path.Combine(baseDir, "CMF 2 - ELECTRIC STATION ( bổ sung 12 tuyến busway sang 3 mpđ mới).rvt")
            };

            var list = new List<object>();

            foreach (var f in files)
            {
                try
                {
                    var modelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(f);
                    var info = BasicFileInfo.Extract(f);
                    list.Add(new
                    {
                        file = Path.GetFileName(f),
                        format = info.Format,
                        isCentral = info.IsCentral,
                        isWorkshared = info.IsWorkshared,
                        isSavedInCurrentVersion = info.IsSavedInCurrentVersion,
                        isSavedInLaterVersion = info.IsSavedInLaterVersion,
                        revitVersion = info.AllLocalChangesSavedToCentral
                    });
                }
                catch (Exception ex)
                {
                    list.Add(new
                    {
                        file = Path.GetFileName(f),
                        error = ex.Message
                    });
                }
            }

            return new { success = true, files = list };
        }
    }
}
