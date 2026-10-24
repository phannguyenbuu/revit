import os
import sys
import json
import math
import comtypes.client
from comtypes.gen import ETABSv1

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def extract():
    src = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\ETABS_IFC\CAI_TAO_PHUONG_AN_B.EDB"
    print("Connecting to ETABS OAPI...")
    helper = comtypes.client.CreateObject('ETABSv1.Helper').QueryInterface(ETABSv1.cHelper)
    app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
    app.ApplicationStart()
    sap = app.SapModel
    sap.File.OpenFile(src)
    print("Opened:", src)

    # Run Design to guarantee concrete design data exists
    print("Running Concrete Frame Design...")
    try:
        sap.DesignConcrete.StartDesign()
    except Exception as e:
        print("StartDesign notice:", e)

    # 1. Grids
    grid_data = {'X': [], 'Y': []}
    tbl_grid = 'Grid Definitions - Grid Lines'
    try:
        ret_g = sap.DatabaseTables.GetTableForDisplayArray(tbl_grid, [], '', 0, [], 0, [])
        cols = ret_g[2]
        data = ret_g[4]
        if len(data) > 0 and len(cols) > 0:
            for i in range(0, len(data), len(cols)):
                row = dict(zip(cols, data[i:i+len(cols)]))
                ltype = row.get('LineType', '')
                gid = row.get('ID', '')
                ord_val = float(row.get('Ordinate', 0))
                if 'X' in ltype:
                    grid_data['X'].append({'id': gid, 'ordinate': ord_val})
                elif 'Y' in ltype:
                    grid_data['Y'].append({'id': gid, 'ordinate': ord_val})
    except Exception as e:
        print("Grid error:", e)

    # 2. Sections
    sections = {}
    for s in sap.PropFrame.GetNameList()[1]:
        try:
            ret = sap.PropFrame.GetRectangle(s)
            sections[s] = {'depth': float(ret[1]), 'width': float(ret[2]), 'mat': str(ret[0])}
        except:
            parts = s.replace('X', 'x').replace('x', ' ').split()
            dims = [float(p) for p in parts if p.isdigit()]
            if len(dims) >= 2:
                sections[s] = {'width': dims[0], 'depth': dims[1], 'mat': 'B22.5'}
            else:
                sections[s] = {'width': 200.0, 'depth': 400.0, 'mat': 'B22.5'}

    # 3. Stories
    stories = []
    ret_s = sap.Story.GetNameList()
    if ret_s[0] > 0:
        for st in ret_s[1]:
            elev = sap.Story.GetElevation(st)[0]
            h = sap.Story.GetHeight(st)[0]
            stories.append({'name': st, 'elevation': float(elev), 'height': float(h)})
    # Sort stories by elevation ascending
    stories.sort(key=lambda s: s['elevation'])

    # 4. Frames (Columns & Beams)
    frames = sap.FrameObj.GetNameList()[1]
    beams = []
    columns = []

    def select_rebar(as_req, b):
        if as_req <= 0:
            return '2D16 (min)'
        bar_areas = {14: 153.94, 16: 201.06, 18: 254.47, 20: 314.16, 22: 380.13, 25: 490.87}
        candidates = []
        for d1 in [16, 18, 20, 22, 25]:
            for n1 in [2, 3, 4]:
                a1 = n1 * bar_areas[d1]
                if a1 >= as_req:
                    candidates.append((a1 - as_req, f"{n1}D{d1}", a1))
            for d2 in [16, 18, 20]:
                if d2 != d1:
                    a2 = 2 * bar_areas[d1] + 1 * bar_areas[d2]
                    if a2 >= as_req:
                        candidates.append((a2 - as_req, f"2D{d1}+1D{d2}", a2))
                    a3 = 2 * bar_areas[d1] + 2 * bar_areas[d2]
                    if a3 >= as_req:
                        candidates.append((a3 - as_req, f"2D{d1}+2D{d2}", a3))
        candidates.sort(key=lambda x: x[0])
        if candidates:
            best = candidates[0]
            return f"{best[1]} ({best[2]/100.0:.2f}cm²)"
        return f"4D25 (19.63cm²)"

    for f in frames:
        lbl, story = sap.FrameObj.GetLabelFromName(f)[:2]
        sec = sap.FrameObj.GetSection(f)[0]
        p1, p2 = sap.FrameObj.GetPoints(f)[:2]
        c1 = [float(x) for x in sap.PointObj.GetCoordCartesian(p1)[:3]]
        c2 = [float(x) for x in sap.PointObj.GetCoordCartesian(p2)[:3]]
        sec_info = sections.get(sec, {'width': 200.0, 'depth': 400.0})
        
        dz = abs(c2[2] - c1[2])
        dx = c2[0] - c1[0]
        dy = c2[1] - c1[1]
        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if dz > 100.0 and math.sqrt(dx*dx + dy*dy) < 50.0:
            columns.append({
                'name': f, 'label': lbl, 'story': story, 'section': sec,
                'width': float(sec_info['width']), 'depth': float(sec_info['depth']),
                'p1': c1, 'p2': c2, 'height': round(length, 1)
            })
        else:
            as_top_left, as_top_mid, as_top_right = 0.0, 0.0, 0.0
            as_bot_left, as_bot_mid, as_bot_right = 0.0, 0.0, 0.0
            as_shear = 0.0
            
            try:
                res_des = sap.DesignConcrete.GetSummaryResultsBeam(f)
                num_st = res_des[0]
                if num_st > 0:
                    top_a = res_des[4]
                    bot_a = res_des[6]
                    v_a = res_des[8]
                    
                    mid_idx = num_st // 2
                    as_top_left = float(top_a[0])
                    as_top_mid = float(top_a[mid_idx])
                    as_top_right = float(top_a[-1])
                    
                    as_bot_left = float(bot_a[0])
                    as_bot_mid = max(float(x) for x in bot_a)
                    as_bot_right = float(bot_a[-1])
                    
                    as_shear = max(float(x) for x in v_a)
            except Exception:
                pass
            
            rebar_top_l = select_rebar(as_top_left, sec_info['width'])
            rebar_top_r = select_rebar(as_top_right, sec_info['width'])
            rebar_bot = select_rebar(as_bot_mid, sec_info['width'])
            stirrup = 'd8a100/a200' if as_shear <= 0.6 else ('d8a100' if as_shear <= 1.0 else 'd10a100')
            
            beams.append({
                'name': f, 'label': lbl, 'story': story, 'section': sec,
                'width': float(sec_info['width']), 'depth': float(sec_info['depth']),
                'p1': c1, 'p2': c2, 'length': round(length, 1),
                'as_top_left_cm2': round(as_top_left / 100.0, 2),
                'as_top_mid_cm2': round(as_top_mid / 100.0, 2),
                'as_top_right_cm2': round(as_top_right / 100.0, 2),
                'as_bot_left_cm2': round(as_bot_left / 100.0, 2),
                'as_bot_mid_cm2': round(as_bot_mid / 100.0, 2),
                'as_bot_right_cm2': round(as_bot_right / 100.0, 2),
                'as_shear_cm2_m': round(as_shear * 10.0, 2),
                'rebar_top_left': rebar_top_l,
                'rebar_top_right': rebar_top_r,
                'rebar_bot_mid': rebar_bot,
                'stirrup': stirrup
            })

    # Areas (stairs and slabs)
    areas_list = []
    try:
        area_names = sap.AreaObj.GetNameList()[1]
        for a in area_names:
            lbl, story = sap.AreaObj.GetLabelFromName(a)[:2]
            prop = sap.AreaObj.GetProperty(a)[0]
            pts = sap.AreaObj.GetPoints(a)[1]
            coords = [[float(x) for x in sap.PointObj.GetCoordCartesian(p)[:3]] for p in pts]
            areas_list.append({
                'name': a, 'label': lbl, 'story': story, 'prop': prop,
                'coords': coords
            })
    except Exception as e:
        print("Areas error:", e)

    app.ApplicationExit(False)

    out_file = r"d:\Dropbox\_Documents\RevitAI\etabs_beam_data.json"
    data_out = {
        'model_name': 'CAI_TAO_PHUONG_AN_B.EDB',
        'grids': grid_data,
        'sections': sections,
        'stories': stories,
        'beams': beams,
        'columns': columns,
        'areas': areas_list
    }
    try:
        from enrich_etabs_data import enrich_beams_data
        data_out = enrich_beams_data(data_out)
    except Exception as e:
        print("Enrich notice:", e)

    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(data_out, f, ensure_ascii=False, indent=2)

    print(f"DONE! Exported {len(beams)} beams, {len(columns)} columns, {len(areas_list)} areas to {out_file}")

if __name__ == '__main__':
    extract()
