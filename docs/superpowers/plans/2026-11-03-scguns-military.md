# Scorched Guns / Superb Warfare military profile

Goal: Scorched supplies infantry firearms; Superb supplies vehicles, military
equipment, explosives and the explicitly retained RPG, Javelin and Igla.
Preserve existing server balance and FPV Curios compatibility.

Design: keep registry IDs and shared vehicle gun machinery for saved-world and
addon compatibility. Import the existing server KubeJS content policy into the
fork; enforce it in built recipe/tag data, a native loot modifier, trade offers,
creative contents and gun activation. Add direct Scorched projectile geometry/damage integration
and narrow tagged Scorched ammunition support for retained vehicle machine guns.
Do not change Scorched turret targeting rules or add new mobs in this change.
User corrected the initial adapter approach: new compatibility changes belong
in the owning SBW/ScGuns sources and must be built from full source. Only the
previously delivered FPV adapter remains, because the installed Drone Warfare
1.0.6 NeoForge sources are unavailable; its public repository is old Forge 1.0.1.

## Tasks and verification

- [x] Pin existing policy: exact disabled IDs/tags, retained launchers, preserved
  server settings; add pure Java policy tests and observe failure before coding.
- [x] Implement content handling and optional damage-type tags; cover recipes from
  other mods, loot, trades, existing disabled guns and preserved vehicle weapons.
- [x] Implement and test vehicle rifle/heavy ammunition count/consume bridge:
  one Scorched round per round; native counters/boxes and damage remain unchanged.
- [x] Implement and test Scorched OBB hits, actual-hit part damage and turret
  projectile vehicle collision. Keep server team/passenger protections intact.
- [x] Compile and package both complete source projects; audit resource policy
  outputs and rerun FPV regression tests. Keep the historical .2 overlay tool
  unchanged, but do not use its output for this source release.
- [x] Review changes and prepare paired client/server artifacts. Production
  installation and managed-file synchronization are deferred; source builds and
  the approved isolated-server check are complete.

Isolated server passed 41 runtime assertions: loading, recipe/research policy,
gun blocking, real rifle/heavy ammo supply, loot filtering, actual vehicle OBB
hits and false-positive rejection. Interactive client combat, component-damage
scenarios, plate protection, trading UI, drone/FPV goggles and reconnect remain
outside that server fixture's coverage.

Ruling: current server config is authoritative for managed gameplay settings;
preserve client options and all existing inventory contents. Do not call static
checks proof of live combat or a guarantee of compatibility with every addon.
