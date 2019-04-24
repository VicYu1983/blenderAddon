import bpy, time
from math import *
from mathutils import *
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

styleSetList = [
    ('0','Normal', 'Normal'),
    ('1','Sin', 'Sin')
]

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

    stepMesh:StringProperty(
        name='Pick Step',
        description='',
        default=''
    )

    bridgeHeight:FloatProperty(
        name='Height',
        min=1,
        default=4
    )

    bridgePow:FloatProperty(
        name='Curve',
        min=.1,
        default=2
    )

    styleSet: EnumProperty(
        name='Style',
        description='',
        items=styleSetList,
        default='0'
    )

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text='Base Mesh')
        box.prop_search(self, "baseMesh", bpy.data, "objects")
        box.prop_search(self, "stepMesh", bpy.data, "objects")
        box.prop(self, 'bridgeHeight')
        box.prop(self, 'bridgePow')
        box.prop(self, 'styleSet')

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
        if self.stepMesh not in bpy.context.view_layer.objects:
            return {'FINISHED'}

        prefab_step = bpy.context.view_layer.objects[self.stepMesh]
        prefab_base = bpy.context.view_layer.objects[self.baseMesh]
        allLength = prefab_base.dimensions.x + .5
        height = self.bridgeHeight
        powFactor = self.bridgePow

        stepLength = prefab_step.dimensions.x
        count = round(allLength / stepLength)
        halfCount = count / 2
        useLength = allLength / count
        xDir = Vector((1,0,0))

        base = copyToScene(prefab_base)
        # 强制修改matrix_world
        base.matrix_world = Matrix.Translation(Vector((allLength/2,0,0)))

        pts = []
        for i in range( count + 1 ):    
            x = useLength * i
            if self.styleSet == styleSetList[0][0]:
                z = 1 - pow(abs(i-halfCount) / halfCount, powFactor)
            elif self.styleSet == styleSetList[1][0]:
                z = sin(x/allLength * pi * 2 - pi / 2)
                # sin值域-1~1，轉爲0~1
                z = (z+1)/2
            else:
                z = 0
            pts.append(Vector((x, 0, z * height)))

        joinList = []
        for i, p in enumerate(pts):
            if i == len(pts)-1:
                break
            first = p
            second = pts[i+1]
            diff = second - first
            dir = diff.normalized()

            radian = atan2(dir.z, dir.x)
            scaleX = diff.length / stepLength
            
            stepObj = copyToScene(prefab_step)
            # 强制修改matrix_world
            matT = Matrix.Translation(first + diff / 2)
            matR = Matrix.Rotation(-radian, 4, Vector((0,1,0)))
            matS = Matrix.Scale(scaleX, 4, Vector((1,0,0)))
            stepObj.matrix_world = matT @ matR @ matS
            joinList.append( stepObj )
            
            self.transformBridge(base, first, second )
            

        joinObj(joinList, joinList[0])
        return {'FINISHED'}