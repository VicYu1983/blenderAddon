import bpy
from .vic_tools import *
from mathutils import *
from math import *

caches = {
    "curve":None,
    "obj":None,
    "obj_materials":None,
    "update":None,
    "clear":None,
    "addRectVertex":None,
    "pilePoints":None,
    "pssProxyPool":[],
    "register":False
}

def onSceneUpdate():
    if not checkAndToggle(bpy.context):
        return
    curve = bpy.context.object
    if "Width" not in curve: return

    bpy.context.window_manager.vic_procedural_stair_update_width = curve["Width"]
    bpy.context.window_manager.vic_procedural_stair_update_wall_inner_distance = curve["Wall_Inner_Distance"]
    bpy.context.window_manager.vic_procedural_stair_update_pile_per_step = curve["Pile_Per_Step"]
    bpy.context.window_manager.vic_procedural_stair_update_pile_z = curve["Pile_Z"]
    bpy.context.window_manager.vic_procedural_stair_update_step = curve["Step"]
    bpy.context.window_manager.vic_procedural_stair_update_step_threshold = curve["Step_Threshold"]
    bpy.context.window_manager.vic_procedural_stair_update_ground = curve["Ground"]
    bpy.context.window_manager.vic_procedural_stair_update_onGround = curve["OnGround"]
    bpy.context.window_manager.vic_procedural_stair_update_pile = curve["Pile"]
    bpy.context.window_manager.vic_procedural_stair_update_wall = curve["Wall"]

def createStairManager():
    for obj in bpy.data.objects:
        if obj.name == "StairManager":
            return
    bpy.ops.object.empty_add(type='CUBE', location=([0,0,0]))
    mgrObj = bpy.context.object
    mgrObj.name = "StairManager"

def createStairProxy(isLive = False):

    curve = caches["curve"]
    update = caches["update"]
    clear = caches["clear"]
    addRectVertex = caches["addRectVertex"]

    curve["Width"] = bpy.context.window_manager.vic_procedural_stair_update_width
    curve["Wall_Inner_Distance"] = bpy.context.window_manager.vic_procedural_stair_update_wall_inner_distance
    curve["Pile_Per_Step"] = bpy.context.window_manager.vic_procedural_stair_update_pile_per_step
    curve["Pile_Z"] = bpy.context.window_manager.vic_procedural_stair_update_pile_z
    curve["Step"] = bpy.context.window_manager.vic_procedural_stair_update_step
    curve["Step_Threshold"] = bpy.context.window_manager.vic_procedural_stair_update_step_threshold
    curve["Ground"] = bpy.context.window_manager.vic_procedural_stair_update_ground
    curve["OnGround"] = bpy.context.window_manager.vic_procedural_stair_update_onGround

    width = curve["Width"]
    wall_inner_distance = curve["Wall_Inner_Distance"]
    pile_per_step = curve["Pile_Per_Step"]
    pile_z = curve["Pile_Z"]
    step = curve["Step"]
    step_threshold = curve["Step_Threshold"]
    ground = curve["Ground"]
    onGround = curve["OnGround"]
    uv_scale = .1

    if width <= 0 or step <= 0: return
    
    length, matrices = getCurvePosAndLength(curve, step)
    if length == 0: return

    stepLength = length / step
    
    # reset mesh data
    clear()
    pilePoints = []

    # 前一對點
    last_pts = None

    # 前一個階梯的高度
    last_height = 0

    # 前一次處理有沒有形成階梯
    last_isStep = False

    # 記錄前一次處理的左邊墻面的前進距離
    uv_last_left_x = 0

    # 記錄前一次處理的右邊墻面的前進距離
    uv_last_right_x = 0

    # 記錄前一次處理的梯面的前進距離
    uv_last_step_x = 0

    # 記錄前一次處理的底部的前進距離
    uv_last_bottom_x = 0

    # 樓梯面的點位置
    pts = (Vector((0,width/2,0)), Vector((0,-width/2,0)))

    # 柱子的位置
    pile_pts = (Vector((0,width/2 - wall_inner_distance,0)), Vector((0,-width/2 + wall_inner_distance,0)))

    # 開始計算
    for i, mat in enumerate(matrices):
        curr_pts = []
        pile_mats = []
        for j, pt in enumerate(pts):

            # 只留下水平的旋轉（yaw），需要單位化，不然轉成矩陣的時候，會有拉扯
            hori_quat = mat.to_quaternion()
            hori_quat.x = hori_quat.y = 0
            hori_quat.normalize()

            # 把處理好的旋轉矩陣乘上位置矩陣，形成新的4x4矩陣
            hori_mat = hori_quat.to_matrix().to_4x4()
            hori_mat = Matrix.Translation(mat.to_translation()) @ hori_mat
            pos = hori_mat @ pt
            curr_pts.append(pos)

            # 檢查是否需要生成柱子
            is_per = (i % pile_per_step == 0)
            is_first = (i == 1)
            is_last = (i == len(matrices)-1)

            # 需要有前一次處理的資料才能開始計算柱子的真正位置
            if last_pts and (is_per or is_first or is_last):
                pile_pos = hori_mat @ pile_pts[j]
                last_pt = last_pts[j]
                offset_pt = (pile_pos + last_pt) / 2
                offset_pt.z = last_pt.z + pile_z
                pile_mat = Matrix.Translation(offset_pt) @ hori_quat.to_matrix().to_4x4()
                pile_mats.append(pile_mat)

        # 記錄下所有柱子的位置，之後生成用
        pilePoints += pile_mats

        # 第二次處理時才有足夠的資訊來計算
        if i > 0: 
            step_pt1 = curr_pts[1].copy()
            step_pt0 = curr_pts[0].copy()

            current_isStep = False

            # 如果階梯間的高度超過設定的閾值，就產生階梯
            current_height = curr_pts[0].z - last_pts[0].z
            if abs(current_height) > step_threshold:
                current_isStep = True

                # 注意這邊的設定也會影響樓梯面的生成
                step_pt1.z = last_pts[1].z
                step_pt0.z = last_pts[0].z

                # 階梯間的垂直面
                addRectVertex((step_pt0,curr_pts[0], curr_pts[1], step_pt1), ((0,uv_last_step_x+stepLength),(0,uv_last_step_x+stepLength+abs(current_height)),(width,uv_last_step_x+stepLength+abs(current_height)),(width,uv_last_step_x+stepLength)), uv_scale)

            # 樓梯面
            addRectVertex((last_pts[0],last_pts[1], step_pt1, step_pt0), ((0,uv_last_step_x),(width,uv_last_step_x),(width,uv_last_step_x+stepLength),(0,uv_last_step_x+stepLength)), uv_scale)

            # 墻面接近地面的點
            side_pt0 = last_pts[0].copy()
            side_pt1 = curr_pts[0].copy()
            side_pt2 = last_pts[1].copy()
            side_pt3 = curr_pts[1].copy()
            
            # 如果設定由地面升起的話，直接設定地面高度為點的高度
            if onGround:
                side_pt0.z = ground
                side_pt1.z = ground
                side_pt2.z = ground
                side_pt3.z = ground
            else:
                if current_height > 0:
                    if last_isStep:
                        side_pt0.z -= last_height
                        side_pt2.z -= last_height

                    if current_isStep:
                        side_pt1.z -= current_height
                        side_pt3.z -= current_height

                    side_pt0.z += ground
                    side_pt1.z += ground
                    side_pt2.z += ground
                    side_pt3.z += ground
                else:
                    side_pt0.z += ground
                    side_pt1.z += ground
                    side_pt2.z += ground
                    side_pt3.z += ground

            # 記錄左右墻面的uv坐標，每一個坐標都對應生成模型的點
            uv_curr_left_x = (side_pt1 - side_pt0)
            uv_curr_left_x.z = 0
            uv_curr_left_x = uv_curr_left_x.length

            uv_curr_right_x = (side_pt3 - side_pt2)
            uv_curr_right_x.z = 0
            uv_curr_right_x = uv_curr_right_x.length

            uv_last_pts0 = (uv_last_left_x,last_pts[0].z)
            uv_last_pts1 = (uv_last_right_x,last_pts[1].z)
            uv_curr_pts0 = (uv_last_left_x+uv_curr_left_x,curr_pts[0].z)
            uv_curr_pts1 = (uv_last_right_x+uv_curr_right_x,curr_pts[1].z)

            uv_side_pt0 = (uv_last_left_x,side_pt0.z)
            uv_side_pt1 = (uv_last_left_x+uv_curr_left_x,side_pt1.z)
            uv_side_pt2 = (uv_last_right_x,side_pt2.z)
            uv_side_pt3 = (uv_last_right_x+uv_curr_right_x,side_pt3.z)

            uv_step_pt0 = (uv_last_left_x+uv_curr_left_x, step_pt0.z)
            uv_step_pt1 = (uv_last_right_x+uv_curr_right_x, step_pt1.z)
                
            # 樓梯左側面，對目前的階梯是往上或是往下的處理也不一樣
            if current_height < 0:
                addRectVertex((last_pts[0],step_pt0, curr_pts[0]), (uv_last_pts0,uv_step_pt0,uv_curr_pts0), uv_scale)
                addRectVertex((last_pts[0],curr_pts[0], side_pt1, side_pt0), (uv_last_pts0,uv_curr_pts0,uv_side_pt1,uv_side_pt0), uv_scale)
            else:

                # 上一次處理時是不是階梯對這次的處理不一樣
                if last_isStep:
                    step_connect_pt = last_pts[0] + Vector((0,0,-last_height))
                else:
                    step_connect_pt = last_pts[0]

                uv_step_connect_pt = (uv_last_left_x, step_connect_pt.z)
                addRectVertex((last_pts[0],step_pt0, step_connect_pt), (uv_last_pts0,uv_step_pt0,uv_step_connect_pt), uv_scale)
                addRectVertex((step_connect_pt, step_pt0, side_pt1, side_pt0), (uv_step_connect_pt,uv_step_pt0,uv_side_pt1,uv_side_pt0), uv_scale)
            
            # 樓梯右側面，對目前的階梯是往上或是往下的處理也不一樣
            if current_height < 0:
                addRectVertex((last_pts[1],step_pt1, curr_pts[1]), (uv_last_pts1,uv_step_pt1,uv_curr_pts1), uv_scale)
                addRectVertex((last_pts[1],curr_pts[1], side_pt3, side_pt2), (uv_last_pts1,uv_curr_pts1,uv_side_pt3,uv_side_pt2), uv_scale)
            else:

                # 上一次處理時是不是階梯對這次的處理不一樣
                if last_isStep:
                    step_connect_pt = last_pts[1] + Vector((0,0,-last_height))
                else:
                    step_connect_pt = last_pts[1]

                uv_step_connect_pt = (uv_last_right_x, step_connect_pt.z)
                addRectVertex((last_pts[1],step_pt1, step_connect_pt), (uv_last_pts1,uv_step_pt1,uv_step_connect_pt), uv_scale)
                addRectVertex((step_connect_pt, step_pt1, side_pt3, side_pt2), (uv_step_connect_pt, uv_step_pt1, uv_side_pt3, uv_side_pt2), uv_scale)

            # 底部mesh
            addRectVertex((side_pt0, side_pt1, side_pt3, side_pt2), ((0,uv_last_bottom_x), (0, uv_last_bottom_x+stepLength),(width, uv_last_bottom_x+stepLength), (width, uv_last_bottom_x)), uv_scale)
                
            last_height = current_height
            last_isStep = current_isStep

            uv_last_left_x += uv_curr_left_x
            uv_last_right_x += uv_curr_right_x

            if current_isStep:
                uv_last_step_x += (stepLength + abs(current_height))
            else:
                uv_last_step_x += stepLength
            uv_last_bottom_x += stepLength
            
        last_pts = curr_pts

    caches["pilePoints"] = pilePoints
    update()

    # 如果是實時模式，就不要直接創建柱子，只創建代理物件，增進效能。
    if isLive:

        for o in caches["pssProxyPool"]: o.hide_viewport = True

        curr_focus = bpy.context.object
        for i, pp in enumerate(pilePoints):

            # 這裏用物件池模式，進一步節約效能
            proxy = getPssProxyFromPool(i)
            proxy.matrix_world = pp
            proxy.hide_viewport = False
        if curr_focus: focusObject(curr_focus)

def getPssProxyFromPool(i):
    pssProxyPool = caches["pssProxyPool"]
    if i < len(pssProxyPool) - 1: return pssProxyPool[i]
    bpy.ops.object.empty_add(type='ARROWS')
    proxy = bpy.context.object
    proxy.name = "auto_build_please_ignore"
    pssProxyPool.append(proxy)
    return proxy

def checkAndToggle(ctx):
    if not ctx.object or ctx.object.type != 'CURVE': 
        return False
    if ctx.mode != 'OBJECT': bpy.ops.object.editmode_toggle()
    return True

class vic_procedural_stair_update(bpy.types.Operator):
    bl_idname = "vic.vic_procedural_stair_update"
    bl_label = "Create & Update"
    bl_description='Please Select One Spline With Object Mode'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        if not checkAndToggle(context):
            self.report({'INFO'}, "Please select at least one CURVE object.")
            return {'FINISHED'}
        currentFocus = context.object
        startEdit()
        createStairProxy()
        endEdit()
        focusObject(currentFocus)
        return {'FINISHED'}

def startEdit():
    ctx = bpy.context
    if not ctx.object or ctx.object.type != 'CURVE': return

    if not caches["register"]:
        subscribe_to = bpy.types.LayerObjects, "active"
        bpy.msgbus.subscribe_rna(
            key = subscribe_to,
            owner = bpy.context.scene,
            args = (),
            notify = onSceneUpdate
        )
        caches["register"] = True
        onSceneUpdate()

    caches["shading"] = bpy.context.space_data.shading.type
    bpy.context.space_data.shading.type = 'WIREFRAME'

    curve = ctx.object
    caches["curve"] = curve

    removeMeshs()

    creator = prepareAndCreateMesh(curve.name + "_step")
     
    obj = creator["obj"]
    update = creator["update"]
    clear = creator["clear"]
    addRectVertex = creator["addRectVertex"]

    caches["obj"] = obj
    caches["update"] = update
    caches["addRectVertex"] = addRectVertex
    caches["clear"] = clear
    caches["pilePoints"] = []
    
    addProps(curve, "Pile", bpy.context.window_manager.vic_procedural_stair_update_pile, True)
    addProps(curve, "Wall", bpy.context.window_manager.vic_procedural_stair_update_wall, True)
    addProps(curve, "Width", bpy.context.window_manager.vic_procedural_stair_update_width, True)
    addProps(curve, "Wall_Inner_Distance", bpy.context.window_manager.vic_procedural_stair_update_wall_inner_distance, True)
    addProps(curve, "Pile_Per_Step", bpy.context.window_manager.vic_procedural_stair_update_pile_per_step, True)
    addProps(curve, "Pile_Z", bpy.context.window_manager.vic_procedural_stair_update_pile_z, True)
    addProps(curve, "Step", bpy.context.window_manager.vic_procedural_stair_update_step, True)
    addProps(curve, "Step_Threshold", bpy.context.window_manager.vic_procedural_stair_update_step_threshold, True)
    addProps(curve, "OnGround", bpy.context.window_manager.vic_procedural_stair_update_onGround, True)
    addProps(curve, "Ground", bpy.context.window_manager.vic_procedural_stair_update_ground, True)

def endEdit():
    curve = caches["curve"]
    if curve.name not in bpy.data.objects.keys(): return

    createWallAndPiles()
    
    smooth_list = []
    step_mesh = curve.name + "_step"
    if step_mesh in bpy.data.objects.keys(): smooth_list.append( step_mesh )

    if caches["obj_materials"]:
        obj_materials = caches["obj_materials"]
        for mat in obj_materials: bpy.data.objects[step_mesh].data.materials.append(mat)

    wall_mesh = curve.name + "_wall"
    if wall_mesh in bpy.data.objects.keys(): smooth_list.append( wall_mesh )

    for smooth in smooth_list:
        obj = bpy.data.objects[smooth]
        obj.select_set(True)
        activeObject(obj)
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.select_all(action='DESELECT')

    # 確認對位用的代理物件被清除乾净
    for o in caches["pssProxyPool"]: o.hide_viewport = False
    removeObjects([o for o in bpy.data.objects if "auto_build_please_ignore" in o.name])
    caches["pssProxyPool"] = []

    bpy.context.space_data.shading.type = caches["shading"]

def createWallAndPiles():
    
    curve = caches["curve"]
    pile = curve["Pile"]
    if pile == "" or pile not in bpy.data.objects: return

    pilePoints = caches["pilePoints"]
    parent = caches["obj"]

    copyFrom = bpy.data.objects[pile]

    for pp in pilePoints:
        pileobj = copyObject(copyFrom, True)
        pileobj.matrix_world = pp
        pileobj.name = curve.name + "_pile"
        pileobj.parent = parent
        addObject(pileobj)

    wall = curve["Wall"]
    if wall == "" or wall not in bpy.data.objects: return

    
    creator = prepareAndCreateMesh(curve.name + "_wall")
    obj = creator["obj"]
    update = creator["update"]
    addVertexByMesh = creator["addVertexByMesh"]

    leftside_pts = pilePoints[::2]
    rightside_pts = pilePoints[1::2]

    copyFrom = bpy.data.objects[wall]
    copyFrom_length = copyFrom.dimensions.x

    materials = copyFrom.data.materials

    def createWall(curr_pp, prev_pp):
        
        def transferVertex(vid, v):
            curr_pp_pos = curr_pp.to_translation()
            prev_pp_pos = prev_pp.to_translation()
            diff = curr_pp_pos - prev_pp_pos
            direct = diff.normalized()

            proj_dir = direct.copy()
            proj_dir.z = 0
            proj_dir.normalize()

            # 確認角度方向，先把方向正規化，再檢查y是正的還是負的，已此來確認兩個向量取角度時，順序是一致的
            # 取得當前方向的水平旋轉矩陣
            rot_mat = Matrix.Rotation(atan2(proj_dir.y, proj_dir.x), 4, 'Z')

            # 以旋轉矩陣而言，倒置矩陣等於逆矩陣。這裏取得反方向的水平旋轉矩陣
            rot_mat.transpose() # rot_mat.inverse() 意思一樣
            
            # 用叉乘取得兩個向量的垂直向量，代表y軸。這個時候因爲我們不能確定取得的垂直向量都能永遠朝同一個方向，所以有下一步
            side_dir = direct.cross(proj_dir)
            side_dir.normalize()

            # 把side方向乘上【反方向的水平旋轉矩陣】，就可以把他轉回正規化的方向(0,1,0) or (0,-1,0)
            side_dir = rot_mat @ side_dir

            # 有了正規化的方向后，就可以依次來確保取角度的時候，不會取到相反的角度
            # angle 等於 acos(direct.dot(proj_dir))，但是這樣算會有不合法參數的問題，改成用内建的算法
            pitch = direct.angle(proj_dir) * side_dir.y

            hori_diff = diff.copy()
            hori_diff.z = 0
            scale_width = hori_diff.length / copyFrom_length

            skew = Vector((v.co.x, v.co.y, v.co.z))
            skew.x *= scale_width
            skew.z += tan(pitch) * skew.x

            pos_mat = Matrix.Translation((curr_pp_pos + prev_pp_pos) / 2)
            rot_mat = Matrix.Rotation(atan2(direct.y, direct.x), 4, 'Z')
            new_mat = pos_mat @ rot_mat
            return new_mat @ skew

        addVertexByMesh(copyFrom, 0, transferVertex)

    for i, curr_pp in enumerate(leftside_pts):
        if i == 0: continue
        prev_pp = leftside_pts[i-1]
        createWall(curr_pp, prev_pp)

    for i, curr_pp in enumerate(rightside_pts):
        if i == 0: continue
        prev_pp = rightside_pts[i-1]
        createWall(curr_pp, prev_pp)

    update()

    # 上材質
    for mat in materials: obj.data.materials.append(mat)

def removeMeshs():
    curve = caches["curve"]

    # 刪掉模型前先把他的材質記下來。等到創建模型的時候再給上
    if curve.name + "_step" in bpy.data.objects.keys():
        bpy.data.objects[curve.name + "_step"].hide_viewport = False
        materials = bpy.data.objects[curve.name + "_step"].data.materials
        caches["obj_materials"] = materials

    removeObjects([o for o in bpy.data.objects if curve.name + "_pile" in o.name])
    removeObjects([o for o in bpy.data.objects if curve.name + "_wall" in o.name])
    removeObjects([o for o in bpy.data.objects if curve.name + "_step" in o.name])

def updateMesh(scene):
    createStairProxy(True)

def invokeLiveEdit(self, context):
    
    if context.window_manager.vic_procedural_stair_update_live:

        if not checkAndToggle(context):
            context.window_manager.vic_procedural_stair_update_live = False
            return

        startEdit()
        bpy.ops.screen.animation_play()
        if updateMesh in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(updateMesh)
        bpy.app.handlers.frame_change_post.append(updateMesh)
    else:

        checkAndToggle(context)

        curr_focus = bpy.context.object

        bpy.ops.screen.animation_cancel()
        if updateMesh in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(updateMesh)
        updateMesh(None)
        endEdit()

        if curr_focus: focusObject(curr_focus)
        

bpy.types.WindowManager.vic_procedural_stair_update_live =   bpy.props.BoolProperty(
                                                            default = False,
                                                            update = invokeLiveEdit,
                                                            description='Please Select One Spline With Object Mode')

bpy.types.WindowManager.vic_procedural_stair_update_onGround =   bpy.props.BoolProperty(
                                                                default = False,
                                                                description='Whether the bottom is close to the ground')

bpy.types.WindowManager.vic_procedural_stair_update_width = bpy.props.FloatProperty(
                                                            name='Width',
                                                            default=.5,
                                                            min=0.01,
                                                            description='The width of the stairs')

bpy.types.WindowManager.vic_procedural_stair_update_wall_inner_distance = bpy.props.FloatProperty(
                                                            name='Wall Inner Distance',
                                                            default=.1,
                                                            description='Inner distance of wall and pillar')

bpy.types.WindowManager.vic_procedural_stair_update_pile_per_step = bpy.props.IntProperty(
                                                            name='Pile Per Step',
                                                            default=5,
                                                            min=1,
                                                            step=1,
                                                            description='Every few steps will produce a pillar')

bpy.types.WindowManager.vic_procedural_stair_update_pile_z = bpy.props.FloatProperty(
                                                            name='Pile Z',
                                                            default=0,
                                                            description='Height of wall and pillar')

bpy.types.WindowManager.vic_procedural_stair_update_step_threshold = bpy.props.FloatProperty(
                                                            name='Step Threshold',
                                                            default=0.01,
                                                            min=0.0,
                                                            description='Steps will be generated when the height between nodes exceeds this height')

bpy.types.WindowManager.vic_procedural_stair_update_step = bpy.props.IntProperty(
                                                            name='Step',
                                                            default=20,
                                                            min=2,
                                                            step=1,
                                                            description='Number of steps')

bpy.types.WindowManager.vic_procedural_stair_update_ground = bpy.props.FloatProperty(
                                                            name='Ground',
                                                            default=-1,
                                                            description='The thickness of the stairs, if it is a pattern that is close to the ground, this parameter is the height of the ground')

bpy.types.WindowManager.vic_procedural_stair_update_pile = bpy.props.StringProperty(
                                                            name='Pile',
                                                            default="")

bpy.types.WindowManager.vic_procedural_stair_update_wall = bpy.props.StringProperty(
                                                            name='Wall',
                                                            default="")

class vic_procedural_stair_update_panel(bpy.types.Panel):
    bl_category = "Vic Addons"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Procedrual Spline Stair"

    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        col.operator(vic_procedural_stair_update.bl_idname)
        col.prop(context.window_manager, 'vic_procedural_stair_update_live', text="Live Edit", toggle=True, icon="EDITMODE_HLT")
        col = layout.column(align=True)
        col.prop(context.window_manager, 'vic_procedural_stair_update_width')
        col.prop(context.window_manager, 'vic_procedural_stair_update_wall_inner_distance')
        col.prop(context.window_manager, 'vic_procedural_stair_update_step')
        col.prop(context.window_manager, 'vic_procedural_stair_update_step_threshold')
        col.prop(context.window_manager, 'vic_procedural_stair_update_pile_per_step')
        col.prop(context.window_manager, 'vic_procedural_stair_update_pile_z')
        col.prop(context.window_manager, 'vic_procedural_stair_update_ground')
        col.prop(context.window_manager, 'vic_procedural_stair_update_onGround', text="On Ground")
        col = layout.column(align=True)
        col.prop_search(context.window_manager, "vic_procedural_stair_update_wall", bpy.data, "objects")
        col.prop_search(context.window_manager, "vic_procedural_stair_update_pile", bpy.data, "objects")
        
        


        
        

        