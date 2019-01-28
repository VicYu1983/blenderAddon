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
    #vic_make_it_voxel
)

def register():
    for p in pluginObj: p.register()

def unregister():
    for p in pluginObj: p.unregister()

      