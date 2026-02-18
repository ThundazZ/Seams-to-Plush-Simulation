"""Panel UI for Seams to Sewing Pattern addon"""

import bpy
from bpy.types import Panel


class VIEW3D_PT_seams_to_sewing_pattern(Panel):
    """Panel for Seams to Sewing Pattern in 3D View N-panel"""
    
    bl_label = "Seams to Sewing Pattern"
    bl_idname = "VIEW3D_PT_seams_to_sewing_pattern"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.seams_to_sewing_pattern_settings
        
        layout.separator()
        
        # Issue Detection section
        row = layout.row()
        row.operator("object.check_mesh_issues", text="Check Issues", icon="CHECKMARK")
        
        layout.separator()
        
        layout.prop(settings, "do_unwrap")
        
        # Warning for KEEP mode
        if settings.do_unwrap == 'KEEP':
            row = layout.row()
            row.alignment = 'EXPAND'
            row.label(text="Ensure your seams match your UV's!", icon='EDGESEL')
        
        layout.prop(settings, "keep_original")
        layout.prop(settings, "apply_modifiers")
        layout.prop(settings, "use_remesh")
        
        # Target tris - only enabled when remesh is on
        row = layout.row()
        row.enabled = settings.use_remesh
        row.prop(settings, "target_tris")
        
        layout.separator()
        
        # Cloth Preparation section

        box = layout.box()
        box.label(text="Preparation Options:", icon='MOD_CLOTH')
        box.prop(settings, "scale_to_5m")
        box.prop(settings, "fix_normals")
        box.prop(settings, "play_animation")
        
        # Cloth Preset section
        box.separator()
        box.label(text="Cloth Preset:", icon='PRESET')
        box.prop(settings, "cloth_preset", text="")
        
        # Show toggle button and editor if a preset is selected
        if settings.cloth_preset != 'NONE':
            # Toggle button for showing/hiding editor
            row = box.row(align=True)
            icon = 'TRIA_DOWN' if settings.show_preset_editor else 'TRIA_RIGHT'
            row.prop(settings, "show_preset_editor", 
                    text="Customize Preset Values", 
                    icon=icon, 
                    toggle=True)
            
            # Show editor only if toggle is enabled
            if settings.show_preset_editor:
                self._draw_preset_editor(box, settings, settings.cloth_preset)
        
        box.separator()
        
        layout.separator()
        
        # Execute button
        row = layout.row()
        row.scale_y = 1.5
        row.operator("object.seams_to_sewingpattern_from_panel", 
                    text="Execute", 
                    icon="PLAY")
    
    def _draw_preset_editor(self, layout, settings, preset_name):
        """Draw preset parameter editor"""
        # Determine prefix based on selected preset
        if preset_name == 'PRESET_1':
            prefix = 'preset1'
            label = "Light Fabric Settings"
        elif preset_name == 'PRESET_2':
            prefix = 'preset2'
            label = "Medium Fabric Settings"
        elif preset_name == 'PRESET_3':
            prefix = 'preset3'
            label = "Heavy Fabric Settings"
        else:
            return
        
        # Main settings box
        editor_box = layout.box()
        editor_box.label(text=label, icon='SETTINGS')
        
        # Basic settings
        col = editor_box.column(align=True)
        col.prop(settings, f"{prefix}_quality")
        col.prop(settings, f"{prefix}_mass")
        col.prop(settings, f"{prefix}_bending_model")
        
        # Stiffness section
        editor_box.separator()
        editor_box.label(text="Stiffness:", icon='FORCE_HARMONIC')
        col = editor_box.column(align=True)
        col.prop(settings, f"{prefix}_tension_stiffness")
        col.prop(settings, f"{prefix}_compression_stiffness")
        col.prop(settings, f"{prefix}_shear_stiffness")
        col.prop(settings, f"{prefix}_bending_stiffness")
        
        # Damping section
        editor_box.separator()
        editor_box.label(text="Damping:", icon='FORCE_DRAG')
        col = editor_box.column(align=True)
        col.prop(settings, f"{prefix}_tension_damping")
        col.prop(settings, f"{prefix}_compression_damping")
        col.prop(settings, f"{prefix}_shear_damping")
        col.prop(settings, f"{prefix}_bending_damping")
        
        # Pressure section
        editor_box.separator()
        editor_box.label(text="Pressure:", icon='FORCE_WIND')
        col = editor_box.column(align=True)
        col.prop(settings, f"{prefix}_use_pressure")
        if getattr(settings, f"{prefix}_use_pressure"):
            col.prop(settings, f"{prefix}_uniform_pressure_force")
            col.prop(settings, f"{prefix}_vertex_group_pressure")
        
        # Sewing section
        editor_box.separator()
        editor_box.label(text="Sewing:", icon='UGLYPACKAGE')
        col = editor_box.column(align=True)
        col.prop(settings, f"{prefix}_use_sewing_springs")
        if getattr(settings, f"{prefix}_use_sewing_springs"):
            col.prop(settings, f"{prefix}_sewing_force_max")
        
        # Collision section
        editor_box.separator()
        editor_box.label(text="Collision:", icon='MOD_PHYSICS')
        col = editor_box.column(align=True)
        col.prop(settings, f"{prefix}_use_self_collision")
        
        # Gravity section
        editor_box.separator()
        editor_box.label(text="Gravity:", icon='FORCE_FORCE')
        col = editor_box.column(align=True)
        col.prop(settings, f"{prefix}_use_gravity")
