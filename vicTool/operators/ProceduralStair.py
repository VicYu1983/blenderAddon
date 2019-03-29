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
        default=3.0
    )

    count = IntProperty(
        name='StepCount',
        min=1,
        default=10
    )

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

            isLastFace = i == len(line)-1
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

            # if i == len(line)-1:
            #     if flip:
            #         f = (i,0,len(line),i+len(line))
            #     else:
            #         f = (i,i+len(line),len(line),0)
            # else:
            #     if flip:
            #         f = (i,i+1,i+len(line)+1,i+len(line))
            #     else:
            #         f = (i,i+len(line),i+len(line)+1,i+1)
            faces.append(f)

        line.extend(anotherLine)
        verts.extend(line)

    def execute(self, context):
        self.verts = []
        #self.faces = [(0, 3, 2, 1)]
        self.faces = []

        x = self.width / 2
        line = []
        for i in range(self.count):
            line.append((i,-x,i))
            line.append((i,-x,i+1))
            line.append((i+1,-x,i+1))
        
        self.addVertexAndFaces(line, (0, self.width, 0), self.verts, self.faces, flip=True)
            

        mesh = bpy.data.meshes.new("stair_mesh")
        obj = bpy.data.objects.new("stair_obj", mesh)

        mesh.from_pydata(self.verts, [], self.faces)

        bpy.context.view_layer.active_layer_collection.collection.objects.link(obj)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self, "width")
        box.prop(self, "count")