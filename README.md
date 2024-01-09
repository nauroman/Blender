# ToCenter Scripts for Blender

Python scripts for Blender provides operators that moves all objects in the scene to the center. Invert Normals - invert all selected objects normals.

## Installation

Copy startup.py to 'C:\Users\user\AppData\Roaming\Blender Foundation\Blender\4.0\scripts\startup' (for Windows users)

## Usage

After installation, operators are available in Blender's F3 menu 

- To Center
- To Wall Center
- To Floor Center
- To Wall Floor Center
- Invert Normals

Invert Normals shortkey is CTRL+ALT+SHIFT+F

## How It Works

The script applies any transformations (location, rotation, scale) to each object.

For each object, it calculates the minimum and maximum x, y, and z coordinates of the object's vertices. These values are used to move the object to the center of the scene.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
