import bpy
from ..vic_tools import *
from mathutils import *


caches = {
    "curve":None,
    "obj":None,
    "update":None,
    "clear":None,
    "addRectVertex":None
}

def createStairManager():
    for obj in bpy.data.objects:
        if obj.name == "StairManager":
            return
    bpy.ops.object.empty_add(type='CUBE', location=([0,0,0]))
    mgrObj = bpy.context.object
    mgrObj.name = "StairManager"

def createStairProxy():

    curve = caches["curve"]
    update = caches["update"]
    clear = caches["clear"]
    addRectVertex = caches["addRectVertex"]

    curve["Width"] = bpy.context.window_manager.vic_procedural_stair_proxy_width
    curve["Step"] = bpy.context.window_manager.vic_procedural_stair_proxy_step

    if curve["Width"] <= 0: return
    width = curve["Width"]
    step = curve["Step"]
    
    length, matrices = getCurvePosAndLength(curve, step)
    if length == 0: return
    
    # reset mesh data
    clear()

    pts = (Vector((0,width/2,0)), Vector((0,-width/2,0)))
    for i, mat in enumerate(matrices):
        curr_pts = []
        for pt in pts:

            # 只留下水平的旋轉（yaw），需要單位化，不然轉成矩陣的時候，會有拉扯
            hori_quat = mat.to_quaternion()
            hori_quat.x = hori_quat.y = 0
            hori_quat.normalize()

            hori_mat = hori_quat.to_matrix().to_4x4()
            hori_mat = Matrix.Translation(mat.to_translation()) @ hori_mat
            pos = hori_mat @ pt
            curr_pts.append(pos)

            # bpy.ops.object.empty_add(type='ARROWS')
            # ctx.object.location = pos
            # ctx.object.name = 'aaaa'
        if i > 0: 
            step_pt1 = curr_pts[1].copy()
            step_pt0 = curr_pts[0].copy()

            # 如果階梯間的高度超過設定的閾值，就產生階梯
            if abs(curr_pts[0].z - last_pts[0].z) > .2:

                # 注意這邊的設定也會影響樓梯面的生成
                step_pt1.z = last_pts[1].z
                step_pt0.z = last_pts[0].z

                # 階梯間的垂直面
                addRectVertex((step_pt0,curr_pts[0], curr_pts[1], step_pt1), ((0,0),(0,0),(0,0),(0,0)))

            # 樓梯面
            addRectVertex((last_pts[0],last_pts[1], step_pt1, step_pt0), ((0,0),(0,0),(0,0),(0,0)))

            side_pt0 = last_pts[0].copy()
            side_pt0.z = -10

            side_pt1 = step_pt0.copy()
            side_pt1.z = -10

            side_pt2 = last_pts[1].copy()
            side_pt2.z = -10

            side_pt3 = step_pt1.copy()
            side_pt3.z = -10

            # 樓梯左右側面
            addRectVertex((last_pts[0],step_pt0, side_pt1, side_pt0), ((0,0),(0,0),(0,0),(0,0)))
            addRectVertex((last_pts[1],step_pt1, side_pt3, side_pt2), ((0,0),(0,0),(0,0),(0,0)))
        last_pts = curr_pts

    update()
    # createStairManager()
    # proxys = [o for o in bpy.data.objects if "ProxyData" in o.name]
    # currentId = -1
    # for proxy in proxys:
    #     if proxy["Id"] > currentId:
    #         currentId = proxy["Id"]

    # bpy.ops.object.empty_add(type='SPHERE')
    # obj = bpy.context.object
    # obj.name = "ProxyData"
    # obj.parent = bpy.data.objects["StairManager"]
    # addProps(obj, "Id", currentId+1)

class vic_procedural_stair_proxy(bpy.types.Operator):
    bl_idname = "vic.vic_procedural_stair_proxy"
    bl_label = "Create Stair Proxy"

    def execute(self, context):
        ctx = bpy.context
        if not ctx.object or ctx.object.type != 'CURVE': 
            self.report({'INFO'}, "Please select at least one CURVE object.")
            return {'FINISHED'}
        startEdit()
        createStairProxy()
        return {'FINISHED'}

def updateMesh(scene):
    createStairProxy()

def startEdit():
    ctx = bpy.context
    if not ctx.object or ctx.object.type != 'CURVE': return

    curve = ctx.object
    caches["curve"] = curve

    if "Mesh" in curve: 
        mesh = curve["Mesh"]
        if mesh in bpy.data.objects: 
            focusObject(bpy.data.objects[mesh])
            bpy.ops.object.delete()

    (obj, update, clear, addRectVertex, addVertexAndFaces, addVertexByMesh) = prepareAndCreateMesh("test")
    caches["obj"] = obj
    caches["update"] = update
    caches["addRectVertex"] = addRectVertex
    caches["clear"] = clear
    
    addProps(curve, "Mesh", obj.name, True)
    addProps(curve, "Width", 1)
    addProps(curve, "Step", 2)

    bpy.context.window_manager.vic_procedural_stair_proxy_width = curve["Width"]
    bpy.context.window_manager.vic_procedural_stair_proxy_step = curve["Step"]
    
def invokeLiveEdit(self, context):
    if context.window_manager.vic_procedural_stair_proxy_live:
        startEdit()
        bpy.ops.screen.animation_play()
        if updateMesh in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(updateMesh)
        bpy.app.handlers.frame_change_post.append(updateMesh)
    else:
        bpy.ops.screen.animation_cancel()
        bpy.app.handlers.frame_change_post.remove(updateMesh)
        updateMesh(None)

bpy.types.WindowManager.vic_procedural_stair_proxy_live =   bpy.props.BoolProperty(
                                                            default = False,
                                                            update = invokeLiveEdit)

bpy.types.WindowManager.vic_procedural_stair_proxy_width = bpy.props.FloatProperty(
                                                            name='Width',
                                                            default=.5,
                                                            min=0.01)

bpy.types.WindowManager.vic_procedural_stair_proxy_step = bpy.props.IntProperty(
                                                            name='Step',
                                                            default=5,
                                                            min=2,
                                                            step=1)