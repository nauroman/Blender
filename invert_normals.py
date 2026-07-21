bl_info = {
    "name": "Nauroman Invert Normals",
    "description": "Invert polygon normals once per unique selected mesh datablock",
    "author": "Roman Naumov",
    "version": (2, 0, 0),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Object menu, F3, or Ctrl+Shift+Alt+F",
    "category": "Object",
}

import bpy


ADDON_KEYMAPS = []


def _selected_editable_meshes(context):
    unique_meshes = {}
    skipped_read_only = 0

    for obj in context.selected_objects:
        if obj.type != 'MESH' or obj.data is None:
            continue
        mesh = obj.data
        if not getattr(mesh, "is_editable", True):
            skipped_read_only += 1
            continue
        unique_meshes.setdefault(mesh.as_pointer(), mesh)

    return tuple(unique_meshes.values()), skipped_read_only


class OBJECT_OT_invert_normals(bpy.types.Operator):
    """Invert every selected unique mesh datablock exactly once"""

    bl_idname = "object.invert_normals"
    bl_label = "Invert Normals"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            cls.poll_message_set("Invert Normals is available in Object Mode")
            return False
        meshes, _ = _selected_editable_meshes(context)
        if not meshes:
            cls.poll_message_set("Select at least one editable mesh object")
            return False
        return True

    def execute(self, context):
        meshes, skipped_read_only = _selected_editable_meshes(context)
        if not meshes:
            self.report({'WARNING'}, "No editable mesh objects selected")
            return {'CANCELLED'}

        polygon_count = 0
        for mesh in meshes:
            for polygon in mesh.polygons:
                polygon.flip()
                polygon_count += 1
            mesh.update()

        message = f"Inverted {polygon_count} polygon(s) in {len(meshes)} unique mesh datablock(s)"
        if skipped_read_only:
            message += f"; skipped {skipped_read_only} read-only mesh(es)"
        self.report({'INFO'}, message)
        return {'FINISHED'}


def draw_object_menu(self, context):
    self.layout.operator(OBJECT_OT_invert_normals.bl_idname, text=OBJECT_OT_invert_normals.bl_label)


def register():
    bpy.utils.register_class(OBJECT_OT_invert_normals)
    bpy.types.VIEW3D_MT_object.append(draw_object_menu)

    keyconfig = bpy.context.window_manager.keyconfigs.addon
    if keyconfig:
        keymap = keyconfig.keymaps.new(name='Object Mode', space_type='EMPTY')
        keymap_item = keymap.keymap_items.new(
            OBJECT_OT_invert_normals.bl_idname,
            'F',
            'PRESS',
            ctrl=True,
            shift=True,
            alt=True,
        )
        ADDON_KEYMAPS.append((keymap, keymap_item))


def unregister():
    for keymap, keymap_item in ADDON_KEYMAPS:
        keymap.keymap_items.remove(keymap_item)
    ADDON_KEYMAPS.clear()

    bpy.types.VIEW3D_MT_object.remove(draw_object_menu)
    bpy.utils.unregister_class(OBJECT_OT_invert_normals)


if __name__ == "__main__":
    register()
