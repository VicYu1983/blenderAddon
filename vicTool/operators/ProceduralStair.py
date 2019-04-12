import bpy
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

class vic_procedural_stair(bpy.types.Operator):
    bl_idname = 'vic.vic_procedural_stair'
    bl_label = 'Create Stair'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    width = FloatProperty(
        name='Width',
        min=1.0,
        default=3.0
    )

    height = FloatProperty(
        name='Height',
        min=1.0,
        default=5.0
    )

    wallHeight = FloatProperty(
        name='Wall Height',
        min=0.0,
        default=1.0
    )

    wallOffsetY = FloatProperty(
        name='Wall OffsetY',
        default=0.0
    )

    count = IntProperty(
        name='Step Count',
        min=1,
        default=10
    )

    stepDepth = FloatProperty(
        name='Step Depth',
        min=.1,
        default=1.
    )

    wallMesh = StringProperty(
        name='Pick Mesh',
        description='DO NOT Pick Self!',
        default=''
    )

    # def scene_mychosenobject_poll(self, object):
    #     return object.type == 'CURVE'

    # wallMeshj = bpy.props.PointerProperty(
    #     type=bpy.types.Object,
    #     poll=scene_mychosenobject_poll
    # )

    # 給定一條綫上的點，再給定一個偏移向量，用程式產生偏移過後的第二條綫段的點
    # 用兩條綫上的點來產生面
    def addVertexAndFaces(self, line, offset, verts, faces, flip = False, close = False):
        anotherLine = []
        startId = len(verts)
        for i, v in enumerate(line):
            offsetVert = (  v[0] + offset[0],
                            v[1] + offset[1],
                            v[2] + offset[2])
            anotherLine.append(offsetVert)

            # 收集面id
            v1 = startId+i
            v2 = v1+len(line)
            v3 = v2+1
            v4 = v1+1

            isLastFace = (i == len(line)-1)
            if isLastFace:
                if close:
                    if flip:
                        f = (v1,startId,startId+len(line),v2)
                    else:
                        f = (v1,v2,startId+len(line),startId)
            else:
                if flip:
                    f = (v1, v4, v3, v2)
                else:
                    f = (v1, v2, v3, v4)
            faces.append(f)

        line.extend(anotherLine)
        verts.extend(line)

    def createOneWall(self, mesh, scaleFactor, tanRadian, startPos, wallPos, offsetY):
        for m in mesh.data.polygons:
            vs = []
            currentVertexCount = len(self.verts)
            for vid in m.vertices:
                vs.append(vid + currentVertexCount)
            self.faces.append(tuple(vs))
        
        for vid,v in enumerate(mesh.data.vertices):
            pos = v.co
            newpos = (
                pos.x * scaleFactor + wallPos.x + startPos.x, 
                pos.y + wallPos.y + startPos.y + offsetY, 
                pos.z + tanRadian * (pos.x * scaleFactor) + wallPos.z + startPos.z + self.wallHeight
            )
            self.verts.append( newpos )

    def createWall(self, mesh):
        print("createWall")

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

        for i in range(count):
            wallPos = wallSingle * (i + .5)
            self.createOneWall(mesh, scaleFactor, tanRadian, startPos, wallPos, self.width/2-self.wallOffsetY)
            self.createOneWall(mesh, scaleFactor, tanRadian, startPos, wallPos, -self.width/2+self.wallOffsetY)

    def execute(self, context):
        self.verts = []
        self.faces = []

        x = self.width / 2
        stepHeight = self.height / self.count
        stepDepth = self.stepDepth

        line = []
        for i in range(self.count):
            line.append((i*stepDepth,-x,i*stepHeight))
            line.append((i*stepDepth,-x,i*stepHeight+stepHeight))
            line.append((i*stepDepth+stepDepth,-x,i*stepHeight+stepHeight))
        lastVertex = line[len(line)-1]
        line.append((lastVertex[0],lastVertex[1],0))
        self.addVertexAndFaces(line, (0, self.width, 0), self.verts, self.faces, flip=True)

        for i in range(self.count):
            self.addVertexAndFaces([
                (i*stepDepth,-x, i*stepHeight+stepHeight),
                (i*stepDepth,-x,0),(i*stepDepth,x,0),
                (i*stepDepth,x,i*stepHeight+stepHeight)
                ], (stepDepth, 0, 0), self.verts, self.faces, flip=True)
        
        meshName = self.wallMesh
        if (meshName != ''):
            wallMesh = bpy.data.objects[meshName]
            if wallMesh.type == 'MESH':
                self.createWall(wallMesh)
            else:
                print('Please Select Mesh Object!')

        mesh = bpy.data.meshes.new("stair_mesh")
        obj = bpy.data.objects.new("stair_obj", mesh)
        mesh.from_pydata(self.verts, [], self.faces)
        bpy.context.view_layer.active_layer_collection.collection.objects.link(obj)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text='Stair Setting')
        row = box.row()
        row.prop(self, 'width')
        row.prop(self, 'height')
        row = box.row()
        row.prop(self, 'count')
        row.prop(self, 'stepDepth')

        box = layout.box()
        box.label(text='Wall Setting')
        row = box.row()
        row.prop(self, 'wallHeight')
        row.prop(self, 'wallOffsetY')
        box.prop_search(self, "wallMesh", scene, "objects")

        box = layout.box()
        box.label(text='Pile')