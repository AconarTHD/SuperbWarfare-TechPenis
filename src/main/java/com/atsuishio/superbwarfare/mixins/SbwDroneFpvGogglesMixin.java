package com.atsuishio.superbwarfare.mixins;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import top.theillusivec4.curios.api.CuriosApi;
import top.theillusivec4.curios.api.SlotResult;

@Pseudo
@Mixin(targets = "nl.smartstreamlabs.sbwdroneconfig.SbwCompat", remap = false)
public abstract class SbwDroneFpvGogglesMixin {

    @Inject(method = "getEquippedFpvGoggles(Lnet/minecraft/world/entity/player/Player;)Lnet/minecraft/world/item/ItemStack;",
            at = @At("RETURN"), cancellable = true, remap = false)
    private static void techpenis$findFpvGoggles(Player player, CallbackInfoReturnable<ItemStack> cir) {
        if (player == null || !cir.getReturnValue().isEmpty()) {
            return;
        }

        CuriosApi.getCuriosInventory(player)
                .flatMap(inventory -> inventory.findCurios("fpv_googles").stream()
                        .map(SlotResult::stack)
                        .filter(stack -> !stack.isEmpty()
                        && ResourceLocation.fromNamespaceAndPath("sbwdroneconfig", "fpv_goggles")
                        .equals(BuiltInRegistries.ITEM.getKey(stack.getItem())))
                        .findFirst())
                .ifPresent(cir::setReturnValue);
    }
}
