import bpy

class vic_line_align(bpy.types.Operator):
    bl_idname = 'vic.vic_line_align'
    bl_label = 'Line Align'
    bl_description = 'Line Align'

    def execute(self, context):

        selectList = bpy.context.selected_objects
        count = len( selectList )
        if count < 2:   return {'FINISHED'}
        distance = 0
        startObj = None
        endObj = None
        for i in range(count):
            for j in range(i+1, count):
                objA = selectList[i]
                objB = selectList[j]
                current = (objB.location - objA.location).length
                if current > distance:
                    distance = current
                    startObj = objA
                    endObj = objB

        dirVector = endObj.location - startObj.location
        dirVectorUnit = dirVector.normalized()
        for obj in selectList:
            objVector = obj.location - startObj.location
            if objVector.length > 0:
                obj.location = dirVectorUnit * objVector.dot(dirVectorUnit) + startObj.location

        return {'FINISHED'}
