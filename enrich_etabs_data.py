# -*- coding: utf-8 -*-
"""
enrich_etabs_data.py
Groups collinear contiguous beams on each story into continuous long beams (dầm dài).
Assigns:
- long_beam_id: DX1, DX2, DX3... for X direction; DY1, DY2, DY3... for Y direction
- span_index: 1-based index within the continuous beam
- span_count: total number of spans in the continuous beam
- direction: 'X' or 'Y'
- axis_name: 'Trục A', 'Trục 1', etc.
"""

import os
import sys
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(CURRENT_DIR, 'etabs_beam_data.json')

def match_grid(coord, grid_list, tol=500):
    for g in grid_list:
        if abs(g['ordinate'] - coord) <= tol:
            return g['id']
    return None

def enrich_beams_data(data):
    beams = data.get('beams', [])
    grids = data.get('grids', {})
    grid_y = grids.get('Y', []) # C (0), B (5970), A (11970)
    grid_x = grids.get('X', []) # 1..7

    stories = sorted(list(set(b['story'] for b in beams)))

    for story in stories:
        s_beams = [b for b in beams if b['story'] == story]
        x_beams = [b for b in s_beams if abs(b['p2'][0] - b['p1'][0]) >= abs(b['p2'][1] - b['p1'][1])]
        y_beams = [b for b in s_beams if abs(b['p2'][0] - b['p1'][0]) < abs(b['p2'][1] - b['p1'][1])]

        # -------------------------------------------------------------
        # 1. Cluster X beams (DX)
        # -------------------------------------------------------------
        y_groups = []
        for b in x_beams:
            y_mid = (b['p1'][1] + b['p2'][1]) / 2.0
            found = False
            for g in y_groups:
                if abs(g['y'] - y_mid) <= 350:
                    g['beams'].append(b)
                    found = True
                    break
            if not found:
                y_groups.append({'y': y_mid, 'beams': [b]})

        all_x_chains = []
        for yg in y_groups:
            b_list = yg['beams']
            b_list.sort(key=lambda b: min(b['p1'][0], b['p2'][0]))
            curr_chain = []
            for b in b_list:
                x_min = min(b['p1'][0], b['p2'][0])
                x_max = max(b['p1'][0], b['p2'][0])
                if not curr_chain:
                    curr_chain.append(b)
                else:
                    prev_b = curr_chain[-1]
                    prev_max = max(prev_b['p1'][0], prev_b['p2'][0])
                    if abs(x_min - prev_max) <= 500:
                        curr_chain.append(b)
                    else:
                        all_x_chains.append((yg['y'], curr_chain))
                        curr_chain = [b]
            if curr_chain:
                all_x_chains.append((yg['y'], curr_chain))

        def x_chain_sort_key(item):
            y_val, chain = item
            gid = match_grid(y_val, grid_y)
            x_start = min(min(b['p1'][0], b['p2'][0]) for b in chain)
            if gid == 'A': return (0, 1, x_start)
            if gid == 'B': return (0, 2, x_start)
            if gid == 'C': return (0, 3, x_start)
            return (1, -y_val, x_start)

        all_x_chains.sort(key=x_chain_sort_key)

        for idx, (y_val, chain) in enumerate(all_x_chains):
            name = f'DX{idx + 1}'
            gid = match_grid(y_val, grid_y)
            axis_name = f'Trục {gid}' if gid else f'Y={(y_val/1000):.1f}m'
            for sp_idx, b in enumerate(chain):
                b['long_beam_id'] = name
                b['span_index'] = sp_idx + 1
                b['span_count'] = len(chain)
                b['direction'] = 'X'
                b['axis_name'] = axis_name

        # -------------------------------------------------------------
        # 2. Cluster Y beams (DY)
        # -------------------------------------------------------------
        x_groups = []
        for b in y_beams:
            x_mid = (b['p1'][0] + b['p2'][0]) / 2.0
            found = False
            for g in x_groups:
                if abs(g['x'] - x_mid) <= 350:
                    g['beams'].append(b)
                    found = True
                    break
            if not found:
                x_groups.append({'x': x_mid, 'beams': [b]})

        all_y_chains = []
        for xg in x_groups:
            b_list = xg['beams']
            b_list.sort(key=lambda b: min(b['p1'][1], b['p2'][1]))
            curr_chain = []
            for b in b_list:
                y_min = min(b['p1'][1], b['p2'][1])
                y_max = max(b['p1'][1], b['p2'][1])
                if not curr_chain:
                    curr_chain.append(b)
                else:
                    prev_b = curr_chain[-1]
                    prev_max = max(prev_b['p1'][1], prev_b['p2'][1])
                    if abs(y_min - prev_max) <= 500:
                        curr_chain.append(b)
                    else:
                        all_y_chains.append((xg['x'], curr_chain))
                        curr_chain = [b]
            if curr_chain:
                all_y_chains.append((xg['x'], curr_chain))

        def y_chain_sort_key(item):
            x_val, chain = item
            gid = match_grid(x_val, grid_x)
            y_start = min(min(b['p1'][1], b['p2'][1]) for b in chain)
            if gid is not None:
                try:
                    g_num = int(gid)
                    return (0, g_num, y_start)
                except:
                    return (0, 99, y_start)
            return (1, x_val, y_start)

        all_y_chains.sort(key=y_chain_sort_key)

        for idx, (x_val, chain) in enumerate(all_y_chains):
            name = f'DY{idx + 1}'
            gid = match_grid(x_val, grid_x)
            axis_name = f'Trục {gid}' if gid else f'X={(x_val/1000):.1f}m'
            for sp_idx, b in enumerate(chain):
                b['long_beam_id'] = name
                b['span_index'] = sp_idx + 1
                b['span_count'] = len(chain)
                b['direction'] = 'Y'
                b['axis_name'] = axis_name

    return data

def main():
    if not os.path.exists(DATA_FILE):
        print(f"Data file not found: {DATA_FILE}")
        return
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    enrich_beams_data(data)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Enriched {len(data['beams'])} beams with DX and DY continuous beam notation in {DATA_FILE}")

if __name__ == '__main__':
    main()
