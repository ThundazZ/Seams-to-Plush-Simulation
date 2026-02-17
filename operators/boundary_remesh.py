"""Boundary-aligned remeshing for Blender"""

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


class BoundaryAlignedRemesher:
    """Core remeshing algorithm that aligns mesh to boundary edges"""
    
    def __init__(self, obj):
        self.obj = obj  # Fixed: was 'object' (builtin) instead of 'obj'
        self.bm = bmesh.new()
        self.bm.from_mesh(obj.data)
        self.bvh = BVHTree.FromBMesh(self.bm)
        
        # Boundary_data is a list of directions and locations of boundaries.
        # This data will serve as guidance for the alignment
        self.boundary_data = []
        
        # Fill the data using boundary edges as source of directional data.
        for edge in self.bm.edges:
            if edge.is_boundary:
                vec = (edge.verts[0].co - edge.verts[1].co).normalized()
                center = (edge.verts[0].co + edge.verts[1].co) / 2
                
                self.boundary_data.append((center, vec))
        
        # Create a KD Tree to easily locate the nearest boundary point
        self.boundary_kd_tree = KDTree(len(self.boundary_data))
        
        for index, (center, vec) in enumerate(self.boundary_data):
            self.boundary_kd_tree.insert(center, index)
        
        self.boundary_kd_tree.balance()
    
    def nearest_boundary_vector(self, location):
        """Gets the nearest boundary direction"""
        location, index, dist = self.boundary_kd_tree.find(location)
        location, vec = self.boundary_data[index]
        return vec
    
    def enforce_edge_length(self, edge_length=0.05, bias=0.333):
        """Replicates dyntopo behavior - subdivide long edges, collapse short ones
        
        This includes critical mesh quality improvements and boundary protection
        """
        upper_length = edge_length + edge_length * bias
        lower_length = edge_length - edge_length * bias
        
        # Subdivide long edges
        subdivide = []
        for edge in self.bm.edges:
            if edge.calc_length() > upper_length:
                subdivide.append(edge)
        
        bmesh.ops.subdivide_edges(self.bm, edges=subdivide, cuts=1)
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces)
        
        # Remove verts with less than 5 edges, this helps improve mesh quality
        dissolve_verts = []
        for vert in self.bm.verts:
            if len(vert.link_edges) < 5:
                if not vert.is_boundary:
                    dissolve_verts.append(vert)
        
        bmesh.ops.dissolve_verts(self.bm, verts=dissolve_verts)
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces)
        
        # Collapse short edges but ignore boundaries and never collapse two chained edges
        lock_verts = set(vert for vert in self.bm.verts if vert.is_boundary)
        collapse = []
        
        for edge in self.bm.edges:
            if edge.calc_length() < lower_length and not edge.is_boundary:
                verts = set(edge.verts)
                if verts & lock_verts:
                    continue
                collapse.append(edge)
                lock_verts |= verts
        
        bmesh.ops.collapse(self.bm, edges=collapse, uvs=True)
        bmesh.ops.beautify_fill(self.bm, faces=self.bm.faces, method="ANGLE")
    
    def align_verts(self, rule=(-1, -2, -3, -4)):
        """Align verts to the nearest boundary by averaging neighbor vert locations
        
        Rules work by sorting edges by angle relative to the boundary.
        Eg1. (0, 1) stands for averaging the biggest angle and the 2nd biggest angle edges.
        Eg2. (-1, -2, -3, -4), averages the four smallest angle edges
        """
        for vert in self.bm.verts:
            if not vert.is_boundary:
                vec = self.nearest_boundary_vector(vert.co)
                neighbor_locations = [edge.other_vert(vert).co for edge in vert.link_edges]
                best_locations = sorted(
                    neighbor_locations, 
                    key=lambda n_loc: abs((n_loc - vert.co).normalized().dot(vec))
                )
                co = vert.co.copy()
                le = len(vert.link_edges)
                for i in rule:
                    co += best_locations[i % le]
                co /= len(rule) + 1
                co -= vert.co
                co -= co.dot(vert.normal) * vert.normal
                vert.co += co
    
    def reproject(self):
        """Recovers original shape by projecting back to surface"""
        for vert in self.bm.verts:
            location, normal, index, dist = self.bvh.find_nearest(vert.co)
            if location:
                vert.co = location
    
    def remesh(self, edge_length=0.05, iterations=30, quads=True, reproject=True):
        """Coordinates remeshing process"""
        wm = bpy.context.window_manager
        wm.progress_begin(0, 99)

        if quads:
            rule = (-1, -2, 0, 1)
        else:
            rule = (0, 1, 2, 3)
        
        try:
            for i in range(iterations):
                wm.progress_update(i / iterations)
                self.enforce_edge_length(edge_length=edge_length)
                self.align_verts(rule=rule)
                if reproject:
                    self.reproject()
            
            if quads:
                bmesh.ops.join_triangles(
                    self.bm, 
                    faces=self.bm.faces,
                    angle_face_threshold=3.14,
                    angle_shape_threshold=3.14
                )
        finally:
            wm.progress_end()
        
        return self.bm


class Remesher(bpy.types.Operator):
    """Boundary-aligned remeshing operator for maintaining edge alignment"""
    
    bl_idname = "remesh.boundary_aligned_remesh"
    bl_label = "Boundary Aligned Remesh"
    bl_options = {"REGISTER", "UNDO"}
    
    edge_length: bpy.props.FloatProperty(
        name="Edge Length",
        min=0,
        default=0.1 
    )
    
    iterations: bpy.props.IntProperty(
        name="Iterations",
        min=1,
        default=30
    )
    
    quads: bpy.props.BoolProperty(
        name="Quads",
        default=False
    )

    reproject: bpy.props.BoolProperty(
        name="Reproject",
        default=True
    )
    
    preserve_uvs: bpy.props.BoolProperty(
        name="Preserve UVs",
        description="Transfer UV maps from original mesh after remeshing. "
                    "Uses nearest-polygon interpolation to reconstruct UVs",
        default=True
    )
    
    def execute(self, context):
        obj = bpy.context.active_object
        print(f"Remeshing {obj.name}")
        
        # Create temp copy of mesh for UV transfer before remeshing
        temp_obj = None
        has_uvs = obj.data.uv_layers.active is not None
        if self.preserve_uvs and has_uvs:
            temp_obj = self._create_uv_source(obj, context)
        
        remesher = BoundaryAlignedRemesher(obj)
        try:
            bm = remesher.remesh(
                self.edge_length, 
                self.iterations, 
                self.quads, 
                self.reproject
            )
            bm.to_mesh(obj.data)
            
            # Transfer UVs from pre-remesh mesh to remeshed mesh
            if temp_obj:
                self._transfer_uvs(obj, temp_obj, context)
            
            context.area.tag_redraw()
            return {"FINISHED"}
        except Exception as e:
            self.report(
                {'ERROR'}, 
                "Remeshing failed, probably because there is a piece that can't "
                "be flattened out. That usually means there are seams missing "
                f"from a piece. Error: {str(e)}"
            )
            return {'CANCELLED'}
        finally:
            if temp_obj:
                self._cleanup_temp(temp_obj)
    
    def _create_uv_source(self, obj, context):
        """Create a temporary copy of the object to serve as UV source"""
        temp_mesh = obj.data.copy()
        temp_obj = bpy.data.objects.new("_S2S_uv_source", temp_mesh)
        temp_obj.matrix_world = obj.matrix_world.copy()
        context.collection.objects.link(temp_obj)
        # Hide from viewport so user doesn't see the temp object
        temp_obj.hide_set(True)
        return temp_obj
    
    def _transfer_uvs(self, obj, source_obj, context):
        """Transfer UV data from source object using nearest-polygon interpolation
        
        This works because:
        - The remeshed mesh has the same overall shape as the original
        - For flat sewing pattern islands, nearest-polygon gives perfect UV mapping
        - Blender's data_transfer handles all edge cases (triangles, quads, etc.)
        """
        # Ensure the remeshed mesh has a UV layer
        if not obj.data.uv_layers:
            obj.data.uv_layers.new(name="UVMap")
        
        # Add data transfer modifier
        mod = obj.modifiers.new("_UV_Transfer", 'DATA_TRANSFER')
        mod.object = source_obj
        mod.use_loop_data = True
        mod.data_types_loops = {'UV'}
        # POLYINTERP_NEAREST: project each point onto nearest source polygon
        # and interpolate UV using barycentric coordinates — ideal for flat meshes
        mod.loop_mapping = 'POLYINTERP_NEAREST'
        
        # Apply the modifier
        prev_active = context.view_layer.objects.active
        context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier="_UV_Transfer")
        context.view_layer.objects.active = prev_active
    
    def _cleanup_temp(self, temp_obj):
        """Remove temporary UV source object and its mesh data"""
        temp_mesh = temp_obj.data
        bpy.data.objects.remove(temp_obj, do_unlink=True)
        bpy.data.meshes.remove(temp_mesh)
