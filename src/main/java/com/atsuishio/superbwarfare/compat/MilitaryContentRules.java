package com.atsuishio.superbwarfare.compat;

import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import java.util.List;

public final class MilitaryContentRules {
    private static final List<TagKey<Item>> TAGS = MilitaryContentPolicy.ITEM_TAGS.stream()
            .map(id -> TagKey.create(Registries.ITEM, ResourceLocation.parse(id))).toList();

    private MilitaryContentRules() {}

    public static boolean isDisabled(ItemStack stack) {
        if (stack.isEmpty()) return false;
        if (MilitaryContentPolicy.blocksItem(BuiltInRegistries.ITEM.getKey(stack.getItem()).toString())) return true;
        for (TagKey<Item> tag : TAGS) if (stack.is(tag)) return true;
        var data = stack.get(DataComponents.BLOCK_ENTITY_DATA);
        return data != null && MilitaryContentPolicy.blocksEntity(data.copyTag().getString("EntityType"));
    }
}
