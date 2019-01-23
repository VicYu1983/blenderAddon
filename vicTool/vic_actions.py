import bpy, bmesh
from mathutils import Vector
from mathutils import noise
from mathutils import Color

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
        avg_col += col/len(cols)
    return avg_col    

def addProps( target, name, value, override = False ):
    if not name in target or override:
        target.data[name] = value
        
def back_to_origin_vertex_position( target ):
    for i, v in enumerate( target.data.vertices, 0 ):
        target.data.vertices[i].co = target.data['vic_init_vertex_position'][i]
        to_proxy = target.matrix_world @ Vector( target.data['vic_init_vertex_position'][i] )
        target.data['vic_proxy_vertex_position'][i][0] = to_proxy.x
        target.data['vic_proxy_vertex_position'][i][1] = to_proxy.y
        target.data['vic_proxy_vertex_position'][i][2] = to_proxy.z
        
def save_vertex_position( target ):
    # active when 1, or close by 0
    addProps( target, 'vic_active', True )
    # no nagetive number, the higher value the more detail
    addProps( target, 'vic_detail', 1.0 )
    # 0.0~1.0 will be best!    
    addProps( target, 'vic_effective', 1.0 )
    # using vertex color
    addProps( target, 'vic_using_vertex_color_map', False  )
    # using vertex color for effective value
    addProps( target, 'vic_effective_by_vertex_color', 'Col' )
    
    detail = target.data['vic_detail']
    map_vertex_color = target.data['vic_effective_by_vertex_color'] 

    addProps( target, 'vic_init_vertex_position', [ v.co.copy() for v in target.data.vertices ], True)
    addProps( target, 'vic_proxy_vertex_position', [ target.matrix_world @ v.co.copy() for v in target.data.vertices ], True )
    
    if map_vertex_color in target.data.vertex_colors:
        collect_color = collectVertexColor( target.data, target.data.vertex_colors[map_vertex_color] )  
        map_vertexs = [avg_col(v).hsv[2] for k, v in collect_color.items() ]
        addProps( target, 'vic_force_for_each_vertex_by_vertex_color', map_vertexs, True )            
    else:
        addProps( target, 'vic_force_for_each_vertex_by_vertex_color', [ .2 for v in target.data.vertices ], True )
    addProps( target, 'vic_force_for_each_vertex', [ ((noise.noise(Vector(v)*detail)) + 1) / 2 for v in target.data['vic_init_vertex_position'] ], True )            
    
def move_vertice( target ):
    mat = target.matrix_world
    vs = target.data.vertices
    
    # check the object is not in the scene
    if not 'vic_init_vertex_position' in target.data: return None

    active = target.data['vic_active']
    if active == 0: return None

    init_pos = target.data['vic_init_vertex_position']
    proxy_pos = target.data['vic_proxy_vertex_position']
    force_pos = target.data['vic_force_for_each_vertex_by_vertex_color'] if target.data['vic_using_vertex_color_map'] else target.data['vic_force_for_each_vertex']
    effective = target.data['vic_effective']
    
    for i, v in enumerate(vs,0):
        toPos = mat @ Vector( init_pos[i] )
        proxy_pos_vec = Vector(proxy_pos[i])
        proxy_pos_vec += (toPos - proxy_pos_vec) * force_pos[i] * effective   
        set_pos = mat.inverted() @ proxy_pos_vec
        v.co = set_pos
                
        proxy_pos[i][0] = proxy_pos_vec.x
        proxy_pos[i][1] = proxy_pos_vec.y
        proxy_pos[i][2] = proxy_pos_vec.z
        
def filterCanEffect( objs ):   
    return [ o for o in objs if o.data is not None and hasattr( o.data, 'vertices' ) ]   

def update( scene ):
    eff_objects = filterCanEffect( bpy.data.objects )
    for o in eff_objects:
        if 'vic_active' in o.data:
            move_vertice( o )
def addListener():
    #if update in bpy.app.handlers.frame_change_pre:
    try:
        bpy.app.handlers.frame_change_pre.remove( update )
    except:
        print( 'update handler is not in the list' )
    bpy.app.handlers.frame_change_pre.append( update )   

class vic_hand_drag(bpy.types.Operator):
    bl_idname = 'vic.hand_drag'
    bl_label = 'Make It Drag'
        
    def doEffect( self ):
        init_objects = filterCanEffect( bpy.context.selected_objects.copy() )
        for o in init_objects:
            save_vertex_position( o )
        addListener() 
    def execute(self, context):
        self.doEffect()
        return {'FINISHED'}
        '''
class vic_set_value_to_all_effect_object( bpy.types.Operator):
    bl_idname = 'vic.set_value_to_all_effect_object'
    bl_label = 'Rewalk All Active Object'
        
    def doEffect( self ):
        init_objects = filterCanEffect( bpy.data.objects )
        for o in init_objects:
            if 'vic_active' in o:
                save_vertex_position( o )
        addListener()
    def execute(self, context):
        self.doEffect()
        return {'FINISHED'}     
    '''
class vic_healing_all_effect_objects( bpy.types.Operator):
    bl_idname = 'vic.healing_all_effect_objects'
    bl_label = 'Healing All'
        
    def doEffect( self ):
        bpy.context.scene.frame_current = 1
        bpy.ops.object.paths_calculate()
        init_objects = filterCanEffect( bpy.data.objects )
        for o in init_objects:
            if 'vic_active' in o.data:
                back_to_origin_vertex_position( o )
        bpy.ops.object.paths_clear()
        addListener()        
    def execute(self, context):
        self.doEffect()
        return {'FINISHED'}          

def createCameraTarget( currobj, targetName ):
    bpy.ops.object.empty_add(type='ARROWS')
    currArrow = bpy.context.object
    currArrow.name = 'vic_camera_target'
    bpy.ops.object.location_clear()
    currArrow.select_set( False )
    currobj.select_set( True )
    bpy.context.view_layer.objects.active = currobj
    bpy.ops.object.constraint_add(type='TRACK_TO')
    currConstraint = currobj.constraints[len(currobj.constraints)-1]
    currConstraint.name = targetName
    currConstraint.target = currArrow
    currConstraint.track_axis = 'TRACK_NEGATIVE_Z'
    currConstraint.up_axis = 'UP_Y'

#===============================================    

class vic_create_camera_target(bpy.types.Operator):
    bl_idname = 'vic.vic_create_camera_target'
    bl_label = 'Create Camera Target'
    
    target_name = "vic_camera_constraint_name"
    
    def execute(self, context):
        currobj = context.object
        cons = currobj.constraints
        for con in cons:
            if con.name == self.target_name:
                self.report( {'ERROR'}, 'already done!' )
                return {'CANCELLED'}
        createCameraTarget( currobj, self.target_name )
        return {'FINISHED'}
        
#==================================================        
        
class vic_select_by_name(bpy.types.Operator):
    bl_idname = 'vic.select_by_name'
    bl_label = 'Select By Name'
    
    def execute(self, context):
        select_name = context.scene.action_properties.string_select_name
        for b in bpy.data.objects:
            find_str = b.name.find( select_name )
            b.select_set( False )
            if find_str != -1:
                b.hide_viewport = False
                b.select_set( True )
        return {'FINISHED'}       
        
#==================================================        

def createMirrorCube():
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.object.editmode_toggle()

    mesh = bmesh.from_edit_mesh(bpy.context.object.data)
    
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    for e in mesh.edges:
        e.select = ( e.index == 2 )
        
    bpy.ops.mesh.loop_multi_select(ring=True)
    bpy.ops.mesh.subdivide()

    for v in mesh.verts:
        v.select = v.co[1] < 0
        
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.editmode_toggle()

    bpy.ops.object.modifier_add(type='MIRROR')
    bpy.context.object.modifiers['Mirror'].use_axis[0] = False
    bpy.context.object.modifiers['Mirror'].use_axis[1] = True

    bpy.ops.object.modifier_add(type='SUBSURF')
        
class mirror_cube_add(bpy.types.Operator):
    bl_idname = 'vic.mirror_cube_add'
    bl_label = 'Create Mirror Cube'
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        if bpy.context.object != None and bpy.context.object.mode == 'EDIT':
            self.report( {'ERROR'}, 'can not using this function in the EDIT mode!' )
            return {'CANCELLED'}
        else:
            createMirrorCube()
        return {'FINISHED'}    

class ActionProperties(bpy.types.PropertyGroup):
    string_select_name = bpy.props.StringProperty( name="", description="Name of select objects", default="")    

class VIC_ACTION_PANEL(bpy.types.Panel):
    bl_category = "Vic Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Actions"

    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        col.operator("vic.mirror_cube_add")
        col.operator("vic.vic_create_camera_target")
        #col.operator("vic.make_meshs_plane")
        col.operator("vic.particle_rigidbody")
        
        row = col.row(align=True)
        row.prop(context.scene.action_properties, 'string_select_name' )
        row.operator("vic.select_by_name")
        
        #col.label(text='Drag Effect')
        #col.operator("vic.hand_drag")
        #col.operator("vic.healing_all_effect_objects")

        #col.label(text="BGE")
        #col.operator("vic.pure_particle")
        #col.operator("vic.pure_particle_sprite")
        #col.operator("vic.pure_particle_sprite_rotable")
        #col.operator("vic.bge_hand_drag")
        #col.operator("vic.bge_quick_motion")
#=======================================        

class ParticlesToRigidbodys(bpy.types.Operator):
    bl_idname = 'vic.particle_rigidbody'
    bl_label = 'Particles To Rigidbodys'
    
    def setting(self, emitter ):
        self.emitter = emitter
        eval_ob = bpy.context.depsgraph.objects.get(self.emitter.name, None)
        self.ps = eval_ob.particle_systems[0]
        self.ps_set = self.ps.settings
        self.ps_set.use_rotation_instance = True
        self.start_frame = int( self.ps_set.frame_start )
        self.end_frame = int( self.ps_set.frame_end + ( self.ps_set.lifetime *  ( 1 + self.ps_set.lifetime_random)))
        self.update_frame = self.end_frame - self.start_frame
        self.mesh_clone = self.ps_set.instance_object
        self.ms = []

    def createMesh(self):
        self.emitter.select_set( False )
        for p in self.ps.particles:
            loc = p.location
            rot = p.rotation.to_euler()
            o = self.mesh_clone.copy()
            bpy.context.view_layer.active_layer_collection.collection.objects.link(o)
            o.scale[0] = p.size
            o.scale[1] = p.size
            o.scale[2] = p.size
            o.select_set( True )
            bpy.context.view_layer.objects.active = o
            bpy.ops.rigidbody.object_add()
            o.location = loc
            o.rotation_euler= rot
            o.rigid_body.kinematic=True
            o.rigid_body.restitution = .2
            o.keyframe_insert('rigid_body.kinematic')
            o.select_set( False )
            self.ms.append( o )
            
    def moveMesh(self, forceEnd = False):
        for i, p in enumerate( self.ps.particles ):
            o = self.ms[i]
            if forceEnd or (p.alive_state == 'DEAD'):
                if o.rigid_body.kinematic:
                    o.rigid_body.kinematic=False
                    o.keyframe_insert('rigid_body.kinematic')
            elif p.alive_state == 'ALIVE':
                o.location = p.location
                o.rotation_euler = p.rotation.to_euler()
                o.keyframe_insert('location')
                o.keyframe_insert('scale')
                o.keyframe_insert('rotation_euler')
            else:
                o.location = p.location
                o.rotation_euler = p.rotation.to_euler()
                
    def clearSetting(self):
        self.ms = []        
            
    def update( self, f ):
        #print( f )
        #print(self.end_frame)
        if f == self.start_frame:
            print("create")
            self.clearSetting()
            self.createMesh()
        elif f == self.end_frame - 1:
            print("end")
            self.moveMesh(True)
            self.clearSetting()
        else:
            print("move")
            self.moveMesh()
        
    def executeAll(self):
        for i in range( self.update_frame ):
            f = self.start_frame + i;
            bpy.context.scene.frame_set(f)
            self.update(f)
            print( 'frame solved:', f )
        '''
        for i in range( self.end_frame ):
            f = i+1;
            bpy.context.scene.frame_set(f)
            self.update(f)
            print( 'frame solved:', f )
        '''    
    def execute(self, context):
        if context.view_layer.objects.active == None:
            self.report( {'ERROR'}, 'please pick one object!' )
            return {'FINISHED'}
        elif len( context.view_layer.objects.active.particle_systems ) == 0:
            self.report( {'ERROR'}, 'need particle system!' )
            return {'FINISHED'}
        elif context.view_layer.objects.active.particle_systems[0].settings.instance_object == None:
            self.report( {'ERROR'}, 'particle system duplicate object need to be setting!' )
            return {'FINISHED'}                    
        else:
            self.setting(context.view_layer.objects.active)
            self.executeAll()
        return {'FINISHED'}

classes = (
    # ui
    ActionProperties,
    VIC_ACTION_PANEL,

    # operation
    vic_create_camera_target,
    vic_select_by_name,
    mirror_cube_add,
    vic_hand_drag,
    vic_healing_all_effect_objects,
    ParticlesToRigidbodys
)
def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.action_properties = bpy.props.PointerProperty(type=ActionProperties)
    
def unregister():
    for cls in classes: bpy.utils.unregister_class(cls)
    del bpy.types.Scene.action_properties