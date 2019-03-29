import bpy
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        FloatVectorProperty,
        IntProperty,
        IntVectorProperty,
        StringProperty,
        )
class vic_procedural_stair(bpy.types.Operator):
    bl_idname = 'vic.vic_procedural_stair'
    bl_label = 'Create Stair'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    width = FloatProperty(
        name='Width',
        description='',
        min=1.0,
        default=1.0
        )
        
    def doEffect( self ):  
        print("doEffect")
    def execute(self, context):
        self.doEffect()

        
        verts = [(-self.width,-1,0), (-1,1,0),(1,1,0),(1,-1,0)]
        faces = [(0, 1, 2, 3)]



        mesh = bpy.data.meshes.new("stair_mesh")
        obj = bpy.data.objects.new("stair_obj", mesh)

        mesh.from_pydata(verts, [], faces)

        bpy.context.view_layer.active_layer_collection.collection.objects.link(obj)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self, "width")