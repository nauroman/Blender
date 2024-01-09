import bpy

# Operator for inverting normals
class OBJECT_OT_invert_normals(bpy.types.Operator):
    bl_idname = "object.invert_normals"
    bl_label = "Invert Normals"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                mesh = obj.data

                # Inverting normals directly on mesh data
                for face in mesh.polygons:
                    face.flip()

                # Update mesh to reflect changes
                mesh.update()

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_invert_normals.bl_idname, text=OBJECT_OT_invert_normals.bl_label)


# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access).
def register_inv():
    bpy.utils.register_class(OBJECT_OT_invert_normals)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Object Mode', space_type='EMPTY')
        kmi = km.keymap_items.new(OBJECT_OT_invert_normals.bl_idname, 'F', 'PRESS', ctrl=True, shift=True, alt=True)

register_inv()