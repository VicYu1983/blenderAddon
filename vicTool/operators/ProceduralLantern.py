import bpy
from ..vic_tools import (
    addProps,
    addVertexAndFaces,
    addVertexByMesh,
    prepareAndCreateMesh,
    getSelectedWithOrder
)

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

        bpy.ops.vic.vic_procedural_lantern()
        return {'FINISHED'}

class vic_procedural_lantern_connect(bpy.types.Operator):
    bl_idname = "vic.vic_procedural_lantern_connect"
    bl_label = "Create Connect"

    def execute(self, context):
        bpy.ops.vic.vic_procedural_lantern_manager()

        objs = [o for o in getSelectedWithOrder() if "ProxyData" in o.name]
        
        if len(objs) >= 2:
            connectIds = [str(o["Id"]) for o in objs]

            bpy.ops.object.empty_add(type='CUBE', location=([0,0,0]))
            connectObj = bpy.context.object
            connectObj.parent = bpy.data.objects["LanternDataStorage"]
            connectObj.name = "ConnectData"
            connectObj["Connect"] = "_".join(connectIds)

        bpy.ops.vic.vic_procedural_lantern()    
        return {'FINISHED'}

class vic_procedural_lantern(bpy.types.Operator):
    bl_idname = "vic.vic_procedural_lantern"
    bl_label = "Generate Lantern"

    def modal(self, context, event):
        if event.type in {'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type in ["LEFTMOUSE", "RIGHTMOUSE"]:
            print("update")
            self.updateMesh()

        return {'PASS_THROUGH'}

    def execute(self, context):
        # wm = context.window_manager
        # # start animating
        # # bpy.ops.screen.animation_play()
        # # self._timer = wm.event_timer_add(1, window=context.window)
        # # self.count = 0
        # wm.modal_handler_add(self)
        # return {'RUNNING_MODAL'}

        self.updateMesh()
        return {'FINISHED'}

    def cancel(self, context):
        pass
        # bpy.ops.screen.animation_cancel(restore_frame=False)


        # wm = context.window_manager
        # wm.event_timer_remove(self._timer)

    def updateMesh(self):
        de = [o for o in bpy.data.objects if "Ropes" in o.name]
        bpy.ops.object.delete({"selected_objects": de})

        meshData = prepareAndCreateMesh("Ropes")
        self.verts = meshData[0]
        self.faces = meshData[1]
        self.uvsMap = meshData[2]
        self.matIds = meshData[3]

        connects = [o for o in bpy.data.objects if "ConnectData" in o.name]
        proxys = [o for o in bpy.data.objects if "ProxyData" in o.name]
        for connect in connects:
            idstr = connect["Connect"]
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
                # print(dir)

                # addVertexAndFaces(
                #     self.verts, self.faces, self.uvsMap, self.matIds,
                #     [nextP.location, p.location],(0,0,1),
                #     [(0,0),(1,0)],(0,0),
                #     1,0
                # )

                addVertexByMesh(self.verts, self.faces, self.uvsMap, self.matIds, bpy.data.objects["Cylinder"])

        meshData[4]()