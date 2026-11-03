package com.atsuishio.superbwarfare.compat;

import net.minecraft.world.entity.npc.AbstractVillager;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

/** Covers existing saved villagers as well as newly generated offers. */
@EventBusSubscriber(modid = "superbwarfare")
public final class MilitaryTradeEvents {
    private MilitaryTradeEvents() {}

    @SubscribeEvent
    public static void onInteract(PlayerInteractEvent.EntityInteract event) {
        if (!event.getLevel().isClientSide() && event.getTarget() instanceof AbstractVillager villager) {
            villager.getOffers().removeIf(offer -> MilitaryContentRules.isDisabled(offer.getResult())
                    || MilitaryContentRules.isDisabled(offer.getCostA())
                    || MilitaryContentRules.isDisabled(offer.getCostB()));
        }
    }
}
