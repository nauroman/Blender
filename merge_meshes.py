bl_info = {
    "name": "Nauroman Mesh Merger",
    "description": "Flatten all mesh objects in the current scene into one mesh and remove every other scene object",
    "author": "Roman Naumov",
    "version": (2, 0, 0),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Add > Mesh > Merge Meshes and F3 search",
    "warning": "This intentionally removes every other object from the current scene",
    "category": "Mesh",
}

import bpy


def _scene_mesh_objects(context):
    return [obj for obj in context.scene.objects if obj.type == 'MESH' and obj.data is not None]


def _make_scene_objects_accessible(context, objects):
    collection = context.collection or context.scene.collection

    for obj in objects:
        if collection.objects.get(obj.name) is None:
            collection.objects.link(obj)
        obj.hide_select = False
        obj.hide_viewport = False
        obj.hide_set(False)

    context.view_layer.update()


def _make_mesh_data_single_user(objects):
    for obj in objects:
        if obj.data.users > 1:
            obj.data = obj.data.copy()


class MESH_OT_merge_meshes(bpy.types.Operator):
    """Flatten every scene mesh and remove every other object from the current scene"""

    bl_idname = "mesh.merge_meshes"
    bl_label = "Merge Meshes"
    bl_description = "Merge all scene meshes and remove all other current-scene objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            cls.poll_message_set("Merge Meshes is available in Object Mode")
            return False
        if len(_scene_mesh_objects(context)) < 2:
            cls.poll_message_set("The current scene needs at least two mesh objects")
            return False
        return True

    def execute(self, context):
        mesh_objects = _scene_mesh_objects(context)
        if len(mesh_objects) < 2:
            self.report({'WARNING'}, "Need at least two mesh objects to merge")
            return {'CANCELLED'}

        read_only = [
            obj.name
            for obj in mesh_objects
            if not getattr(obj, "is_editable", True) or not getattr(obj.data, "is_editable", True)
        ]
        if read_only:
            self.report({'ERROR'}, "Cannot flatten read-only mesh objects: " + ", ".join(read_only[:5]))
            return {'CANCELLED'}

        scene_objects = list(context.scene.objects)
        removed_object_count = len(scene_objects) - 1
        _make_scene_objects_accessible(context, scene_objects)
        _make_mesh_data_single_user(mesh_objects)

        bpy.ops.object.select_all(action='DESELECT')
        for obj in mesh_objects:
            obj.select_set(True)

        active = context.active_object if context.active_object in mesh_objects else min(mesh_objects, key=lambda obj: obj.name)
        context.view_layer.objects.active = active

        with context.temp_override(
            active_object=active,
            object=active,
            selected_objects=mesh_objects,
            selected_editable_objects=mesh_objects,
        ):
            bpy.ops.object.transform_apply(
                location=True,
                rotation=True,
                scale=True,
                isolate_users=True,
            )
            join_result = bpy.ops.object.join()

        if join_result != {'FINISHED'}:
            self.report({'ERROR'}, "Blender could not join the scene meshes")
            return {'CANCELLED'}

        merged_object = context.view_layer.objects.active
        merged_object.name = active.name

        with context.temp_override(
            active_object=merged_object,
            object=merged_object,
            selected_objects=[merged_object],
            selected_editable_objects=[merged_object],
        ):
            bpy.ops.object.transform_apply(
                location=True,
                rotation=True,
                scale=True,
                isolate_users=True,
            )

        bpy.ops.object.select_all(action='DESELECT')
        objects_to_delete = [obj for obj in context.scene.objects if obj != merged_object]
        for obj in objects_to_delete:
            obj.select_set(True)

        if objects_to_delete:
            with context.temp_override(
                active_object=objects_to_delete[0],
                object=objects_to_delete[0],
                selected_objects=objects_to_delete,
                selected_editable_objects=[obj for obj in objects_to_delete if getattr(obj, "is_editable", True)],
            ):
                bpy.ops.object.delete(use_global=False)

        merged_object.select_set(True)
        context.view_layer.objects.active = merged_object

        self.report(
            {'INFO'},
            f"Merged {len(mesh_objects)} mesh object(s) and removed {removed_object_count} other scene object(s)",
        )
        return {'FINISHED'}


def draw_mesh_add_menu(self, context):
    self.layout.operator(MESH_OT_merge_meshes.bl_idname, text=MESH_OT_merge_meshes.bl_label)


def register():
    bpy.utils.register_class(MESH_OT_merge_meshes)
    bpy.types.VIEW3D_MT_mesh_add.append(draw_mesh_add_menu)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(draw_mesh_add_menu)
    bpy.utils.unregister_class(MESH_OT_merge_meshes)


if __name__ == "__main__":
    register()
