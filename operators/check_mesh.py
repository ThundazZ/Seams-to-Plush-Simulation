"""Mesh checking operator for detecting common issues"""

import bpy
import bmesh
from bpy.types import Operator
from mathutils.kdtree import KDTree


class OBJECT_OT_check_mesh_issues(Operator):
    """Check for mesh issues: unmerged vertices, non-manifold edges (3+ faces), loose geometry"""
    
    bl_idname = "object.check_mesh_issues"
    bl_label = "Check Mesh Issues"
    bl_options = {'REGISTER'}
    
    @staticmethod
    def check_and_select_unmerged_verts(obj):
        """Check for unmerged vertices and select them in edit mode using KDTree
        
        Time complexity: O(n log n) instead of O(n²) brute force
        Returns: count of unmerged vertices
        """
        if obj.type != 'MESH':
            return 0
        
        # Get bmesh from edit mode (already in edit mode from execute)
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        
        # Build KDTree from all vertices
        kd = KDTree(len(bm.verts))
        for vert in bm.verts:
            kd.insert(vert.co, vert.index)
        kd.balance()
        
        # Find duplicates using range search
        tolerance = 0.0001
        unmerged_count = 0
        checked_indices = set()
        
        for vert in bm.verts:
            if vert.index in checked_indices:
                continue
            
            # Find all vertices within tolerance distance
            nearby = kd.find_range(vert.co, tolerance)
            
            # If more than 1 vertex found (including self), we have duplicates
            if len(nearby) > 1:
                # Select all duplicates
                for co, index, dist in nearby:
                    if index not in checked_indices:
                        bm.verts[index].select = True
                        if index != vert.index:
                            unmerged_count += 1
                        checked_indices.add(index)
        
        # Update mesh
        bmesh.update_edit_mesh(obj.data)
        
        return unmerged_count
    
    @staticmethod
    def check_and_select_internal_faces(obj):
        """Check for non-manifold geometry (edges with 3+ faces), select them in edit mode
        
        Returns tuple: (non_manifold_edges_count, loose_geometry_count)
        """
        if obj.type != 'MESH':
            return 0, 0
        
        # Get bmesh from edit mode (assumes already in edit mode)
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        
        non_manifold_edges = []
        loose_verts = []
        loose_edges = []
        
        # Check for non-manifold edges (strictly more than 2 faces)
        # This catches internal partitions and T-junctions
        for edge in bm.edges:
            if len(edge.link_faces) > 2:
                non_manifold_edges.append(edge)
                edge.select = True
                # Also select connected faces for visibility
                for face in edge.link_faces:
                    face.select = True
        
        # Check for loose geometry (vertices/edges not connected to any face)
        for vert in bm.verts:
            if not vert.link_faces:
                loose_verts.append(vert)
                vert.select = True
        
        for edge in bm.edges:
            if not edge.link_faces:
                loose_edges.append(edge)
                edge.select = True
        
        # Update mesh
        bmesh.update_edit_mesh(obj.data)
        
        loose_count = len(loose_verts) + len(loose_edges)
        
        return len(non_manifold_edges), loose_count
    
    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}
        
        # Save current mode
        original_mode = obj.mode
        
        # Enter edit mode and deselect all
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # Check and select all issues
        unmerged = self.check_and_select_unmerged_verts(obj)
        non_manifold_edges, loose_geometry = self.check_and_select_internal_faces(obj)
        
        # Build report message
        issues = []
        if unmerged > 0:
            issues.append(f"{unmerged} unmerged vertices")
        if non_manifold_edges > 0:
            issues.append(f"{non_manifold_edges} non-manifold edges (3+ faces)")
        if loose_geometry > 0:
            issues.append(f"{loose_geometry} loose vertices/edges")
        
        if issues:
            msg = f"Found: {', '.join(issues)} (selected in edit mode)"
            self.report({'WARNING'}, msg)
        else:
            msg = "No mesh issues found"
            self.report({'INFO'}, msg)
            # Return to original mode if no issues
            if original_mode == 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
        
        return {'FINISHED'}
