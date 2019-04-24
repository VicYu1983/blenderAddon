import bpy, time
from math import *
from mathutils import Vector
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        FloatVectorProperty,
        IntProperty,
        IntVectorProperty,
        StringProperty,
        PointerProperty
        )
from ..vic_tools import *

class vic_procedural_bridge(bpy.types.Operator):
    bl_idname = 'vic.vic_procedural_bridge'
    bl_label = 'Bridge Generator'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    baseMesh:StringProperty(
        name='Pick Base',
        description='',
        default=''
    )

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text='Base Mesh')
        box.prop_search(self, "baseMesh", bpy.data, "objects")

    def transformBridge( self, obj, min, max ):
        localMin = obj.matrix_world.inverted() @ min
        localMax = obj.matrix_world.inverted() @ max
        height = localMax.z - localMin.z
        width = localMax.x - localMin.x
        for v in obj.data.vertices:
            if v.co.x >= localMin.x and v.co.x < localMax.x:
                percentX = (v.co.x - localMin.x)/width
                v.co.z += percentX * height + localMin.z

    def execute(self, context):
        # parameters

        if self.baseMesh not in bpy.context.view_layer.objects:
            return {'FINISHED'}

        prefab_step = bpy.data.objects['Cube']
        prefab_base = bpy.context.view_layer.objects[self.baseMesh]
        allLength = prefab_base.dimensions.x + .5
        height = 10
        powFactor = 2

        stepLength = prefab_step.dimensions.x
        count = round(allLength / stepLength)
        halfCount = count / 2
        useLength = allLength / count
        xDir = Vector((1,0,0))

        # 正常來説應該用這裏的方式。但是他在特定情況下不會更新matrix_world，所以改爲以下的方式
        # base = copyToScene(prefab_base)
        # base.location.x = allLength/2
        # base.location.y = 0
        # base.location.z = 0
        # bpy.context.scene.update()

        # 强制修改matrix_world
        base = copyToScene(prefab_base)
        base.matrix_world.row[0][3] = allLength/2
        base.matrix_world.row[1][3] = 0
        base.matrix_world.row[2][3] = 0

        pts = []
        for i in range( count + 1 ):    
            x = useLength * i
            z = 1 - pow(abs(i-halfCount) / halfCount, powFactor)
            z = sin(x/allLength * pi * 2 - pi / 2)
            pts.append(Vector((x, 0, z * height)))

        for i, p in enumerate(pts):
            if i == len(pts)-1:
                print('last')
                break
            first = p
            second = pts[i+1]
            diff = second - first
            dir = diff.normalized()
            
            # no navigate
            # radian = dir.angle(xDir)
            radian = atan2(dir.z, dir.x)
            scaleX = diff.length / stepLength
            
            stepObj = copyToScene(prefab_step)
            stepObj.location = first + diff / 2
            stepObj.rotation_euler.y = -radian
            stepObj.scale.x = scaleX
            
            self.transformBridge(base, first, second )
        #for v in base.data.vertices:
        #    print( v.co )
            
        return {'FINISHED'}