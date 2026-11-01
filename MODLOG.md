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
