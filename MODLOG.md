# TechPenis FPV Curios compatibility — 2026-11-02

- Upstream: Mercurows/SuperbWarfare, pinned c22d98c232aeb8f6150799e16387ffa09b488681.
- User clarified the exact item: `sbwdroneconfig:fpv_goggles`, from installed
  SBW Drone Warfare 1.0.6, not Superb Warfare's own thermal goggles.
- Existing pack slot: `fpv_googles`, size 1, order 55. Client had its definition
  and icon but no matching item tag/player assignment; server lacked the slot.
- Installed addon bytecode (`javap -c -p`) proves `SbwCompat.getEquippedFpvGoggles`
  reads only `EquipmentSlot.HEAD`. `hasEquippedFpvGoggles` delegates to it;
  `MonitorItem089Mixin` checks that method before monitor activation.
  `FpvGogglesOverlayClient.shouldRender` calls the getter too.
- Route: optional common-side `@Pseudo` Mixin in the requested Superb Warfare
  fork, injecting on return, preserving helmet priority and querying only the
  functional `fpv_googles` slot. No compile/runtime linkage to addon classes.
- Server's existing techpenis.1 differed from original in Mixin JSON alone:
  it removed duplicate ClientLevelMixin from the common list. Preserved here.
- Initial tests failed for missing implementation/registration. After the
  change, both test groups and all ten Java boundary cases passed.
- Verified real Curios implementation: `findFirstCurio(Predicate, String)` uses
  a cache key, not a slot filter. An initial version failed the wrong-slot test
  after correcting the API double. Final code uses `findCurios(String...)`,
  which selects slot identifiers, excludes cosmetics and (Curios 9.5) inactive
  slots. Confirmed signature compatibility with bundled Curios 9.2 too.
- Compiled the new class using Java 21 against real Minecraft/NeoForge APIs and
  the release's bundled Curios 9.2.0 API. Original classes/dependencies remained
  byte-identical; archive verification passed.
- Full upstream Gradle configuration could not resolve moddev plugin 2.0.80
  offline. Used the documented pinned-release overlay build instead.
- No server/client restart or live drone-flight test was performed.

# Full source military integration — 2026-11-04

- User confirmed keeping RPG, Javelin and Igla; Scorched supplies infantry guns.
- User requested direct changes in full source forks. New integration Mixins were
  removed. Only the previously approved FPV addon adapter remains. Drone Warfare
  1.0.6 NeoForge sources were unavailable; public author source is Forge 1.0.1.
- Source changes: native inventory ammunition bridge, gun activation policy,
  native loot modifier, creative/trade policy, optional Scorched damage tags,
  precise vehicle/component hits from Scorched bullets and beams, physical turret
  projectile impacts and online turret owner attribution. Turret AI rules and
  weapon/vehicle damage values remain as configured.
- Imported policy exactly matches current server military_ecosystem.js SHA256.
  It includes 200 item IDs. Source resource preparation disabled 251 recipes and
  removed 241 tag entries; kept launchers and their recipes were checked in JAR.
- Full Gradle source builds passed with JDK 21: SBW .3 and Scorched .11. Existing
  dirty Scorched changes were preserved; targeted snapshots are under build/.
- Boundary tests passed: 22 policy cases + copied-resource assertions, 41 ammo
  cases, 19 actual OBB/context assertions and 10 FPV cases.
- Isolated NeoForge 21.1.264 server with both source builds, Drone 1.0.6 and pack
  dependency/config versions passed all 41 runtime assertions and exited 0.
  Record: build/military-smoke/20261104-041328-0e1372/smoke-result.txt.
  It verified recipes, research tags, blocked gun use, native count/consume, loot
  filtering, actual Scorched vehicle hit routing and rejection of AABB false hits.
- SBW source JAR SHA256: 98cce1b1604fcf1affda81817f26dec56826fccce6f2cb7602045590f6ba5746.
- Scorched source JAR SHA256: 45ab232e4a61d6e8a017ab81173423c8110becd6642246d08a0c20b5d6d18a93.
- Production installation/restart and an interactive client combat/drone check
  have not been performed. No production worlds or running server were changed.
