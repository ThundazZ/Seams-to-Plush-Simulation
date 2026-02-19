"""Panel-based operator for Seams to Plush Simulation with cloth prep options"""

import bpy
from bpy.types import Operator


class OBJECT_OT_seams_to_plush_from_panel(Operator):
    """Execute Seams to Plush Simulation with panel settings and optional cloth preparation"""
    
    bl_idname = "object.seams_to_plush_from_panel"
    bl_label = "Seams to Plush Simulation from Panel"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        settings = context.scene.seams_to_plush_settings
        
        # Validate object selection
        active_object = context.active_object
        if not active_object or active_object.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}
        
        # Ensure we're in Object mode
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # If scale_to_5m is on we must scale before seams runs.
        # When keep_original is also on, duplicate here first so the original
        # is never touched, then tell the seams operator not to duplicate again.
        use_keep_original = settings.keep_original
        if settings.scale_to_5m:
            if settings.keep_original:
                # Duplicate now, work on the copy
                bpy.ops.object.duplicate()
                active_object = context.active_object
                use_keep_original = False  # already duplicated
            self._scale_to_5m(active_object)
            self._prepare_mesh()
        
        # Main operation: Run Seams to Plush Simulation
        if not self._run_seams_to_plush(settings, use_keep_original):
            return {'CANCELLED'}
        
        # Fix normals if enabled
        if settings.fix_normals:
            self._fix_normals()
        
        # Apply cloth preset if one is selected
        if settings.cloth_preset != 'NONE':
            self._apply_cloth_preset(context, settings.cloth_preset)
        
        # Play animation if enabled
        if settings.play_animation:
            self._start_animation(context)
        
        return {'FINISHED'}
    
    def _scale_to_5m(self, obj):
        """Scale object to 5m height for realistic cloth simulation"""
        current_z = obj.dimensions.z
        if current_z > 0:
            target_z = 5.0
            scale_factor = target_z / current_z
            obj.scale *= scale_factor
        else:
            self.report({'WARNING'}, "Object has zero Z dimension, skipping scale")
    
    def _prepare_mesh(self):
        """Convert to mesh and set origin"""
        try:
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        except Exception as e:
            self.report({'WARNING'}, f"Could not prepare mesh: {str(e)}")
    
    def _run_seams_to_plush(self, settings, use_keep_original):
        """Execute the main Seams to Plush Simulation operator"""
        try:
            bpy.ops.object.seams_to_plush(
                do_unwrap=settings.do_unwrap,
                keep_original=use_keep_original,
                apply_modifiers=settings.apply_modifiers,
                use_remesh=settings.use_remesh,
                target_tris=settings.target_tris
            )
            return True
        except Exception as e:
            self.report({'ERROR'}, f"Failed to run seams_to_plush: {str(e)}")
            return False
    
    def _fix_normals(self):
        """Recalculate face normals after unfolding"""
        try:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.set_normals_from_faces()
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception as e:
            self.report({'WARNING'}, f"Could not fix normals: {str(e)}")
    
    def _apply_cloth_preset(self, context, preset_name):
        """Apply cloth simulation preset to the active object"""
        try:
            obj = context.active_object
            if not obj:
                self.report({'WARNING'}, "No active object to apply cloth preset")
                return
            
            settings = context.scene.seams_to_plush_settings
            
            # Determine prefix based on preset
            if preset_name == 'PRESET_1':
                prefix = 'preset1'
                name = 'Preset 1'
            elif preset_name == 'PRESET_2':
                prefix = 'preset2'
                name = 'Preset 2'
            elif preset_name == 'PRESET_3':
                prefix = 'preset3'
                name = 'Preset 3'
            else:
                self.report({'WARNING'}, f"Unknown preset: {preset_name}")
                return
            
            # Add cloth modifier
            cloth_mod = obj.modifiers.new(name="Cloth", type='CLOTH')
            
            # Apply settings from properties
            cloth_mod.settings.quality = getattr(settings, f"{prefix}_quality")
            cloth_mod.settings.mass = getattr(settings, f"{prefix}_mass")
            cloth_mod.settings.bending_model = getattr(settings, f"{prefix}_bending_model")
            
            # Stiffness
            cloth_mod.settings.tension_stiffness = getattr(settings, f"{prefix}_tension_stiffness")
            cloth_mod.settings.compression_stiffness = getattr(settings, f"{prefix}_compression_stiffness")
            cloth_mod.settings.shear_stiffness = getattr(settings, f"{prefix}_shear_stiffness")
            cloth_mod.settings.bending_stiffness = getattr(settings, f"{prefix}_bending_stiffness")
            
            # Damping
            cloth_mod.settings.tension_damping = getattr(settings, f"{prefix}_tension_damping")
            cloth_mod.settings.compression_damping = getattr(settings, f"{prefix}_compression_damping")
            cloth_mod.settings.shear_damping = getattr(settings, f"{prefix}_shear_damping")
            cloth_mod.settings.bending_damping = getattr(settings, f"{prefix}_bending_damping")
            
            # Pressure
            cloth_mod.settings.use_pressure = getattr(settings, f"{prefix}_use_pressure")
            cloth_mod.settings.uniform_pressure_force = getattr(settings, f"{prefix}_uniform_pressure_force")
            vertex_group = getattr(settings, f"{prefix}_vertex_group_pressure")
            if vertex_group:
                cloth_mod.settings.vertex_group_pressure = vertex_group
            
            # Sewing
            cloth_mod.settings.use_sewing_springs = getattr(settings, f"{prefix}_use_sewing_springs")
            cloth_mod.settings.sewing_force_max = getattr(settings, f"{prefix}_sewing_force_max")
            
            # Collision
            cloth_mod.collision_settings.use_collision = False
            cloth_mod.collision_settings.use_self_collision = getattr(settings, f"{prefix}_use_self_collision")
            
            # Gravity
            use_gravity = getattr(settings, f"{prefix}_use_gravity")
            cloth_mod.settings.effector_weights.gravity = 1.0 if use_gravity else 0.0
            
        except Exception as e:
            self.report({'WARNING'}, f"Could not apply cloth preset: {str(e)}")
    
    def _start_animation(self, context):
        """Enter local view, then start animation playback"""
        try:
            found = False
            for window in bpy.context.window_manager.windows:
                if found:
                    break
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D':
                        for region in area.regions:
                            if region.type == 'WINDOW':
                                with bpy.context.temp_override(
                                    window=window,
                                    area=area,
                                    region=region,
                                ):
                                    bpy.ops.view3d.localview()
                                found = True
                                break
                        break

            context.scene.frame_set(0)
            bpy.ops.screen.animation_play()
        except Exception as e:
            self.report({'WARNING'}, f"Could not start animation/local view: {str(e)}")
