import bpy
import sys


def _mesh_objects_in_view_layer(context):
    return [
        obj
        for obj in context.view_layer.objects
        if hasattr(getattr(obj, "data", None), "vertices")
    ]


def _apply_transforms(context, objects):
    for obj in objects:
        with context.temp_override(
            active_object=obj,
            object=obj,
            selected_objects=[obj],
            selected_editable_objects=[obj],
        ):
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


class ToCenter(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.to_center"
    bl_label = "To Center"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def to_center(cls, context):
        min_x = sys.float_info.max
        max_x = -sys.float_info.max
        min_y = sys.float_info.max
        max_y = -sys.float_info.max
        min_z = sys.float_info.max
        max_z = -sys.float_info.max

        mesh_objects = _mesh_objects_in_view_layer(context)
        if not mesh_objects:
            return False

        _apply_transforms(context, mesh_objects)

        for obj in mesh_objects:
            mx = obj.matrix_world
            obj_min_x = min((mx @ v.co)[0] for v in obj.data.vertices)
            obj_max_x = max((mx @ v.co)[0] for v in obj.data.vertices)
            obj_min_y = min((mx @ v.co)[1] for v in obj.data.vertices)
            obj_max_y = max((mx @ v.co)[1] for v in obj.data.vertices)
            obj_min_z = min((mx @ v.co)[2] for v in obj.data.vertices)
            obj_max_z = max((mx @ v.co)[2] for v in obj.data.vertices)

            min_x = min(obj_min_x, min_x)
            max_x = max(obj_max_x, max_x)
            min_y = min(obj_min_y, min_y)
            max_y = max(obj_max_y, max_y)
            min_z = min(obj_min_z, min_z)
            max_z = max(obj_max_z, max_z)

        for obj in mesh_objects:
            mx = obj.matrix_world
            mx.translation.x -= min_x + (max_x - min_x) / 2
            mx.translation.y -= min_y + (max_y - min_y) / 2
            mx.translation.z -= min_z + (max_z - min_z) / 2

        _apply_transforms(context, mesh_objects)

        return True

    def execute(self, context):
        self.to_center(context)
        self.to_center(context)
        self.to_center(context)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ToCenter.bl_idname, text=ToCenter.bl_label)


def register():
    bpy.utils.register_class(ToCenter)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ToCenter)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    register()
    bpy.ops.object.to_center()
