"""Dependency-free boundary tests; Minecraft and Curios are small API doubles."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/main/java/com/atsuishio/superbwarfare/mixins/SbwDroneFpvGogglesMixin.java'
RESOURCES = ROOT / 'src/main/resources'


class FpvCuriosTests(unittest.TestCase):
    def test_equipment_lookup(self):
        self.assertTrue(SOURCE.exists(), 'FPV Curios compatibility mixin is missing')
        sources = {
            'net/minecraft/resources/ResourceLocation.java': '''package net.minecraft.resources;
public record ResourceLocation(String value) {
 public static ResourceLocation fromNamespaceAndPath(String n,String p){return new ResourceLocation(n+":"+p);}
}''',
            'net/minecraft/core/registries/BuiltInRegistries.java': '''package net.minecraft.core.registries;
import net.minecraft.resources.ResourceLocation;
public class BuiltInRegistries {
 public static final Registry ITEM=new Registry();
 public static class Registry {public ResourceLocation getKey(Object item){return (ResourceLocation)item;}}
}''',
            'net/minecraft/world/item/ItemStack.java': '''package net.minecraft.world.item;
import net.minecraft.resources.ResourceLocation;
public class ItemStack {
 public static final ItemStack EMPTY=new ItemStack(null);
 private final ResourceLocation item;
 public ItemStack(ResourceLocation item){this.item=item;}
 public boolean isEmpty(){return item==null;}
 public ResourceLocation getItem(){return item;}
}''',
            'net/minecraft/world/entity/player/Player.java': '''package net.minecraft.world.entity.player;
public class Player {}''',
            'top/theillusivec4/curios/api/SlotResult.java': '''package top.theillusivec4.curios.api;
import net.minecraft.world.item.ItemStack;
public record SlotResult(ItemStack stack) {}''',
            'top/theillusivec4/curios/api/CuriosApi.java': '''package top.theillusivec4.curios.api;
import java.util.*;
import net.minecraft.world.item.ItemStack; import net.minecraft.world.entity.player.Player;
public class CuriosApi {
 public static Inventory inventory; public static int calls;
 public static Optional<Inventory> getCuriosInventory(Player p){calls++;return Optional.ofNullable(inventory);}
 public static class Inventory {
  public String slot="fpv_googles"; public ItemStack stack=ItemStack.EMPTY, cosmetic=ItemStack.EMPTY;
  public boolean active=true;
  public List<SlotResult> findCurios(String... identifiers){
   return active&&Arrays.asList(identifiers).contains(slot)&&!stack.isEmpty()?List.of(new SlotResult(stack)):List.of();
  }
 }
}''',
            'org/spongepowered/asm/mixin/Mixin.java': '''package org.spongepowered.asm.mixin;
public @interface Mixin {String[] targets(); boolean remap() default true;}''',
            'org/spongepowered/asm/mixin/Pseudo.java': '''package org.spongepowered.asm.mixin;
public @interface Pseudo {}''',
            'org/spongepowered/asm/mixin/injection/At.java': '''package org.spongepowered.asm.mixin.injection;
public @interface At {String value();}''',
            'org/spongepowered/asm/mixin/injection/Inject.java': '''package org.spongepowered.asm.mixin.injection;
public @interface Inject {String[] method(); At at(); boolean cancellable() default false; boolean remap() default true;}''',
            'org/spongepowered/asm/mixin/injection/callback/CallbackInfoReturnable.java': '''package org.spongepowered.asm.mixin.injection.callback;
public class CallbackInfoReturnable<T> {
 private T value; public boolean cancelled;
 public CallbackInfoReturnable(T value){this.value=value;}
 public T getReturnValue(){return value;}
 public void setReturnValue(T value){this.value=value;cancelled=true;}
}''',
            'FpvLookupTest.java': '''import java.lang.reflect.Method;
import net.minecraft.world.item.ItemStack; import net.minecraft.world.entity.player.Player;
import net.minecraft.resources.ResourceLocation; import top.theillusivec4.curios.api.CuriosApi;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
public class FpvLookupTest {
 static Method method;
 static ItemStack stack(String id){return new ItemStack(new ResourceLocation(id));}
 static void check(String name,Player player,ItemStack original,ItemStack expected) throws Exception {
  var callback=new CallbackInfoReturnable<ItemStack>(original);
  method.invoke(null,player,callback);
  if(callback.getReturnValue()!=expected)throw new AssertionError(name);
  if(callback.cancelled!=(original!=expected))throw new AssertionError(name+" cancellation");
  System.out.println("PASS "+name);
 }
 public static void main(String[] args) throws Exception {
  var type=Class.forName("com.atsuishio.superbwarfare.mixins.SbwDroneFpvGogglesMixin");
  method=type.getDeclaredMethod("techpenis$findFpvGoggles",Player.class,CallbackInfoReturnable.class);
  method.setAccessible(true);
  var player=new Player(); var goggles=stack("sbwdroneconfig:fpv_goggles");
  check("null player",null,ItemStack.EMPTY,ItemStack.EMPTY);
  check("existing helmet preserved",player,goggles,goggles);
  if(CuriosApi.calls!=0)throw new AssertionError("Unnecessary Curios access");
  check("missing inventory",player,ItemStack.EMPTY,ItemStack.EMPTY);
  CuriosApi.inventory=new CuriosApi.Inventory();
  check("empty slot",player,ItemStack.EMPTY,ItemStack.EMPTY);
  CuriosApi.inventory.stack=stack("superbwarfare:thermal_imaging_goggles");
  check("other item rejected",player,ItemStack.EMPTY,ItemStack.EMPTY);
  CuriosApi.inventory.stack=goggles;
  check("FPV slot activates goggles",player,ItemStack.EMPTY,goggles);
  CuriosApi.inventory.slot="head";
  check("other Curios slot ignored",player,ItemStack.EMPTY,ItemStack.EMPTY);
  CuriosApi.inventory.slot="fpv_googles"; CuriosApi.inventory.stack=ItemStack.EMPTY;
  check("removing goggles deactivates",player,ItemStack.EMPTY,ItemStack.EMPTY);
  CuriosApi.inventory.cosmetic=goggles;
  check("cosmetic goggles ignored",player,ItemStack.EMPTY,ItemStack.EMPTY);
  CuriosApi.inventory.stack=goggles; CuriosApi.inventory.active=false;
  check("inactive slot ignored",player,ItemStack.EMPTY,ItemStack.EMPTY);
 }
}''',
        }
        with tempfile.TemporaryDirectory(prefix='fpv-curios-tests-') as directory:
            temp = Path(directory)
            files = []
            for name, contents in sources.items():
                path = temp / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents, encoding='utf-8')
                files.append(str(path))
            subprocess.run(['javac', '--release', '21', '-d', str(temp), str(SOURCE), *files], check=True)
            subprocess.run(['java', '-cp', str(temp), 'FpvLookupTest'], check=True)

    def test_pack_resources(self):
        mixins = json.loads((RESOURCES / 'mixins.superbwarfare.json').read_text())
        self.assertIn('SbwDroneFpvGogglesMixin', mixins['mixins'])
        self.assertNotIn('ClientLevelMixin', mixins['mixins'])
        self.assertIn('ClientLevelMixin', mixins['client'])
        tag = json.loads((RESOURCES / 'data/curios/tags/item/fpv_googles.json').read_text())
        self.assertIn({'id': 'sbwdroneconfig:fpv_goggles', 'required': False}, tag['values'])
        slots = json.loads((RESOURCES / 'data/superbwarfare/curios/entities/fpv_goggles.json').read_text())
        self.assertIn('fpv_googles', slots['slots'])
        self.assertIn('minecraft:player', slots['entities'])


if __name__ == '__main__':
    unittest.main()
