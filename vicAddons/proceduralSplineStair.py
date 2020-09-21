import bpy
from .vic_tools import *
from mathutils import *
from math import *

caches = {
    "curve":None,
    "obj":None,
    "update":None,
    "clear":None,
    "addRectVertex":None,
    "pilePoints":None
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

    curve["Width"] = bpy.context.window_manager.vic_procedural_stair_update_width
    curve["Step"] = bpy.context.window_manager.vic_procedural_stair_update_step
    curve["Step_Threshold"] = bpy.context.window_manager.vic_procedural_stair_update_step_threshold
    curve["Ground"] = bpy.context.window_manager.vic_procedural_stair_update_ground
    curve["OnGround"] = bpy.context.window_manager.vic_procedural_stair_update_onGround

    width = curve["Width"]
    step = curve["Step"]
    step_threshold = curve["Step_Threshold"]
    ground = curve["Ground"]
    onGround = curve["OnGround"]

    if width <= 0 or step <= 0: return
    
    length, matrices = getCurvePosAndLength(curve, step)
    if length == 0: return

    stepLength = length / step
    
    # reset mesh data
    clear()
    pilePoints = []
    if curve.name + "_wall" in bpy.data.objects.keys(): removeObjects([bpy.data.objects[curve.name + "_wall"]])

    last_pts = None
    last_height = 0
    last_isStep = False

    pts = (Vector((0,width/2,0)), Vector((0,-width/2,0)))
    pile_pts = (Vector((0,width/2 - .5,0)), Vector((0,-width/2 + .5,0)))
    for i, mat in enumerate(matrices):
        curr_pts = []
        pile_mats = []
        for j, pt in enumerate(pts):

            # 只留下水平的旋轉（yaw），需要單位化，不然轉成矩陣的時候，會有拉扯
            hori_quat = mat.to_quaternion()
            hori_quat.x = hori_quat.y = 0
            hori_quat.normalize()

            hori_mat = hori_quat.to_matrix().to_4x4()
            hori_mat = Matrix.Translation(mat.to_translation()) @ hori_mat
            pos = hori_mat @ pt
            curr_pts.append(pos)

            if last_pts and i % 5 == 0:
                pile_pos = hori_mat @ pile_pts[j]
                last_pt = last_pts[j]
                offset_pt = (pile_pos + last_pt) / 2
                offset_pt.z = last_pt.z
                pile_mat = Matrix.Translation(offset_pt) @ hori_quat.to_matrix().to_4x4()
                pile_mats.append(pile_mat)

        pilePoints += pile_mats

        # 第二步開始才有足夠的資訊來計算
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
                addRectVertex((step_pt0,curr_pts[0], curr_pts[1], step_pt1), ((0,0),(0,0),(0,0),(0,0)))

            # 樓梯面
            addRectVertex((last_pts[0],last_pts[1], step_pt1, step_pt0), ((0,0),(0,0),(0,0),(0,0)))

            side_pt0 = last_pts[0].copy()
            side_pt1 = curr_pts[0].copy()
            side_pt2 = last_pts[1].copy()
            side_pt3 = curr_pts[1].copy()
            
            if onGround:
                side_pt0.z = ground
                side_pt1.z = ground
                side_pt2.z = ground
                side_pt3.z = ground
            else:
                side_pt0.z += ground
                side_pt1.z += ground
                side_pt2.z += ground
                side_pt3.z += ground

            # 樓梯左側面
            if current_height < 0:
                addRectVertex((last_pts[0],step_pt0, curr_pts[0]), ((0,0),(0,0),(0,0),(0,0)))
                addRectVertex((last_pts[0],curr_pts[0], side_pt1, side_pt0), ((0,0),(0,0),(0,0),(0,0)))
            else:
                if last_isStep:
                    step_connect_pt = last_pts[0] + Vector((0,0,-last_height))
                else:
                    step_connect_pt = last_pts[0]

                addRectVertex((last_pts[0],step_pt0, step_connect_pt), ((0,0),(0,0),(0,0),(0,0)))
                addRectVertex((step_connect_pt, step_pt0, side_pt1, side_pt0), ((0,0),(0,0),(0,0),(0,0)))
            

            # 樓梯右側面
            if current_height < 0:
                addRectVertex((last_pts[1],step_pt1, curr_pts[1]), ((0,0),(0,0),(0,0),(0,0)))
                addRectVertex((last_pts[1],curr_pts[1], side_pt3, side_pt2), ((0,0),(0,0),(0,0),(0,0)))
            else:
                if last_isStep:
                    step_connect_pt = last_pts[1] + Vector((0,0,-last_height))
                else:
                    step_connect_pt = last_pts[1]

                addRectVertex((last_pts[1],step_pt1, step_connect_pt), ((0,0),(0,0),(0,0),(0,0)))
                addRectVertex((step_connect_pt, step_pt1, side_pt3, side_pt2), ((0,0),(0,0),(0,0),(0,0)))

            # 底部mesh
            addRectVertex((side_pt0, side_pt1, side_pt3, side_pt2), ((0,0),(0,0),(0,0),(0,0)))
                
            last_height = current_height
            last_isStep = current_isStep
        last_pts = curr_pts

    caches["pilePoints"] = pilePoints
    update()

class vic_procedural_stair_update(bpy.types.Operator):
    bl_idname = "vic.vic_procedural_stair_update"
    bl_label = "Create & Update"

    def execute(self, context):
        ctx = bpy.context
        if not ctx.object or ctx.object.type != 'CURVE': 
            self.report({'INFO'}, "Please select at least one CURVE object.")
            return {'FINISHED'}
        currentFocus = ctx.object
        startEdit()
        createStairProxy()
        endEdit()
        focusObject(currentFocus)
        return {'FINISHED'}

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

    meshName = curve.name + "_step"

    creator = prepareAndCreateMesh(meshName)
    obj = creator["obj"]
    update = creator["update"]
    clear = creator["clear"]
    addRectVertex = creator["addRectVertex"]

    caches["obj"] = obj
    caches["update"] = update
    caches["addRectVertex"] = addRectVertex
    caches["clear"] = clear
    caches["pilePoints"] = []
    
    addProps(curve, "Mesh", obj.name, True)
    addProps(curve, "Pile", "")
    addProps(curve, "Width", 1)
    addProps(curve, "Step", 50)
    addProps(curve, "Step_Threshold", .2)
    addProps(curve, "OnGround", 0)
    addProps(curve, "Ground", -1)

    bpy.context.window_manager.vic_procedural_stair_update_width = curve["Width"]
    bpy.context.window_manager.vic_procedural_stair_update_step = curve["Step"]
    bpy.context.window_manager.vic_procedural_stair_update_step_threshold = curve["Step_Threshold"]
    bpy.context.window_manager.vic_procedural_stair_update_ground = curve["Ground"]
    bpy.context.window_manager.vic_procedural_stair_update_onGround = curve["OnGround"]

    removePiles()

def endEdit():
    curve = caches["curve"]
    if curve.name not in bpy.data.objects.keys(): return
    if curve["Mesh"] != "" and curve["Mesh"] in bpy.data.objects.keys():
        obj = bpy.data.objects[curve["Mesh"]]
        obj.select_set(True)
        activeObject(obj)
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        # bpy.ops.mesh.faces_shade_smooth()
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.select_all(action='DESELECT')
        createPiles()

def createPiles():
    
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


    creator = prepareAndCreateMesh(curve.name + "_wall")
    obj = creator["obj"]
    update = creator["update"]
    addVertexByMesh = creator["addVertexByMesh"]

    leftside_pts = pilePoints[::2]
    rightside_pts = pilePoints[1::2]

    copyFrom = bpy.data.objects["Cube"]

    def createWall(curr_pp, prev_pp):
        
        def transferVertex(vid, v):
            curr_pp_pos = curr_pp.to_translation()
            prev_pp_pos = prev_pp.to_translation()
            direct = (curr_pp_pos - prev_pp_pos).normalized()

            proj_dir = direct.copy()
            proj_dir.z = 0
            proj_dir.normalize()

            # 確認角度方向，先把方向正規化，再檢查y是正的還是負的
            side_dir = direct.cross(proj_dir)
            side_dir.normalize()
            rot_mat = Matrix.Rotation(atan2(direct.y, direct.x), 4, 'Z')
            rot_mat.transpose()
            side_dir = rot_mat @ side_dir

            cos_a = direct.dot(proj_dir)
            pitch = acos(cos_a) * side_dir.y

            skew = Vector((v.co.x, v.co.y, v.co.z))
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

def removePiles():
    curve = caches["curve"]
    removeObjects([o for o in bpy.data.objects if curve.name + "_pile" in o.name])
    removeObjects([o for o in bpy.data.objects if curve.name + "_wall" in o.name])

def invokeLiveEdit(self, context):
    def updateMesh(scene):
        createStairProxy()

    if context.window_manager.vic_procedural_stair_update_live:
        startEdit()
        bpy.ops.screen.animation_play()
        if updateMesh in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(updateMesh)
        bpy.app.handlers.frame_change_post.append(updateMesh)
    else:
        bpy.ops.screen.animation_cancel()
        bpy.app.handlers.frame_change_post.remove(updateMesh)
        updateMesh(None)
        endEdit()
        

bpy.types.WindowManager.vic_procedural_stair_update_live =   bpy.props.BoolProperty(
                                                            default = False,
                                                            update = invokeLiveEdit)

bpy.types.WindowManager.vic_procedural_stair_update_onGround =   bpy.props.BoolProperty(
                                                                default = False)

bpy.types.WindowManager.vic_procedural_stair_update_width = bpy.props.FloatProperty(
                                                            name='Width',
                                                            default=.5,
                                                            min=0.01)

bpy.types.WindowManager.vic_procedural_stair_update_step_threshold = bpy.props.FloatProperty(
                                                            name='Step Threshold',
                                                            default=.2,
                                                            min=0.0)

bpy.types.WindowManager.vic_procedural_stair_update_step = bpy.props.IntProperty(
                                                            name='Step',
                                                            default=5,
                                                            min=2,
                                                            step=1)

bpy.types.WindowManager.vic_procedural_stair_update_ground = bpy.props.FloatProperty(
                                                            name='Ground',
                                                            default=-1)                                                            

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
        col.prop(context.window_manager, 'vic_procedural_stair_update_width')
        col.prop(context.window_manager, 'vic_procedural_stair_update_step')
        col.prop(context.window_manager, 'vic_procedural_stair_update_step_threshold')
        col.prop(context.window_manager, 'vic_procedural_stair_update_onGround', text="On Ground")
        col.prop(context.window_manager, 'vic_procedural_stair_update_ground')

        # col = layout.column(align=True)
        # col.operator(vic_procedural_stair_pile.bl_idname)
        

        
        

        