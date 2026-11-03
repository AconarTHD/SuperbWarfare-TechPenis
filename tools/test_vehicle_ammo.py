"""Exercise the actual ammo bridge against small item-handler API doubles."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'src/main/java/com/atsuishio/superbwarfare'


class VehicleAmmoTests(unittest.TestCase):
    def test_optional_narrow_tags(self):
        for kind, expected in [('rifle', ['standard_copper_round', 'advanced_round']),
                               ('heavy', ['krahg_round'])]:
            path = ROOT / f'src/main/resources/data/techpenis/tags/item/vehicle_{kind}_ammo.json'
            self.assertEqual(json.loads(path.read_text()), {
                'replace': False,
                'values': [{'id': f'scguns:{name}', 'required': False} for name in expected],
            })

    def test_inventory_boundaries(self):
        sources = {
            'net/minecraft/resources/ResourceLocation.java': '''package net.minecraft.resources;
public record ResourceLocation(String namespace,String path){
 public static ResourceLocation fromNamespaceAndPath(String n,String p){return new ResourceLocation(n,p);}}
''',
            'net/minecraft/core/registries/Registries.java': '''package net.minecraft.core.registries;
public class Registries {public static final Object ITEM=new Object();}''',
            'net/minecraft/tags/TagKey.java': '''package net.minecraft.tags;
import net.minecraft.resources.ResourceLocation;
public record TagKey<T>(ResourceLocation location){
 public static <T> TagKey<T> create(Object r,ResourceLocation l){return new TagKey<T>(l);}}''',
            'net/minecraft/world/item/Item.java': '''package net.minecraft.world.item;
public class Item {}''',
            'net/minecraft/world/item/ItemStack.java': '''package net.minecraft.world.item;
import net.minecraft.tags.TagKey;
public class ItemStack {
 public static final ItemStack EMPTY=new ItemStack(new Item(),0,"");
 public Item item;public int amount;public String tag;
 public ItemStack(Item item,int amount,String tag){this.item=item;this.amount=amount;this.tag=tag;}
 public boolean isEmpty(){return amount<=0;}public int getCount(){return amount;}
 public Item getItem(){return item;}
 public boolean is(TagKey<Item> key){return tag.equals(key.location().path());}}
''',
            'net/neoforged/neoforge/items/IItemHandler.java': '''package net.neoforged.neoforge.items;
import net.minecraft.world.item.ItemStack;
public interface IItemHandler {int getSlots();ItemStack getStackInSlot(int s);
 ItemStack extractItem(int slot,int amount,boolean simulate);}''',
            'com/atsuishio/superbwarfare/data/gun/Ammo.java': '''package com.atsuishio.superbwarfare.data.gun;
public enum Ammo {RIFLE,HEAVY,HANDGUN,SHOTGUN,SNIPER}''',
            'com/atsuishio/superbwarfare/item/ammo/AmmoSupplierItem.java': '''package com.atsuishio.superbwarfare.item.ammo;
public class AmmoSupplierItem extends net.minecraft.world.item.Item {}''',
            'com/atsuishio/superbwarfare/item/ammo/AmmoBoxItem.java': '''package com.atsuishio.superbwarfare.item.ammo;
public class AmmoBoxItem extends net.minecraft.world.item.Item {}''',
            'VehicleAmmoTest.java': '''import net.minecraft.world.item.*;
import net.neoforged.neoforge.items.IItemHandler;
import com.atsuishio.superbwarfare.data.gun.Ammo;
import com.atsuishio.superbwarfare.item.ammo.*;
import com.atsuishio.superbwarfare.compat.VehicleAmmoCompat;
public class VehicleAmmoTest {
 static int checks;
 static class Inventory implements IItemHandler {
  ItemStack[] stacks;int extracted;boolean denied;int limit=Integer.MAX_VALUE;
  Inventory(ItemStack... stacks){this.stacks=stacks;}
  public int getSlots(){return stacks.length;}
  public ItemStack getStackInSlot(int s){return stacks[s];}
  public ItemStack extractItem(int slot,int amount,boolean simulate){
   if(amount<=0||simulate)throw new AssertionError("invalid extraction");
   if(denied)return ItemStack.EMPTY;
   ItemStack source=stacks[slot];int actual=Math.min(limit,Math.min(source.amount,amount));
   source.amount-=actual;extracted+=actual;return new ItemStack(source.item,actual,source.tag);
  }
 }
 static ItemStack rounds(int n,String tag){return new ItemStack(new Item(),n,"vehicle_"+tag+"_ammo");}
 static int count(IItemHandler h,Ammo a,int original)throws Exception{
  return VehicleAmmoCompat.count(h,a,original);}
 static int consume(IItemHandler h,Ammo a,int request,int original)throws Exception{
  return VehicleAmmoCompat.consume(h,a,request,original);}
 static void eq(int expected,int actual){checks++;if(expected!=actual)throw new AssertionError(expected+" != "+actual);}
 public static void main(String[] args)throws Exception{
  eq(7,count(null,Ammo.RIFLE,7));eq(5,count(new Inventory(rounds(9,"rifle")),null,5));
  eq(0,count(new Inventory(ItemStack.EMPTY),Ammo.RIFLE,0));
  Inventory mixed=new Inventory(rounds(4,"rifle"),rounds(6,"heavy"),rounds(3,"rifle"),new ItemStack(new Item(),8,""));
  eq(12,count(mixed,Ammo.RIFLE,5));eq(11,count(mixed,Ammo.HEAVY,5));
  for(Ammo a:new Ammo[]{Ammo.HANDGUN,Ammo.SHOTGUN,Ammo.SNIPER})eq(5,count(mixed,a,5));
  eq(Integer.MAX_VALUE,count(mixed,Ammo.RIFLE,Integer.MAX_VALUE-2));
  Inventory nativeTagged=new Inventory(new ItemStack(new AmmoSupplierItem(),4,"vehicle_rifle_ammo"),
   new ItemStack(new AmmoBoxItem(),4,"vehicle_rifle_ammo"));
  eq(20,count(nativeTagged,Ammo.RIFLE,20));eq(0,consume(nativeTagged,Ammo.RIFLE,3,0));eq(0,nativeTagged.extracted);
  eq(5,consume(null,Ammo.RIFLE,9,5));eq(2,consume(mixed,null,5,2));
  eq(2,consume(mixed,Ammo.SHOTGUN,5,2));eq(0,mixed.extracted);
  eq(3,consume(mixed,Ammo.RIFLE,3,0));eq(3,mixed.extracted);eq(1,mixed.stacks[0].amount);
  eq(3,mixed.stacks[2].amount);eq(6,mixed.stacks[1].amount);
  eq(5,consume(mixed,Ammo.RIFLE,5,3));eq(5,mixed.extracted);eq(0,mixed.stacks[0].amount);eq(2,mixed.stacks[2].amount);
  eq(6,consume(mixed,Ammo.RIFLE,9,4));eq(7,mixed.extracted);
  eq(9,consume(mixed,Ammo.RIFLE,9,9));eq(30,consume(mixed,Ammo.RIFLE,9,30));eq(7,mixed.extracted);
  eq(0,consume(mixed,Ammo.HEAVY,0,0));eq(0,consume(mixed,Ammo.HEAVY,-3,0));eq(7,mixed.extracted);
  mixed.denied=true;eq(2,consume(mixed,Ammo.HEAVY,5,2));eq(7,mixed.extracted);
  mixed.denied=false;eq(3,consume(mixed,Ammo.HEAVY,3,0));eq(10,mixed.extracted);eq(3,mixed.stacks[1].amount);
  Inventory limited=new Inventory(rounds(9,"heavy"));limited.limit=1;
  eq(3,consume(limited,Ammo.HEAVY,7,2));eq(1,limited.extracted);eq(8,limited.stacks[0].amount);
  System.out.println("VEHICLE_AMMO_PASS checks="+checks);
 }
}''',
        }
        with tempfile.TemporaryDirectory(prefix='vehicle-ammo-tests-') as directory:
            temp = Path(directory)
            files = []
            for name, contents in sources.items():
                path = temp / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents, encoding='utf-8')
                files.append(str(path))
            subprocess.run(['javac', '--release', '21', '-proc:none', '-d', str(temp),
                            str(JAVA / 'compat/VehicleAmmoCompat.java'),
                            *files], check=True)
            subprocess.run(['java', '-cp', str(temp), 'VehicleAmmoTest'], check=True)


if __name__ == '__main__':
    unittest.main()
