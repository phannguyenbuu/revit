import os
import ezdxf

def get_dxf_template_doc():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "dim.dxf")
    if not os.path.exists(template_path):
        template_path = os.path.expanduser("~/Downloads/dim.dxf")
    if os.path.exists(template_path):
        try:
            doc = ezdxf.readfile(template_path)
            for e in list(doc.modelspace()):
                doc.modelspace().delete_entity(e)
            # Ensure Standard style uses tahoma.ttf
            if "Standard" in doc.styles:
                doc.styles.get("Standard").dxf.font = "tahoma.ttf"
            return doc
        except Exception as e:
            print("Fallback due to:", e)
    doc = ezdxf.new("R2010", setup=True)
    if "Standard" in doc.styles:
        doc.styles.get("Standard").dxf.font = "tahoma.ttf"
    else:
        doc.styles.new("Standard", dxfattribs={"font": "tahoma.ttf"})
    return doc

def ensure_layer(doc, name, **kwargs):
    if name not in doc.layers:
        doc.layers.add(name, **kwargs)

doc = get_dxf_template_doc()
layers_to_test = [
    ("BE_TONG", dict(color=7, lineweight=15)),
    ("THEP_CHU", dict(color=1, lineweight=50)),
    ("THEP_TANG_CUONG", dict(color=6, lineweight=50)),
    ("COT_DAI", dict(color=4, lineweight=15)),
    ("DIM", dict(color=3, lineweight=9)),
    ("TRUC", dict(color=1, linetype="CENTER", lineweight=15)),
    ("TEXT", dict(color=7, lineweight=15)),
    ("KHUNG_TEN", dict(color=7, lineweight=35)),
    ("COLUMN_GRID", dict(color=1, linetype="CENTER")),
    ("BEAM_LINE", dict(color=4, lineweight=30)),
]

for name, kwargs in layers_to_test:
    # If linetype specified, ensure linetype exists or skip
    if "linetype" in kwargs and kwargs["linetype"] not in doc.linetypes:
        kwargs.pop("linetype")
    ensure_layer(doc, name, **kwargs)

msp = doc.modelspace()
msp.add_text("TEST TIẾNG VIỆT ĐÀ KIỀNG CỘT DẦM", dxfattribs={"layer": "TEXT", "style": "Standard", "height": 200})

doc.saveas("test_template_export.dxf")
print("Exported successfully, size:", os.path.getsize("test_template_export.dxf"))
