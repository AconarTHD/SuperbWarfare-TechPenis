# Superb Warfare — TechPenis

Based on [Mercurows/SuperbWarfare](https://github.com/Mercurows/SuperbWarfare),
Minecraft 1.21.1 / NeoForge, upstream commit
`c22d98c232aeb8f6150799e16387ffa09b488681` (0.8.9.2).
Upstream authors and licensing are retained in `COPYING` and `COPYING.LESSER`.

## 0.8.9.2-techpenis.2

Adds support for **SBW Drone Warfare 1.0.6** goggles
`sbwdroneconfig:fpv_goggles` in the pack's Curios slot **`fpv_googles`**.
The spelling is intentional: it matches the existing pack slot.

The addon normally checks only the helmet slot. An optional common-side Mixin
extends `SbwCompat.getEquippedFpvGoggles(Player)` with a lookup in the functional
Curios slot. This covers both the server's monitor-use requirement and the
client's FPV overlay. Helmet goggles retain priority. Ordinary inventory items,
other Curios slots and cosmetic slots do not activate the goggles. Removing the
goggles causes the next equipment query to return empty.

Includes the slot definition, player assignment, slot icon and optional item tag.
The addon remains optional: `@Pseudo` skips its absent target, and the optional
tag entry does not require its item. This change does not add a third-person
Curios renderer for the goggles.

Retains the pack's `techpenis.1` dedicated-server fix: `ClientLevelMixin` is
registered only in the client list.

Install the same fork JAR on client and server, replacing the previous Superb
Warfare JAR, then restart both. Keep SBW Drone Warfare and Curios installed.
Bind a drone to a monitor as usual, equip goggles in `fpv_googles`, then use the
monitor. Existing head-slot use is still supported.

## Build and checks

The ordinary upstream Gradle build includes all changes. An additional offline
packaging route avoids rebuilding unrelated Kotlin code and resolving all of
upstream's optional development dependencies:

```text
python tools/test_fpv_curios.py
python tools/build_fpv_curios.py --base-jar <upstream-release.jar> --classpath <compile-classpath>
```

Requires Python 3 and JDK 21 (`java` and `javac` on PATH). Supply a platform-
separated Java classpath containing mapped Minecraft 1.21.1, NeoForge, Curios
9.2.0+1.21.1 or compatible, Mixin, DataFixerUpper and Guava. The base must be
the original `superbwarfare-0.8.9.2-mc1.21.1-c22d98c2.jar`, SHA256
`c06b4da8258adbc7d623c5c8e36ffc642c28831ddf6c9aa9c05c10dd18997490`.

The packaging script compiles the new Java class against real APIs, preserves
every original class and bundled dependency byte-for-byte, changes the Mixin
configuration and mod version, and adds the compatibility resources. It checks
archive integrity and records provenance in `META-INF/techpenis-fpv-curios.json`.
It refuses to overwrite the base or an existing output.

The tests exercise the real injection method with isolated Minecraft/Curios API
doubles: null player, helmet priority, absent inventory, empty slot, wrong item,
equipped FPV goggles, wrong slot, removal, cosmetic goggles and inactive slots.
Resource checks cover registration,
player slot assignment and the optional item tag. These checks do not establish
that Mixin weaving or an actual drone flight succeeds in the running game.

Authored with assistance from OpenAI Codex.
