"""Run inside a fresh Blender process with --factory-startup --python-exit-code 1."""

import runpy
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import alignment_tools
import invert_normals
import merge_meshes
import mesh_cleaner
import remove_duplicate_materials


def world_points(objects):
    return np.array([tuple(obj.matrix_world @ vertex.co)
                     for obj in objects for vertex in obj.data.vertices])


def bounds(objects):
    points = world_points(objects)
    return points.min(axis=0), points.max(axis=0)


def check_alignment():
    scene = bpy.context.scene
    layer = bpy.context.view_layer
    cube = layer.objects.active
    cube.location = (-8, -5, -4)
    cube.scale = (2, 1, 3)
    cube.rotation_euler = (0.1, 0.4, 0.6)
    child = cube.copy()
    scene.collection.objects.link(child)
    child.parent = cube
    child.location = (-4, 2, 1)

    excluded = bpy.data.collections.new("Excluded")
    scene.collection.children.link(excluded)
    other = cube.copy()
    excluded.objects.link(other)
    layer.layer_collection.children[excluded.name].exclude = True
    layer.update()
    original_vertices = [v.co.copy() for v in other.data.vertices]
    targets = [cube, child]
    original = world_points(targets)
    lo, hi = bounds(targets)
    np.testing.assert_allclose(alignment_tools._combined_world_bounds(targets), (lo, hi), atol=1e-5)
    for op, axes in [
        (bpy.ops.object.to_floor_center, ("mid", "mid", "min")),
        (bpy.ops.object.to_center, ("mid", "mid", "mid")),
        (bpy.ops.object.to_ceiling_center, ("mid", "mid", "max")),
        (bpy.ops.object.to_wall_center, ("mid", "max", "mid")),
        (bpy.ops.object.to_wall_floor_center, ("mid", "max", "min")),
    ]:
        assert op() == {'FINISHED'}
        low, high = bounds(targets)
        marks = dict(mid=(low + high) / 2, min=low, max=high)
        np.testing.assert_allclose([marks[name][i] for i, name in enumerate(axes)], 0, atol=1e-4)
        np.testing.assert_allclose(high - low, hi - lo, atol=1e-4)
        np.testing.assert_allclose(world_points(targets) - low, original - lo, atol=1e-4)
    assert all(v.co == co for v, co in zip(other.data.vertices, original_vertices))
    return cube


def check_materials_and_normals(cube):
    mesh = cube.data
    mesh.materials.clear()
    first = bpy.data.materials.new("Paint")
    first["asset"] = {"finish": "matte"}
    equivalent = first.copy()
    second = first.copy()
    second["asset"] = {"finish": "gloss"}
    for material in (first, second, first, equivalent):
        mesh.materials.append(material)
    for i, poly in enumerate(mesh.polygons):
        poly.material_index = i % 3
    instance = cube.copy()
    bpy.context.scene.collection.objects.link(instance)
    instance.material_slots[2].link = 'OBJECT'
    instance.material_slots[2].material = second
    bpy.ops.object.select_all(action='DESELECT')
    cube.select_set(True)
    assert bpy.ops.object.remove_duplicate_materials() == {'FINISHED'}
    assert len(mesh.materials) == 4 and instance.material_slots[2].material == second
    instance.material_slots[2].link = 'DATA'
    assert bpy.ops.object.remove_duplicate_materials() == {'FINISHED'}
    assert list(mesh.materials) == [first, second]
    assert [p.material_index for p in mesh.polygons] == [0, 1, 0, 0, 1, 0]
    instance.select_set(True)
    normal = mesh.polygons[0].normal.copy()
    assert bpy.ops.object.invert_normals() == {'FINISHED'}
    assert mesh.polygons[0].normal.dot(normal) < -0.99
    bpy.data.objects.remove(instance, do_unlink=True)


def check_cleaner():
    bpy.ops.mesh.primitive_plane_add()
    plane = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    assert bpy.ops.mesh.quick_clean_up() == {'FINISHED'}
    assert plane["nauroman_boundary_component_count"] == 1
    assert plane["nauroman_boundary_edge_count"] == 4
    bpy.ops.object.mode_set(mode='OBJECT')


def check_merge(cube):
    other_scene = bpy.data.scenes.new("Shared")
    other_scene.collection.objects.link(cube)
    count = len(bpy.context.scene.objects)
    assert bpy.ops.mesh.merge_meshes() == {'CANCELLED'}
    assert len(bpy.context.scene.objects) == count and cube in other_scene.objects[:]
    bpy.data.scenes.remove(other_scene)
    nverts = sum(len(o.data.vertices) for o in bpy.context.scene.objects if o.type == 'MESH')
    assert bpy.ops.mesh.merge_meshes() == {'FINISHED'}
    result, = bpy.context.scene.objects
    assert len(result.data.vertices) == nverts


def check_exports():
    with tempfile.TemporaryDirectory() as directory:
        for name in ("Unity", "Unreal"):
            path = ROOT / "presets/export_scene.fbx" / (name + ".py")
            # The preset normally receives the active export dialog as its operator.
            options = SimpleNamespace()
            with patch.object(bpy, "context", SimpleNamespace(active_operator=options)):
                runpy.run_path(str(path))
            target = Path(directory) / (path.stem + ".fbx")
            assert bpy.ops.export_scene.fbx(filepath=str(target), **vars(options)) == {'FINISHED'}
            assert target.stat().st_size > 0


modules = (alignment_tools, invert_normals, merge_meshes, mesh_cleaner, remove_duplicate_materials)
for module in modules:
    module.register()
try:
    cube = check_alignment()
    check_materials_and_normals(cube)
    check_cleaner()
    check_merge(cube)
    check_exports()
finally:
    for module in reversed(modules):
        module.unregister()
print("All Blender smoke checks passed")
