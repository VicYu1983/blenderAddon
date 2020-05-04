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
        mgrObj["NGon"] = 3
        mgrObj["Segment"] = 1.0
        mgrObj["Gravity"] = 20.0
        mgrObj["Radius"] = 1.0
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
            connectObj["NGon Add"] = 0
            connectObj["Radius Scale"] = 1.0
            connectObj["Gravity Scale"] = 1.0
            connectObj["Segment Scale"] = 1.0

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

        mats = None
        if "Ropes" in bpy.data.objects.keys():
            mats = bpy.data.objects["Ropes"].data.materials
            bpy.ops.object.delete({"selected_objects": [bpy.data.objects["Ropes"]]})

        meshData = prepareAndCreateMesh("Ropes")
        verts = meshData[0]
        faces = meshData[1]
        uvsMap = meshData[2]
        matIds = meshData[3]

        segment = bpy.data.objects["LanternDataStorage"]["Segment"]
        gravity = bpy.data.objects["LanternDataStorage"]["Gravity"]
        radius = bpy.data.objects["LanternDataStorage"]["Radius"]
        ngon = bpy.data.objects["LanternDataStorage"]["NGon"]

        connects = [o for o in bpy.data.objects if "ConnectData" in o.name]
        proxys = [o for o in bpy.data.objects if "ProxyData" in o.name]
        for connect in connects:
            idstr = connect["Connect"]
            ngonAdd = connect["NGon Add"]
            radiusScale = connect["Radius Scale"]
            gravityScale = connect["Gravity Scale"]
            segmentScale = connect["Segment Scale"]

            cngon = ngon + ngonAdd
            cngon = max(cngon, 3)

            cradius = radius * radiusScale
            cradius = max(cradius, 0.01)
            
            cgravity = gravity * gravityScale

            csegment = segment * segmentScale
            csegment = max(csegment, .01)

            # 繩子的橫截面的點的坐標
            shape = []
            for i in range(cngon):
                radian = (2 * math.pi) * i / cngon
                shape.append((0, math.cos(radian)*cradius,math.sin(radian)*cradius))
            shape.append(shape[0])
            
            # 賦予constraint前先清空
            connect.constraints.clear()

            # 依照所選的順序收集點
            proxyWithOrder = []

            currentConstraintId = 0
            ids = idstr.split("_")
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

            # 按照順序來產生繩子
            for i in range(len(proxyWithOrder)-1):
                p = proxyWithOrder[i]
                nextP = proxyWithOrder[i+1]

                # 全域坐標只能從世界矩陣來取
                pWorldLocation = Vector((p.matrix_world[0][3], p.matrix_world[1][3], p.matrix_world[2][3]))
                nextPWorldLocation = Vector((nextP.matrix_world[0][3], nextP.matrix_world[1][3], nextP.matrix_world[2][3]))

                # 取得方向
                dir = nextPWorldLocation - pWorldLocation

                # 取得總長
                dist = dir.length

                # 每一小段的長度，不能超過總長
                segLength = min(csegment, dist )

                # 總共有幾段
                seg = round(dist / segLength)

                # 算出兩個端點之間的路徑
                segpoint = []
                for i in range(seg):
                    gravityEffect = Vector((0,0,-self.getCurve(i, seg, cgravity)))
                    pos = i * dir / seg + pWorldLocation + gravityEffect
                    segpoint.append(pos)
                segpoint.append(nextPWorldLocation)

                # 算出路徑當中每一個點的方向
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

                # 產生所有的點
                for i, rotmat in enumerate(rotmats):

                    # for debug
                    # bpy.ops.object.empty_add(type='ARROWS')
                    # bpy.context.object.matrix_world = rotmat
                    # bpy.context.object.name = "Ropes"

                    # 用橫截面加上矩陣來產生所有的點（當前的點）
                    shapeOffset = []
                    for pos in shape:
                        pos = Vector(pos)
                        pos = rotmat @ pos
                        shapeOffset.append((pos.x, pos.y, pos.z))

                    # 用橫截面加上矩陣來產生所有的點（下一點）
                    nextShapeOffset = []
                    if i == len(rotmats)-1:

                        # 如果當前的點是最後一個點，他的下一點就是端點，取nextPWorldLocation
                        for pos in shapeOffset:
                            pos = Vector(pos)
                            pos += nextPWorldLocation - Vector((rotmat[0][3], rotmat[1][3], rotmat[2][3]))
                            nextShapeOffset.append((pos.x, pos.y, pos.z))
                    else:

                        # 如果當前的點不是最後一點，就取下一點。i+1
                        for pos in shape:
                            pos = Vector(pos)
                            pos = rotmats[i+1] @ pos
                            nextShapeOffset.append((pos.x, pos.y, pos.z))

                    # 收集所有的點及uv
                    for i in range(len(shapeOffset)-1):
                        segheight = (1 / (len(shapeOffset)-1))
                        uvy = segheight * i
                        uvheight = uvy + segheight
                        addRectVertex(
                            verts, faces, uvsMap, matIds,
                            [shapeOffset[i+1], shapeOffset[i], nextShapeOffset[i], nextShapeOffset[i+1]], [(0,uvheight), (0,uvy), (1,uvy), (1,uvheight)]
                        )
                        
        obj = meshData[4]()
        if mats is not None:
            for mat in mats:
                obj.data.materials.append(mat)

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