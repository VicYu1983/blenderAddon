import bpy

class ParticlesToRigidbodys(bpy.types.Operator):
    bl_idname = 'vic.particle_rigidbody'
    bl_label = 'Particles To Rigidbodys'
    bl_description = 'Particles To Rigidbodys'
    
    def setting(self, emitter ):
        self.emitter = emitter
        eval_ob = bpy.context.evaluated_depsgraph_get().objects.get(self.emitter.name, None)
        self.ps = eval_ob.particle_systems[0]
        self.ps_set = self.ps.settings
        self.ps_set.use_rotation_instance = True
        self.start_frame = int( self.ps_set.frame_start )
        self.end_frame = int( self.ps_set.frame_end + ( self.ps_set.lifetime *  ( 1 + self.ps_set.lifetime_random)))
        self.update_frame = self.end_frame - self.start_frame
        self.mesh_clone = self.ps_set.instance_object
        self.ms = []

    def createMesh(self):
        self.emitter.select_set( False )
        for p in self.ps.particles:
            loc = p.location
            rot = p.rotation.to_euler()
            o = self.mesh_clone.copy()
            bpy.context.view_layer.active_layer_collection.collection.objects.link(o)
            o.scale[0] = p.size
            o.scale[1] = p.size
            o.scale[2] = p.size
            o.select_set( True )
            bpy.context.view_layer.objects.active = o
            bpy.ops.rigidbody.object_add()
            o.location = loc
            o.rotation_euler= rot
            o.rigid_body.kinematic=True
            o.rigid_body.restitution = .2
            o.keyframe_insert('rigid_body.kinematic')
            o.select_set( False )
            self.ms.append( o )
            
    def moveMesh(self):
        for i, p in enumerate( self.ps.particles ):
            o = self.ms[i]
            if p.alive_state == 'DEAD':
                if o.rigid_body.kinematic:
                    o.rigid_body.kinematic=False
                    o.keyframe_insert('rigid_body.kinematic')
            elif p.alive_state == 'ALIVE':
                o.location = p.location
                o.rotation_euler = p.rotation.to_euler()
                o.keyframe_insert('location')
                o.keyframe_insert('scale')
                o.keyframe_insert('rotation_euler')
            else:
                o.location = p.location
                o.rotation_euler = p.rotation.to_euler()
                
    def clearSetting(self):
        self.ms = []        
            
    def update( self, f ):
        if f == self.start_frame:
            self.clearSetting()
            self.createMesh()
        elif f == self.end_frame - 1:
            self.moveMesh()
            self.clearSetting()
        else:
            self.moveMesh()
        
    def executeAll(self):
        for i in range( self.update_frame ):
            f = self.start_frame + i
            bpy.context.scene.frame_set(f)
            self.update(f)
            print( 'frame solved:', f )

    def execute(self, context):
        if context.view_layer.objects.active == None:
            self.report( {'ERROR'}, 'please pick one object!' )
            return {'FINISHED'}
        elif len( context.view_layer.objects.active.particle_systems ) == 0:
            self.report( {'ERROR'}, 'need particle system!' )
            return {'FINISHED'}
        elif context.view_layer.objects.active.particle_systems[0].settings.instance_object == None:
            self.report( {'ERROR'}, 'particle system duplicate object need to be setting!' )
            return {'FINISHED'}                    
        else:
            self.setting(context.view_layer.objects.active)
            self.executeAll()
        return {'FINISHED'}