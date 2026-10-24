import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import mep_cad_operator

res = mep_cad_operator.run_on_active_autocad(
    action="add_leaders",
    layer="P-PIPE*",
    search_char="+",
    max_dist=5000.0,
    offset_y=250.0
)
print("OPERATOR RESULT:", res)
