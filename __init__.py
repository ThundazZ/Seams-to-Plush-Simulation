"""Plush Cloth Simulation Blender Addon

This addon prepares meshes with seams for plush cloth simulation.
Refactored for Blender 5.0+.
"""

bl_info = {
    'name': 'Seams to Plush Simulation',
    'author': 'Thomas Kole (original), ThundazZ (fork)',
    'version': (0, 0, 1),
    'blender': (5, 0, 0),
    'category': 'Cloth',
    'description': 'Prepares meshes with seams for plush cloth simulation',
    'location': 'N-panel > Tool > Plush Cloth Simulation',
}

import bpy
from bpy.utils import register_class, unregister_class

# Reload support for development
if "properties" in locals():
    import importlib
    importlib.reload(properties)
    importlib.reload(panel)
    # Reload operator submodules before reloading the operators package
    from .operators import seams_to_sewing, boundary_remesh, quick_clothsim, check_mesh, panel_execute
    importlib.reload(seams_to_sewing)
    importlib.reload(boundary_remesh)
    importlib.reload(quick_clothsim)
    importlib.reload(check_mesh)
    importlib.reload(panel_execute)
    importlib.reload(operators)
else:
    from . import properties
    from . import panel
    from . import operators

# Import classes for registration
from .properties import SeamsToPlushSettings
from .panel import VIEW3D_PT_seams_to_plush
from .operators import (
    OBJECT_OT_seams_to_plush,
    Remesher,
    QuickClothsim,
    OBJECT_OT_check_mesh_issues,
    OBJECT_OT_seams_to_plush_from_panel,
)


# Classes to register
classes = [
    SeamsToPlushSettings,
    OBJECT_OT_check_mesh_issues,
    OBJECT_OT_seams_to_plush,
    QuickClothsim,
    Remesher,
    OBJECT_OT_seams_to_plush_from_panel,
    VIEW3D_PT_seams_to_plush,
]


def draw_remesh_context_menu(self, context):
    """Add Boundary Aligned Remesh to object context menu"""
    self.layout.operator("remesh.boundary_aligned_remesh", text="Boundary Aligned Remesh")


def register():
    """Register addon classes and properties"""
    for cls in classes:
        register_class(cls)
    
    # Add property group to scene
    bpy.types.Scene.seams_to_plush_settings = \
        bpy.props.PointerProperty(type=SeamsToPlushSettings)
    
    # Add context menu entry for remesher
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_remesh_context_menu)


def unregister():
    """Unregister addon classes and properties"""
    # Remove context menu entry
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_remesh_context_menu)
    
    # Unregister classes in reverse order
    for cls in reversed(classes):
        unregister_class(cls)
    
    # Remove scene property
    if hasattr(bpy.types.Scene, 'seams_to_plush_settings'):
        del bpy.types.Scene.seams_to_plush_settings


if __name__ == "__main__":
    register()

