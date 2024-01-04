import bpy
import sys


class ToFloorCenter(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.to_floor_center"
    bl_label = "To Floor Center"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def to_floor_center(cls, context):
        #    context = bpy.context
        min_x = sys.float_info.max
        max_x = sys.float_info.min
        min_y = sys.float_info.max
        max_y = sys.float_info.min
        min_z = sys.float_info.max

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
                obj_min_y = min((mx @ v.co)[1] for v in obj.data.vertices)
                obj_max_y = max((mx @ v.co)[1] for v in obj.data.vertices)
                obj_min_z = min((mx @ v.co)[2] for v in obj.data.vertices)
                min_x = min(obj_min_x, min_x)
                max_x = max(obj_max_x, max_x)
                min_y = min(obj_min_y, min_y)
                max_y = max(obj_max_y, max_y)
                min_z = min(obj_min_z, min_z)

        for obj in selected_objects:
            mx = obj.matrix_world
            if hasattr(obj.data, 'vertices'):
                mx.translation.x -= min_x + (max_x - min_x) / 2
                mx.translation.y -= min_y + (max_y - min_y) / 2
                mx.translation.z -= min_z

        for obj in selected_objects:
            context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        bpy.ops.object.select_all(action='DESELECT')

        return context.active_object is not None

    def execute(self, context):
        self.to_floor_center(context)
        self.to_floor_center(context)
        self.to_floor_center(context)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ToFloorCenter.bl_idname, text=ToFloorCenter.bl_label)


# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access).
def register():
    bpy.utils.register_class(ToFloorCenter)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ToFloorCenter)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.object.to_floor_center()
