param(
    [string]$BlenderExecutable = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe',
    [switch]$MigrateLegacyScripts
)

$ErrorActionPreference = 'Stop'

$sourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$blender52Root = Join-Path $env:APPDATA 'Blender Foundation\Blender\5.2'
$scriptsRoot = Join-Path $blender52Root 'scripts'
$addonsRoot = Join-Path $scriptsRoot 'addons'
$startupRoot = Join-Path $scriptsRoot 'startup'
$presetRoot = Join-Path $scriptsRoot 'presets\operator\export_scene.fbx'
$backupRoot = Join-Path $blender52Root ("codex-migration-backup-" + (Get-Date -Format 'yyyyMMdd-HHmmss-fffffff'))

if (-not (Test-Path -LiteralPath $BlenderExecutable -PathType Leaf)) {
    throw "Blender 5.2 executable was not found: $BlenderExecutable"
}

$version = & $BlenderExecutable --version
if ($LASTEXITCODE -ne 0 -or $version[0] -notmatch '^Blender 5\.2\.') {
    throw 'This installer requires a Blender 5.2 executable.'
}

$addonFiles = @(
    'alignment_tools.py',
    'invert_normals.py',
    'merge_meshes.py',
    'mesh_cleaner.py',
    'remove_duplicate_materials.py'
)

$legacyFiles = @(
    (Join-Path $startupRoot 'startup.py'),
    (Join-Path $addonsRoot 'to_center.py'),
    (Join-Path $addonsRoot 'to_floor_center.py'),
    (Join-Path $addonsRoot 'to_ceiling_center.py'),
    (Join-Path $addonsRoot 'to_wall_center.py'),
    (Join-Path $addonsRoot 'to_wall_floor_center.py')
)

$legacyFiles = @($legacyFiles | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
if ($legacyFiles.Count -and -not $MigrateLegacyScripts) {
    throw ("Review the following scripts before migrating. Use -MigrateLegacyScripts to back up and remove them:`n" + ($legacyFiles -join "`n"))
}

New-Item -ItemType Directory -Path $addonsRoot, $presetRoot, $backupRoot -Force | Out-Null

$filesToBackUp = @($legacyFiles) + @(Join-Path $blender52Root 'config\userpref.blend')
foreach ($name in $addonFiles) {
    $filesToBackUp += Join-Path $addonsRoot $name
}
$filesToBackUp += Join-Path $presetRoot 'Unity.py'
$filesToBackUp += Join-Path $presetRoot 'Unreal.py'

foreach ($path in $filesToBackUp) {
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        $relative = $path.Substring($blender52Root.Length).TrimStart('\')
        $backupPath = Join-Path $backupRoot $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $backupPath) -Force | Out-Null
        Copy-Item -LiteralPath $path -Destination $backupPath -Force
    }
}

foreach ($name in $addonFiles) {
    Copy-Item -LiteralPath (Join-Path $sourceRoot $name) -Destination (Join-Path $addonsRoot $name) -Force
}

Copy-Item -LiteralPath (Join-Path $sourceRoot 'presets\export_scene.fbx\Unity.py') -Destination (Join-Path $presetRoot 'Unity.py') -Force
Copy-Item -LiteralPath (Join-Path $sourceRoot 'presets\export_scene.fbx\Unreal.py') -Destination (Join-Path $presetRoot 'Unreal.py') -Force

foreach ($path in $legacyFiles) {
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        Remove-Item -LiteralPath $path -Force
    }
}

$modules = $addonFiles | ForEach-Object { [System.IO.Path]::GetFileNameWithoutExtension($_) }
$pythonModules = ($modules | ForEach-Object { "'$($_)'" }) -join ','
$pythonExpression = @"
import bpy
modules = [$pythonModules]
for module in modules:
    result = bpy.ops.preferences.addon_enable(module=module)
    if result != {'FINISHED'} or module not in bpy.context.preferences.addons:
        raise RuntimeError(f'Could not enable {module}')
if bpy.ops.wm.save_userpref() != {'FINISHED'}:
    raise RuntimeError('Could not save Blender preferences')
"@

Write-Output "Backup created at: $backupRoot"
& $BlenderExecutable --background --python-exit-code 1 --python-expr $pythonExpression
if ($LASTEXITCODE -ne 0) {
    throw "Blender returned exit code $LASTEXITCODE while enabling the add-ons"
}

Write-Output "Installed Blender 5.2 tools into: $scriptsRoot"
