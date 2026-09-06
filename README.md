# CS2-ONLINE

Source-first gameplay integration project for a Minecraft Bedrock Counter-Strike Online 2 remake.

## Included gameplay scope

This repository intentionally contains only the DLavie gameplay systems requested for CS2-ONLINE:

- **DLavie CS2 Gore VFX** — standalone blood particles, physical droplets, pooling, impact fragments, head/torso/leg severity and death burst. It has no terrorist/NPC AI dependency and no HUD override.
- **DLavie Ragdoll Runtime V1.5 integration slot** — imported locally at build time.
- **S7D Parkour DLavie/AG2 compatibility slot** — imported locally at build time.
- **Actual Guns CSO + CSO2 DLC** — supplied locally by the project owner and bundled at build time.

## Explicitly excluded

The build script rejects/does not import these DLavie systems:

- NPC / terrorist AI
- Heist / vault gameplay
- Tactical Flashlight
- DLavie HUD / minimap / PlayerStats integration
- Ballistic block destruction

Actual Guns' own required UI/resources remain untouched because they are part of Actual Guns itself.

## Why Ragdoll/Parkour are not committed here

The supplied Parkour pack contains an `All Rights Reserved` notice prohibiting redistribution/modification without permission, and the supplied Ragdoll Runtime also declares `All Rights Reserved`. To avoid turning this public repository into a re-upload of third-party packs, they stay in `vendor/` locally and are never committed. Their author metadata is preserved byte-for-byte in the final local build.

## Local vendor files

Place these files in `vendor/`:

```text
Actual Guns 1.mcaddon
CSO2 DLC.mcaddon
DLavie_Ragdoll_Runtime_V1.5[BP].mcpack
DLavie_Ragdoll_Runtime_V1.5[RP].mcpack
S7D_Parkour_DLavie_Compat_V1.1.4[BP].mcpack
S7D_Parkour_DLavie_Compat_V1.1.4[RP].mcpack
```

Then run:

```bash
pip install -r requirements.txt
python tools/build_bundle.py
python tools/validate.py
```

Output:

```text
releases/CS2_ONLINE_GAMEPLAY_CORE_V0.1.0.mcaddon
```

## Gameplay architecture

`Actual Guns` remains authoritative for weapons, firing, reload, ammo and its own UI. The Gore module observes Bedrock `entityHurt` / `entityDie` events and therefore does not replace AG2 weapon controllers. Ragdoll and Parkour remain separate packs so their original manifests/provenance can be retained.
