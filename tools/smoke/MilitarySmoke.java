package techpenis.smoke;

import com.atsuishio.superbwarfare.compat.MilitaryContentRules;
import com.atsuishio.superbwarfare.compat.MilitaryLootFilter;
import com.atsuishio.superbwarfare.compat.scguns.ScorchedVehicleHits;
import com.atsuishio.superbwarfare.data.gun.Ammo;
import com.atsuishio.superbwarfare.data.gun.GunData;
import com.atsuishio.superbwarfare.entity.vehicle.base.VehicleEntity;
import com.atsuishio.superbwarfare.tools.InventoryTool;
import com.atsuishio.superbwarfare.tools.OBB;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.predicates.LootItemCondition;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.items.ItemStackHandler;
import top.ribs.scguns.compat.SuperbWarfareCompat;
import top.ribs.scguns.entity.projectile.ProjectileEntity;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** Temporary isolated-server fixture. This class is never added to production jars. */
@Mod("techpenis_military_smoke")
public final class MilitarySmoke {
    private int checks;

    public MilitarySmoke() {
        NeoForge.EVENT_BUS.addListener(this::started);
    }

    private static ResourceLocation id(String value) {
        return ResourceLocation.parse(value);
    }

    private static ItemStack stack(String value, int count) {
        Item item = BuiltInRegistries.ITEM.get(id(value));
        if (item == net.minecraft.world.item.Items.AIR) throw new AssertionError("Missing item " + value);
        return new ItemStack(item, count);
    }

    private void check(String name, boolean value) {
        if (!value) throw new AssertionError(name);
        checks++;
        System.out.println("MILITARY_SMOKE_CHECK PASS " + name);
    }

    private void started(ServerStartedEvent event) {
        MinecraftServer server = event.getServer();
        String result;
        try {
            content(server);
            ammo();
            loot();
            vehicleHit(server);
            result = "MILITARY_SMOKE_PASS checks=" + checks;
        } catch (Throwable failure) {
            failure.printStackTrace();
            result = "MILITARY_SMOKE_FAIL checks=" + checks + " cause=" + failure;
        }
        System.out.println(result);
        try {
            Files.writeString(Path.of("smoke-result.txt"), result + System.lineSeparator(), StandardCharsets.UTF_8);
        } catch (Exception failure) {
            failure.printStackTrace();
        } finally {
            server.halt(false);
        }
    }

    private void content(MinecraftServer server) {
        var recipes = server.getRecipeManager();
        check("disabled AK recipe absent", recipes.byKey(id("superbwarfare:ak_47_smithing")).isEmpty());
        ItemStack ak = stack("superbwarfare:ak_47", 1);
        check("disabled AK item classifier", MilitaryContentRules.isDisabled(ak));
        check("blocked gun cannot shoot", !GunData.from(ak).canShoot(null));
        for (String launcher : new String[]{"rpg", "javelin", "igla_9k38"}) {
            check("retained " + launcher + " item", !MilitaryContentRules.isDisabled(stack("superbwarfare:" + launcher, 1)));
            check("retained " + launcher + " smithing", recipes.byKey(id("superbwarfare:" + launcher + "_smithing")).isPresent());
        }
        ItemStack blueprint = stack("superbwarfare:ak_47_blueprint", 1);
        for (String tier : new String[]{"common", "rare", "epic", "legendary", "superb", "virtual", "cannon",
                "enlarged/common", "enlarged/rare", "enlarged/epic", "enlarged/legendary"}) {
            TagKey<Item> tag = TagKey.create(Registries.ITEM, id("superbwarfare:blueprint/" + tier));
            check("research tag excludes AK " + tier, !blueprint.is(tag));
        }
        check("trade classifier rejects disabled ammo", MilitaryContentRules.isDisabled(stack("superbwarfare:rifle_ammo", 1)));
        check("trade classifier rejects disabled blueprint", MilitaryContentRules.isDisabled(blueprint));
    }

    private void ammo() {
        ItemStackHandler inventory = new ItemStackHandler(3);
        inventory.setStackInSlot(0, stack("scguns:advanced_round", 7));
        inventory.setStackInSlot(1, stack("scguns:krahg_round", 4));
        inventory.setStackInSlot(2, stack("scguns:standard_copper_round", 3));
        check("real rifle count", InventoryTool.countAmmoItem(inventory, Ammo.RIFLE) == 10);
        check("real heavy count", InventoryTool.countAmmoItem(inventory, Ammo.HEAVY) == 4);
        check("handgun supply unchanged", InventoryTool.countAmmoItem(inventory, Ammo.HANDGUN) == 0);
        check("real rifle consume", InventoryTool.consumeAmmoItem(inventory, Ammo.RIFLE, 8) == 8);
        check("real rifle remaining", InventoryTool.countAmmoItem(inventory, Ammo.RIFLE) == 2);
        check("heavy unchanged after rifle", inventory.getStackInSlot(1).getCount() == 4);
        check("real heavy partial supply", InventoryTool.consumeAmmoItem(inventory, Ammo.HEAVY, 6) == 4);
        check("real heavy exhausted", inventory.getStackInSlot(1).isEmpty());
        check("remaining rifle untouched", InventoryTool.countAmmoItem(inventory, Ammo.RIFLE) == 2);
        check("zero request unchanged", InventoryTool.consumeAmmoItem(inventory, Ammo.RIFLE, 0) == 0
                && InventoryTool.countAmmoItem(inventory, Ammo.RIFLE) == 2);
    }

    private void loot() throws Exception {
        ObjectArrayList<ItemStack> contents = new ObjectArrayList<>();
        contents.add(stack("superbwarfare:ak_47", 1));
        contents.add(stack("superbwarfare:rifle_ammo", 1));
        contents.add(stack("superbwarfare:rpg", 1));
        contents.add(stack("scguns:advanced_round", 1));
        // Exercise the real classifier/filter implementation without inventing a chest context.
        var method = MilitaryLootFilter.class.getDeclaredMethod("doApply", ObjectArrayList.class, LootContext.class);
        method.setAccessible(true);
        method.invoke(new MilitaryLootFilter(new LootItemCondition[0]), contents, null);
        check("actual loot filter removes disabled items", contents.size() == 2
                && contents.stream().noneMatch(MilitaryContentRules::isDisabled));
        check("actual loot filter preserves launcher and SG ammo", contents.get(0).is(stack("superbwarfare:rpg", 1).getItem())
                && contents.get(1).is(stack("scguns:advanced_round", 1).getItem()));
    }

    private void vehicleHit(MinecraftServer server) {
        var level = server.overworld();
        var entity = BuiltInRegistries.ENTITY_TYPE.get(id("superbwarfare:lav_150")).create(level);
        check("fresh LAV instance", entity instanceof VehicleEntity);
        VehicleEntity vehicle = (VehicleEntity) entity;
        vehicle.setPos(0, 80, 0);
        vehicle.updateOBB();
        check("optional SG wrapper active", SuperbWarfareCompat.isVehicle(vehicle)
                && SuperbWarfareCompat.hasPreciseHitbox(vehicle));
        OBB box = vehicle.getOBBs().stream().filter(value -> value.part != OBB.Part.COLLISION).findFirst().orElseThrow();
        Vec3 center = new Vec3(box.center.x, box.center.y, box.center.z);
        Vec3 from = center.add(-100, 0, 0);
        Vec3 to = center.add(100, 0, 0);
        var expected = ScorchedVehicleHits.clip(vehicle.getOBBs(), from, to);
        check("real vehicle OBB ray intersects", expected != null);
        var projectile = (ProjectileEntity) BuiltInRegistries.ENTITY_TYPE.get(id("scguns:projectile")).create(level);
        check("fresh SG projectile instance", projectile != null);
        var actual = projectile.getHitResult(vehicle, from, to);
        check("actual SG getHitResult routes through OBB", actual != null && actual.getEntity() == vehicle
                && actual.getHitPos().distanceToSqr(expected.position()) < 1.0e-10);
        // A deliberate broad AABB false positive proves getHitResult uses OBB geometry.
        vehicle.setBoundingBox(new AABB(-2000, -2000, -2000, 2000, 2000, 2000));
        Vec3 missFrom = new Vec3(3000, 1000, 0);
        Vec3 missTo = new Vec3(0, 1000, 0);
        check("false-positive AABB probe intersects", vehicle.getBoundingBox().clip(missFrom, missTo).isPresent());
        check("actual SG OBB miss rejects AABB false positive", projectile.getHitResult(vehicle, missFrom, missTo) == null);
        projectile.discard();
        vehicle.discard();
    }
}
