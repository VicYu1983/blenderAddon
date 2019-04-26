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
    #bpy.context.view_layer.active_layer_collection.collection.objects.link(obj)
    bpy.context.collection.objects.link(obj)

def activeObject( obj ):
    bpy.context.view_layer.objects.active = obj

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