import bpy
import sys


class ToWallCenter(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.to_wall_center"
    bl_label = "To Wall Center"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def to_wall_center(cls, context):
        #    context = bpy.context
        min_x = sys.float_info.max
        max_x = sys.float_info.min
        max_y = sys.float_info.min
        min_z = sys.float_info.max
        max_z = sys.float_info.min
        scene = context.scene

        bpy.ops.object.select_all(action='DESELECT')

        for obj in scene.objects:
            obj.select_set(True)

        selected_objects = context.selected_objects

        for obj in selected_objects:
            context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        for obj in selected_objects:
            mx = obj.matrix_world
            if hasattr(obj.data, 'vertices'):
                obj_min_x = min((mx @ v.co)[0] for v in obj.data.vertices)
                obj_max_x = max((mx @ v.co)[0] for v in obj.data.vertices)
                obj_max_y = max((mx @ v.co)[1] for v in obj.data.vertices)
                obj_min_z = min((mx @ v.co)[2] for v in obj.data.vertices)
                obj_max_z = max((mx @ v.co)[2] for v in obj.data.vertices)

                min_x = min(obj_min_x, min_x)
                max_x = max(obj_max_x, max_x)
                max_y = max(obj_max_y, max_y)
                min_z = min(obj_min_z, min_z)
                max_z = max(obj_max_z, max_z)

        for obj in selected_objects:
            mx = obj.matrix_world
            if hasattr(obj.data, 'vertices'):
                mx.translation.x -= min_x + (max_x - min_x) / 2
                mx.translation.y -= max_y
                mx.translation.z -= min_z + (max_z - min_z) / 2

        for obj in selected_objects:
            context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        bpy.ops.object.select_all(action='DESELECT')

        return context.active_object is not None

    def execute(self, context):
        self.to_wall_center(context)
        self.to_wall_center(context)
        self.to_wall_center(context)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ToWallCenter.bl_idname, text=ToWallCenter.bl_label)


# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access).
def register():
    bpy.utils.register_class(ToWallCenter)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ToWallCenter)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.object.to_wall_center()
