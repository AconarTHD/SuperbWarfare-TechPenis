package com.atsuishio.superbwarfare.compat;

import com.atsuishio.superbwarfare.data.gun.Ammo;
import com.atsuishio.superbwarfare.item.ammo.AmmoBoxItem;
import com.atsuishio.superbwarfare.item.ammo.AmmoSupplierItem;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.items.IItemHandler;

/** Optional loose-round supply; native ammo and its surplus accounting run first. */
public final class VehicleAmmoCompat {
    private static final TagKey<Item> RIFLE = TagKey.create(Registries.ITEM,
            ResourceLocation.fromNamespaceAndPath("techpenis", "vehicle_rifle_ammo"));
    private static final TagKey<Item> HEAVY = TagKey.create(Registries.ITEM,
            ResourceLocation.fromNamespaceAndPath("techpenis", "vehicle_heavy_ammo"));

    private VehicleAmmoCompat() {
    }

    private static TagKey<Item> tag(Ammo type) {
        if (type == Ammo.RIFLE) return RIFLE;
        if (type == Ammo.HEAVY) return HEAVY;
        return null;
    }

    private static boolean matches(ItemStack stack, TagKey<Item> tag) {
        return !stack.isEmpty()
                && !(stack.getItem() instanceof AmmoSupplierItem)
                && !(stack.getItem() instanceof AmmoBoxItem)
                && stack.is(tag);
    }

    public static int count(IItemHandler handler, Ammo type, int nativeCount) {
        TagKey<Item> tag = tag(type);
        if (handler == null || tag == null) return nativeCount;

        long total = nativeCount;
        for (int slot = 0; slot < handler.getSlots(); slot++) {
            ItemStack stack = handler.getStackInSlot(slot);
            if (matches(stack, tag)) {
                total += stack.getCount();
                if (total >= Integer.MAX_VALUE) return Integer.MAX_VALUE;
            }
        }
        return (int) total;
    }

    public static int consume(IItemHandler handler, Ammo type, int requested, int nativeConsumed) {
        TagKey<Item> tag = tag(type);
        if (handler == null || tag == null || requested <= 0 || nativeConsumed >= requested) {
            return nativeConsumed;
        }

        int remaining = requested - nativeConsumed;
        int consumed = nativeConsumed;
        for (int slot = 0; slot < handler.getSlots() && remaining > 0; slot++) {
            ItemStack stack = handler.getStackInSlot(slot);
            if (!matches(stack, tag)) continue;

            // Credit the actual extraction, including handlers that refuse extraction.
            ItemStack extracted = handler.extractItem(slot, Math.min(remaining, stack.getCount()), false);
            int amount = extracted.getCount();
            consumed += amount;
            remaining -= amount;
        }
        return consumed;
    }
}
