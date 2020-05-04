import bpy, math, time
from mathutils import *
from ..vic_tools import *

class vic_procedural_lantern_manager(bpy.types.Operator):
    bl_idname = "vic.vic_procedural_lantern_manager"
    bl_label = "Create Manager"
    def execute(self, context):

        for obj in bpy.data.objects:
            if obj.name == "LanternDataStorage":
                return {'FINISHED'}

        bpy.ops.object.empty_add(type='CUBE', location=([0,0,0]))
        mgrObj = context.object
        mgrObj.name = "LanternDataStorage"
        # mgrObj["segment"] = 1.0
        return {'FINISHED'}

class vic_procedural_lantern_proxy(bpy.types.Operator):
    bl_idname = "vic.vic_procedural_lantern_proxy"
    bl_label = "Create Proxy"

    _timer = None
    count = 0

    def execute(self, context):
        bpy.ops.vic.vic_procedural_lantern_manager()

        proxys = [o for o in bpy.data.objects if "ProxyData" in o.name]
        currentId = -1
        for proxy in proxys:
            if proxy["Id"] > currentId:
                currentId = proxy["Id"]

        bpy.ops.object.empty_add(type='SPHERE')
        obj = bpy.context.object
        obj.name = "ProxyData"
        obj.parent = bpy.data.objects["LanternDataStorage"]

        addProps(obj, "Id", currentId+1)

        return {'FINISHED'}

class vic_procedural_lantern_connect(bpy.types.Operator):
    bl_idname = "vic.vic_procedural_lantern_connect"
    bl_label = "Create Connect"

    def execute(self, context):
        bpy.ops.vic.vic_procedural_lantern_manager()

        objs = [o for o in getSelectedWithOrder() if "ProxyData" in o.name]
        
        if len(objs) >= 2:
            connectIds = [str(o["Id"]) for o in objs]

            bpy.ops.object.empty_add(type='PLAIN_AXES', location=([0,0,0]))
            connectObj = bpy.context.object
            connectObj.parent = bpy.data.objects["LanternDataStorage"]
            connectObj.name = "ConnectData"
            connectObj["Connect"] = "_".join(connectIds)
            connectObj["Radius"] = 1.0
            connectObj["NGon"] = 3
            connectObj["Gravity"] = 20.0
            connectObj["Segment"] = 1.0

        bpy.ops.vic.vic_procedural_lantern()    
        return {'FINISHED'}

class vic_procedural_lantern(bpy.types.Operator):
    bl_idname = "vic.vic_procedural_lantern"
    bl_label = "Generate Lantern"

    def execute(self, context):
        self.updateMesh()
        return {'FINISHED'}

    def getCurve(self, index, segment, gravity):
        return (1-pow((abs(index - segment/2)/(segment/2)), 2)) * gravity

    def updateMesh(self):

        de = [o for o in bpy.data.objects if "Ropes" in o.name]
        bpy.ops.object.delete({"selected_objects": de})

        meshData = prepareAndCreateMesh("Ropes")
        verts = meshData[0]
        faces = meshData[1]
        uvsMap = meshData[2]
        matIds = meshData[3]

        # segment = bpy.data.objects["LanternDataStorage"]["segment"]

        connects = [o for o in bpy.data.objects if "ConnectData" in o.name]
        proxys = [o for o in bpy.data.objects if "ProxyData" in o.name]
        for connect in connects:
            idstr = connect["Connect"]
            radius = connect["Radius"]
            numTri = connect["NGon"]
            gravity = connect["Gravity"]
            segment = connect["Segment"]

            radius = max(radius, 0.01)
            numTri = max(numTri, 3)
            segment = max(segment, .01)

            shape = []
            uv = []
            for i in range(numTri):
                radian = (2 * math.pi) * i / numTri
                shape.append((0, math.cos(radian)*radius,math.sin(radian)*radius))
                uv.append((0,0))
            shape.append(shape[0])
            uv.append(uv[0])
            
            ids = idstr.split("_")
            connect.constraints.clear()

            proxyWithOrder = []
            currentConstraintId = 0
            for id in ids:
                for p in proxys:
                    if p["Id"] == int(id):
                        bpy.context.view_layer.objects.active = connect
                        bpy.ops.object.constraint_add(type='COPY_LOCATION')
                        bpy.context.object.constraints[currentConstraintId].target = p
                        bpy.context.object.constraints[currentConstraintId].influence = 0.5
                        currentConstraintId += 1
                        proxyWithOrder.append(p)
                        continue

            for i in range(len(proxyWithOrder)-1):
                p = proxyWithOrder[i]
                nextP = proxyWithOrder[i+1]
                dir = nextP.location - p.location

                dirForDegree = dir.copy()
                dirForDegree.z = 0
                dist = dir.length
                radian = dirForDegree.angle(Vector([0,1,0]))
                cross = dirForDegree.cross(Vector([0,1,0]))
                if cross.z > 0:
                    radian *= -1
                rotMat = Matrix.Rotation(radian, 4, 'Z')

                segLength = min(segment, dist )
                seg = round(dist / segLength)

                segpoint = []
                for i in range(seg):
                    gravityEffect = Vector((0,0,-self.getCurve(i, seg, gravity)))
                    pos = i * dir / seg + p.location + gravityEffect
                    segpoint.append(pos)
                segpoint.append(nextP.location)

                rotmats = []
                for i in range(len(segpoint)-1):
                    p = segpoint[i]
                    np = segpoint[i+1]
                    forward = np - p
                    forward.normalize()
                    right = forward.cross(Vector((0,0,1)))
                    right.normalize()
                    up = right.cross(forward)
                    up.normalize()

                    rotmat = Matrix((
                        (forward.x, right.x, up.x, p.x), 
                        (forward.y, right.y, up.y, p.y), 
                        (forward.z, right.z, up.z, p.z), 
                        (0,0,0,1)
                    ))
                    rotmats.append(rotmat)

                for i, rotmat in enumerate(rotmats):

                    # for debug
                    # bpy.ops.object.empty_add(type='ARROWS')
                    # bpy.context.object.matrix_world = rotmat
                    # bpy.context.object.name = "Ropes"

                    shapeOffset = []
                    for pos in shape:
                        pos = Vector(pos)
                        pos = rotmat @ pos
                        shapeOffset.append((pos.x, pos.y, pos.z))

                    nextShapeOffset = []
                    if i == len(rotmats)-1:
                        for pos in shapeOffset:
                            pos = Vector(pos)
                            pos += nextP.location - Vector((rotmat[0][3], rotmat[1][3], rotmat[2][3]))
                            nextShapeOffset.append((pos.x, pos.y, pos.z))
                    else:
                        for pos in shape:
                            pos = Vector(pos)
                            pos = rotmats[i+1] @ pos
                            nextShapeOffset.append((pos.x, pos.y, pos.z))

                    for i in range(len(shapeOffset)-1):
                        uvy = (1 / (len(shapeOffset)-1)) * i
                        uvheight = uvy + (1 / (len(shapeOffset)-1))
                        addRectVertex(
                            verts, faces, uvsMap, matIds,
                            [shapeOffset[i+1], shapeOffset[i], nextShapeOffset[i], nextShapeOffset[i+1]], [(0,uvheight), (0,uvy), (1,uvy), (1,uvheight)]
                        )
                        
        obj = meshData[4]()

        mergeOverlayVertex(obj)

        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.faces_shade_smooth()
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.select_all(action='DESELECT')


# def updateMesh(scene):
#     print(scene.frame_current)
    
#     if scene.frame_current % 5 == 0:
#         time.sleep(.01)
#         bpy.ops.vic.vic_procedural_lantern()

# class vic_procedural_lantern_life(bpy.types.Operator):
#     bl_idname = "vic.vic_procedural_lantern_life"
#     bl_label = "Live Edit"

#     def execute(self, context):
#         bpy.ops.screen.animation_play()
#         # if updateMesh in bpy.app.handlers.frame_change_post:
#             # bpy.app.handlers.frame_change_post.remove(updateMesh)
#         bpy.app.handlers.frame_change_post.clear()
#         # try:
#         #     bpy.app.handlers.frame_change_post.remove(updateMesh)
#         #     print("delte")
#         # except:
#         #     print("not in")
#         bpy.app.handlers.frame_change_post.append(updateMesh)

#         return {'FINISHED'}