bl_info = {
    "name": "Nauroman Remove Duplicate Materials",
    "description": "Safely remove duplicate material slots from selected mesh datablocks",
    "author": "Roman Naumov",
    "version": (2, 0, 0),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Object menu and F3 search",
    "category": "Material",
}

import math

import bpy


class UnsafeMaterialSignature(RuntimeError):
    pass


ID_PROPERTY_NAMES = {
    "rna_type",
    "name",
    "name_full",
    "users",
    "use_fake_user",
    "is_embedded_data",
    "is_missing",
    "is_runtime_data",
    "is_evaluated",
    "original",
    "session_uid",
    "tag",
    "library",
    "library_weak_reference",
    "override_library",
    "asset_data",
    "preview",
}

NODE_UI_PROPERTY_NAMES = {
    "select",
    "show_options",
    "show_preview",
    "show_texture",
    "width",
    "width_hidden",
    "height",
    "dimensions",
    "location",
    "parent",
}


def _float_signature(value):
    value = float(value)
    if math.isnan(value):
        return ("nan",)
    return value.hex()


def _id_signature(value):
    library = value.library.filepath if getattr(value, "library", None) else None
    return (value.bl_rna.identifier, value.name_full, library)


def _plain_value_signature(value, visited):
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return _float_signature(value)
    if isinstance(value, bpy.types.ID):
        return ("ID", _id_signature(value))
    if isinstance(value, bpy.types.bpy_struct):
        return _rna_signature(value, visited=visited)

    try:
        return tuple(_plain_value_signature(item, visited) for item in value)
    except TypeError as exc:
        raise UnsafeMaterialSignature(f"Unsupported RNA value type: {type(value).__name__}") from exc


def _custom_property_signature(value):
    if isinstance(value, dict):
        return tuple(sorted((str(key), _custom_property_signature(item)) for key, item in value.items()))
    if isinstance(value, float):
        return _float_signature(value)
    if isinstance(value, (bool, int, str)) or value is None:
        return value
    try:
        return tuple(_custom_property_signature(item) for item in value)
    except TypeError:
        return repr(value)


def _rna_signature(owner, ignored=(), visited=None):
    ignored = set(ignored) | ID_PROPERTY_NAMES
    visited = set() if visited is None else visited

    pointer = owner.as_pointer() if hasattr(owner, "as_pointer") else id(owner)
    visit_key = (owner.bl_rna.identifier, pointer)
    if visit_key in visited:
        return ("CYCLE", owner.bl_rna.identifier)

    visited.add(visit_key)
    values = []
    try:
        for prop in owner.bl_rna.properties:
            identifier = prop.identifier
            if identifier in ignored:
                continue
            try:
                value = getattr(owner, identifier)
                values.append((identifier, _plain_value_signature(value, visited)))
            except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                raise UnsafeMaterialSignature(
                    f"Could not serialize {owner.bl_rna.identifier}.{identifier}: {exc}"
                ) from exc

        try:
            custom_property_keys = owner.keys()
        except (AttributeError, TypeError):
            custom_property_keys = ()
        custom_properties = tuple(
            sorted(
                (str(key), _custom_property_signature(owner[key]))
                for key in custom_property_keys
                if key != "_RNA_UI"
            )
        )
        return owner.bl_rna.identifier, tuple(values), custom_properties
    finally:
        visited.remove(visit_key)


def _socket_signature(socket):
    default_value = None
    if hasattr(socket, "default_value"):
        default_value = _plain_value_signature(socket.default_value, set())
    default_attribute_name = getattr(socket, "default_attribute_name", None)
    return (
        socket.bl_idname,
        socket.identifier,
        default_value,
        default_attribute_name,
    )


def _node_signature(node):
    properties = _rna_signature(
        node,
        ignored={"inputs", "outputs", "internal_links"} | NODE_UI_PROPERTY_NAMES,
    )
    inputs = tuple(_socket_signature(socket) for socket in node.inputs)
    outputs = tuple(_socket_signature(socket) for socket in node.outputs)
    return node.bl_idname, properties, inputs, outputs


def _node_tree_signature(node_tree):
    if node_tree is None:
        return None
    if node_tree.animation_data is not None:
        raise UnsafeMaterialSignature("Animated node trees are not automatically deduplicated")

    nodes = list(node_tree.nodes)
    node_indices = {node.as_pointer(): index for index, node in enumerate(nodes)}
    node_signatures = tuple(_node_signature(node) for node in nodes)

    links = []
    for link in node_tree.links:
        try:
            from_socket = list(link.from_node.outputs).index(link.from_socket)
            to_socket = list(link.to_node.inputs).index(link.to_socket)
        except ValueError as exc:
            raise UnsafeMaterialSignature("Could not resolve a node link socket") from exc
        links.append(
            (
                node_indices[link.from_node.as_pointer()],
                from_socket,
                node_indices[link.to_node.as_pointer()],
                to_socket,
            )
        )

    tree_properties = _rna_signature(
        node_tree,
        ignored={"nodes", "links", "interface", "animation_data"},
    )
    return tree_properties, node_signatures, tuple(links)


def material_signature(material):
    if material.animation_data is not None:
        raise UnsafeMaterialSignature("Animated materials are not automatically deduplicated")

    material_properties = _rna_signature(
        material,
        ignored={"node_tree", "animation_data"},
    )
    return material_properties, _node_tree_signature(material.node_tree)


def _selected_unique_meshes(context):
    unique_meshes = {}
    for obj in context.selected_objects:
        if obj.type != 'MESH' or obj.data is None:
            continue
        mesh = obj.data
        if not getattr(mesh, "is_editable", True):
            continue
        unique_meshes.setdefault(mesh.as_pointer(), mesh)
    return tuple(unique_meshes.values())


def _deduplicate_mesh_slots(mesh, signature_cache):
    materials = list(mesh.materials)
    if len(materials) < 2:
        return 0, 0

    key_to_original_index = {}
    canonical_index = {}
    indices_to_remove = []
    unsafe_materials = 0

    for index, material in enumerate(materials):
        if material is None:
            key = ("EMPTY_SLOT", index)
        else:
            pointer = material.as_pointer()
            if pointer not in signature_cache:
                try:
                    signature_cache[pointer] = ("SIGNATURE", material_signature(material))
                except UnsafeMaterialSignature:
                    signature_cache[pointer] = ("MATERIAL_DATABLOCK", pointer)
                    unsafe_materials += 1
            key = signature_cache[pointer]

        if key in key_to_original_index:
            canonical_index[index] = key_to_original_index[key]
            indices_to_remove.append(index)
        else:
            key_to_original_index[key] = index
            canonical_index[index] = index

    if not indices_to_remove:
        return 0, unsafe_materials

    removed_set = set(indices_to_remove)
    kept_indices = [index for index in range(len(materials)) if index not in removed_set]
    new_index = {old_index: index for index, old_index in enumerate(kept_indices)}
    polygon_material_indices = [polygon.material_index for polygon in mesh.polygons]

    for index in sorted(indices_to_remove, reverse=True):
        mesh.materials.pop(index=index)

    for polygon, old_index in zip(mesh.polygons, polygon_material_indices):
        polygon.material_index = new_index[canonical_index.get(old_index, old_index)]

    mesh.update()
    return len(indices_to_remove), unsafe_materials


class OBJECT_OT_remove_duplicate_materials(bpy.types.Operator):
    """Remove only material slots proven equivalent from selected mesh datablocks"""

    bl_idname = "object.remove_duplicate_materials"
    bl_label = "Remove Duplicate Materials"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            cls.poll_message_set("Remove Duplicate Materials is available in Object Mode")
            return False
        meshes = _selected_unique_meshes(context)
        if not any(len(mesh.materials) >= 2 for mesh in meshes):
            cls.poll_message_set("Select an editable mesh with at least two material slots")
            return False
        return True

    def execute(self, context):
        meshes = _selected_unique_meshes(context)
        signature_cache = {}
        removed_count = 0
        unsafe_materials = 0

        for mesh in meshes:
            removed, unsafe = _deduplicate_mesh_slots(mesh, signature_cache)
            removed_count += removed
            unsafe_materials += unsafe

        message = f"Removed {removed_count} duplicate material slot(s) from {len(meshes)} unique mesh datablock(s)"
        if unsafe_materials:
            message += f"; kept {unsafe_materials} material(s) that could not be compared safely"
        self.report({'INFO'}, message)
        return {'FINISHED'}


def draw_object_menu(self, context):
    self.layout.operator(
        OBJECT_OT_remove_duplicate_materials.bl_idname,
        text=OBJECT_OT_remove_duplicate_materials.bl_label,
    )


def register():
    bpy.utils.register_class(OBJECT_OT_remove_duplicate_materials)
    bpy.types.VIEW3D_MT_object.append(draw_object_menu)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(draw_object_menu)
    bpy.utils.unregister_class(OBJECT_OT_remove_duplicate_materials)


if __name__ == "__main__":
    register()
