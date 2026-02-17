# Blender Seams to Plush Cloth Simulation (Fork)

A fork of the original Seams to Sewing Pattern addon for Blender, refactored for Blender 5.0+


## What's New

This fork represents changes of the original addon:
- **Blender 5.0+ Compatibility**
- **UI/UX** - New panel based workflow
- **Mesh Analysis** - Issue detection before processing
- **Cloth Settings Presets** - Configurable settings for different fabric types
- **Workflow** - One-click setup


## Installation

1. Download this repository as a ZIP file
2. In Blender, go to `Edit > Preferences > Add-ons > Install...`
3. Select the downloaded ZIP file
4. Enable the addon "Seams to Sewing Pattern" in the list

## Troubleshooting

**Long stripes flying out after unfolding**
- Indicates non-manifold geometry.
- Run "Check Mesh Issues" first
- Repair any issues before unfolding suchs as merging vertices, filling holes.


## Credits

This is a fork of the original **Seams to Sewing Pattern** addon by **Thomas Kole**

- Original repository: https://gitlab.com/thomaskole/blender-seams-to-sewing-pattern
- Website: https://thomaskole.nl/index.html


## License

GPL V2 - See [license.txt](./license.txt)

This fork maintains the same GPL V2 license as the original addon.



