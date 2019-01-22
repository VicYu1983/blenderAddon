
import bpy, math
from mathutils import Vector
from mathutils import Matrix
from mathutils import Quaternion

def clearAllBonesKey( bones, start_frame, end_frame):
    for f in range( start_frame, end_frame ):
        for b in bones:
            try:
                b.keyframe_delete(data_path="rotation_quaternion" ,frame=f)
            except RuntimeError:
                print( "no action!" )
            b.rotation_quaternion = Quaternion( Vector(), 1 )
            
def getLocalQuaternion( m, axis, angle ):
    b_rot_mat = getRotationMatrixFromMatrix( m )
    localAxis = b_rot_mat.inverted() * axis
    return Quaternion (localAxis, angle)            
    
def getRotationMatrixFromMatrix( m ):
    return m.to_quaternion().to_matrix().to_4x4().copy()    

def getTailMatrix( body, bone, pos ):
    qua_mat = body.matrix_world @ bone.matrix
    qua_mat = qua_mat.to_quaternion().to_matrix().to_4x4()
    pos_mat = Matrix.Translation( body.matrix_world @ pos )
    return pos_mat @ qua_mat

def collectBonesFromRoot( root_bone ):
    bones = []
    temp_bone = root_bone
    while( len( temp_bone.children ) != 0 ):
        bones.append( temp_bone.children[0] )
        temp_bone = temp_bone.children[0]
    return bones   

def getBoneRelativeData( root, pts):
    pos_data = []
    dist_data = []
    
    for i, p in enumerate( pts, 0 ):
        first_point = None
        if i == 0:
            first_point = root
        else:
            first_point = pts[i-1]
        pos_data.append( first_point.inverted().copy() @ p.to_translation().copy() )
        dist_data.append( (first_point.to_translation().copy() - p.to_translation().copy()).magnitude )
    return pos_data, dist_data     

def saveRootPosition( root, root_locs ):
    root_locs.append( root.to_translation().copy() )
    if len( root_locs ) > 100:
        root_locs.pop(0)
        
def getDiffPosition(root_locs, prev_count):
    last = len(root_locs)-1
    target = last - prev_count
    if target < 0:
        return Vector()
    if len( root_locs ) < target + 1:
        return Vector()
    pa = root_locs[target]
    pb = root_locs[target-1]
    return pa-pb

def setTranslationForMatrix( mat, pos ):
    return Matrix.Translation( pos ) @ mat.to_quaternion().to_matrix().to_4x4()

def setRotationForMatrix( mat, qua ):
    return Matrix.Translation( mat.to_translation() ) @ qua.to_matrix().to_4x4()
    
def addForce(pts, pts_spd, root, root_locs, pos_data, gravity):
    for i, p in enumerate( pts, 0 ):
        first_point = None
        if i == 0:
            first_point = root
        else:
            first_point = pts[i-1]
        
        back_pos = first_point @ pos_data[i].copy()
        back_force = back_pos - p.to_translation().copy()
        
        if bpy.context.scene.SpringBoneProperties.spring_bone_keep_is_spring:
            spd = pts_spd[i]
        
            diff = getDiffPosition( root_locs, i * 3 )
            
            spd += diff * bpy.context.scene.SpringBoneProperties.spring_bone_extend_factor
            spd += back_force * bpy.context.scene.SpringBoneProperties.spring_bone_spring_factor
            spd += gravity * bpy.context.scene.SpringBoneProperties.spring_bone_gravity_factor
            spd *= bpy.context.scene.SpringBoneProperties.spring_bone_friction_factor
            pts[i] = setTranslationForMatrix( p, p.to_translation() + spd )
        else:
            pts[i] = setTranslationForMatrix( p, p.to_translation() + back_force * bpy.context.scene.SpringBoneProperties.spring_bone_spring_factor )
        
def setRotation(root, pts, up_vec):
    for i, p in enumerate( pts, 0 ):
        first_point = None
        if i == 0:
            first_point = root
        else:
            first_point = pts[i-1]
        
        z_vec = ( first_point.to_translation() - p.to_translation() ).normalized()
        rot_quat = z_vec.to_track_quat('-Y', 'Z')
        pts[i] = setRotationForMatrix( p, rot_quat )
        
        # another method I offen used
        '''
        z_vec = ( first_point.to_translation() - p.to_translation() ).normalized()
        spin_vec = z_vec.cross( up_vec ).normalized()
        spin_angle = z_vec.angle( up_vec )
        pts[i] = setRotationForMatrix( p, Quaternion( spin_vec, spin_angle ).inverted() )
        '''
        
def limitDistance(root, pts, pts_len):
    for i, p in enumerate( pts, 0 ):
        first_point = None
        if i == 0:
            first_point = root
        else:
            first_point = pts[i-1]
        len = pts_len[i] 
        pts[i] = setTranslationForMatrix( p, ( p.to_translation() - first_point.to_translation() ).normalized() * len + first_point.to_translation() )     
        
def syncToDebugView( f, start_frame, body, debug_views, pts ):
    for i, v in enumerate( debug_views, 0 ):
        v.matrix_world = pts[i]
        if f >= start_frame:
            v.keyframe_insert(data_path="rotation_quaternion" ,frame=f)     
            v.keyframe_insert(data_path="location" ,frame=f)     
    
def mapToBone( f, start_frame, body, root, root_bone, bones, pts ):
    for i, b in enumerate( bones, 0 ):
        b.matrix = body.matrix_world.inverted() @ pts[i]
        if f >= start_frame:
            b.keyframe_insert(data_path="rotation_quaternion" ,frame=f)       

        # this update is very important, blender will update matrix with this function call, if not call will occur strange performance
        bpy.context.scene.update() 
    
    # another method, using quaternion
    '''
    global_proxy_qua = pts[i].to_quaternion()
    global_bone_gua = ( body.matrix_world * b.matrix ).to_quaternion()
    global_diff_qua = global_bone_gua.inverted() * global_proxy_qua
    
    b.rotation_quaternion *= global_diff_qua
    
    if f >= start_frame:
        b.keyframe_insert(data_path="rotation_quaternion" ,frame=f)   
    '''

debugView = False

class vic_spring_bone(bpy.types.Operator):
    bl_idname = 'vic.spring_bone'
    bl_label = 'Bake Spring Bone'
    
    def process(self,context):
        
        objs = bpy.data.objects
        body = bpy.context.object

        up_vec = Vector([0, -1, 0])        
        gravity = Vector([0,0,-1])   
        
        start_frame = context.scene.SpringBoneProperties.spring_bone_frame_start
        end_frame = context.scene.SpringBoneProperties.spring_bone_frame_end
        
        selected_pose_bones = context.selected_pose_bones

        for root_bone in selected_pose_bones:
            root = getTailMatrix( body, root_bone, root_bone.tail )
            bones = collectBonesFromRoot( root_bone ) 

            pts = [ getTailMatrix( body, b, b.tail ) for b in bones ]
            pts_spd = [Vector() for p in pts]
            
            # for prev force
            root_locs = []
            
            # set new mat for relative data
            setRotation( root, pts, up_vec )  
            
            # save relative data for children
            pos_data, dist_data = getBoneRelativeData( root, pts )
            
            # debug view
            # maybe will add new method for create fake bone
            
            if debugView:
                debug_views = []
                for b in bones:
                    bpy.ops.mesh.primitive_cone_add()
                    bpy.context.object.rotation_mode = 'QUATERNION'
                    #bpy.context.object.name = 'abc'
                    #bpy.ops.transform.resize(value=(.1,.1,.1))
                    debug_views.append( bpy.context.object )
            
            for i in range( start_frame, end_frame ): 
                bpy.context.scene.frame_set( i )
                
                root = getTailMatrix( body, root_bone, root_bone.tail )
                saveRootPosition( root, root_locs )
                setRotation( root, pts, up_vec )  
                addForce( pts, pts_spd, root, root_locs, pos_data, gravity )
                limitDistance( root, pts, dist_data )   
                mapToBone( i, start_frame, body, root, root_bone, bones, pts )
                
                # maybe will add new method for create fake bone
                if debugView:
                    syncToDebugView( i, start_frame, body, debug_views, pts )
                
                print( 'On Bone: ' + root_bone.name + ', Frame Complete: ' + str( i ) )
            bpy.context.scene.frame_set( 1 )             
        
    def execute(self, context):
        if context.object == None:
            return {'FINISHED'}
        else:
            if not hasattr( context.object, 'pose' ):
                return {'FINISHED'}
        if context.active_pose_bone == None:
            return {'FINISHED'}
        self.process( context )
        return {'FINISHED'}
        
class vic_bones_clear_key(bpy.types.Operator):
    bl_idname = 'vic.bones_clear_key'
    bl_label = 'Clear All Bones Key'      

    def process( self, context ):
        selected_pose_bones = context.selected_pose_bones

        for root_bone in selected_pose_bones:
            bones = collectBonesFromRoot( root_bone ) 
            
            start_frame = context.scene.SpringBoneProperties.spring_bone_frame_start
            end_frame = context.scene.SpringBoneProperties.spring_bone_frame_end
            
            clearAllBonesKey( bones, start_frame, end_frame )

    def execute(self, context):
            if context.object == None:
                return {'FINISHED'}
            else:
                if not hasattr( context.object, 'pose' ):
                    return {'FINISHED'}
            if context.active_pose_bone == None:
                return {'FINISHED'}                    
            self.process( context )
            return {'FINISHED'}
        
class VIC_SPRING_BONE_TOOL(bpy.types.Panel):
    bl_category = "Vic Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Spring Bone Tool"

    def draw(self, context):
        layout = self.layout     
        
        col = layout.column(align=True)
        col.operator("vic.spring_bone")        
        col.operator("vic.bones_clear_key")        
        col.prop(context.scene.SpringBoneProperties, 'spring_bone_frame_start' ) 
        col.prop(context.scene.SpringBoneProperties, 'spring_bone_frame_end' ) 
        col = layout.column(align=True)
        col.prop(context.scene.SpringBoneProperties, 'spring_bone_extend_factor' ) 
        col.prop(context.scene.SpringBoneProperties, 'spring_bone_spring_factor' ) 
        col.prop(context.scene.SpringBoneProperties, 'spring_bone_gravity_factor' ) 
        col.prop(context.scene.SpringBoneProperties, 'spring_bone_friction_factor' ) 
        col.prop(context.scene.SpringBoneProperties, 'spring_bone_keep_is_spring' ) 
       # col = layout.column(align=True)
       # col.prop(context.scene, 'spring_bone_roop_gravity', 'Roop Gravity' ) 
        
#=======================================

class SpringBoneProperties(bpy.types.PropertyGroup):
    spring_bone_extend_factor = bpy.props.FloatProperty(
        name='Extend',
        default=0.0,
        min=0.0,
        max=1.0
    )

    spring_bone_spring_factor = bpy.props.FloatProperty(
        name='Keep',
        default=.6,
        min=0.0,
        max=1.0
    )

    spring_bone_gravity_factor = bpy.props.FloatProperty(
        name='Gravity',
        default=0.0,
        min=0.0,
        max=1.0
    )

    spring_bone_friction_factor = bpy.props.FloatProperty(
        name='Friction',
        default=0.5,
        min=0.0,
        max=1.0
    )

    spring_bone_keep_is_spring = bpy.props.BoolProperty(
        name='Spring',
        default=True)

    spring_bone_frame_start = bpy.props.IntProperty(
        name="Start Frame", description="Start frame of animation", 
        default=1, step=1, min=1, max=100000)
            
    spring_bone_frame_end = bpy.props.IntProperty(
        name="End Frame", description="End frame of animation", 
        default=50, step=1, min=2, max=100000)    

classes = (
    # ui
    SpringBoneProperties,
    VIC_SPRING_BONE_TOOL,

    # operation
    vic_bones_clear_key,
    vic_spring_bone,
)
def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.SpringBoneProperties = bpy.props.PointerProperty(type=SpringBoneProperties)
    
def unregister():
    for cls in classes: bpy.utils.unregister_class(cls)
    del bpy.types.Scene.SpringBoneProperties