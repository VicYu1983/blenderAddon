import bpy

class vic_procedural_stair(bpy.types.Operator):
    bl_idname = 'vic.vic_procedural_stair'
    bl_label = 'Create Stair'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}
        
    def doEffect( self ):  
        print("doEffect")
    def execute(self, context):
        self.doEffect()
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="addc")