import bpy
from mathutils import *

def scaleObjVertex(obj, scale):
    for v in obj.data.vertices:
        v.co.x = v.co.x * scale[0]
        v.co.y = v.co.y * scale[1]
        v.co.z = v.co.z * scale[2]

def joinObj( joinList, target ):
    focusObject(target)
    for obj in joinList:
        obj.select_set(True)
    bpy.ops.object.join()
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')

def copyToScene( prefab, sameData = False ):
    obj = copyObject(prefab, sameData)
    addObject(obj)
    return obj

def addObject( obj ):
    bpy.context.collection.objects.link(obj)

def activeObject( obj ):
    bpy.context.view_layer.objects.active = obj

def updateMatrix():
    bpy.context.view_layer.update()

def copyObject(obj, sameData = False):
    newobj = obj.copy()
    if not sameData:
        newobj.data = obj.data.copy()
        newobj.animation_data_clear()
    return newobj

def focusObject(focusObj):
    # unselect all of object, and then can join my own object
    for obj in bpy.data.objects:
        obj.select_set(False)
    focusObj.select_set(True)
    activeObject(focusObj)

def removeObjects(objs):
    curr_focus = bpy.context.object
    for obj in objs:
        focusObject(obj)
        bpy.ops.object.delete()
    if curr_focus: focusObject(curr_focus)

def addProps( target, name, value, override = False ):
    if not name in target or override:
        target[name] = value

def getSelectedWithOrder():
    count = 0

    if not bpy.context.active_object: return []
        
    # start list with current active object:
    order = list([bpy.context.active_object.name])

    #keep going back in time (undo) as long as objects are selected
    while len(bpy.context.selected_objects) >= 2:
        bpy.ops.ed.undo()
        order.insert(0,bpy.context.active_object.name) # add previous active object
        count += 1

    # Get back to the future (redo, redo, redo, ...)
    for x in range(0, count):
        bpy.ops.ed.redo()

    # Collect obj from order names
    objs = []
    for name in order:
        for o in bpy.data.objects:
            if o.name == name:
                objs.append(o)
                continue
    return objs

def prepareAndCreateMesh(name):
    verts = []
    faces = []
    uvsMap = {}
    matIds = []

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    addObject(obj)

    def clear():
        nonlocal verts, faces, uvsMap, matIds, mesh
        verts = []
        faces = []
        uvsMap = {}
        matIds = []
        mesh.clear_geometry()
    
    # 給定一條綫上的點，再給定一個偏移向量，用程式產生偏移過後的第二條綫段的點
    # 用兩條綫上的點來產生面
    # 搭配 prepareAndCreateMesh 一起使用
    def addVertexAndFaces(  line, offset, uvLine, uvOffset, 
                            uvScale = 1, matId = 0, flip = False, close = False):
        line = line.copy()
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
                    # last point, not need to create face
                    continue
            else:
                if flip:
                    f = (v1, v4, v3, v2)
                else:
                    f = (v1, v2, v3, v4)

            currentFaceId = len(faces)
            uvsMap['%i_%i' % (currentFaceId, f[0])] = (
                (uvLine[i][0])*uvScale,
                (uvLine[i][1])*uvScale
            )
            uvsMap['%i_%i' % (currentFaceId, f[1])] = (
                (uvLine[i+1][0])*uvScale,
                (uvLine[i+1][1])*uvScale
            )
            uvsMap['%i_%i' % (currentFaceId, f[2])] = (
                (uvLine[i+1][0]+uvOffset[0])*uvScale,
                (uvLine[i+1][1]+uvOffset[1])*uvScale
            )
            uvsMap['%i_%i' % (currentFaceId, f[3])] = (
                (uvLine[i][0]+uvOffset[0])*uvScale,
                (uvLine[i][1]+uvOffset[1])*uvScale
            )

            faces.append(f)
            matIds.append(matId)

        line.extend(anotherLine)
        verts.extend(line)

    def addRectVertex(  addverts, adduvs, 
                        uvScale = 1, matId = 0):

        startId = len(verts)
        face = []
        currentFaceId = len(faces)
        for i, v in enumerate(addverts):
            verts.append(v)

            vid = i+startId
            face.append(vid)

            adduv = adduvs[i]
            uvsMap['%i_%i' % (currentFaceId, vid)] = (
                adduv[0]*uvScale,
                adduv[1]*uvScale
            )
            
        faces.append(tuple(face))
        matIds.append(matId)

    # 搭配 prepareAndCreateMesh 一起使用
    def addVertexByMesh(mesh, matIdOffset = 0, transformVertex = None):
        currentFaceId = len(faces)
        currentVertId = len(verts)
        for m in mesh.data.polygons:
            vs = []
            currentVertexCount = len(verts)
            for vid in m.vertices:
                vs.append(vid + currentVertexCount)
            faces.append(tuple(vs))
            matIds.append(m.material_index+matIdOffset)

            for vert_idx, loop_idx in zip(m.vertices, m.loop_indices):
                uvsMap["%i_%i" % (m.index+currentFaceId,vert_idx+currentVertId)] = mesh.data.uv_layers.active.data[loop_idx].uv

        for vid,v in enumerate(mesh.data.vertices):
            if transformVertex: newpos = transformVertex(vid, v)
            else: newpos = (v.co.x, v.co.y, v.co.z)
            verts.append( newpos )
            
    def update():
        mesh.from_pydata(verts, [], faces)

        # assign uv
        obj.data.uv_layers.new()
        for i, face in enumerate(obj.data.polygons):
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                uv = uvsMap['%i_%i' % (face.index, vert_idx)]
                obj.data.uv_layers.active.data[loop_idx].uv = uv
            face.material_index = matIds[i]

    return {
        "obj": obj, 
        "update": update, 
        "clear": clear, 
        "addRectVertex": addRectVertex,
        "addVertexAndFaces": addVertexAndFaces,
        "addVertexByMesh": addVertexByMesh
    }

def mergeOverlayVertex(obj):
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.object.editmode_toggle()    

# example:
# curve = bpy.data.objects["BezierCurve"]
# total_length, matrices = getCurvePosAndLength(curve, 10)
def getCurvePosAndLength(curve, count):  

    if bpy.context.area == None: return (0, [])
    if bpy.context.area.type != 'VIEW_3D': return (0, [])
    if bpy.context.mode != 'OBJECT': return (0, [])

    current_focus = bpy.context.object
    
    bpy.ops.object.empty_add(type='ARROWS')
    bpy.ops.object.location_clear()
    bpy.ops.object.constraint_add(type='FOLLOW_PATH')
    constraint = bpy.context.object.constraints["Follow Path"]
    constraint.target = curve
    constraint.forward_axis = 'FORWARD_X'
    constraint.up_axis = 'UP_Z'
    constraint.use_fixed_location = True
    constraint.use_curve_follow = True

    total_length = 0
    current_pos = None
    matrices = []

    for i in range(count+1):
        offset = i / count
        constraint.offset_factor = offset

        # update matrix while python running
        updateMatrix()
        
        world_mat = bpy.context.object.matrix_world.copy()
        world_pos = world_mat.to_translation()
        matrices.append( world_mat )
        
        if i == 0: pass
        else: total_length += (world_pos - current_pos).length
        
        current_pos = world_pos
    
    bpy.ops.object.delete()

    if current_focus: focusObject(current_focus)
    return total_length, matrices
