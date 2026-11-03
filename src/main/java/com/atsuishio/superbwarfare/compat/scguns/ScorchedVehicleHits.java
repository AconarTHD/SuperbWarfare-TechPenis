package com.atsuishio.superbwarfare.compat.scguns;

import com.atsuishio.superbwarfare.entity.vehicle.base.VehicleEntity;
import com.atsuishio.superbwarfare.tools.OBB;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3d;

import java.util.List;

/** Geometry and impact-scoped component routing; probing candidates never changes impact state. */
public final class ScorchedVehicleHits {
    private ScorchedVehicleHits() {}

    public record Hit(Vec3 position, OBB.Part part) {}
    private record Impact(Object projectile, Object target, OBB.Part part) {}
    private static final ThreadLocal<Impact> IMPACT = new ThreadLocal<>();
    public interface ImpactScope extends AutoCloseable {
        @Override void close();
    }

    public static Hit clip(List<OBB> boxes, Vec3 start, Vec3 end) {
        Hit nearest = null;
        double distance = Double.POSITIVE_INFINITY;
        for (OBB box : boxes) {
            if (box.part == OBB.Part.COLLISION) continue;
            Vector3d intersection = box.contains(start)
                    ? new Vector3d(start.x, start.y, start.z)
                    : box.clip(new Vector3d(start.x, start.y, start.z),
                            new Vector3d(end.x, end.y, end.z)).orElse(null);
            if (intersection == null) continue;
            Vec3 point = new Vec3(intersection.x, intersection.y, intersection.z);
            double candidateDistance = start.distanceToSqr(point);
            if (candidateDistance < distance) {
                distance = candidateDistance;
                nearest = new Hit(point, box.part);
            }
        }
        return nearest;
    }

    public static boolean sameVehicle(Entity shooter, Entity target) {
        return shooter != null && (shooter == target ||
                shooter.getVehicle() != null && shooter.getRootVehicle() == target.getRootVehicle());
    }

    public static ImpactScope beginImpact(Entity projectile, Entity target, Vec3 start, Vec3 end) {
        OBB.Part part = null;
        if (target instanceof VehicleEntity vehicle && !vehicle.enableAABB()) {
            Hit hit = clip(vehicle.getOBBs(), start, end);
            if (hit != null) part = hit.part();
        }
        return openImpact(projectile, target, part);
    }

    static ImpactScope openImpact(Object projectile, Object target, OBB.Part part) {
        Impact previous = IMPACT.get();
        IMPACT.set(new Impact(projectile, target, part));
        return () -> {
            if (previous == null) IMPACT.remove();
            else IMPACT.set(previous);
        };
    }

    static OBB.Part currentPart(Object projectile, Object target) {
        Impact hit = IMPACT.get();
        return hit != null && hit.projectile() == projectile && hit.target() == target ? hit.part() : null;
    }

    public static void damageComponent(VehicleEntity vehicle, DamageSource source, float damage) {
        OBB.Part part = currentPart(source.getDirectEntity(), vehicle);
        if (part == null) return;
        switch (part) {
            case TURRET -> vehicle.setTurretHealth(vehicle.getTurretHealth() - damage);
            case WHEEL_LEFT -> vehicle.setLeftWheelHealth(vehicle.getLeftWheelHealth() - damage);
            case WHEEL_RIGHT -> vehicle.setRightWheelHealth(vehicle.getRightWheelHealth() - damage);
            case MAIN_ENGINE -> vehicle.setMainEngineHealth(vehicle.getMainEngineHealth() - damage);
            case SUB_ENGINE -> vehicle.setSubEngineHealth(vehicle.getSubEngineHealth() - damage);
            default -> { }
        }
    }
}
