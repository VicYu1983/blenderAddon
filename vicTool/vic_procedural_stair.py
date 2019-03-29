import bpy

class vic_procedural_stair(bpy.types.Operator):
    bl_idname = 'vic.vic_procedural_stair'
    bl_label = ''
    bl_description = ''
        
    def doEffect( self ):  
        print("doEffect")
    def execute(self, context):
        self.doEffect()
        return {'FINISHED'}