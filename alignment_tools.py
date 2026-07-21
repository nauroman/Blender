bl_info = {
    "name": "Nauroman Alignment Tools",
    "description": "Align all editable mesh objects in the active View Layer to world center, floor, ceiling, or wall planes",
    "author": "Roman Naumov",
    "version": (2, 0, 0),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Object menu and F3 search",
    "category": "Object",
}

import math

import bpy
from mathutils import Vector


ALIGNMENT_LABELS = {
    "CENTER": "To Center",
    "FLOOR_CENTER": "To Floor Center",
    "CEILING_CENTER": "To Ceiling Center",
    "WALL_CENTER": "To Wall Center",
    "WALL_FLOOR_CENTER": "To Wall Floor Center",
}


def _eligible_mesh_objects(context):
    objects = []
    skipped_empty = 0
    skipped_read_only = 0

    for obj in context.view_layer.objects:
        if obj.type != 'MESH' or obj.data is None:
            continue
        if not obj.data.vertices:
            skipped_empty += 1
            continue
        if not getattr(obj, "is_editable", True) or not getattr(obj.data, "is_editable", True):
            skipped_read_only += 1
            continue
        objects.append(obj)

    return objects, skipped_empty, skipped_read_only


def _apply_transforms(context, objects):
    if not objects:
        return

    active = objects[0]
    with context.temp_override(
        active_object=active,
        object=active,
        selected_objects=objects,
        selected_editable_objects=objects,
    ):
        result = bpy.ops.object.transform_apply(
            location=True,
            rotation=True,
            scale=True,
            isolate_users=True,
        )

    if result != {'FINISHED'}:
        raise RuntimeError("Blender could not apply object transforms")


def _make_mesh_data_single_user(objects):
    for obj in objects:
        if obj.data.users > 1:
            obj.data = obj.data.copy()


def _combined_world_bounds(objects):
    minimum = Vector((math.inf, math.inf, math.inf))
    maximum = Vector((-math.inf, -math.inf, -math.inf))

    for obj in objects:
        matrix = obj.matrix_world
        for vertex in obj.data.vertices:
            point = matrix @ vertex.co
            minimum.x = min(minimum.x, point.x)
            minimum.y = min(minimum.y, point.y)
            minimum.z = min(minimum.z, point.z)
            maximum.x = max(maximum.x, point.x)
            maximum.y = max(maximum.y, point.y)
            maximum.z = max(maximum.z, point.z)

    return minimum, maximum


def _alignment_offset(mode, minimum, maximum):
    center = (minimum + maximum) * 0.5

    if mode == "CENTER":
        return center
    if mode == "FLOOR_CENTER":
        return Vector((center.x, center.y, minimum.z))
    if mode == "CEILING_CENTER":
        return Vector((center.x, center.y, maximum.z))
    if mode == "WALL_CENTER":
        return Vector((center.x, maximum.y, center.z))
    if mode == "WALL_FLOOR_CENTER":
        return Vector((center.x, maximum.y, minimum.z))

    raise ValueError(f"Unknown alignment mode: {mode}")


def _root_objects(objects):
    object_set = set(objects)
    roots = []

    for obj in objects:
        parent = obj.parent
        while parent is not None and parent not in object_set:
            parent = parent.parent
        if parent is None:
            roots.append(obj)

    return roots


def align_meshes(context, mode):
    objects, skipped_empty, skipped_read_only = _eligible_mesh_objects(context)
    if not objects:
        return 0, skipped_empty, skipped_read_only

    _make_mesh_data_single_user(objects)
    _apply_transforms(context, objects)
    minimum, maximum = _combined_world_bounds(objects)
    offset = _alignment_offset(mode, minimum, maximum)

    for obj in _root_objects(objects):
        matrix = obj.matrix_world.copy()
        matrix.translation -= offset
        obj.matrix_world = matrix

    context.view_layer.update()
    _apply_transforms(context, objects)
    return len(objects), skipped_empty, skipped_read_only


class _AlignmentOperatorMixin:
    bl_options = {'REGISTER', 'UNDO'}
    alignment_mode = "CENTER"

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            cls.poll_message_set("Alignment is available in Object Mode")
            return False
        objects, _, _ = _eligible_mesh_objects(context)
        if not objects:
            cls.poll_message_set("No non-empty editable meshes in the active View Layer")
            return False
        return True

    def execute(self, context):
        try:
            moved, skipped_empty, skipped_read_only = align_meshes(context, self.alignment_mode)
        except RuntimeError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        if moved == 0:
            self.report({'WARNING'}, "No eligible mesh objects were found")
            return {'CANCELLED'}

        message = f"Aligned {moved} mesh object(s)"
        skipped = skipped_empty + skipped_read_only
        if skipped:
            message += f"; skipped {skipped} empty or read-only mesh(es)"
        self.report({'INFO'}, message)
        return {'FINISHED'}


class OBJECT_OT_to_center(_AlignmentOperatorMixin, bpy.types.Operator):
    """Move the combined mesh bounds center to the world origin"""

    bl_idname = "object.to_center"
    bl_label = "To Center"
    alignment_mode = "CENTER"


class OBJECT_OT_to_floor_center(_AlignmentOperatorMixin, bpy.types.Operator):
    """Center the combined mesh bounds on X/Y and place the bottom at Z = 0"""

    bl_idname = "object.to_floor_center"
    bl_label = "To Floor Center"
    alignment_mode = "FLOOR_CENTER"


class OBJECT_OT_to_ceiling_center(_AlignmentOperatorMixin, bpy.types.Operator):
    """Center the combined mesh bounds on X/Y and place the top at Z = 0"""

    bl_idname = "object.to_ceiling_center"
    bl_label = "To Ceiling Center"
    alignment_mode = "CEILING_CENTER"


class OBJECT_OT_to_wall_center(_AlignmentOperatorMixin, bpy.types.Operator):
    """Center the combined mesh bounds on X/Z and place the positive Y side at Y = 0"""

    bl_idname = "object.to_wall_center"
    bl_label = "To Wall Center"
    alignment_mode = "WALL_CENTER"


class OBJECT_OT_to_wall_floor_center(_AlignmentOperatorMixin, bpy.types.Operator):
    """Center on X and place the positive Y side and bottom at the world wall/floor planes"""

    bl_idname = "object.to_wall_floor_center"
    bl_label = "To Wall Floor Center"
    alignment_mode = "WALL_FLOOR_CENTER"


CLASSES = (
    OBJECT_OT_to_center,
    OBJECT_OT_to_floor_center,
    OBJECT_OT_to_ceiling_center,
    OBJECT_OT_to_wall_center,
    OBJECT_OT_to_wall_floor_center,
)


def draw_alignment_menu(self, context):
    layout = self.layout
    layout.separator()
    for cls in CLASSES:
        layout.operator(cls.bl_idname, text=cls.bl_label)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_object.append(draw_alignment_menu)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(draw_alignment_menu)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
