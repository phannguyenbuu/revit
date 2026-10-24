import ifcopenshell
import ifcopenshell.geom
import ezdxf
import numpy as np
import os

def export_clean_ifc_to_dxf(ifc_path, dxf_path, weld_tolerance=0.0008):
    """
    Cleans micro-slivers (<0.8mm) from IFC mesh and exports to 3D DXF.
    This prevents Revit's 1/32" (0.79mm) tolerance limit from dropping faces.
    """
    model = ifcopenshell.open(ifc_path)
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)

    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    doc.header['$INSUNITS'] = 6  # Meters

    for item in model.by_type('IfcBuildingElementProxy'):
        try:
            shape = ifcopenshell.geom.create_shape(settings, item)
            verts = np.array(shape.geometry.verts).reshape(-1, 3)
            faces = np.array(shape.geometry.faces).reshape(-1, 3)

            # Weld vertices below tolerance
            rounded = np.round(verts / weld_tolerance) * weld_tolerance
            unique_verts, inverse = np.unique(rounded, axis=0, return_inverse=True)
            new_faces = inverse[faces]

            # Filter degenerate triangles
            valid_mask = (new_faces[:, 0] != new_faces[:, 1]) & \
                         (new_faces[:, 1] != new_faces[:, 2]) & \
                         (new_faces[:, 0] != new_faces[:, 2])
            clean_faces = new_faces[valid_mask]

            layer_name = item.Name or item.is_a()
            if layer_name not in doc.layers:
                doc.layers.new(name=layer_name)

            # Add 3D polyface mesh
            mesh = msp.add_mesh(dxfattribs={'layer': layer_name})
            with mesh.edit_data() as mesh_data:
                mesh_data.vertices = [tuple(v) for v in unique_verts]
                mesh_data.faces = [tuple(f) for f in clean_faces]

        except Exception as e:
            print(f"Error processing {item.Name}: {e}")

    doc.saveas(dxf_path)
    print(f"Clean DXF saved to {dxf_path}")

if __name__ == "__main__":
    ifc = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\machine\charger.ifc"
    dxf = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\machine\charger_clean.dxf"
    export_clean_ifc_to_dxf(ifc, dxf)
