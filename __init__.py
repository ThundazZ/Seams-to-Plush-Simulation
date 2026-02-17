"""Plush Cloth Simulation Blender Addon

This addon prepares meshes with seams for plush cloth simulation.
Refactored for Blender 5.0+.
"""

bl_info = {
    'name': 'Plush Cloth Simulation',
    'author': 'Thomas Kole (original), rtghgvf (fork)',
    'version': 'First Init (0, 0)',
    'blender': (5, 0, 0),
    'category': 'Cloth',
    'description': 'Prepares meshes with seams for plush cloth simulation',
    'location': 'N-panel > Tool > Plush Cloth Simulation',
}

import bpy
from bpy.utils import register_class, unregister_class

# Reload support for development
if "bpy" in locals():
    import importlib
    
    # Reload core modules
    from . import properties
    from . import panel
    from . import operators
    
    importlib.reload(properties)
    importlib.reload(panel)
    importlib.reload(operators)
else:
    from . import properties
    from . import panel
    from . import operators

# Import classes for registration
from .properties import SeamsToSewingPatternSettings
from .panel import VIEW3D_PT_seams_to_sewing_pattern
from .operators import (
    Seams_To_SewingPattern,
    Remesher,
    QuickClothsim,
    OBJECT_OT_check_mesh_issues,
    OBJECT_OT_seams_to_sewing_pattern_from_panel,
)


# Classes to register
classes = [
    SeamsToSewingPatternSettings,
    OBJECT_OT_check_mesh_issues,
    Seams_To_SewingPattern,
    QuickClothsim,
    Remesher,
    OBJECT_OT_seams_to_sewing_pattern_from_panel,
    VIEW3D_PT_seams_to_sewing_pattern,
]


def draw_remesh_context_menu(self, context):
    """Add Boundary Aligned Remesh to object context menu"""
    self.layout.operator("remesh.boundary_aligned_remesh", text="Boundary Aligned Remesh")


def register():
    """Register addon classes and properties"""
    for cls in classes:
        register_class(cls)
    
    # Add property group to scene
    bpy.types.Scene.seams_to_sewing_pattern_settings = \
        bpy.props.PointerProperty(type=SeamsToSewingPatternSettings)
    
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
    if hasattr(bpy.types.Scene, 'seams_to_sewing_pattern_settings'):
        del bpy.types.Scene.seams_to_sewing_pattern_settings


if __name__ == "__main__":
    register()

