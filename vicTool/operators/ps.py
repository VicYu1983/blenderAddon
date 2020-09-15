import bpy
from ..vic_tools import *
from mathutils import *

def createStairManager():
    for obj in bpy.data.objects:
        if obj.name == "StairManager":
            return
    bpy.ops.object.empty_add(type='CUBE', location=([0,0,0]))
    mgrObj = bpy.context.object
    mgrObj.name = "StairManager"

def createStairProxy():

    ctx = bpy.context
    if ctx.object.type != 'CURVE': return

    (obj, update, addRectVertex, addVertexAndFaces, addVertexByMesh) = prepareAndCreateMesh("test")

    curve = ctx.object
    length, matrices = getCurvePosAndLength(curve, 80)

    pts = (Vector((0,1,0)), Vector((0,-1,0)))
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
        createStairProxy()
        return {'FINISHED'}