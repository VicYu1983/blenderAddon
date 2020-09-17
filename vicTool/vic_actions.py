import bpy

from .operators import (
    CreateCameraTarget,
    MirrorCubeAdd,
    SelectByName,
    HandDrag,
    ParticleToRigidbody,
    MeshFlatten,
    ProceduralStair,
    ProceduralBridge,
    LineAlign
)


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
        
        row = col.row(align=True)
        row.prop(context.scene.action_properties, 'string_select_name' )
        row.operator(SelectByName.vic_select_by_name.bl_idname)

        col.label(text='Generator')
        col.operator(ProceduralStair.vic_procedural_stair.bl_idname)
        col.operator(ProceduralBridge.vic_procedural_bridge.bl_idname)

        col.label(text='Stair Generator')
        col.operator(ProceduralSplineStair.vic_procedural_stair_proxy.bl_idname)
        col.prop(context.window_manager, 'vic_procedural_stair_proxy_live', text="Live Edit", toggle=True, icon="EDITMODE_HLT")
        col.prop(context.window_manager, 'vic_procedural_stair_proxy_width')
        col.prop(context.window_manager, 'vic_procedural_stair_proxy_step')

        col.label(text='Lantern Generator')
        col.operator(ProceduralLantern.vic_procedural_lantern_proxy.bl_idname)
        col.operator(ProceduralLantern.vic_procedural_lantern_connect.bl_idname)
        col.operator(ProceduralLantern.vic_procedural_lantern.bl_idname)

        col.prop(context.window_manager, 'vic_procedural_lantern_live', text="Live Edit", toggle=True, icon="EDITMODE_HLT")

        col.label(text='Drag Effect')
        col.operator(HandDrag.vic_hand_drag.bl_idname)
        col.operator(HandDrag.vic_healing_all_effect_objects.bl_idname)

        col.label(text='Align')
        col.operator(LineAlign.vic_line_align.bl_idname)

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
    ProceduralStair.vic_procedural_stair,
    ProceduralBridge.vic_procedural_bridge,
    LineAlign.vic_line_align
)
def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.action_properties = bpy.props.PointerProperty(type=ActionProperties)
    
def unregister():
    for cls in classes: bpy.utils.unregister_class(cls)
    del bpy.types.Scene.action_properties