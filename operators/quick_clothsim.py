"""Quick cloth simulation setup operator"""

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, EnumProperty


class QuickClothsim(Operator):
    """Add cloth simulation setup to the selected objects"""
    
    bl_idname = "object.quick_clothsim"
    bl_label = "Quick Clothsim"
    bl_options = {'REGISTER', 'UNDO'}

    use_sewing: BoolProperty(
        name="Sewing",
        description="Enable Shape > Sewing",
        default=True,
    )
    use_gravity: BoolProperty(
        name="Gravity",
        description="Use world gravity",
        default=False,
    )
    pressure_style: EnumProperty(
        name="Pressure",
        items=(
            ('OFF', "Off", "No pressure"),
            ('MEDIUM', "Medium", "Medium pressure"),
            ('HIGH', "High", "High pressure")
        ),
        default='MEDIUM',
    )
    air_visc: BoolProperty(
        name="Increase Air Viscosity",
        description="Increase Physical Properties > Air Viscosity. Use when the object collapses in on itself during simulation",
        default=True,
    )
    
    @classmethod
    def poll(cls, context):
        """Only available in object mode"""
        return context.mode == 'OBJECT'

    def execute(self, context):
        objects = context.selected_objects
        for obj in objects:
            cloth_mod = obj.modifiers.new(name='Cloth', type='CLOTH')
            
            # Pressure settings
            if self.pressure_style != 'OFF':
                cloth_mod.settings.use_pressure = True
                
            if self.pressure_style == 'MEDIUM':
                cloth_mod.settings.uniform_pressure_force = 10
            elif self.pressure_style == 'HIGH':
                cloth_mod.settings.uniform_pressure_force = 50
                    
            # Sewing settings
            cloth_mod.settings.use_sewing_springs = self.use_sewing
            if self.use_sewing:
                if self.pressure_style == 'MEDIUM':
                    cloth_mod.settings.sewing_force_max = 5
                elif self.pressure_style == 'HIGH':
                    cloth_mod.settings.sewing_force_max = 15
                else:
                    cloth_mod.settings.sewing_force_max = 5
            
            # Air viscosity
            if self.air_visc:
                cloth_mod.settings.air_damping = 10

            # Gravity
            if not self.use_gravity:
                cloth_mod.settings.effector_weights.gravity = 0

        return {'FINISHED'}
