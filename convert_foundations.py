import ifcopenshell
import ifcopenshell.geom
import ezdxf

def ifc_to_clean_dxf(ifc_path, dxf_path):
    m = ifcopenshell.open(ifc_path)
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    doc.header['$INSUNITS'] = 6  # Meters
    
    for item in m.by_type('IfcBuildingElementProxy'):
        shape = ifcopenshell.geom.create_shape(settings, item)
        verts = shape.geometry.verts
        faces = shape.geometry.faces
        
        vertices = [(verts[i], verts[i+1], verts[i+2]) for i in range(0, len(verts), 3)]
        face_tuples = [(faces[i], faces[i+1], faces[i+2]) for i in range(0, len(faces), 3)]
        
        layer = item.Name or 'FOUNDATION'
        if layer not in doc.layers:
            doc.layers.new(name=layer)
            
        mesh = msp.add_mesh(dxfattribs={'layer': layer})
        with mesh.edit_data() as md:
            md.vertices = vertices
            md.faces = face_tuples
            
        print(f'{item.Name}: {len(vertices)} verts, {len(face_tuples)} faces exported to DXF')
        
    doc.saveas(dxf_path)
    print('Saved:', dxf_path)

if __name__ == '__main__':
    ifc_to_clean_dxf(r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\machine\foundation_001.ifc', r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\machine\foundation_001.dxf')
    ifc_to_clean_dxf(r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\machine\foundation_002.ifc', r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\machine\foundation_002.dxf')
