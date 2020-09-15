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
from ..vic_tools import (
    addObject,
    activeObject,
    copyObject,
    focusObject,
    prepareAndCreateMesh
)

class vic_procedural_stair(bpy.types.Operator):
    bl_idname = 'vic.vic_procedural_stair'
    bl_label = 'Stair Generator'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    width:FloatProperty(
        name='Width',
        min=1.0,
        default=3.0
    )

    height:FloatProperty(
        name='Height',
        min=1.0,
        default=5.0
    )

    wallHeight:FloatProperty(
        name='Wall Height',
        default=0.0
    )

    wallOffsetY:FloatProperty(
        name='Wall OffsetY',
        default=0.5
    )

    stairUvCenter:FloatProperty(
        name='UV Center',
        min=0.0,
        max=1.0,
        default=.5
    )

    stairUvScaleX:FloatProperty(
        name='UV Scale X',
        default=1.0
    )

    stairUvStep:IntProperty(
        name='UV Step',
        min=1,
        max=10,
        default=4
    )

    stairSideUvScale:FloatProperty(
        name='Side UV Scale',
        default=1.0
    )

    stairMaterial:StringProperty(
        name='Stair',
        default='StairMaterial'
    )

    stairSideMaterial:StringProperty(
        name='Side',
        default='StairSideMaterial'
    )

    count:IntProperty(
        name='Step Count',
        min=1,
        max=50,
        default=10
    )

    stepDepth:FloatProperty(
        name='Step Depth',
        min=.1,
        default=1.
    )

    showWall:BoolProperty(
        name='Show Wall',
        default=True
    )

    editMode:BoolProperty(
        name='Edit Mode',
        default=False,
        description='Turn off this will combine all mesh to one'
    )

    wallMesh:StringProperty(
        name='Pick Wall',
        description='',
        default=''
    )

    pileMesh:StringProperty(
        name='Pick Pile',
        description='',
        default=''
    )

    pileCount:IntProperty(
        name='Pile Per Step',
        min=1,
        default=4
    )

    # def scene_mychosenobject_poll(self, object):
    #     return object.type == 'CURVE'

    # wallMeshj = bpy.props.PointerProperty(
    #     type=bpy.types.Object,
    #     poll=scene_mychosenobject_poll
    # )

    # def createPileMesh(self, mesh, pilePos, offsetY):
    #     uvMap = {}
    #     currentFaceId = len(self.faces)
    #     currentVertId = len(self.verts)
    #     for m in mesh.data.polygons:
    #         vs = []
    #         currentVertexCount = len(self.verts)
    #         for vid in m.vertices:
    #             vs.append(vid + currentVertexCount)
    #         self.faces.append(tuple(vs))
    #         self.matIds.append(m.material_index+3)

    #         for vert_idx, loop_idx in zip(m.vertices, m.loop_indices):
    #             self.uvsMap["%i_%i" % (m.index+currentFaceId,vert_idx+currentVertId)] = mesh.data.uv_layers.active.data[loop_idx].uv

    #     for vid,v in enumerate(mesh.data.vertices):
    #         pos = v.co
    #         newpos = (
    #             pos.x + pilePos[0], 
    #             pos.y + offsetY, 
    #             pos.z + pilePos[2]
    #         )
    #         self.verts.append( newpos )

    # def createOneWall(self, mesh, scaleFactor, tanRadian, startPos, wallPos, offsetY):
    #     currentFaceId = len(self.faces)
    #     currentVertId = len(self.verts)
    #     for m in mesh.data.polygons:
    #         vs = []
    #         currentVertexCount = len(self.verts)
    #         for vid in m.vertices:
    #             vs.append(vid + currentVertexCount)
    #         self.faces.append(tuple(vs))
    #         self.matIds.append(m.material_index+2)

    #         for vert_idx, loop_idx in zip(m.vertices, m.loop_indices):
    #             self.uvsMap["%i_%i" % (m.index+currentFaceId,vert_idx+currentVertId)] = mesh.data.uv_layers.active.data[loop_idx].uv

    #     for vid,v in enumerate(mesh.data.vertices):
    #         pos = v.co
    #         newpos = (
    #             pos.x * scaleFactor + wallPos.x + startPos.x, 
    #             pos.y + wallPos.y + startPos.y + offsetY, 
    #             pos.z + tanRadian * (pos.x * scaleFactor) + wallPos.z + startPos.z + self.wallHeight
    #         )
    #         self.verts.append( newpos )

    def addMaterial(self, name):
        if not name in bpy.data.materials:
            bpy.data.materials.new(name=name)

    def assignMaterial(self, obj, wallMesh, pileMesh):
        self.addMaterial('StairMaterial')
        self.addMaterial('StairSideMaterial')
        if self.stairMaterial != '':
            obj.data.materials.append(bpy.data.materials.get(self.stairMaterial))
        if self.stairSideMaterial != '':
            obj.data.materials.append(bpy.data.materials.get(self.stairSideMaterial))
        if wallMesh is not None:
            for mat in wallMesh.data.materials:
                obj.data.materials.append(mat)
        if pileMesh is not None:
            for mat in pileMesh.data.materials:
                obj.data.materials.append(mat)

    def createPile(self, mesh, piles):
        def cacheParam(pilePos, offsetY):
            def transformWall(vid, v):
                pos = v.co
                newpos = (
                    pos.x + pilePos[0], 
                    pos.y + offsetY, 
                    pos.z + pilePos[2]
                )
                return newpos
            return transformWall
        for p in piles:
            self.addVertexByMesh(mesh, 3, cacheParam(p, self.width/2-self.wallOffsetY))
            self.addVertexByMesh(mesh, 3, cacheParam(p, -self.width/2+self.wallOffsetY))
            # self.createPileMesh(mesh, p, self.width/2-self.wallOffsetY)
            # self.createPileMesh(mesh, p, -self.width/2+self.wallOffsetY)

    def createWall(self, mesh):
        stepHeight = self.height / self.count
        totalLength = self.count * self.stepDepth
        startPos = Vector((self.stepDepth / 2, 0, stepHeight))
        endPos = Vector((totalLength - self.stepDepth / 2, 0, self.height))
        connect = endPos - startPos

        count = round(connect.x / mesh.dimensions.x)
        targetWidth = connect.x / count
        scaleFactor = targetWidth / mesh.dimensions.x

        wallSingle = connect / count
        radian = Vector((1,0,0)).angle(connect.normalized())
        tanRadian = tan(radian)

        def cacheParam(scaleFactor, tanRadian, startPos, wallPos, offsetY):
            def transformWall(vid, v):
                pos = v.co
                newpos = (
                    pos.x * scaleFactor + wallPos.x + startPos.x, 
                    pos.y + wallPos.y + startPos.y + offsetY, 
                    pos.z + tanRadian * (pos.x * scaleFactor) + wallPos.z + startPos.z + self.wallHeight
                )
                return newpos
            return transformWall

        #create mesh in the same object
        if not self.editMode:
            for i in range(count):
                wallPos = wallSingle * (i + .5)

                self.addVertexByMesh(mesh, 2, cacheParam(scaleFactor, tanRadian, startPos, wallPos, self.width/2-self.wallOffsetY))
                self.addVertexByMesh(mesh, 2, cacheParam(scaleFactor, tanRadian, startPos, wallPos, -self.width/2+self.wallOffsetY))

                # self.createOneWall(mesh, scaleFactor, tanRadian, startPos, wallPos, self.width/2-self.wallOffsetY)
                # self.createOneWall(mesh, scaleFactor, tanRadian, startPos, wallPos, -self.width/2+self.wallOffsetY)
        else:
            # create mesh for every wall
            wallPrototype = copyObject(mesh)
            for v in wallPrototype.data.vertices:
                pos = v.co
                v.co = (
                    pos.x * scaleFactor, 
                    pos.y, 
                    pos.z + tanRadian * (pos.x * scaleFactor)
                )
            wallObj = []
            for i in range(count):
                wallPos = wallSingle * (i + .5)
                cloneWall = copyObject(wallPrototype, True)
                cloneWall.location.x = wallPos.x + startPos.x
                cloneWall.location.y = wallPos.y + startPos.y + self.width/2-self.wallOffsetY
                cloneWall.location.z = wallPos.z + startPos.z + self.wallHeight
                addObject(cloneWall)
                wallObj.append(cloneWall)

                cloneWall = copyObject(wallPrototype, True)
                cloneWall.location.x = wallPos.x + startPos.x
                cloneWall.location.y = wallPos.y + startPos.y + -self.width/2+self.wallOffsetY
                cloneWall.location.z = wallPos.z + startPos.z + self.wallHeight
                addObject(cloneWall)
                wallObj.append(cloneWall)
            bpy.data.objects.remove(wallPrototype, do_unlink=True)

    def execute(self, context):

        (obj, update, addRectVertex, addVertexAndFaces, addVertexByMesh) = prepareAndCreateMesh("Stair")
        self.addVertexByMesh = addVertexByMesh

        # unselect all of object, and then can join my own object
        for obj in bpy.context.view_layer.objects:
            obj.select_set(False)

        x = self.width / 2
        stepHeight = self.height / self.count
        stepDepth = self.stepDepth

        pilePerStep = self.pileCount
        if pilePerStep > self.count:
            pilePerStep = self.count - 1
            self.pileCount = pilePerStep

        line = []
        uv = []
        piles = []
        for i in range(self.count):
            line.append((i*stepDepth,-x,i*stepHeight))
            line.append((i*stepDepth,-x,i*stepHeight+stepHeight))
            line.append((i*stepDepth+stepDepth,-x,i*stepHeight+stepHeight))

            uvIndex = i % self.stairUvStep
            uv.append((0,uvIndex/self.stairUvStep))
            uv.append((0,uvIndex/self.stairUvStep + self.stairUvCenter/self.stairUvStep))
            uv.append((0,uvIndex/self.stairUvStep + 1/self.stairUvStep))

            if i % pilePerStep == 0 or (i == self.count - 1):
                piles.append((i*stepDepth + stepDepth/2,-x,i*stepHeight+stepHeight))

        lastVertex = line[len(line)-1]
        # 階梯的點及uv
        addVertexAndFaces(
            line, (0, self.width, 0), 
            uv, (-self.stairUvScaleX,0), 
            1, 0, flip=True)

        # 背面的點及uv
        addVertexAndFaces(
            [lastVertex, (lastVertex[0],lastVertex[1],0)], (0, self.width, 0), 
            [(0,lastVertex[2]),(0,0)], (self.width,0),
            self.stairSideUvScale, 1, flip=True)

        # 側墻的點及uv
        for i in range(self.count):
            addVertexAndFaces(
                [(i*stepDepth,-x, i*stepHeight+stepHeight),
                (i*stepDepth,-x,0),
                (i*stepDepth,x,0),
                (i*stepDepth,x,i*stepHeight+stepHeight)
                ], (stepDepth, 0, 0),[
                (i*stepDepth,i*stepHeight+stepHeight),
                (i*stepDepth,0),
                (i*stepDepth,0),
                (i*stepDepth,i*stepHeight+stepHeight)
                ], (stepDepth,0), self.stairSideUvScale, 1, flip=True)
        
        # check the name of object in the scene! if not, set value to empty
        try:
            bpy.context.view_layer.objects[self.wallMesh]
        except:
            self.wallMesh = ''
        
        try:
            bpy.context.view_layer.objects[self.pileMesh]
        except:
            self.pileMesh = ''

        wallMesh = None
        pileMesh = None
        if (self.showWall):
            if self.wallMesh != '':
                wallMesh = bpy.context.view_layer.objects[self.wallMesh]
                if wallMesh.type == 'MESH':
                    self.createWall(wallMesh)
            if (self.pileMesh != ''):
                pileMesh = bpy.context.view_layer.objects[self.pileMesh]
                if pileMesh.type == 'MESH':
                    self.createPile(pileMesh, piles)

        update()
        self.assignMaterial(obj, wallMesh, pileMesh)

        activeObject(obj)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text='Stair Mesh')
        row = box.row()
        row.prop(self, 'width')
        row.prop(self, 'height')
        row = box.row()
        row.prop(self, 'count')
        row.prop(self, 'stepDepth')

        box = layout.box()
        box.label(text='Wall Mesh')
        row = box.row()
        row.prop(self, 'showWall')
        #row.prop(self, 'editMode')
        box.prop_search(self, "wallMesh", bpy.data, "objects")
        box.prop_search(self, "pileMesh", bpy.data, "objects")
        #row.prop(self, "wallMesh")
        row = box.row()
        row.prop(self, 'wallHeight')
        row.prop(self, 'wallOffsetY')
        box.prop(self, 'pileCount')

        box = layout.box()
        box.label(text='Stair Material')
        row = box.row()
        box.prop(self, 'stairUvStep')
        row.prop(self, 'stairUvCenter')
        row.prop(self, 'stairUvScaleX')
        box.prop(self, 'stairSideUvScale')
        box.prop_search(self, "stairMaterial", bpy.data, "materials")
        box.prop_search(self, "stairSideMaterial", bpy.data, "materials")

        