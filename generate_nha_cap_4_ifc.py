import os
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.geom
import ifcopenshell.util.placement

def create_ifc_model(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    ifc_path = os.path.join(output_dir, "NhaCap4_BIM.ifc")
    
    # Create blank IFC4 project
    model = ifcopenshell.api.run("project.create_file", version="IFC4")
    
    # 1. Project setup
    project = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name="NhaCap4_BIM_Project")
    ifcopenshell.api.run("unit.assign_unit", model, length={"is_metric": True, "raw": "MILLIMETERS"})
    
    # Contexts
    context = ifcopenshell.api.run("context.add_context", model, context_type="Model")
    body_context = ifcopenshell.api.run(
        "context.add_context", model,
        context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=context
    )
    
    # Site, Building, Storey
    site = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSite", name="KhuDat_NhaCap4")
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=project, products=[site])
    
    building = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuilding", name="ToaNha_Cap4")
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=site, products=[building])
    
    storey = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="Tang_1")
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=building, products=[storey])
    
    # Helper to add extruded solid geometry
    def add_extrusion(product, profile_pts, depth, z_offset=0.0):
        # profile_pts is list of (x, y)
        poly = model.create_entity(
            "IfcPolyline",
            Points=[model.create_entity("IfcCartesianPoint", Coordinates=list(pt)) for pt in profile_pts]
        )
        profile = model.create_entity("IfcArbitraryClosedProfileDef", ProfileType="AREA", OuterCurve=poly)
        
        pos = model.create_entity("IfcAxis2Placement3D",
            Location=model.create_entity("IfcCartesianPoint", Coordinates=[0.0, 0.0, z_offset]),
            Axis=model.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]),
            RefDirection=model.create_entity("IfcDirection", DirectionRatios=[1.0, 0.0, 0.0])
        )
        
        solid = model.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=profile,
            Position=pos,
            ExtrudedDirection=model.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]),
            Depth=float(depth)
        )
        
        rep = model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=body_context,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[solid]
        )
        
        product.Representation = model.create_entity("IfcProductDefinitionShape", Representations=[rep])

    # 1. NỀN (IfcSlab)
    slab = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSlab", name="Nen_BeTong")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey, products=[slab])
    pts_slab = [(0.0, 0.0), (11000.0, 0.0), (11000.0, 7200.0), (0.0, 7200.0), (0.0, 0.0)]
    add_extrusion(slab, pts_slab, depth=470.0, z_offset=-470.0)

    # 2. TƯỜNG (IfcWall)
    # Tường bao ngoại thất (Back, Left, Right, Front)
    # Back wall: X: 0..11000, Y: 7000..7200, Z: 0..2800
    w_back = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Tuong_Sau")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey, products=[w_back])
    pts_w_back = [(0.0, 7000.0), (11000.0, 7000.0), (11000.0, 7200.0), (0.0, 7200.0), (0.0, 7000.0)]
    add_extrusion(w_back, pts_w_back, depth=2800.0, z_offset=0.0)

    # Left wall: X: 0..200, Y: 200..7000, Z: 0..2800
    w_left = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Tuong_Hong_Trai")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey, products=[w_left])
    pts_w_left = [(0.0, 200.0), (200.0, 200.0), (200.0, 7000.0), (0.0, 7000.0), (0.0, 200.0)]
    add_extrusion(w_left, pts_w_left, depth=2800.0, z_offset=0.0)

    # Right wall: X: 10800..11000, Y: 200..7000, Z: 0..2800
    w_right = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Tuong_Hong_Phai")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey, products=[w_right])
    pts_w_right = [(10800.0, 200.0), (11000.0, 200.0), (11000.0, 7000.0), (10800.0, 7000.0), (10800.0, 200.0)]
    add_extrusion(w_right, pts_w_right, depth=2800.0, z_offset=0.0)

    # Front wall segments
    w_front = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Tuong_Mat_Tien")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey, products=[w_front])
    # Tường mặt tiền (mục 1: 0..1500, cao 2800)
    pts_wf1 = [(0.0, 0.0), (1500.0, 0.0), (1500.0, 200.0), (0.0, 200.0), (0.0, 0.0)]
    add_extrusion(w_front, pts_wf1, depth=2800.0, z_offset=0.0)

    # 3. CỬA ĐI (IfcDoor)
    door = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcDoor", name="Cua_Chinh_4Canh")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey, products=[door])
    door.OverallWidth = 3300.0
    door.OverallHeight = 2700.0
    pts_door = [(1500.0, 30.0), (4800.0, 30.0), (4800.0, 170.0), (1500.0, 170.0), (1500.0, 30.0)]
    add_extrusion(door, pts_door, depth=2700.0, z_offset=0.0)

    # 4. CỬA SỔ (IfcWindow)
    window = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWindow", name="Cua_So_Mat_Tien")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey, products=[window])
    window.OverallWidth = 2500.0
    window.OverallHeight = 2350.0
    pts_win = [(7500.0, 40.0), (10000.0, 40.0), (10000.0, 160.0), (7500.0, 160.0), (7500.0, 40.0)]
    add_extrusion(window, pts_win, depth=2350.0, z_offset=350.0)

    # 5. MÁI (IfcRoof)
    roof = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcRoof", name="Mai_Nhat_HopNgoc")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey, products=[roof])
    pts_roof = [(-1200.0, -1200.0), (12200.0, -1200.0), (12200.0, 8400.0), (-1200.0, 8400.0), (-1200.0, -1200.0)]
    add_extrusion(roof, pts_roof, depth=2140.0, z_offset=2800.0)

    # Write IFC
    model.write(ifc_path)
    print(f"Generated IFC: {ifc_path} ({os.path.getsize(ifc_path)} bytes)")
    return ifc_path

if __name__ == "__main__":
    out_dir = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads"
    create_ifc_model(out_dir)
