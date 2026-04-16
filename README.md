# Blender Centering Scripts for Blender 5.1

This repository contains a small set of Blender Python operators for quickly repositioning mesh objects by their combined bounds.

The goal is simple: make it fast to place an asset at the world center, on the floor, against a wall, or in a wall-floor corner before export or further scene work. This is especially useful when preparing models for Unity, Unreal, catalog renders, prefab creation, or any workflow where object placement needs to be predictable and repeatable.

This project is intended for Blender 5.1 and documents the current behavior of the scripts in that version.

## Why this exists

When you receive or assemble assets from different sources, their location is often inconsistent:

- the whole model may be offset from the origin
- the bottom of the asset may not sit on `Z = 0`
- the front or back of the model may not line up with a wall plane
- exporting to another tool may produce awkward placement because the mesh set is not centered

These scripts solve that by measuring the world-space bounds of the mesh objects in the active View Layer, then moving them so the combined result aligns with a chosen target position.

## Included scripts

| File | What it does |
| --- | --- |
| `startup.py` | Registers the core centering operators automatically when Blender starts. |
| `to_center.py` | Moves the combined mesh bounds to the world origin `(0, 0, 0)`. |
| `to_floor_center.py` | Centers the asset on X and Y and places its bottom on `Z = 0`. |
| `to_ceiling_center.py` | Centers the asset on X and Y and places its top on `Z = 0`. |
| `to_wall_center.py` | Centers the asset on X and Z and places its furthest positive Y side on `Y = 0`. |
| `to_wall_floor_center.py` | Centers the asset on X, places the positive Y side on `Y = 0`, and the bottom on `Z = 0`. |
| `invert_normals.py` | Flips polygon normals for the currently selected mesh objects. |

## What the operators actually move

The centering scripts move objects, not just their origin points.

In practice that means:

- the mesh objects in the active View Layer are repositioned
- world-space bounds are recalculated from actual vertex positions
- the asset ends up aligned to the chosen target plane or center

This is useful when you care about the final placement of the visible geometry, not only about the object origin.

## How the centering logic works

For the centering operators, the process is:

1. Collect mesh objects from the active View Layer.
2. Apply location, rotation, and scale to those objects.
3. Read their vertex positions in world space.
4. Compute the combined minimum and maximum bounds.
5. Shift every mesh object so the combined bounds match the requested target.
6. Apply transforms again so the result is stable for export and follow-up operations.

The scripts use Blender 5.1-compatible context handling with `context.temp_override(...)`, which avoids the View Layer selection error that older selection-based approaches can trigger in newer Blender versions.

## Operator behavior reference

### `To Center`

Moves the combined bounds center to:

- `X = 0`
- `Y = 0`
- `Z = 0`

### `To Floor Center`

Moves the asset so that:

- it is centered on X
- it is centered on Y
- its lowest point touches `Z = 0`

### `To Ceiling Center`

Moves the asset so that:

- it is centered on X
- it is centered on Y
- its highest point touches `Z = 0`

### `To Wall Center`

Moves the asset so that:

- it is centered on X
- it is centered on Z
- its furthest positive Y point touches `Y = 0`

This is useful if you treat the world Y plane as a wall.

### `To Wall Floor Center`

Moves the asset so that:

- it is centered on X
- its furthest positive Y point touches `Y = 0`
- its lowest point touches `Z = 0`

This is useful for pushing an object into a wall-floor corner.

### `Invert Normals`

Flips the polygon winding of the currently selected mesh objects and updates the mesh data.

## Compatibility

This repository is intended for Blender 5.1.

The current implementation accounts for Blender 5.1 View Layer behavior by operating on objects visible to the active View Layer instead of trying to select every object in the scene blindly.

## Installation

There are two practical ways to use this repository.

### Option 1: Auto-load the main operators at Blender startup

Copy `startup.py` into Blender's startup scripts folder.

Typical Blender 5.1 script locations:

- Windows: `%APPDATA%\Blender Foundation\Blender\5.1\scripts\startup`
- macOS: `~/Library/Application Support/Blender/5.1/scripts/startup`
- Linux: `~/.config/blender/5.1/scripts/startup`

After restarting Blender, the operators from `startup.py` are registered automatically.

### Option 2: Run an individual script manually

Open any of the standalone `.py` files in Blender's Text Editor and run it.

This is useful when:

- you only want one operator
- you want to inspect or modify the script first
- you want to register `to_ceiling_center.py` or `invert_normals.py` separately

## How to use in Blender

After registration, use one of these approaches:

- open the `Object` menu in the 3D Viewport
- press `F3` and search for the operator name

Available names depend on which scripts you loaded.

`startup.py` currently registers:

- `To Center`
- `To Floor Center`
- `To Wall Center`
- `To Wall Floor Center`

If you also run the standalone files, you can additionally register:

- `To Ceiling Center`
- `Invert Normals`

`Invert Normals` also registers the shortcut:

- `Ctrl + Shift + Alt + F`

## Important behavior notes

- The centering operators act on mesh objects in the active View Layer.
- They do not limit themselves to the current selection.
- Non-mesh objects are ignored by the bounds calculation.
- `Invert Normals` works on the current selection only.
- Because transforms are applied during processing, these operators are best used intentionally as asset-preparation tools, not as a non-destructive layout system.

## Recommended use cases

- preparing marketplace or library assets
- cleaning imported CAD or kitbash models
- aligning props before export to game engines
- normalizing placement for thumbnails and turntable renders
- moving furniture or product assets onto a clean floor plane

## Repository structure

This repository is intentionally simple. It is not packaged as a full Blender add-on yet. Instead, it provides plain Python scripts that are easy to copy, inspect, and modify.

That makes it convenient if you prefer lightweight startup scripting over add-on packaging.

## Contributing

Pull requests are welcome. If you want to change behavior, add new alignment modes, or package this as a formal add-on, feel free to open an issue or submit a PR.

## License

This project is distributed under the license included in [`LICENSE`](LICENSE).
