import bpy
from ..vic_tools import addProps

class vic_procedural_lantern_proxy(bpy.types.Operator):
    bl_idname = "object.vic_procedural_lantern_proxy"
    bl_label = "Create Proxy"

    def execute(self, context):

        bpy.ops.object.empty_add(type='SPHERE')
        obj = bpy.context.object

        addProps(obj, "Active", False)
        addProps(obj, "Instance", "Cube")
        return {'FINISHED'}

class vic_procedural_lantern(bpy.types.Operator):
    bl_idname = "object.vic_procedural_lantern"
    bl_label = "Generate Lantern"

    def execute(self, context):
        return {'FINISHED'}