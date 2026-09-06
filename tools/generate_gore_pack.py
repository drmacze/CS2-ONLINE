from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import json, random

ROOT=Path(__file__).resolve().parents[1]
BP=ROOT/'src'/'gore_bp'; RP=ROOT/'src'/'gore_rp'
for p in (BP/'entities',RP/'entity',RP/'models/entity',RP/'render_controllers',RP/'particles',RP/'textures/entity',RP/'textures/vfx'):
    p.mkdir(parents=True,exist_ok=True)

def write(path,obj):
    path.write_text(json.dumps(obj,indent=2,separators=(',',': '))+'\n')

write(BP/'manifest.json',{
 'format_version':2,'header':{'name':'DLavie CS2 Gore VFX V1.0 [BP]','description':'AG2-safe standalone blood physics and gore VFX. No NPC, Heist, Flashlight or HUD dependency.','uuid':'b0f9699c-0e15-4baa-a122-c28b8ee63cf2','version':[1,0,0],'min_engine_version':[1,26,40]},
 'modules':[{'type':'data','uuid':'2010f0de-29a5-4d28-b40e-cf6324f7521b','version':[1,0,0]},{'type':'script','language':'javascript','entry':'scripts/main.js','uuid':'47224061-05cb-4fc2-93fd-d1cc1db21d3f','version':[1,0,0]}],
 'dependencies':[{'module_name':'@minecraft/server','version':'2.9.0'},{'uuid':'b4e99bca-494e-44f9-a24d-0edb86e7fd59','version':[1,0,0]}]
})
write(RP/'manifest.json',{
 'format_version':2,'header':{'name':'DLavie CS2 Gore VFX V1.0 [RP]','description':'Standalone CS2 blood particles, physical droplets, pools and fragments.','uuid':'b4e99bca-494e-44f9-a24d-0edb86e7fd59','version':[1,0,0],'min_engine_version':[1,26,40]},
 'modules':[{'type':'resources','uuid':'30f70135-1bb7-4aba-ae34-68e1180d5b11','version':[1,0,0]}]
})

for name,ident,timer,wh,gravity in [
 ('blood_drop_phys','dlv:blood_drop_phys',3.0,(.08,.08),True),('blood_pool','dlv:blood_pool',38.0,(.01,.01),False),
 ('gore_chunk','dlv:gore_chunk',9.0,(.14,.14),True),('bone_fragment','dlv:bone_fragment',10.0,(.10,.10),True)]:
    write(BP/'entities'/f'{name}.json',{'format_version':'1.21.0','minecraft:entity':{
      'description':{'identifier':ident,'is_spawnable':False,'is_summonable':True,'is_experimental':False},
      'component_groups':{'dlv:despawn':{'minecraft:instant_despawn':{}}},
      'components':{'minecraft:collision_box':{'width':wh[0],'height':wh[1]},'minecraft:physics':{'has_gravity':gravity,'has_collision':gravity},'minecraft:pushable':{'is_pushable':False,'is_pushable_by_piston':False},'minecraft:timer':{'looping':False,'time':timer,'time_down_event':{'event':'dlv:remove','target':'self'}}},
      'events':{'dlv:remove':{'add':{'component_groups':['dlv:despawn']}}}}})

geos=[]
for ident,tw,th,bounds,cube in [
 ('blood_drop',16,16,(1,1,[0,.5,0]),([-1,0,-1],[2,2,2],[0,0])),
 ('blood_pool',32,32,(3,1,[0,.1,0]),([-8,0,-8],[16,.25,16],[0,0])),
 ('gore_chunk',16,16,(1,1,[0,.5,0]),([-2,0,-1.5],[4,3,3],[0,0])),
 ('bone_fragment',16,16,(1,1,[0,.5,0]),([-2,0,-.7],[4,1.4,1.4],[0,0]))]:
    geos.append({'description':{'identifier':f'geometry.dlv.{ident}','texture_width':tw,'texture_height':th,'visible_bounds_width':bounds[0],'visible_bounds_height':bounds[1],'visible_bounds_offset':bounds[2]},'bones':[{'name':'root','pivot':[0,0,0],'cubes':[{'origin':cube[0],'size':cube[1],'uv':cube[2]}]}]})
write(RP/'models/entity/gore.geo.json',{'format_version':'1.12.0','minecraft:geometry':geos})
rc={}
for name in ('blood_drop','blood_pool','gore_chunk','bone_fragment'):
    rc[f'controller.render.dlv.{name}']={'geometry':'Geometry.default','materials':[{'*':'Material.default'}],'textures':['Texture.default']}
write(RP/'render_controllers/gore.render_controllers.json',{'format_version':'1.8.0','render_controllers':rc})
for fn,ident,geo,tex,controller in [
 ('blood_drop_phys','dlv:blood_drop_phys','blood_drop','dlv_blood_drop','blood_drop'),('blood_pool','dlv:blood_pool','blood_pool','dlv_blood_pool','blood_pool'),('gore_chunk','dlv:gore_chunk','gore_chunk','dlv_gore_chunk','gore_chunk'),('bone_fragment','dlv:bone_fragment','bone_fragment','dlv_bone_fragment','bone_fragment')]:
    write(RP/'entity'/f'{fn}.entity.json',{'format_version':'1.10.0','minecraft:client_entity':{'description':{'identifier':ident,'materials':{'default':'entity_alphatest'},'textures':{'default':f'textures/entity/{tex}'},'geometry':{'default':f'geometry.dlv.{geo}'},'render_controllers':[f'controller.render.dlv.{controller}']}}})

particle_specs={
 'blood_splat':(8,.035,(.25,.85),(1.2,4.2),(-10.5,1.1),(.025,.07),'rotate_xyz','dlv_blood_drop'),
 'blood_mist':(22,.08,(.22,.72),(2.0,6.2),(-6.5,2.1),(.035,.10),'rotate_xyz','dlv_blood_mist'),
 'blood_jet':(14,.025,(.38,1.15),(3.4,8.6),(-13.5,.52),(.018,.038),'direction_y','dlv_blood_streak'),
 'blood_headshot':(34,.12,(.45,1.45),(3.0,8.0),(-15.0,.42),(.025,.085),'rotate_xyz','dlv_blood_drop')}
for name,(count,radius,life,speed,motion,size,facing,texture) in particle_specs.items():
    spread=.50 if name=='blood_headshot' else (.25 if name=='blood_mist' else .12 if name=='blood_jet' else .35)
    yexpr='0.35 + variable.dir_y + math.random(-0.15,0.55)' if name=='blood_headshot' else f'variable.dir_y + math.random(-{spread:.2f},{spread:.2f})'
    wh=[f'math.random({size[0]},{size[1]})',f'math.random({size[0]},{.20 if name=="blood_jet" else size[1]})']
    write(RP/'particles'/f'{name}.json',{'format_version':'1.10.0','particle_effect':{'description':{'identifier':f'dlv:{name}','basic_render_parameters':{'material':'particles_blend','texture':f'textures/vfx/{texture}'}},'components':{
      'minecraft:emitter_rate_instant':{'num_particles':count},'minecraft:emitter_lifetime_once':{'active_time':.03},'minecraft:emitter_shape_sphere':{'radius':radius,'direction':[f'variable.dir_x + math.random(-{spread:.2f},{spread:.2f})',yexpr,f'variable.dir_z + math.random(-{spread:.2f},{spread:.2f})']},
      'minecraft:particle_lifetime_expression':{'max_lifetime':f'math.random({life[0]},{life[1]})'},'minecraft:particle_initial_speed':f'math.random({speed[0]},{speed[1]})','minecraft:particle_motion_dynamic':{'linear_acceleration':[0,motion[0],0],'linear_drag_coefficient':motion[1]},'minecraft:particle_appearance_billboard':{'size':wh,'facing_camera_mode':facing},'minecraft:particle_appearance_tinting':{'color':[.58,.008,.012,'1-v.particle_age/v.particle_lifetime']}}}})

TEX=RP/'textures'; rng=random.Random(20260907)
def save(path,size,painter):
    im=Image.new('RGBA',(size,size),(0,0,0,0)); d=ImageDraw.Draw(im); painter(im,d); im.save(path)
def speckle(im,d,base,n):
    for _ in range(n):
        x=rng.randrange(im.width); y=rng.randrange(im.height); r=rng.choice([1,1,1,2]); c=tuple(max(0,min(255,v+rng.randrange(-24,25))) for v in base[:3])+(base[3],); d.ellipse((x-r,y-r,x+r,y+r),fill=c)
save(TEX/'entity/dlv_blood_drop.png',16,lambda im,d:(d.ellipse((3,3,12,12),fill=(112,2,5,235)),speckle(im,d,(104,2,4,220),25)))
save(TEX/'entity/dlv_gore_chunk.png',16,lambda im,d:(d.rectangle((1,1,14,14),fill=(108,9,12,255)),speckle(im,d,(126,16,19,255),65)))
save(TEX/'entity/dlv_bone_fragment.png',16,lambda im,d:(d.rectangle((1,1,14,14),fill=(214,204,174,255)),speckle(im,d,(205,190,160,255),45)))
def pool(im,d): d.ellipse((2,7,29,25),fill=(72,0,3,205)); d.ellipse((6,5,24,22),fill=(105,2,5,225)); speckle(im,d,(92,1,4,180),70)
save(TEX/'entity/dlv_blood_pool.png',32,pool)
def drop(im,d): d.ellipse((5,4,26,27),fill=(120,1,5,220)); d.ellipse((9,7,18,16),fill=(172,18,22,165))
save(TEX/'vfx/dlv_blood_drop.png',32,drop)
def mist(im,d):
    for _ in range(60):
        x=rng.randrange(4,28); y=rng.randrange(4,28); r=rng.randrange(2,7); a=rng.randrange(15,55); d.ellipse((x-r,y-r,x+r,y+r),fill=(120,0,4,a))
    im.alpha_composite(im.filter(ImageFilter.GaussianBlur(2)))
save(TEX/'vfx/dlv_blood_mist.png',32,mist)
def streak(im,d): d.rounded_rectangle((13,1,19,31),radius=3,fill=(118,0,4,225)); d.rectangle((15,2,17,28),fill=(175,12,17,155))
save(TEX/'vfx/dlv_blood_streak.png',32,streak)
print('generated gore pack sources/assets')
