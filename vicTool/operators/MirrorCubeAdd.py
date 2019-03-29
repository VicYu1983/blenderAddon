import bpy, bmesh

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
        
# class mirror_cube_add(bpy.types.Operator):
#     bl_idname = 'vic.mirror_cube_add'
#     bl_label = 'Create Mirror Cube'
#     bl_description = 'Create Mirror Cube'

#     bl_options = {'REGISTER', 'UNDO'}
#     def execute(self, context):
#         if bpy.context.object != None and bpy.context.object.mode == 'EDIT':
#             self.report( {'ERROR'}, 'can not using this function in the EDIT mode!' )
#             return {'CANCELLED'}
#         else:
#             createMirrorCube()
#         return {'FINISHED'}    

class mirror_cube_add(bpy.types.Operator):
    bl_idname = 'vic.mirror_cube_add'
    bl_label = 'Create Mirror Cube'
    bl_description = 'Create Mirror Cube'

    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        if bpy.context.object != None and bpy.context.object.mode == 'EDIT':
            self.report( {'ERROR'}, 'can not using this function in the EDIT mode!' )
            return {'CANCELLED'}
        else:
            createMirrorCube()
        return {'FINISHED'}    