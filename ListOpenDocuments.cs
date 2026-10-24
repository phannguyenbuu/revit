using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ListOpenDocuments
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            var list = new List<object>();

            foreach (Document d in app.Documents)
            {
                list.Add(new
                {
                    title = d.Title,
                    path = d.PathName,
                    isFamily = d.IsFamilyDocument,
                    isMod = d.IsModified
                });
            }

            return new { count = list.Count, docs = list };
        }
    }
}
