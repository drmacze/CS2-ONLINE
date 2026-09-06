from pathlib import Path
import json, zipfile, shutil, hashlib, sys

ROOT=Path(__file__).resolve().parents[1]
VENDOR=ROOT/'vendor'; RELEASES=ROOT/'releases'
OUT=RELEASES/'CS2_ONLINE_GAMEPLAY_CORE_V0.1.0.mcaddon'
REQUIRED=[
 'Actual Guns 1.mcaddon','CSO2 DLC.mcaddon',
 'DLavie_Ragdoll_Runtime_V1.5[BP].mcpack','DLavie_Ragdoll_Runtime_V1.5[RP].mcpack',
 'S7D_Parkour_DLavie_Compat_V1.1.4[BP].mcpack','S7D_Parkour_DLavie_Compat_V1.1.4[RP].mcpack'
]
BANNED=('Terrorist','Heist','Flashlight','Tactical','Minimap','Block_Physics')

def pack_dir(src:Path, out:Path):
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(src.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(src).as_posix())

def nested_from_mcaddon(path:Path):
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.lower().endswith('.mcpack') and not any(x.lower() in n.lower() for x in BANNED):
                yield Path(n).name,z.read(n)

def main():
    import subprocess, sys
    subprocess.run([sys.executable, str(ROOT/'tools'/'generate_gore_pack.py')], check=True)
    missing=[x for x in REQUIRED if not (VENDOR/x).exists()]
    if missing: raise SystemExit('Missing vendor files: '+', '.join(missing))
    RELEASES.mkdir(exist_ok=True)
    gore_bp=RELEASES/'DLavie_CS2_Gore_V1.0[BP].mcpack'; gore_rp=RELEASES/'DLavie_CS2_Gore_V1.0[RP].mcpack'
    pack_dir(ROOT/'src'/'gore_bp',gore_bp); pack_dir(ROOT/'src'/'gore_rp',gore_rp)
    entries=[]
    for base in ('Actual Guns 1.mcaddon','CSO2 DLC.mcaddon'):
        entries.extend(nested_from_mcaddon(VENDOR/base))
    for name in REQUIRED[2:]: entries.append((name,(VENDOR/name).read_bytes()))
    entries.extend([(gore_bp.name,gore_bp.read_bytes()),(gore_rp.name,gore_rp.read_bytes())])
    names=[n for n,_ in entries]
    if len(names)!=len(set(names)): raise SystemExit('Duplicate nested pack names')
    if any(any(x.lower() in n.lower() for x in BANNED) for n in names): raise SystemExit('Banned module leaked into build')
    with zipfile.ZipFile(OUT,'w',zipfile.ZIP_STORED) as z:
        for n,b in entries: z.writestr(n,b)
    print(OUT)
    print('nested packs:',len(entries))
    print('sha256:',hashlib.sha256(OUT.read_bytes()).hexdigest())
if __name__=='__main__': main()
