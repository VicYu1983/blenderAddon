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
from .vic_tools import *

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
        default='Base'
    )

    stepMesh:StringProperty(
        name='Pick Step',
        description='',
        default='Step'
    )

    wallMesh:StringProperty(
        name='Pick Wall',
        description='',
        default='Wall'
    )

    pileMesh:StringProperty(
        name='Pick Pile',
        description='',
        default='Pile'
    )

    bridgeLength:FloatProperty(
        name='Length',
        min=1,
        default=100
    )

    bridgeHeight:FloatProperty(
        name='Height',
        min=0,
        default=4
    )

    bridgeWidth:FloatProperty(
        name='Width',
        min=1,
        default=10
    )

    bridgePow:FloatProperty(
        name='Curve',
        min=.1,
        default=2
    )

    stableBridge:BoolProperty(
        name='Stable',
        default=False
    )

    bridgeStableHeight:FloatProperty(
        name='Stable Height',
        default=-5
    )

    stepHeight:FloatProperty(
        name='Step Height',
        min=0,
        default=.1
    )

    wallHeight:FloatProperty(
        name='Wall Height',
        default=0
    )

    wallInset:FloatProperty(
        name='Wall Inset',
        default=1,
    )

    pileCount:IntProperty(
        name='Pile Count',
        min=2,
        max=30,
        default=10
    )

    styleSet: EnumProperty(
        name='Style',
        description='',
        items=styleSetList,
        default='0'
    )

    pilePerWall: BoolProperty(
        name='Per Wall',
        default=True
    )

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text='Base Shape')
        box.prop_search(self, "baseMesh", bpy.data, "objects")
        box.prop_search(self, "stepMesh", bpy.data, "objects")
        box.prop(self, 'bridgeWidth')
        box.prop(self, 'bridgeLength')
        box.prop(self, 'bridgeHeight')
        box.prop(self, 'bridgePow')
        box.prop(self, 'stepHeight')
        box.prop(self, 'styleSet')

        # row = box.row()
        # row.prop(self, 'stableBridge')
        # row.prop(self, 'bridgeStableHeight')

        box = layout.box()
        box.label(text='Wall & Pile')
        box.prop_search(self, "wallMesh", bpy.data, "objects")
        box.prop_search(self, "pileMesh", bpy.data, "objects")
        box.prop(self, 'wallHeight')
        box.prop(self, 'wallInset')
        box.prop(self, 'pileCount')
        box.prop(self, 'pilePerWall')

    def transformMesh( self, obj, minpt, maxpt, firstpt, offsetZ = 0 ):
        localMin = obj.matrix_world.inverted() @ minpt
        localMax = obj.matrix_world.inverted() @ maxpt
        localFirst = obj.matrix_world.inverted() @ firstpt
        height = localMax.z - localMin.z
        width = localMax.x - localMin.x
        for v in obj.data.vertices:
            # effectFactor = 1
            # if self.stableBridge:
            #     if v.co.z < self.bridgeStableHeight:
            #         effectFactor = 0
            #     else:
            #         effectFactor = (v.co.z - self.bridgeStableHeight) / abs(self.bridgeStableHeight)
            #         effectFactor = min(1, effectFactor)
                    
            if v.co.x >= localMin.x and v.co.x < localMax.x:
                percentX = (v.co.x - localMin.x)/width
                v.co.z += (percentX * height + (localMin.z - localFirst.z) + offsetZ)
                # v.co.z += (percentX * height + (localMin.z - localFirst.z) + offsetZ) * effectFactor

    def getCurveLocation(self, count, allLength):
        halfCount = count / 2
        useLength = allLength / count
        pts = []
        for i in range( count + 1 ):    
            x = useLength * i
            if self.styleSet == styleSetList[0][0]:
                z = 1 - pow(abs(i-halfCount) / halfCount, self.bridgePow )
            elif self.styleSet == styleSetList[1][0]:
                z = sin(x/allLength * pi * 2 - pi / 2)
                # sin值域-1~1，轉爲0~1
                z = (z+1)/2
            else:
                z = 0
            pts.append(Vector((x, 0, z * self.bridgeHeight)))
        return pts

    def createWall(self, allLength):
        prefab_wall = None
        if self.wallMesh in bpy.context.view_layer.objects and bpy.context.view_layer.objects[self.wallMesh].type == 'MESH':
            prefab_wall = bpy.context.view_layer.objects[self.wallMesh]

        wall = None
        if prefab_wall != None:
            stepLength = prefab_wall.dimensions.x
            count = round(self.bridgeLength / stepLength)
            usingLength = (self.bridgeLength / count)
            scaleX = usingLength / stepLength
            joinList = []
            joinList2 = []
            for i in range(count):
                wallObj = copyToScene(prefab_wall)
                matT = Matrix.Translation(Vector(((i+.5) * usingLength, self.bridgeWidth/2 - self.wallInset, 0)))
                matS = Matrix.Scale(scaleX, 4, Vector((1,0,0)))
                wallObj.matrix_world = matT @ matS
                joinList.append(wallObj)

                wallObj = copyToScene(prefab_wall)
                matT = Matrix.Translation(Vector(((i+.5) * usingLength, -self.bridgeWidth/2 + self.wallInset, 0)))
                wallObj.matrix_world = matT @ matS
                joinList.append(wallObj)

            joinObj(joinList, joinList[0])
            wall = joinList[0]
            wall.matrix_world.row[0][3] = allLength/2
        return wall

    def createPile(self, allLength):
        prefab_pile = None
        if self.pileMesh in bpy.context.view_layer.objects and bpy.context.view_layer.objects[self.pileMesh].type == 'MESH':
            prefab_pile = bpy.context.view_layer.objects[self.pileMesh]

        prefab_wall = None
        if self.wallMesh in bpy.context.view_layer.objects and bpy.context.view_layer.objects[self.wallMesh].type == 'MESH':
            prefab_wall = bpy.context.view_layer.objects[self.wallMesh]

        pile = None
        if prefab_pile != None:
            count = self.pileCount-1
            if self.pilePerWall and prefab_wall != None:
                stepLength = prefab_wall.dimensions.x
                count = round(self.bridgeLength / stepLength)

            pts = self.getCurveLocation(count, self.bridgeLength)
            joinList = []
            for p in pts:
                pileObj = copyToScene(prefab_pile)
                pileObj.matrix_world = Matrix.Translation(Vector((p.x, self.bridgeWidth/2 - self.wallInset, p.z + self.wallHeight)))
                joinList.append(pileObj)

                pileObj = copyToScene(prefab_pile)
                pileObj.matrix_world = Matrix.Translation(Vector((p.x, -self.bridgeWidth/2 + self.wallInset, p.z + self.wallHeight)))
                joinList.append(pileObj)

            joinObj(joinList, joinList[0])
            pile = joinList[0]
            pile.matrix_world.row[0][3] = allLength/2
        return pile

    def createStep(self, prefab_step, allLength, base, wall):
        stepLength = prefab_step.dimensions.x
        count = round(allLength / stepLength)
        pts = self.getCurveLocation(count, allLength)
        widthScaleForStep = self.bridgeWidth / prefab_step.dimensions.y

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
            matT = Matrix.Translation(first + diff / 2 + Vector((0,0,self.stepHeight)))
            matR = Matrix.Rotation(-radian, 4, Vector((0,1,0)))
            matS = Matrix.Scale(scaleX, 4, Vector((1,0,0)))
            matS2 = Matrix.Scale(widthScaleForStep, 4, Vector((0,1,0)))
            stepObj.matrix_world = matT @ matR @ matS @ matS2
            joinList.append( stepObj )
            
            self.transformMesh(base, first, second, pts[0] )
            if wall != None:
                self.transformMesh(wall, first, second, pts[0], self.wallHeight )

        joinObj(joinList, joinList[0])
        step = joinList[0]
        return step

    def createBase(self, prefab_base, allLength):
        widthScale = self.bridgeWidth / prefab_base.dimensions.y
        lengthScale = self.bridgeLength / prefab_base.dimensions.x 
        base = copyToScene(prefab_base)
        scaleObjVertex(base, (lengthScale, widthScale, 1))
        base.matrix_world = Matrix.Translation(Vector((allLength/2,0,0))) # 强制修改matrix_world
        return base

    def execute(self, context):
        if self.baseMesh not in bpy.context.view_layer.objects or bpy.context.view_layer.objects[self.baseMesh].type != 'MESH':
            return {'FINISHED'}
        if self.stepMesh not in bpy.context.view_layer.objects or bpy.context.view_layer.objects[self.stepMesh].type != 'MESH':
            return {'FINISHED'}

        prefab_base = bpy.context.view_layer.objects[self.baseMesh]
        prefab_step = bpy.context.view_layer.objects[self.stepMesh]
        allLength = self.bridgeLength + .5
        
        base = self.createBase(prefab_base, allLength)
        wall = self.createWall(allLength)
        pile = self.createPile(allLength)
        step = self.createStep(prefab_step, allLength, base, wall)

        joinList = filter(lambda obj: obj != None, [base, wall, pile, step])
        joinObj(joinList, base)
        base.name = 'ProcedrualBridge'
        
        return {'FINISHED'}

class vic_procedural_bridge_panel(bpy.types.Panel):
    bl_category = "Vic Addons"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Procedrual Bridge"

    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        col.operator(vic_procedural_bridge.bl_idname)  