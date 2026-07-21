bl_info = {
    "name": "Nauroman Mesh Cleaner",
    "description": "Analyze and clean the active Edit Mode mesh with Blender-native BMesh operations",
    "author": "Rob Dickinson, maintained by Roman Naumov",
    "version": (2, 0, 0),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Sidebar > Mesh Cleaner",
    "category": "Mesh",
}

import math

import bmesh
import bpy


MERGE_DISTANCE = 0.0001
QUAD_ANGLE = math.radians(40.0)


def _active_edit_mesh(context):
    obj = context.active_object
    if obj is None or obj.type != 'MESH' or obj.mode != 'EDIT':
        return None, None
    return obj, bmesh.from_edit_mesh(obj.data)


def _update_mesh(obj, destructive=False):
    bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=destructive)


def _set_stat(obj, name, value):
    obj[f"nauroman_{name}"] = value


def _get_stat(obj, name, default):
    return obj.get(f"nauroman_{name}", default)


def _boundary_summary(bm):
    boundary_edges = [edge for edge in bm.edges if edge.is_boundary]
    unvisited = set(boundary_edges)
    components = 0

    while unvisited:
        components += 1
        stack = [unvisited.pop()]
        while stack:
            edge = stack.pop()
            for vertex in edge.verts:
                for linked in vertex.link_edges:
                    if linked in unvisited and linked.is_boundary:
                        unvisited.remove(linked)
                        stack.append(linked)

    return boundary_edges, components


def _flipped_face_count(bm):
    if not bm.faces:
        return 0

    probe = bm.copy()
    try:
        probe.faces.ensure_lookup_table()
        probe.faces.index_update()
        probe.normal_update()
        original_normals = [face.normal.copy() for face in probe.faces]
        bmesh.ops.recalc_face_normals(probe, faces=list(probe.faces))
        probe.normal_update()
        return sum(
            1
            for before, face in zip(original_normals, probe.faces)
            if before.dot(face.normal) < 0.0
        )
    finally:
        probe.free()


def _convert_triangles_to_quads(bm):
    triangles = [face for face in bm.faces if len(face.verts) == 3]
    if not triangles:
        return 0

    result = bmesh.ops.join_triangles(
        bm,
        faces=triangles,
        cmp_seam=False,
        cmp_sharp=False,
        cmp_uvs=False,
        cmp_vcols=False,
        cmp_materials=False,
        angle_face_threshold=QUAD_ANGLE,
        angle_shape_threshold=QUAD_ANGLE,
    )
    return len(result.get("faces", ()))


def _remove_loose_geometry(bm):
    removed_edges = [edge for edge in bm.edges if not edge.link_faces]
    if removed_edges:
        bmesh.ops.delete(bm, geom=removed_edges, context='EDGES')

    removed_verts = [vertex for vertex in bm.verts if not vertex.link_edges]
    if removed_verts:
        bmesh.ops.delete(bm, geom=removed_verts, context='VERTS')

    return len(removed_verts), len(removed_edges)


def _refresh_stats(obj, bm):
    duplicate_map = bmesh.ops.find_doubles(bm, verts=list(bm.verts), dist=MERGE_DISTANCE)["targetmap"]
    _set_stat(obj, "double_count", len(duplicate_map))
    _set_stat(obj, "triangle_count", sum(1 for face in bm.faces if len(face.verts) == 3))
    _set_stat(obj, "flipped_normals_count", _flipped_face_count(bm))
    boundary_edges, boundary_components = _boundary_summary(bm)
    _set_stat(obj, "boundary_edge_count", len(boundary_edges))
    _set_stat(obj, "boundary_component_count", boundary_components)


class _EditMeshOperatorMixin:
    @classmethod
    def poll(cls, context):
        obj, bm = _active_edit_mesh(context)
        if obj is None or bm is None:
            cls.poll_message_set("This command requires an active mesh in Edit Mode")
            return False
        return True


class MESH_OT_analyze_mesh(_EditMeshOperatorMixin, bpy.types.Operator):
    bl_idname = "mesh.analyze_mesh"
    bl_label = "Analyze Mesh"
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj, bm = _active_edit_mesh(context)
        _refresh_stats(obj, bm)
        self.report({'INFO'}, "Mesh analysis updated")
        return {'FINISHED'}


class MESH_OT_check_doubles(_EditMeshOperatorMixin, bpy.types.Operator):
    bl_idname = "mesh.check_doubles"
    bl_label = "Check Doubles"
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj, bm = _active_edit_mesh(context)
        duplicate_map = bmesh.ops.find_doubles(bm, verts=list(bm.verts), dist=MERGE_DISTANCE)["targetmap"]
        _set_stat(obj, "double_count", len(duplicate_map))
        self.report({'INFO'}, f"Found {len(duplicate_map)} mergeable duplicate vertex/vertices")
        return {'FINISHED'}


class MESH_OT_custom_remove_doubles(_EditMeshOperatorMixin, bpy.types.Operator):
    bl_idname = "mesh.custom_remove_doubles"
    bl_label = "Remove Doubles"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj, bm = _active_edit_mesh(context)
        before = len(bm.verts)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=MERGE_DISTANCE)
        removed = before - len(bm.verts)
        _set_stat(obj, "double_count", 0)
        _update_mesh(obj, destructive=True)
        self.report({'INFO'}, f"Removed {removed} duplicate vertex/vertices")
        return {'FINISHED'}


class MESH_OT_check_flipped_normals(_EditMeshOperatorMixin, bpy.types.Operator):
    bl_idname = "mesh.check_flipped_normals"
    bl_label = "Check Flipped Normals"
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj, bm = _active_edit_mesh(context)
        count = _flipped_face_count(bm)
        _set_stat(obj, "flipped_normals_count", count)
        self.report({'INFO'}, f"Recalculate Outside would flip {count} face(s)")
        return {'FINISHED'}


class MESH_OT_fix_flipped_normals(_EditMeshOperatorMixin, bpy.types.Operator):
    bl_idname = "mesh.fix_flipped_normals"
    bl_label = "Recalculate Outside"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj, bm = _active_edit_mesh(context)
        before = _flipped_face_count(bm)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.normal_update()
        _set_stat(obj, "flipped_normals_count", 0)
        _update_mesh(obj)
        self.report({'INFO'}, f"Recalculated normals; flipped {before} face(s)")
        return {'FINISHED'}


class MESH_OT_remove_loose_geometry(_EditMeshOperatorMixin, bpy.types.Operator):
    bl_idname = "mesh.remove_loose_geometry"
    bl_label = "Remove Loose Geometry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj, bm = _active_edit_mesh(context)
        removed_verts, removed_edges = _remove_loose_geometry(bm)
        _update_mesh(obj, destructive=True)
        self.report({'INFO'}, f"Removed {removed_verts} loose vertex/vertices and {removed_edges} loose edge(s)")
        return {'FINISHED'}


class MESH_OT_convert_to_quads(_EditMeshOperatorMixin, bpy.types.Operator):
    bl_idname = "mesh.convert_to_quads"
    bl_label = "Convert to Quads"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj, bm = _active_edit_mesh(context)
        created = _convert_triangles_to_quads(bm)
        _set_stat(obj, "triangle_count", sum(1 for face in bm.faces if len(face.verts) == 3))
        _update_mesh(obj, destructive=True)
        self.report({'INFO'}, f"Created {created} quad face(s)")
        return {'FINISHED'}


class MESH_OT_check_holes(_EditMeshOperatorMixin, bpy.types.Operator):
    bl_idname = "mesh.check_holes"
    bl_label = "Check Holes"
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj, bm = _active_edit_mesh(context)
        boundary_edges, boundary_components = _boundary_summary(bm)
        _set_stat(obj, "boundary_edge_count", len(boundary_edges))
        _set_stat(obj, "boundary_component_count", boundary_components)
        self.report(
            {'INFO'},
            f"Found {len(boundary_edges)} boundary edge(s) in {boundary_components} boundary component(s)",
        )
        return {'FINISHED'}


class MESH_OT_fix_holes(_EditMeshOperatorMixin, bpy.types.Operator):
    bl_idname = "mesh.fix_holes"
    bl_label = "Fill Holes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj, bm = _active_edit_mesh(context)
        boundary_edges, _ = _boundary_summary(bm)
        if not boundary_edges:
            self.report({'INFO'}, "No boundary holes were found")
            return {'CANCELLED'}

        result = bmesh.ops.holes_fill(bm, edges=boundary_edges, sides=0)
        _set_stat(obj, "boundary_edge_count", 0)
        _set_stat(obj, "boundary_component_count", 0)
        _update_mesh(obj, destructive=True)
        self.report({'INFO'}, f"Created {len(result.get('faces', ()))} face(s) while filling holes")
        return {'FINISHED'}


class MESH_OT_quick_clean_up(_EditMeshOperatorMixin, bpy.types.Operator):
    bl_idname = "mesh.quick_clean_up"
    bl_label = "Quick Clean Up"
    bl_description = "Remove doubles, convert suitable triangles to quads, recalculate normals, and remove loose geometry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj, bm = _active_edit_mesh(context)

        verts_before = len(bm.verts)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=MERGE_DISTANCE)
        removed_doubles = verts_before - len(bm.verts)
        created_quads = _convert_triangles_to_quads(bm)
        flipped_faces = _flipped_face_count(bm)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        removed_verts, removed_edges = _remove_loose_geometry(bm)

        _update_mesh(obj, destructive=True)
        _refresh_stats(obj, bm)
        self.report(
            {'INFO'},
            "Cleaned mesh: "
            f"{removed_doubles} duplicate vertex/vertices, {created_quads} quad(s), "
            f"{flipped_faces} flipped face(s), {removed_verts} loose vertex/vertices, "
            f"{removed_edges} loose edge(s)",
        )
        return {'FINISHED'}


class MESH_PT_mesh_cleaner(bpy.types.Panel):
    bl_label = "Mesh Cleaner"
    bl_idname = "MESH_PT_nauroman_mesh_cleaner"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Mesh Cleaner'

    @classmethod
    def poll(cls, context):
        obj, bm = _active_edit_mesh(context)
        return obj is not None and bm is not None

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        layout.operator(MESH_OT_analyze_mesh.bl_idname, icon='VIEWZOOM')

        layout.separator()
        layout.label(text="Double Geometry")
        layout.operator(MESH_OT_check_doubles.bl_idname)
        double_count = _get_stat(obj, "double_count", 0)
        layout.label(text=f"Mergeable vertices: {double_count}")
        if double_count:
            layout.operator(MESH_OT_custom_remove_doubles.bl_idname)

        layout.separator()
        layout.label(text="Triangles")
        layout.label(text=f"Triangle faces: {_get_stat(obj, 'triangle_count', 0)}")
        layout.operator(MESH_OT_convert_to_quads.bl_idname)

        layout.separator()
        layout.label(text="Normals")
        layout.operator(MESH_OT_check_flipped_normals.bl_idname)
        layout.label(text=f"Faces to flip: {_get_stat(obj, 'flipped_normals_count', 0)}")
        layout.operator(MESH_OT_fix_flipped_normals.bl_idname)

        layout.separator()
        layout.label(text="Boundaries")
        layout.operator(MESH_OT_check_holes.bl_idname)
        layout.label(text=f"Boundary edges: {_get_stat(obj, 'boundary_edge_count', 0)}")
        layout.label(text=f"Boundary components: {_get_stat(obj, 'boundary_component_count', 0)}")
        layout.operator(MESH_OT_fix_holes.bl_idname)

        layout.separator()
        layout.operator(MESH_OT_remove_loose_geometry.bl_idname)

        layout.separator()
        layout.operator(MESH_OT_quick_clean_up.bl_idname, icon='BRUSH_DATA')


def draw_edit_mesh_context_menu(self, context):
    self.layout.operator(MESH_OT_quick_clean_up.bl_idname, text=MESH_OT_quick_clean_up.bl_label)


CLASSES = (
    MESH_OT_analyze_mesh,
    MESH_OT_check_doubles,
    MESH_OT_custom_remove_doubles,
    MESH_OT_check_flipped_normals,
    MESH_OT_fix_flipped_normals,
    MESH_OT_remove_loose_geometry,
    MESH_OT_convert_to_quads,
    MESH_OT_check_holes,
    MESH_OT_fix_holes,
    MESH_OT_quick_clean_up,
    MESH_PT_mesh_cleaner,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(draw_edit_mesh_context_menu)


def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(draw_edit_mesh_context_menu)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
