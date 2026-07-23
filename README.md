# Nauroman Blender Tools for Blender 5.2

This repository contains Roman Naumov's separate Blender 5.2 workflow scripts for asset alignment, mesh cleanup, material cleanup, full-scene mesh merging, normal inversion, and FBX export presets.

The five alignment commands share one implementation in `alignment_tools.py`. The other tools remain separate add-ons so each one can be enabled, disabled, or maintained independently.

## Compatibility and scope

- Target version: Blender 5.2 LTS.
- The installer writes only to the Blender `5.2` user configuration directory.
- Blender 5.1 files and preferences are not read, changed, or removed.
- Operators use Blender 5.2 context checks and are searchable with `F3` in their valid mode.

## Included files

| File | Purpose |
| --- | --- |
| `alignment_tools.py` | Registers all five world-alignment commands. |
| `invert_normals.py` | Inverts each unique selected Mesh datablock exactly once. |
| `merge_meshes.py` | Intentionally flattens every scene mesh and removes every other object in the current scene. |
| `mesh_cleaner.py` | Provides fast Edit Mode mesh analysis and cleanup tools. |
| `remove_duplicate_materials.py` | Removes only material slots that can be proven equivalent. |
| `presets/export_scene.fbx/Unity.py` | Existing Unity FBX preset. |
| `presets/export_scene.fbx/Unreal.py` | Existing Unreal FBX preset. |
| `install_blender_52.ps1` | Backs up the old Blender 5.2 scripts, installs these files, removes obsolete alignment duplicates, and enables the add-ons. |

## Installation on Windows

Close or restart Blender 5.2 after installation so the currently open UI reloads the operator registry.

Run from PowerShell:

```powershell
.\install_blender_52.ps1
```

The installer:

1. Targets `%APPDATA%\Blender Foundation\Blender\5.2` only.
2. Creates a timestamped backup inside that directory.
3. Copies the five separate add-on files to `scripts\addons`.
4. Copies the Unity and Unreal presets to `scripts\presets\operator\export_scene.fbx`.
5. Removes the obsolete Blender 5.2 `startup.py` and individual `to_*.py` duplicates after backing them up.
6. Enables the five add-ons and saves the Blender 5.2 preferences.

If Blender is installed elsewhere, pass its executable explicitly:

```powershell
.\install_blender_52.ps1 -BlenderExecutable 'D:\Apps\Blender 5.2\blender.exe'
```

## Manual installation

Copy these files into `%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons`:

- `alignment_tools.py`
- `invert_normals.py`
- `merge_meshes.py`
- `mesh_cleaner.py`
- `remove_duplicate_materials.py`

Enable all five in Blender 5.2 under **Edit > Preferences > Add-ons**.

Copy the preset files into:

```text
%APPDATA%\Blender Foundation\Blender\5.2\scripts\presets\operator\export_scene.fbx
```

Remove old Blender 5.2 copies of `startup.py` and the individual `to_center.py`, `to_floor_center.py`, `to_ceiling_center.py`, `to_wall_center.py`, and `to_wall_floor_center.py` files to prevent duplicate operator registration.

## Alignment Tools

Available from the Object menu and `F3`:

- `To Center`
- `To Floor Center`
- `To Ceiling Center`
- `To Wall Center`
- `To Wall Floor Center`

The commands operate on every non-empty editable mesh in the active View Layer. They intentionally preserve the previous workflow of applying location, rotation, and scale before and after alignment.

Implementation improvements:

- all five commands use one shared bounds algorithm;
- every vertex is transformed and inspected once rather than in separate coordinate passes;
- the operation runs once instead of three times;
- empty and read-only meshes are skipped safely;
- linked mesh data is made single-user when required so transforms can be applied correctly;
- parent/child mesh hierarchies are translated as one group;
- invalid Edit Mode invocation is blocked by `poll()`.

### Alignment reference

| Command | Result |
| --- | --- |
| `To Center` | Combined bounds centered on X, Y, and Z. |
| `To Floor Center` | Centered on X/Y with the lowest point at `Z = 0`. |
| `To Ceiling Center` | Centered on X/Y with the highest point at `Z = 0`. |
| `To Wall Center` | Centered on X/Z with the positive-Y side at `Y = 0`. |
| `To Wall Floor Center` | Centered on X with the positive-Y side at `Y = 0` and bottom at `Z = 0`. |

## Invert Normals

`Invert Normals` is available in the Object menu, through `F3`, and with `Ctrl + Shift + Alt + F`.

It operates once per unique selected Mesh datablock. Selecting multiple linked instances no longer flips shared polygon data multiple times. The shortcut is removed cleanly when the add-on is disabled or reloaded.

## Merge Meshes

> **Warning:** this command intentionally flattens the entire current scene. It merges all scene mesh objects and removes every camera, light, Empty, armature, and other remaining object from that scene. There is no confirmation dialog.

This destructive full-scene behavior is intentional and retained for the existing workflow. The implementation now:

- blocks invalid Edit Mode execution;
- handles linked mesh data before transforms are applied;
- avoids applying transforms to cameras, lights, and Empty objects that will be removed;
- makes objects in excluded collections temporarily accessible so scene meshes are not silently omitted;
- chooses the active mesh as the output when possible;
- reports how many meshes were merged and how many other scene objects were removed.

The operation supports Blender Undo when run interactively.

## Mesh Cleaner

Open the **Mesh Cleaner** tab in the 3D Viewport sidebar while editing a mesh.

Available tools:

- Analyze Mesh
- Check/Remove Doubles
- Check Flipped Normals
- Recalculate Outside
- Convert to Quads
- Check/Fill Holes
- Remove Loose Geometry
- Quick Clean Up

Important changes:

- duplicate detection uses `bmesh.ops.find_doubles` instead of an `O(V²)` Python loop;
- normal checking compares the current mesh with Blender's own Recalculate Outside result instead of guessing from the local origin;
- every operator has a correct Edit Mode poll;
- analysis results are stored per object rather than globally on the Scene;
- the panel displays cached results and no longer rescans every face on every redraw;
- cleanup uses direct BMesh operations and does not select every element;
- `Quick Clean Up` remains one command and does not automatically fill boundary holes;
- `Fill Holes` remains available as an explicit separate command.

`Quick Clean Up` performs, in order:

1. Remove doubles.
2. Convert suitable triangles to quads.
3. Recalculate normals outside.
4. Remove loose geometry.

## Remove Duplicate Materials

Run `Remove Duplicate Materials` in Object Mode on selected mesh objects.

The add-on handles each unique Mesh datablock once and safely remaps polygon material indices after removing slots.

It removes:

- repeated slots referencing the exact same Material datablock;
- separate materials whose complete supported material settings, node order, node properties, socket defaults, datablock references, and node links match.

It keeps materials when:

- node values or connections differ;
- referenced images or node groups differ;
- the material or node tree is animated;
- a property cannot be serialized and compared safely.

The comparison fails closed: uncertainty keeps the material instead of risking visible data loss.

## FBX presets

The existing preset names and export scope are intentionally unchanged:

- `Unity`
- `Unreal`

Both export visible mesh objects rather than selection-only. They target static mesh export and do not include armature objects or animation.

## Validation

The Blender 5.2 validation suite covers:

- registration and unregister/reload cycles for all add-ons;
- all five alignment results with rotated and scaled geometry;
- empty meshes, linked duplicates, and parent/child hierarchies;
- linked-data normal inversion;
- correct operator polls;
- fast duplicate detection and removal;
- offset-geometry normal analysis;
- Quick Clean Up boundary preservation;
- safe material preservation and exact-duplicate removal;
- intentional full-scene merge behavior;
- Unity and Unreal FBX property compatibility and actual export.

## License

See [`LICENSE`](LICENSE).
