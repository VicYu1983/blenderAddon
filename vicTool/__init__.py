bl_info = {
    "name": "Vic Tools",
    "author": "Vic",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "3D View",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "category": "Tools"
}

from . import vic_actions
from . import vic_spring_bone
from . import vic_make_it_voxel

pluginObj = (
    vic_actions,
    vic_spring_bone,

    # hide_viewport目前insert key在2.8好像有點bug
    # 2.8的材質沒有using vertex color的屬性，還不知道在哪裏
    #vic_make_it_voxel
)

def register():
    for p in pluginObj: p.register()

def unregister():
    for p in pluginObj: p.unregister()

      