package com.atsuishio.superbwarfare.compat;

import com.atsuishio.superbwarfare.init.ModLootModifier;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.predicates.LootItemCondition;
import net.neoforged.neoforge.common.loot.IGlobalLootModifier;
import net.neoforged.neoforge.common.loot.LootModifier;

/** Native loot-modifier registration, after this mod's loot additions. */
public final class MilitaryLootFilter extends LootModifier {
    public static final MapCodec<MilitaryLootFilter> CODEC = RecordCodecBuilder.mapCodec(
            instance -> codecStart(instance).apply(instance, MilitaryLootFilter::new));

    public MilitaryLootFilter(LootItemCondition[] conditions) { super(conditions); }

    @Override
    protected ObjectArrayList<ItemStack> doApply(ObjectArrayList<ItemStack> loot, LootContext context) {
        loot.removeIf(MilitaryContentRules::isDisabled);
        return loot;
    }

    @Override
    public MapCodec<? extends IGlobalLootModifier> codec() { return ModLootModifier.MILITARY_LOOT_FILTER.get(); }
}
