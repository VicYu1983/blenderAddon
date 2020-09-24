import bpy

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
    
class vic_create_camera_target(bpy.types.Operator):
    bl_idname = 'vic.vic_create_camera_target'
    bl_label = 'Create Look At'
    bl_description = 'Create Look At'

    target_name = "vic_camera_constraint_name"
    
    def execute(self, context):
        currobj = context.object
        if currobj == None: return {'FINISHED'}
        cons = currobj.constraints
        for con in cons:
            if con.name == self.target_name:
                self.report( {'ERROR'}, 'already done!' )
                return {'CANCELLED'}
        createCameraTarget( currobj, self.target_name )
        return {'FINISHED'}