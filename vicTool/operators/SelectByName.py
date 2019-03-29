import bpy

class vic_select_by_name(bpy.types.Operator):
    bl_idname = 'vic.select_by_name'
    bl_label = 'Select By Name'
    bl_description = 'Select By Name'
    
    def execute(self, context):
        select_name = context.scene.action_properties.string_select_name
        for b in bpy.data.objects:
            find_str = b.name.find( select_name )
            b.select_set( False )
            if find_str != -1:
                b.hide_viewport = False
                b.select_set( True )
        return {'FINISHED'}   