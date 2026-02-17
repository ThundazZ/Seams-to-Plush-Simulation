"""Property definitions for Seams to Sewing Pattern addon"""

import bpy
from bpy.props import BoolProperty, IntProperty, EnumProperty, FloatProperty, StringProperty
from bpy.types import PropertyGroup


class SeamsToSewingPatternSettings(PropertyGroup):
    """Settings for Seams to Sewing Pattern operator
    
    This serves as the single source of truth for all operator settings.
    Properties are stored in the scene and accessed by panel operators.
    """
    
    # Core operator settings
    do_unwrap: EnumProperty(
        name="Unwrap",
        description="Perform an unwrap before unfolding. Identical to UV > Unwrap",
        items=(
            ('ANGLE_BASED', "Angle based", ""),
            ('CONFORMAL', "Conformal", ""),
            ('KEEP', "Keep existing", ""),
        ),
        default='ANGLE_BASED',
    )
    
    keep_original: BoolProperty(
        name="Work on duplicate",
        description="Creates a duplicate of the selected object and operates on that instead. This keeps your original object intact.",
        default=True,
    )
    
    use_remesh: BoolProperty(
        name="Remesh",
        description="Use Boundary Aligned Remesh to remesh",
        default=True,
    )
    
    apply_modifiers: BoolProperty(
        name="Apply modifiers",
        description="Applies all modifiers before operating.",
        default=True,
    )
    
    target_tris: IntProperty(
        name="Target number of triangles",
        description="Actual number of triangle might be a bit off",
        default=5000,
        min=100,
        max=100000,
    )
    
    # Cloth preparation options
    # Note: enable_cloth_prep is not exposed in the UI - the cloth prep options
    # box is always visible in the panel, but the execution logic gates on this
    # property. This is by design to keep the code clear while not cluttering UI.
    enable_cloth_prep: BoolProperty(
        name="Enable Cloth Prep",
        description="Enable additional cloth preparation steps (internal use)",
        default=False,
    )
    
    scale_to_5m: BoolProperty(
        name="Scale to 5m",
        description="Scale object to 5m height for realistic cloth simulation",
        default=True,
    )
    
    fix_normals: BoolProperty(
        name="Fix Normals",
        description="Recalculate face normals after unfolding",
        default=True,
    )
    
    # Cloth preset system (replaces copy_cloth_settings)
    cloth_preset: EnumProperty(
        name="Cloth Preset",
        description="Select cloth simulation preset to apply",
        items=(
            ('NONE', "None", "Do not apply cloth settings"),
            ('PRESET_1', "Preset 1", "Light Fabric"),
            ('PRESET_2', "Preset 2", "Medium Fabric"),
            ('PRESET_3', "Preset 3", "Heavy Fabric"),
        ),
        default='PRESET_1',
    )
    
    # Toggle for showing/hiding preset editor
    show_preset_editor: BoolProperty(
        name="Show Preset Editor",
        description="Show or hide custom preset values editor",
        default=False,
    )
    
    # === PRESET 1 Settings ===
    preset1_quality: IntProperty(name="Quality", default=5, min=1, max=20)
    preset1_mass: FloatProperty(name="Mass", default=0.3, min=0.0, max=10.0)
    preset1_bending_model: EnumProperty(
        name="Bending Model",
        items=[('LINEAR', "Linear", ""), ('ANGULAR', "Angular", "")],
        default='LINEAR'
    )
    preset1_tension_stiffness: FloatProperty(name="Tension", default=15, min=0.0, max=1000.0)
    preset1_compression_stiffness: FloatProperty(name="Compression", default=15, min=0.0, max=1000.0)
    preset1_shear_stiffness: FloatProperty(name="Shear", default=5, min=0.0, max=1000.0)
    preset1_bending_stiffness: FloatProperty(name="Bending", default=1.5, min=0.0, max=1000.0)
    preset1_tension_damping: FloatProperty(name="Tension Damp", default=5, min=0.0, max=50.0)
    preset1_compression_damping: FloatProperty(name="Compression Damp", default=5, min=0.0, max=50.0)
    preset1_shear_damping: FloatProperty(name="Shear Damp", default=5, min=0.0, max=50.0)
    preset1_bending_damping: FloatProperty(name="Bending Damp", default=0.5, min=0.0, max=50.0)
    preset1_use_pressure: BoolProperty(name="Use Pressure", default=True)
    preset1_uniform_pressure_force: FloatProperty(name="Pressure", default=10, min=0.0, max=1000.0)
    preset1_vertex_group_pressure: StringProperty(name="Pressure Group", default="")
    preset1_use_sewing_springs: BoolProperty(name="Use Sewing", default=True)
    preset1_sewing_force_max: FloatProperty(name="Sewing Force", default=5, min=0.0, max=1000.0)
    preset1_use_gravity: BoolProperty(name="Use Gravity", default=False)
    preset1_use_self_collision: BoolProperty(name="Self Collision", default=True)
    
    # === PRESET 2 Settings ===
    preset2_quality: IntProperty(name="Quality", default=8, min=1, max=20)
    preset2_mass: FloatProperty(name="Mass", default=0.5, min=0.0, max=10.0)
    preset2_bending_model: EnumProperty(
        name="Bending Model",
        items=[('LINEAR', "Linear", ""), ('ANGULAR', "Angular", "")],
        default='ANGULAR'
    )
    preset2_tension_stiffness: FloatProperty(name="Tension", default=25, min=0.0, max=1000.0)
    preset2_compression_stiffness: FloatProperty(name="Compression", default=25, min=0.0, max=1000.0)
    preset2_shear_stiffness: FloatProperty(name="Shear", default=10, min=0.0, max=1000.0)
    preset2_bending_stiffness: FloatProperty(name="Bending", default=5, min=0.0, max=1000.0)
    preset2_tension_damping: FloatProperty(name="Tension Damp", default=10, min=0.0, max=50.0)
    preset2_compression_damping: FloatProperty(name="Compression Damp", default=10, min=0.0, max=50.0)
    preset2_shear_damping: FloatProperty(name="Shear Damp", default=10, min=0.0, max=50.0)
    preset2_bending_damping: FloatProperty(name="Bending Damp", default=1, min=0.0, max=50.0)
    preset2_use_pressure: BoolProperty(name="Use Pressure", default=True)
    preset2_uniform_pressure_force: FloatProperty(name="Pressure", default=20, min=0.0, max=1000.0)
    preset2_vertex_group_pressure: StringProperty(name="Pressure Group", default="")
    preset2_use_sewing_springs: BoolProperty(name="Use Sewing", default=True)
    preset2_sewing_force_max: FloatProperty(name="Sewing Force", default=10, min=0.0, max=1000.0)
    preset2_use_gravity: BoolProperty(name="Use Gravity", default=False)
    preset2_use_self_collision: BoolProperty(name="Self Collision", default=True)
    
    # === PRESET 3 Settings ===
    preset3_quality: IntProperty(name="Quality", default=10, min=1, max=20)
    preset3_mass: FloatProperty(name="Mass", default=1.0, min=0.0, max=10.0)
    preset3_bending_model: EnumProperty(
        name="Bending Model",
        items=[('LINEAR', "Linear", ""), ('ANGULAR', "Angular", "")],
        default='ANGULAR'
    )
    preset3_tension_stiffness: FloatProperty(name="Tension", default=40, min=0.0, max=1000.0)
    preset3_compression_stiffness: FloatProperty(name="Compression", default=40, min=0.0, max=1000.0)
    preset3_shear_stiffness: FloatProperty(name="Shear", default=20, min=0.0, max=1000.0)
    preset3_bending_stiffness: FloatProperty(name="Bending", default=10, min=0.0, max=1000.0)
    preset3_tension_damping: FloatProperty(name="Tension Damp", default=15, min=0.0, max=50.0)
    preset3_compression_damping: FloatProperty(name="Compression Damp", default=15, min=0.0, max=50.0)
    preset3_shear_damping: FloatProperty(name="Shear Damp", default=15, min=0.0, max=50.0)
    preset3_bending_damping: FloatProperty(name="Bending Damp", default=2, min=0.0, max=50.0)
    preset3_use_pressure: BoolProperty(name="Use Pressure", default=True)
    preset3_uniform_pressure_force: FloatProperty(name="Pressure", default=30, min=0.0, max=1000.0)
    preset3_vertex_group_pressure: StringProperty(name="Pressure Group", default="")
    preset3_use_sewing_springs: BoolProperty(name="Use Sewing", default=True)
    preset3_sewing_force_max: FloatProperty(name="Sewing Force", default=15, min=0.0, max=1000.0)
    preset3_use_gravity: BoolProperty(name="Use Gravity", default=False)
    preset3_use_self_collision: BoolProperty(name="Self Collision", default=True)
    
    play_animation: BoolProperty(
        name="Play Animation",
        description="Start animation playback and enter local view",
        default=True,
    )
