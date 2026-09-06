import { world, system, MolangVariableMap } from "@minecraft/server";

const DROP = "dlv:blood_drop_phys";
const POOL = "dlv:blood_pool";
const MEAT = "dlv:gore_chunk";
const BONE = "dlv:bone_fragment";
const MAX_DROPS = 110;
const MAX_FRAGMENTS = 70;
const MAX_POOLS = 42;
const trackedDrops = new Map();
const trackedFragments = new Map();
const pools = [];
const lastImpact = new Map();

const EXCLUDED = new Set([
  "minecraft:armor_stand", "minecraft:item", "minecraft:xp_orb", "minecraft:arrow",
  "dlv:blood_drop_phys", "dlv:blood_pool", "dlv:gore_chunk", "dlv:bone_fragment"
]);

function clamp(v,a,b){ return Math.max(a,Math.min(b,v)); }
function rnd(a,b){ return a + Math.random()*(b-a); }
function norm(v){ const m=Math.hypot(v.x,v.y,v.z)||1; return {x:v.x/m,y:v.y/m,z:v.z/m}; }
function biological(e){
  try {
    if(!e?.isValid || EXCLUDED.has(e.typeId)) return false;
    if(e.typeId.startsWith("dlv:")) return false;
    return !!e.getComponent("minecraft:health");
  } catch { return false; }
}
function impactPoint(victim, source){
  const base=victim.location;
  try {
    const p=source?.damagingProjectile;
    if(p?.isValid){ const q=p.location; return {x:q.x,y:q.y,z:q.z}; }
  } catch {}
  const h=victim.typeId==="minecraft:player" ? 1.8 : 1.45;
  return {x:base.x+rnd(-.12,.12),y:base.y+h*rnd(.42,.82),z:base.z+rnd(-.12,.12)};
}
function hitPart(victim, at){
  const dy=at.y-victim.location.y;
  if(victim.typeId==="minecraft:player"){
    if(dy>1.38) return "head";
    if(dy<.70) return "leg";
    return "torso";
  }
  if(dy>1.12) return "head";
  if(dy<.52) return "leg";
  return "torso";
}
function direction(victim, source){
  try {
    const a=source?.damagingEntity;
    if(a?.isValid){ const p=a.location,q=victim.location; return norm({x:q.x-p.x,y:(q.y+1)-p.y,z:q.z-p.z}); }
  } catch {}
  return norm({x:rnd(-1,1),y:rnd(.05,.45),z:rnd(-1,1)});
}
function vars(dir){
  const m=new MolangVariableMap();
  m.setFloat("variable.dir_x",dir.x); m.setFloat("variable.dir_y",dir.y); m.setFloat("variable.dir_z",dir.z);
  return m;
}
function particle(dim,id,at,dir){ try{ dim.spawnParticle(id,at,vars(dir)); }catch{} }
function spawnPool(dim,loc,scale=1){
  try{
    while(pools.length>=MAX_POOLS){ const old=pools.shift(); try{if(old?.isValid)old.remove();}catch{} }
    const e=dim.spawnEntity(POOL,{x:loc.x+rnd(-.18,.18),y:loc.y+.02,z:loc.z+rnd(-.18,.18)});
    try{e.setProperty?.("dlv:scale",clamp(scale,.7,2.8));}catch{}
    pools.push(e);
  }catch{}
}
function spawnDrop(dim,at,dir,power=1){
  if(trackedDrops.size>=MAX_DROPS) return;
  try{
    const e=dim.spawnEntity(DROP,{x:at.x+rnd(-.05,.05),y:at.y+rnd(-.03,.08),z:at.z+rnd(-.05,.05)});
    e.applyImpulse({x:dir.x*rnd(.08,.19)*power+rnd(-.035,.035),y:rnd(.05,.15)*power,z:dir.z*rnd(.08,.19)*power+rnd(-.035,.035)});
    trackedDrops.set(e.id,{e,born:system.currentTick,last:e.location});
  }catch{}
}
function spawnFragment(dim,type,at,dir,power=1){
  if(trackedFragments.size>=MAX_FRAGMENTS) return;
  try{
    const e=dim.spawnEntity(type,{x:at.x+rnd(-.09,.09),y:at.y+rnd(-.04,.12),z:at.z+rnd(-.09,.09)});
    e.applyImpulse({x:dir.x*rnd(.13,.29)*power+rnd(-.08,.08),y:rnd(.09,.25)*power,z:dir.z*rnd(.13,.29)*power+rnd(-.08,.08)});
    trackedFragments.set(e.id,{e,born:system.currentTick});
  }catch{}
}
function bloodBurst(victim,damage,source,death=false){
  if(!biological(victim)) return;
  const dim=victim.dimension, at=impactPoint(victim,source), dir=direction(victim,source), part=hitPart(victim,at);
  const projectile=!!source?.damagingProjectile || String(source?.cause??"")==="projectile";
  const level=death?3:(damage>=10?3:damage>=5?2:1);
  particle(dim,"dlv:blood_splat",at,dir);
  if(level>=2 || projectile) particle(dim,"dlv:blood_mist",at,dir);
  if(level>=2) particle(dim,"dlv:blood_jet",at,dir);
  if(part==="head" && (level>=2 || death)) particle(dim,"dlv:blood_headshot",at,dir);
  const drops=(death?16:level===3?10:level===2?6:3)+(part==="head"?3:0);
  for(let i=0;i<drops;i++) spawnDrop(dim,at,dir,level*.48);
  const meat=death?8:(level===3?4:level===2?1:0);
  const bone=(death?3:(part==="head"&&level===3?2:level===3?1:0));
  for(let i=0;i<meat;i++) spawnFragment(dim,MEAT,at,dir,death?1.35:1);
  for(let i=0;i<bone;i++) spawnFragment(dim,BONE,at,dir,death?1.2:.9);
  if(level>=2 && Math.random()<(death?.95:.42)) spawnPool(dim,victim.location,death?2.1:1.15);
  lastImpact.set(victim.id,{tick:system.currentTick,at,dir,part,level});
}

world.afterEvents.entityHurt.subscribe(ev=>{
  try{ bloodBurst(ev.hurtEntity,Number(ev.damage)||0,ev.damageSource,false); }catch{}
});
world.afterEvents.entityDie.subscribe(ev=>{
  try{
    const v=ev.deadEntity; if(!biological(v)) return;
    const last=lastImpact.get(v.id);
    if(last && system.currentTick-last.tick<16){
      bloodBurst(v,14,ev.damageSource,true);
    } else bloodBurst(v,10,ev.damageSource,true);
    system.runTimeout(()=>lastImpact.delete(v.id),20);
  }catch{}
});

system.runInterval(()=>{
  const now=system.currentTick;
  for(const[id,r] of [...trackedDrops]){
    try{
      const e=r.e;
      if(!e?.isValid || now-r.born>60){ trackedDrops.delete(id); continue; }
      const loc=e.location, vel=e.getVelocity?.()??{x:0,y:0,z:0};
      const speed=Math.hypot(vel.x,vel.y,vel.z);
      const moved=Math.hypot(loc.x-r.last.x,loc.y-r.last.y,loc.z-r.last.z); r.last={...loc};
      let grounded=false;
      try{ const b=e.dimension.getBlock({x:Math.floor(loc.x),y:Math.floor(loc.y-.06),z:Math.floor(loc.z)}); grounded=!!b&&!b.isAir; }catch{}
      if((grounded&&speed<.18)||(moved<.006&&now-r.born>4)){
        particle(e.dimension,"dlv:blood_splat",{x:loc.x,y:loc.y+.015,z:loc.z},{x:0,y:1,z:0});
        if(Math.random()<.72) spawnPool(e.dimension,loc,rnd(.72,1.3));
        try{e.remove();}catch{} trackedDrops.delete(id);
      }
    }catch{ trackedDrops.delete(id); }
  }
  for(const[id,r] of [...trackedFragments]){
    try{ if(!r.e?.isValid || now-r.born>190) trackedFragments.delete(id); }catch{ trackedFragments.delete(id); }
  }
  while(pools.length && !pools[0]?.isValid) pools.shift();
},1);
