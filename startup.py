import bpy
import sys

class ToCenter(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.to_center"
    bl_label = "To Center"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def to_center(cls, context):
        #    context = bpy.context
        min_x = sys.float_info.max
        max_x = sys.float_info.min
        min_y = sys.float_info.max
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

        for obj in selected_objects:
            mx = obj.matrix_world
            if hasattr(obj.data, 'vertices'):
                mx.translation.x -= min_x + (max_x - min_x) / 2
                mx.translation.y -= min_y + (max_y - min_y) / 2
                mx.translation.z -= min_z + (max_z - min_z) / 2

        for obj in selected_objects:
            context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        bpy.ops.object.select_all(action='DESELECT')

        return context.active_object is not None

    def execute(self, context):
        self.to_center(context)
        self.to_center(context)
        self.to_center(context)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ToCenter.bl_idname, text=ToCenter.bl_label)


# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access).
def register():
    bpy.utils.register_class(ToCenter)
    bpy.types.VIEW3D_MT_object.append(menu_func)


register()

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


def menu_func1(self, context):
    self.layout.operator(ToFloorCenter.bl_idname, text=ToFloorCenter.bl_label)


# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access).
def register1():
    bpy.utils.register_class(ToFloorCenter)
    bpy.types.VIEW3D_MT_object.append(menu_func1)

register1()

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


def menu_func2(self, context):
    self.layout.operator(ToWallCenter.bl_idname, text=ToWallCenter.bl_label)


# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access).
def register2():
    bpy.utils.register_class(ToWallCenter)
    bpy.types.VIEW3D_MT_object.append(menu_func2)

register2()

class ToWallFloorCenter(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.to_wall_floor_center"
    bl_label = "To Wall Floor Center"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def to_wall_floor_center(cls, context):
        #    context = bpy.context
        min_x = sys.float_info.max
        max_x = sys.float_info.min
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
                obj_max_y = max((mx @ v.co)[1] for v in obj.data.vertices)
                obj_min_z = min((mx @ v.co)[2] for v in obj.data.vertices)

                min_x = min(obj_min_x, min_x)
                max_x = max(obj_max_x, max_x)
                max_y = max(obj_max_y, max_y)
                min_z = min(obj_min_z, min_z)

        for obj in selected_objects:
            mx = obj.matrix_world
            if hasattr(obj.data, 'vertices'):
                mx.translation.x -= min_x + (max_x - min_x) / 2
                mx.translation.y -= max_y
                mx.translation.z -= min_z

        for obj in selected_objects:
            context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        bpy.ops.object.select_all(action='DESELECT')

        return context.active_object is not None

    def execute(self, context):
        self.to_wall_floor_center(context)
        self.to_wall_floor_center(context)
        self.to_wall_floor_center(context)
        return {'FINISHED'}


def menu_func3(self, context):
    self.layout.operator(ToWallFloorCenter.bl_idname, text=ToWallFloorCenter.bl_label)


# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access).
def register3():
    bpy.utils.register_class(ToWallFloorCenter)
    bpy.types.VIEW3D_MT_object.append(menu_func3)


register3()

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