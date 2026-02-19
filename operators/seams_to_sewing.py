"""Main Seams to Plush Simulation operator"""

import bpy
from collections import defaultdict
from bpy.types import Operator
import bmesh
import mathutils
import math
from bpy.props import (
    BoolProperty,
    IntProperty,
    EnumProperty,
)


class OBJECT_OT_seams_to_plush(Operator):
    """Convert a manifold mesh with seams into patterns for plush cloth simulation"""
    
    bl_idname = "object.seams_to_plush"
    bl_label = "Seams to Plush Simulation"
    bl_description = (
        "Converts a manifold mesh with seams into flattened patterns for plush"
        " cloth simulation"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    do_unwrap: EnumProperty(
        name="Unwrap",
        description="Perform an unwrap before unfolding. Identical to UV > Unwrap",
        items=(
            ('ANGLE_BASED', "Angle based", ""),
            ('CONFORMAL', "Conformal", ""),
            ('KEEP', "Keep existing (advanced)", ""),
        ),
        default='ANGLE_BASED',
    )
    keep_original: BoolProperty(
        name="Work on duplicate",
        description="Creates a duplicate of the selected object and operates on that instead.",
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
        description="Actual number of triangles might be a bit off",
        default=5000,
    )

    def execute(self, context):
        """Main execution method"""
        wm = context.window_manager
        
        # Prepare object (duplicate, apply modifiers)
        obj = self._prepare_object(context)
        if obj is None:
            return {'CANCELLED'}
        
        # Enter edit mode and unwrap
        bpy.ops.object.mode_set(mode='EDIT')
        obj = context.edit_object
        me = obj.data
        
        bm = self._unwrap_mesh(context, obj, me)
        
        # Store initial volume for reference
        obj["S2S_InitialVolume"] = bm.calc_volume()
        
        # Calculate target edge length for remeshing
        max_edge_length = None
        if self.use_remesh:
            max_edge_length = self._calculate_target_edge_length(bm, wm)
        
        # Process seams and validate
        if not self._process_seams(bm, me):
            self.report(
                {'ERROR'},
                (
                    'There are no seams in this mesh. Please add seams where'
                    ' you want to cut the model.'
                )
            )
            return {'CANCELLED'}
        
        # Separate into islands and flatten
        face_groups = self._separate_islands(bm, wm)
        area_before, area_after = self._flatten_islands(bm, me, face_groups, wm)
        
        # Final adjustments
        self._finalize(obj, me, area_before, area_after, max_edge_length)
        
        # Fix progress cursor issue
        context.window.cursor_set('NONE')
        context.window.cursor_set('DEFAULT')
        
        return {'FINISHED'}
    
    def _prepare_object(self, context):
        """Duplicate object if needed and apply modifiers"""
        if self.keep_original:
            # Duplicate selection to keep original
            src_obj = context.active_object
            obj = src_obj.copy()
            obj.data = src_obj.data.copy()
            obj.animation_data_clear()
            context.collection.objects.link(obj)

            obj.select_set(True)
            src_obj.select_set(False)
            context.view_layer.objects.active = obj
        else:
            obj = context.active_object

        if self.apply_modifiers:
            bpy.ops.object.convert(target='MESH')
            obj = context.active_object
        
        return obj
    
    def _unwrap_mesh(self, context, obj, me):
        """Perform UV unwrap if requested"""
        bpy.ops.mesh.select_mode(type="EDGE")
        bpy.ops.mesh.select_all(action='SELECT')
        
        if self.do_unwrap != 'KEEP':
            bpy.ops.uv.unwrap(method=self.do_unwrap, margin=0.02)
        
        bpy.ops.mesh.select_all(action='DESELECT')
        
        bm = bmesh.from_edit_mesh(me)
        bmesh.update_edit_mesh(me)
        
        return bm
    
    def _calculate_target_edge_length(self, bm, wm):
        """Calculate ideal edge length based on target triangle count"""
        current_area = sum(f.calc_area() for f in bm.faces)
        target_triangle_count = self.target_tris
        area_per_triangle = current_area / target_triangle_count

        max_edge_length = math.sqrt(area_per_triangle / (math.sqrt(3) / 4))

        # A bias to compensate for stretching
        self.ensure_edgelength(max_edge_length * 0.8, bm, wm)
        
        return max_edge_length
    
    def _process_seams(self, bm, me):
        """Process seam edges with beveling and degenerate face cleanup"""
        warn_any_seam = False

        # Select all seam edges
        for e in bm.edges:
            if e.seam:
                e.select = True
                warn_any_seam = True

        if not warn_any_seam:
            return False

        # Bevel seam edges (Blender 5.0 API)
        bpy.ops.mesh.bevel(affect='EDGES', offset=0.0002)

        # Fix fanning seams - find degenerate faces
        degenerate_edges = list()
        for f in list(filter(lambda f: (f.select), bm.faces)):
            is_degenerate = False
            for v in f.verts:
                vert_degenerate = True
                for e in v.link_edges:
                    if e.seam:
                        vert_degenerate = False
                if vert_degenerate:
                    is_degenerate = True

            for e in f.edges:
                if e.is_boundary:
                    is_degenerate = False

            if is_degenerate:
                for e in f.edges:
                    degenerate_edges.append(e)

        # Collapse degenerate edges
        bmesh.ops.collapse(bm, edges=degenerate_edges, uvs=True)
        bmesh.update_edit_mesh(me)
        bpy.ops.mesh.delete(type='ONLY_FACE')
        
        return True
    
    def _separate_islands(self, bm, wm):
        """Isolate all face islands"""
        bpy.ops.mesh.select_mode(type="FACE")
        face_groups = []
        faces = set(bm.faces[:])
        
        wm.progress_begin(0, 99)
        progress_max = len(faces)
        progress = 0
        
        while faces:
            bpy.ops.mesh.select_all(action='DESELECT')
            face = faces.pop()
            face.select = True
            bpy.ops.mesh.select_linked()
            selected_faces = {f for f in faces if f.select}
            selected_faces.add(face)
            face_groups.append(selected_faces)
            faces -= selected_faces

            progress += len(selected_faces)
            wm.progress_update((progress / progress_max) * 99)
        
        wm.progress_end()
        return face_groups
    
    def _flatten_islands(self, bm, me, face_groups, wm):
        """Flatten each island using UV coordinates"""
        wm.progress_begin(0, 99)
        uv_layer = bm.loops.layers.uv.active
        progress = 0
        area_before = 0
        area_after = 0

        for g in face_groups:
            progress += 1
            wm.progress_update((progress / len(face_groups)) * 99)
            
            bpy.ops.mesh.select_mode(type='FACE')
            bpy.ops.mesh.select_all(action='DESELECT')
            
            average_position = mathutils.Vector((0, 0, 0))
            facenum = 0

            # Calculate the area and average position
            for f in g:
                f.select = True
                area_before += f.calc_area()
                average_position += f.calc_center_median()
                facenum += 1

            average_position /= facenum

            average_tangent = mathutils.Vector((0, 0, 0))
            average_bitangent = mathutils.Vector((0, 0, 0))

            # Calculate a rough tangent and a bitangent
            average_uv_position = mathutils.Vector((0, 0))
            uv_position_samples = 0

            for face in g:
                for loop in face.loops:
                    uv = loop[uv_layer].uv
                    uv_position_samples += 1
                    average_uv_position += uv
                    delta = loop.vert.co - average_position
                    average_tangent += delta * (uv.x - 0.5)
                    average_bitangent += delta * (uv.y - 0.5)

            # Reorient the tangent and bitangent
            average_uv_position /= uv_position_samples
            average_tangent = average_tangent.normalized()
            average_bitangent = average_bitangent.normalized()
            average_normal = average_tangent.cross(average_bitangent)
            if average_normal.length < 1e-6:
                # Fallback for degenerate UV islands (collinear/coincident UVs)
                average_normal = mathutils.Vector((0, 0, 1))
            else:
                average_normal = average_normal.normalized()
            halfvector = average_bitangent + average_tangent
            halfvector /= 2
            if halfvector.length < 1e-6:
                halfvector = average_tangent.copy()
            else:
                halfvector.normalize()
            
            # Straighten out half vector
            halfvector = average_normal.cross(halfvector)
            halfvector = average_normal.cross(halfvector)
            
            cw = mathutils.Matrix.Rotation(
                math.radians(45.0), 4, average_normal
            )
            ccw = mathutils.Matrix.Rotation(
                math.radians(-45.0), 4, average_normal
            )

            average_tangent = mathutils.Vector(halfvector)
            average_tangent.rotate(ccw)

            average_bitangent = mathutils.Vector(halfvector)
            average_bitangent.rotate(cw)

            # Offset each face island by their UV value, using the tangent and bitangent
            for face in g:
                for loop in face.loops:
                    uv = loop[uv_layer].uv
                    vert = loop.vert
                    pos = mathutils.Vector((0, 0, 0))
                    pos += average_position
                    pos += average_tangent * -(uv.x - average_uv_position.x)
                    pos += average_bitangent * -(uv.y - average_uv_position.y)
                    # Arbitrary offset - should probably depend on object scale
                    pos += average_normal * 0.3
                    vert.co = pos

            bmesh.update_edit_mesh(me)
            area_after += sum(f.calc_area() for f in g)
        
        wm.progress_end()
        return area_before, area_after
    
    def _finalize(self, obj, me, area_before, area_after, max_edge_length):
        """Final scaling, cleanup, and remeshing"""
        # Scale to maintain area
        if area_after == 0:
            self.report({'WARNING'}, "Could not calculate area ratio (area_after=0), skipping scale")
            area_ratio = 1.0
        else:
            area_ratio = math.sqrt(area_before / area_after)
        bpy.ops.mesh.select_all(action='SELECT')
        previous_pivot = bpy.context.scene.tool_settings.transform_pivot_point
        bpy.context.scene.tool_settings.transform_pivot_point = (
            'INDIVIDUAL_ORIGINS'
        )
        bpy.ops.transform.resize(value=(area_ratio, area_ratio, area_ratio))
        bpy.context.scene.tool_settings.transform_pivot_point = previous_pivot

        obj["S2S_UVtoWORLDscale"] = area_ratio

        bmesh.update_edit_mesh(me)
        bpy.ops.mesh.select_all(action='SELECT')

        # Remove doubles
        bpy.ops.mesh.remove_doubles(threshold=0.0004, use_unselected=False)

        # Optional remesh
        if self.use_remesh and max_edge_length is not None:
            bpy.ops.mesh.dissolve_limited(angle_limit=0.01)
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            bpy.ops.remesh.boundary_aligned_remesh(
                edge_length=max_edge_length, iterations=10, 
                reproject=False, preserve_uvs=True
            )

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    def ensure_edgelength(self, max_length, mesh, wm):
        """Subdivide long seam edges to target length"""
        seam_edges = list(filter(lambda e: e.seam, mesh.edges))
        edge_groups = defaultdict(list)
        for e in seam_edges:
            edge_groups[math.floor(e.calc_length() / max_length)].append(e)

        wm.progress_begin(0, 99)
        progress = 0

        # Group edges by number of required cuts for efficient subdivision
        for eg in edge_groups.values():
            edge_length = eg[0].calc_length()
            wm.progress_update((progress / len(edge_groups)) * 99)
            bmesh.ops.subdivide_edges(
                mesh, edges=eg, cuts=math.floor(edge_length / max_length)
            )
            progress += 1

        bmesh.ops.triangulate(
            mesh, faces=mesh.faces, quad_method='BEAUTY', ngon_method='BEAUTY'
        )
        wm.progress_end()
