# ToCenter Scripts for Blender

Python scripts for Blender provides operators that moves all objects in the scene to the center.

## Installation

1. Open Blender.
2. Go to `Edit > Preferences > Add-ons > Install...`.
3. Navigate to the `*.py` file and click `Install Add-on`.

## Usage

After installation, operators are available in Blender's F3 menu 

To Center
To Wall Center
To Floor Center
To Wall Floor Center

## How It Works

The script applies any transformations (location, rotation, scale) to each object.

For each object, it calculates the minimum and maximum x, y, and z coordinates of the object's vertices. These values are used to move the object to the center of the scene.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
