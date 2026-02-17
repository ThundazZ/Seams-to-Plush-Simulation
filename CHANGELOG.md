# Changelog


- **Blender 5.0+ Support** - Updated to Blender 5.0+ API, removed support for older versions.
- New N-panel UI in 3D View tab
- Changed codebase

### New Features
- **Mesh Issue Detection** - Detects unmerged vertices, non-manifold edges, loose geometry 
- **Cloth Preset System** - Three fabric presets with customizable parameters
- **Post Preparation Options** - Scale to 5m, Fix Normals, Play Animation


### Removed Features
- **SVG Export** - Removed export to .svg files functionality


### Bug Fixes
- Fixed variable naming bug in `BoundaryAlignedRemesher`
- Updated UV preservation after remeshing
- (KDTree O(n log n) performance)


