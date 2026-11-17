# Nauroman Blender Tools

Prepare static assets for export from **Blender 5.2 LTS**. The five independent add-ons handle placement, mesh cleanup, face orientation, material slots and scene flattening. FBX presets are included for Unity and Unreal. For the earlier Blender 5.1 scripts, see the [5.1 snapshot](https://github.com/nauroman/Blender/tree/cfc4498).

## Put a chair on the floor

1. Put the chair parts in the active View Layer. Exclude collections containing other mesh assets, including any modeled floor.
2. In Object Mode, hover over the 3D Viewport, press **F3** and run **To Floor Center**.
3. The lowest vertex now sits on world `Z = 0`. The midpoint between the leftmost and rightmost vertices sits at `X = 0`, and the front-to-back midpoint sits at `Y = 0`. The chair parts keep their spacing.
4. Choose **File > Export > FBX**, pick **Unity** or **Unreal** from Operator Presets, and export.

Placement uses every eligible mesh in the active View Layer, including deselected meshes. Hiding an object with the eye icon can leave it in that layer. **Exclude its collection** to leave it out of the bounds calculation. Alignment applies location, rotation and scale to the meshes, so use an export copy when you need the original transforms.

## Install

**Windows.** Close Blender 5.2. Download and extract the repository, open PowerShell in the extracted folder and run

```powershell
.\install_blender_52.ps1
```

For a custom installation, pass `-BlenderExecutable 'D:\Apps\Blender 5.2\blender.exe'`. The installer checks the executable version, copies the five add-ons and two presets into your Blender 5.2 user directory, enables the add-ons and saves preferences. It prints the backup directory containing previous copies of replaced files and any existing `config/userpref.blend`.

If the installer finds an older `startup.py` or a legacy alignment script, it lists the paths and stops before changing files. Review the list. If those files can be retired, run `.\install_blender_52.ps1 -MigrateLegacyScripts` to back them up and remove them. To recover previous files, close Blender and copy their matching paths from the backup into the 5.2 user directory.

**Manual installation.** In Blender's Python Console, run `bpy.utils.user_resource('SCRIPTS')` to find the user scripts directory. Copy the five root-level Python files into its `addons` subdirectory. Copy both preset files from [presets/export_scene.fbx](presets/export_scene.fbx) into `presets/operator/export_scene.fbx` under the same scripts directory. Create missing folders, restart Blender and enable the tools you need under **Edit > Preferences > Add-ons**. Retire any earlier copies registering the same commands.

## Choose a tool

| Command | Mode and scope | Result |
| --- | --- | --- |
| **To Center** | Object Mode, active View Layer | Centers the combined bounds on all three world axes. |
| **To Floor Center** / **To Ceiling Center** | Object Mode, active View Layer | Centers X and Y. Places the lowest / highest vertex at Z = 0. |
| **To Wall Center** | Object Mode, active View Layer | Centers X and Z. Places the maximum Y at Y = 0. |
| **To Wall Floor Center** | Object Mode, active View Layer | Centers X. Places the maximum Y at Y = 0 and the minimum Z at Z = 0. |
| **Invert Normals** | Object Mode, selected meshes | Reverses face winding once per shared mesh. Shortcut **Ctrl + Shift + Alt + F**. |
| **Remove Duplicate Materials** | Object Mode, selected meshes | Collapses equivalent material slots and remaps faces to the surviving slots. |
| **Mesh Cleaner** | Edit Mode, active mesh | Open the 3D Viewport sidebar with **N** and select **Mesh Cleaner**. |
| **Merge Meshes** | Object Mode, entire current scene | Joins the meshes and removes all other scene objects, including cameras, lights and armatures. |

### Geometry and materials

- **Alignment** measures world-space vertices of the base meshes. Empty meshes and read-only data are skipped. It gives shared geometry separate mesh data before applying transforms. If a modifier changes the silhouette, apply it on the export copy to include its result in alignment.
- **Mesh Cleaner** shows the last analysis of the active mesh. Run **Analyze Mesh** after manual edits. **Quick Clean Up** merges vertices within 0.0001 local units, joins eligible triangles into quads, recalculates normals outside and removes loose geometry. Open boundaries are preserved until you explicitly choose **Fill Holes**.
- **Invert Normals** edits the mesh datablock. Unselected objects sharing that datablock also display the reversed faces. Blender's winding operation does not recalculate custom split normals.
- **Remove Duplicate Materials** compares material settings, node graphs and referenced data. Animated or unsupported materials can still be consolidated when slots reference the exact same datablock. A mesh with object-linked slots on any instance is skipped to preserve per-object assignments. Material datablocks remain in the file.
- **Merge Meshes** is intended for a disposable export scene. It includes meshes in excluded collections, requires at least two meshes, and runs immediately when invoked. It prefers the active mesh as the output. If an object belongs to another scene as well, use **New Scene > Full Copy** before flattening.

### FBX presets

Both presets export visible meshes, apply mesh modifiers, embed textures where supported and disable animation. Check visibility before export because the presets include deselected meshes.

| Preset | Forward | Up | Smoothing |
| --- | --- | --- | --- |
| Unity | -Z | Y | Normals only |
| Unreal | Y | Z | Face |

## Run the checks

From the repository root, run the [smoke tests](tests/blender_smoke.py) in a fresh Blender process

```sh
blender --background --factory-startup --python-exit-code 1 --python tests/blender_smoke.py
```

Use the full path to the Blender 5.2 executable if it is outside your PATH. The checks register all five add-ons, exercise placement on a rotated hierarchy, verify material assignments and normals on linked meshes, clean an open mesh, flatten a test scene and write both FBX variants to a temporary directory. A failed check exits with a nonzero status.

[MIT License](LICENSE)
