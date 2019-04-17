import bpy
from .operators import CreateCameraTarget
from .operators import MirrorCubeAdd
from .operators import SelectByName
from .operators import HandDrag
from .operators import ParticleToRigidbody
from .operators import MeshFlatten
from .operators import ProceduralStair

class ActionProperties(bpy.types.PropertyGroup):
    string_select_name:bpy.props.StringProperty( name="", description="Name of select objects", default="")    

class VIC_PT_ACTION_PANEL(bpy.types.Panel):
    bl_category = "Vic Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Actions"

    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        col.operator(MirrorCubeAdd.mirror_cube_add.bl_idname)
        col.operator(CreateCameraTarget.vic_create_camera_target.bl_idname)
        col.operator(MeshFlatten.vic_make_meshs_plane.bl_idname)
        col.operator(ParticleToRigidbody.ParticlesToRigidbodys.bl_idname)
        col.operator(ProceduralStair.vic_procedural_stair.bl_idname)
        
        row = col.row(align=True)
        row.prop(context.scene.action_properties, 'string_select_name' )
        row.operator(SelectByName.vic_select_by_name.bl_idname)
        
        col.label(text='Drag Effect')
        col.operator(HandDrag.vic_hand_drag.bl_idname)
        col.operator(HandDrag.vic_healing_all_effect_objects.bl_idname)

classes = (
    # ui
    ActionProperties,
    VIC_PT_ACTION_PANEL,

    # operation
    CreateCameraTarget.vic_create_camera_target,
    MirrorCubeAdd.mirror_cube_add,
    SelectByName.vic_select_by_name,
    HandDrag.vic_hand_drag,
    HandDrag.vic_healing_all_effect_objects,
    ParticleToRigidbody.ParticlesToRigidbodys,
    MeshFlatten.vic_make_meshs_plane,
    ProceduralStair.vic_procedural_stair
)
def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.action_properties = bpy.props.PointerProperty(type=ActionProperties)
    
def unregister():
    for cls in classes: bpy.utils.unregister_class(cls)
    del bpy.types.Scene.action_properties