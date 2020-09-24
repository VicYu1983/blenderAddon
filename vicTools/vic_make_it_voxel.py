import bpy
from mathutils import geometry
from mathutils import Vector
from mathutils import Color
from numpy import arange
import time
import platform

voxel_name = 'Voxel_map'
ray_dir = [Vector([1,0,0]),Vector([0,1,0]),Vector([0,0,1])]

def collectVertexColor( mesh, color_layer ):
    ret = {}
    i = 0
    for poly in mesh.polygons:
        for idx in poly.loop_indices:
            loop = mesh.loops[idx]
            v = loop.vertex_index
            linked = ret.get(v, [])
            linked.append(color_layer.data[i].color)
            ret[v] = linked
            i += 1
    return ret    

def avg_col(cols):
    avg_col = Color((0.0, 0.0, 0.0))
    for col in cols:
        avg_col[0] += col[0]/len(cols)
        avg_col[1] += col[1]/len(cols)
        avg_col[2] += col[2]/len(cols)
    return avg_col   
    
class vic_make_it_voxel(bpy.types.Operator):
    bl_idname = 'vic.make_it_voxel'
    bl_label = 'Make It Voxel'
    
    proxy = None
    obj = None
    attach = None
    size = None
    obj_vertex_color = None    
    create_voxel = []
    color_map = None
    simple_way = True
    cubes_map = {}
    
    def getCubeByColor(self, color, temp_map):
        color_str = str(color)
        self.createVoxel( self.size, color )
        new_obj = bpy.context.object 
        #if self.bool_voxel_animation:
        #    new_obj.scale.x = new_obj.scale.y = new_obj.scale.z = 1   
        if color_str in self.cubes_map:
            self.cubes_map[color_str].append( new_obj )
        else:
            self.cubes_map[color_str] = [new_obj]
        return new_obj
    
    def createVoxel( self, resize, color ):
        resize = resize / 2
        bpy.ops.mesh.primitive_cube_add()
        
        if self.hasColorMap():
            bpy.context.object.data.vertex_colors.new()
            bpy.context.object.data.vertex_colors['Col'].name = voxel_name
            for c in bpy.context.object.data.vertex_colors[voxel_name].data:
                c.color[0] = color[0]
                c.color[1] = color[1]
                c.color[2] = color[2]
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.transform.resize(value=(resize, resize, resize), constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.object.editmode_toggle()
     
    def placeCubeAndSetColor( self, cube, loc, resize, color ):
        resize = resize / 2
        cube.select_set( True )
        cube.location = loc
        bpy.context.view_layer.objects.active = cube
        
        if not voxel_name in bpy.context.object.data.vertex_colors:
            bpy.context.object.data.vertex_colors.new()
            bpy.context.object.data.vertex_colors['Col'].name = voxel_name
        for c in bpy.context.object.data.vertex_colors[voxel_name].data:
            c.color[0] = color[0]
            c.color[1] = color[1]
            c.color[2] = color[2]
        
    def checkHitAndCreateVoxel( self, temp_cubes ):
        v1 = self.proxy.location
        v2 = self.obj.location
        
        pos = None
        hit = False
        id = None
        if self.simple_way:
            hit_simple, pos, normal, id_simple = self.obj.ray_cast( self.obj.matrix_world.inverted() * v1, v2-v1 )
            pos = self.obj.matrix_world * pos
            hit = hit_simple
            id = id_simple
        else:
            hit_data = []
            use_dir = ray_dir.copy()
            use_dir.append( v2-v1 )
            for dir in use_dir:
                hit, pos, normal, id = self.obj.ray_cast( self.obj.matrix_world.inverted() @ v1, dir )
                if hit:
                    hit_data.append( [pos, id] )
            if len( hit_data ) > 0:
                hit = True
                min_dist = 1000000
                for h_p in hit_data:
                    dist_proxy = (h_p[0] - self.obj.matrix_world.inverted() @ v1).magnitude
                    if dist_proxy < min_dist:
                        min_dist = dist_proxy
                        pos = self.obj.matrix_world @ h_p[0]
                        id = h_p[1]
        if hit:
            dist = ( pos - self.proxy.location ).magnitude
            if dist < (self.size if self.sensor_as_size else self.sensor_distance):
                color = Color()
                if self.hasColorMap():
                    color_id = self.obj.data.polygons[id].vertices[0]
                    color = self.obj_vertex_color[color_id]
                c = self.getCubeByColor( color, temp_cubes )
                if not 'Voxel_material' in c.data.materials:
                    c.data.materials.append( bpy.data.materials['Voxel_material'] )
                self.placeCubeAndSetColor( c, self.proxy.location, self.size, color )
                
                
    def hasColorMap( self ):
        return self.color_map in self.obj.data.vertex_colors
        
    def getVoxelCount( self, temp ):
        count = 0
        for ary in temp:
            for v in temp[ary]:
                count += 1
        return count
        
    def doVoxel(self, scene):
        
        bounding_box = self.obj.bound_box
        border_size = self.voxel_border_distance
        
        min_x = 0
        min_y = 0
        min_z = 0
        max_x = 0
        max_y = 0
        max_z = 0
        
        for v in self.obj.bound_box:
            globalV = self.obj.matrix_world @ Vector( v )
            
            now_x = globalV[0]
            now_y = globalV[1]
            now_z = globalV[2]
            
            if now_x < min_x:
                min_x = now_x
            if now_x > max_x:
                max_x = now_x
            if now_y < min_y:
                min_y = now_y
            if now_y > max_y:
                max_y = now_y
            if now_z < min_z:
                min_z = now_z
            if now_z > max_z:
                max_z = now_z
        
        obj_faces_normal = []
        obj_faces_vertex = []

        for m in self.obj.data.polygons:
            face_normal = m.normal
            face_vertex = self.obj.matrix_world @ self.obj.data.vertices[m.vertices[0]].co
            obj_faces_normal.append( face_normal )
            obj_faces_vertex.append( face_vertex )
        
        self.create_voxel = []
        
        usingForPop = {}
        for color_str in self.cubes_map:
            usingForPop[color_str] = self.cubes_map[color_str].copy()
        
        for i in arange( min_x, max_x, self.size ):
            print( 'Create Voxles: ' + str(int(( i - min_x ) / ( max_x - min_x ) * 100)) + '%' )
            for j in arange( min_y, max_y, self.size ):
                for k in arange( min_z, max_z, self.size ):
                    self.proxy.location = Vector([i, j, k])
                    self.checkHitAndCreateVoxel(usingForPop)        
            
    def addHideShowKey( self,obj, f):
        # key as visible on the current frame
        # insert keys in the hide_viewport have some bug in blender 2.8
        obj.hide_viewport = False
        obj.hide_render = False
        obj.keyframe_insert('hide_viewport',frame=f+1)
        obj.keyframe_insert('hide_render',frame=f+1)
        # hide it
        obj.hide_viewport = True
        obj.hide_render = True
        # key as hidden on the previous frame
        if f != self.int_frame_start:
            obj.keyframe_insert('hide_viewport',frame=f)
            obj.keyframe_insert('hide_render',frame=f)
        # key as hidden on the next frame
        if f != self.int_frame_end - 1:
            obj.keyframe_insert('hide_viewport',frame=f+2)
            obj.keyframe_insert('hide_render',frame=f+2)
            
    def createOneFrame( self, f ):
        if self.attach:
            self.createVoxel( self.size, Color() )
            real = bpy.context.object
            real.name = self.obj.name + '_Voxels_Frame_' + str( f )
            real.location = self.obj.location
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.object.editmode_toggle()
            
        self.doVoxel(bpy.context.scene)
        
        if self.attach:
            for o in bpy.data.objects:
                o.select_set( False )  
            for color_str in self.cubes_map:
                for c in self.cubes_map[color_str]:
                    c.select_set( True )
            real.select_set( True )
            bpy.context.view_layer.objects.active = real
            bpy.ops.object.join()
            if self.bool_voxel_animation:
                self.addHideShowKey( real, f )

        self.cubes_map = {}
            
    def execute(self, context):
        
        if context.object == None:
            return {'FINISHED'}
        else:
            if not hasattr( context.object.data, 'vertices' ):
                return {'FINISHED'}
            
        if platform.system() == 'Windows':
            bpy.ops.wm.console_toggle()             
            
        self.cubes_map = {}       
            
        self.size = bpy.context.scene.VoxelProperties.float_voxel_size
        self.color_map = bpy.context.scene.VoxelProperties.string_voxel_color_map
        self.simple_way = False
        self.sensor_distance = bpy.context.scene.VoxelProperties.float_voxel_sensor_distance
        self.sensor_as_size = bpy.context.scene.VoxelProperties.bool_sensor_as_size
        self.voxel_border_distance = 1
        self.obj = bpy.context.object
        self.int_frame_start = bpy.context.scene.VoxelProperties.int_frame_start
        self.int_frame_end = bpy.context.scene.VoxelProperties.int_frame_end
        self.bool_voxel_animation = bpy.context.scene.VoxelProperties.bool_voxel_animation
        self.attach = bpy.context.scene.VoxelProperties.bool_voxel_attach
        if self.bool_voxel_animation:
            self.attach = True
        
        if self.int_frame_end <= self.int_frame_start:
            self.int_frame_end = self.int_frame_start + 1
        
        if self.hasColorMap():
            collect_color = collectVertexColor( self.obj.data, self.obj.data.vertex_colors[self.color_map] )  
            self.obj_vertex_color = [avg_col(v) for k, v in collect_color.items() ]
            
        if not 'Voxel_material' in bpy.data.materials:
            bpy.data.materials.new(name="Voxel_material")
        #bpy.data.materials['Voxel_material'].use_vertex_color_paint = True
        
        self.createVoxel( self.size, Color() )
        self.proxy = bpy.context.object
        
        if self.bool_voxel_animation:
            for i in range( self.int_frame_start, self.int_frame_end ):
                bpy.context.scene.frame_current = i
                
                bpy.context.view_layer.objects.active = self.obj
                self.obj.select_set( True )
                
                bpy.ops.object.paths_calculate()
                self.createOneFrame( bpy.context.scene.frame_current )
                
                bpy.context.view_layer.objects.active = self.obj
                self.obj.select_set( True )
                bpy.ops.object.paths_clear()
                print( 'Frame Complete: ' + str( i ) )
        else:
            self.createOneFrame( bpy.context.scene.frame_current )
       
        for o in bpy.data.objects:
            o.select_set( False )
        self.proxy.select_set( True )
        bpy.ops.object.delete() 
        
        if platform.system() == 'Windows':
            bpy.ops.wm.console_toggle()    
        return {'FINISHED'}

class VoxelProperties(bpy.types.PropertyGroup):
    int_frame_start = bpy.props.IntProperty(
            name="Start Frame", description="Start frame of animation", 
            default=1, step=1, min=1, max=100000)
            
    int_frame_end = bpy.props.IntProperty(
            name="End Frame", description="End frame of animation", 
            default=2, step=1, min=2, max=100000)            
            
    bool_voxel_animation = bpy.props.BoolProperty(
            name="Animation", description="",
            default=False)            
    
    '''
    int_voxel_pool = bpy.props.IntProperty(
            name="Count", description="Count of Voxel", 
            default=10, step=1, min=10, max=100000)
    
    bool_voxel_simple_way = bpy.props.BoolProperty(
            name="Simple Way", description="Simple way for sensor",
            default=True)
    '''        
    bool_voxel_attach = bpy.props.BoolProperty(
            name="Single Voxel", description="Attach all voxels together",
            default=True)
            
    bool_sensor_as_size = bpy.props.BoolProperty(
            name="Sensor As Size", description="As same as size",
            default=True)
            
    float_voxel_size = bpy.props.FloatProperty(
            name="Size", description="Size for voxel.", 
            default=1.0, step=1.0, min=0.1, max=100.0)
            
    float_voxel_sensor_distance = bpy.props.FloatProperty(
            name="Sensor", description="Sensor distance for ray.", 
            default=1.0, step=1.0, min=0.01, max=100.0)
    '''        
    float_voxel_border_distance = bpy.props.FloatProperty(
            name="Border Size Scale", description="Border size scale value, less value more speed", 
            default=2.0, step=1.0, min=1.0, max=4.0)
    '''        
    string_voxel_color_map = bpy.props.StringProperty(
            name="Color Map", description="Color map for voxel", default="Col")

class VIC_VOXEL_PANEL(bpy.types.Panel):
    bl_category = "Vic Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Voxel Tool"

    def draw(self, context):
        layout = self.layout     
        
        col = layout.column(align=True)
        col.operator("vic.make_it_voxel")
        
        #col.prop(context.scene, 'int_voxel_pool' )
        col.prop(context.scene.VoxelProperties, 'float_voxel_size' ) 
        col.prop(context.scene.VoxelProperties, 'float_voxel_sensor_distance' ) 
        #col.prop(context.scene, 'float_voxel_border_distance' ) 
        col.prop(context.scene.VoxelProperties, 'string_voxel_color_map' ) 
        col.prop(context.scene.VoxelProperties, 'bool_sensor_as_size' ) 
        col.prop(context.scene.VoxelProperties, 'bool_voxel_attach' ) 
        col.prop(context.scene.VoxelProperties, 'bool_voxel_animation' )
        col.prop(context.scene.VoxelProperties, 'int_frame_start' )
        col.prop(context.scene.VoxelProperties, 'int_frame_end' )
        
        #col.prop(context.scene, 'bool_voxel_simple_way' ) 

classes = (
    # ui
    VoxelProperties,
    VIC_VOXEL_PANEL,

    # operation
    vic_make_it_voxel,
)
def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.VoxelProperties = bpy.props.PointerProperty(type=VoxelProperties)
    
def unregister():
    for cls in classes: bpy.utils.unregister_class(cls)
    del bpy.types.Scene.VoxelProperties