"""Compile the optional bridge and exercise real SBW geometry and impact lifetime.

Pass a classpath file containing Minecraft/NeoForge, installed SCG/SBW, JOML,
Kotlin and SBW's runtime dependencies. No game or world is started.
"""
import argparse
import pathlib
import subprocess


HARNESS = r"""
package com.atsuishio.superbwarfare.compat.scguns;

import com.atsuishio.superbwarfare.tools.OBB;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaterniond;
import org.joml.Vector3d;
import java.util.List;

public final class ScorchedGeometryTest {
    static int checks;
    static void check(boolean value, String message) {
        checks++;
        if (!value) throw new AssertionError(message);
    }
    static OBB box(double x, double z, OBB.Part part) {
        return new OBB(new Vector3d(x, 0, z), new Vector3d(1, 1, 1), new Quaterniond(), part);
    }
    public static void main(String[] args) {
        Vec3 start = new Vec3(0, 0, 0), end = new Vec3(20, 0, 0);
        OBB near = box(4, 0, OBB.Part.WHEEL_LEFT);
        OBB far = box(10, 0, OBB.Part.TURRET);
        var hit = ScorchedVehicleHits.clip(List.of(far, near), start, end);
        check(hit.part() == OBB.Part.WHEEL_LEFT, "nearest part, independent of list order");
        check(Math.abs(hit.position().x - 3) < 1e-9, "real OBB entry coordinate");
        check(ScorchedVehicleHits.clip(List.of(near), start, hit.position()).part() == OBB.Part.WHEEL_LEFT,
                "beam scope recomputes the part with ray ending exactly at impact");
        check(ScorchedVehicleHits.clip(List.of(near, far), start, end).part() == hit.part(), "reversed candidates");
        check(ScorchedVehicleHits.clip(List.of(far), start, end).part() == OBB.Part.TURRET, "second query has its own part");
        check(ScorchedVehicleHits.clip(List.of(near), start, new Vec3(2, 0, 0)) == null,
                "block-truncated ray cannot reach vehicle");
        check(ScorchedVehicleHits.clip(List.of(box(3, 0, OBB.Part.COLLISION), far), start, end).part() == OBB.Part.TURRET,
                "collision-only box is not a damage part");
        check(ScorchedVehicleHits.clip(List.of(near), new Vec3(4, 0, 0), end).position().x == 4, "ray starts inside");
        OBB rotated = new OBB(new Vector3d(5, 0, 0), new Vector3d(3, 1, .25),
                new Quaterniond().rotateY(Math.PI / 4), OBB.Part.MAIN_ENGINE);
        check(ScorchedVehicleHits.clip(List.of(rotated), new Vec3(0, 0, 2), new Vec3(10, 0, 2)) != null,
                "rotated long hull extends beyond unrotated width");
        check(ScorchedVehicleHits.clip(List.of(rotated), new Vec3(6.8, 0, 2), new Vec3(7.2, 0, 2)) == null,
                "empty corner of rotated AABB is not a hit");

        Object projectile = new Object(), target = new Object(), other = new Object();
        check(ScorchedVehicleHits.currentPart(projectile, target) == null, "no initial damage context");
        try (var scope = ScorchedVehicleHits.openImpact(projectile, target, hit.part())) {
            check(ScorchedVehicleHits.currentPart(projectile, target) == OBB.Part.WHEEL_LEFT, "selected impact only");
            ScorchedVehicleHits.clip(List.of(far), start, end);
            check(ScorchedVehicleHits.currentPart(projectile, target) == OBB.Part.WHEEL_LEFT, "probing another candidate cannot overwrite damage part");
            check(ScorchedVehicleHits.currentPart(projectile, other) == null, "splash/other target gets no component damage");
            check(ScorchedVehicleHits.currentPart(other, target) == null, "other projectile gets no component damage");
            try (var nested = ScorchedVehicleHits.openImpact(projectile, other, OBB.Part.TURRET)) {
                check(ScorchedVehicleHits.currentPart(projectile, target) == null, "nested impact hides previous target");
            }
            check(ScorchedVehicleHits.currentPart(projectile, target) == OBB.Part.WHEEL_LEFT, "nested impact restores current target");
        }
        check(ScorchedVehicleHits.currentPart(projectile, target) == null, "no stale damage after impact");
        try (var scope = ScorchedVehicleHits.openImpact(null, target, OBB.Part.MAIN_ENGINE)) {
            check(ScorchedVehicleHits.currentPart(null, target) == OBB.Part.MAIN_ENGINE,
                    "beam null direct source still routes its selected target part");
        }
        check(ScorchedVehicleHits.currentPart(null, target) == null, "beam leaves no stale null-source damage context");
        try {
            try (var scope = ScorchedVehicleHits.openImpact(projectile, target, OBB.Part.TURRET)) {
                throw new IllegalStateException("simulated impact exception");
            }
        } catch (IllegalStateException expected) { }
        check(ScorchedVehicleHits.currentPart(projectile, target) == null, "exception cannot retain damage context");
        try (var scope = ScorchedVehicleHits.openImpact(projectile, target, null)) {
            check(ScorchedVehicleHits.currentPart(projectile, target) == null, "nonvehicle/miss has no component damage");
        }
        System.out.println("PASS: " + checks + " real OBB and impact-lifetime assertions");
    }
}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--classpath-file", required=True, type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("build/compat-scguns-test/run"))
    args = parser.parse_args()
    root = pathlib.Path(__file__).resolve().parents[1]
    cp = args.classpath_file.read_text(encoding="utf-8-sig").strip()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    harness = output / "ScorchedGeometryTest.java"
    harness.write_text(HARNESS, encoding="utf-8")
    sources = sorted((root / "src/main/java/com/atsuishio/superbwarfare/compat/scguns").glob("*.java"))
    subprocess.run(["javac", "-proc:none", "-encoding", "UTF-8", "-classpath", cp,
                    "-d", str(output), *map(str, sources), str(harness)], check=True)
    subprocess.run(["java", "-cp", str(output) + ";" + cp,
                    "com.atsuishio.superbwarfare.compat.scguns.ScorchedGeometryTest"], check=True)


if __name__ == "__main__":
    main()
