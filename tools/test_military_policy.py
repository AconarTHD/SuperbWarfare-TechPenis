"""Run policy behavior against real Gson without booting Minecraft."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'src/main/java/com/atsuishio/superbwarfare/compat/MilitaryContentPolicy.java'
RESOURCES = ROOT / 'src/main/resources'


class MilitaryPolicyTests(unittest.TestCase):
    def test_prepared_source_resources(self):
        from prepare_military_resources import prepare
        with tempfile.TemporaryDirectory(prefix='military-resources-test-') as directory:
            resources = Path(directory)
            fixtures = {
                'techpenis/military_profile.json': json.loads((RESOURCES / 'techpenis/military_profile.json').read_text()),
                'data/superbwarfare/recipe/ak_47.json': {'result': {'id': 'superbwarfare:ak_47'}},
                'data/superbwarfare/recipe/rpg.json': {'result': {'id': 'superbwarfare:rpg'}},
                'data/superbwarfare/recipe/attachment.json': {'ingredients': [{'tag': 'superbwarfare:attachment'}]},
                'data/superbwarfare/tags/item/blueprint/rare.json': {
                    'values': ['superbwarfare:ak_47_blueprint', 'superbwarfare:rpg_blueprint', '#superbwarfare:blueprint/nested']},
                'data/superbwarfare/sbw/mob_guns/skeleton.json': {
                    'Probability': 1, 'Guns': {'ID': 'superbwarfare:m_79'}},
            }
            for name, value in fixtures.items():
                path = resources / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value), encoding='utf-8')
            prepare(resources)
            def read(name):
                return json.loads((resources / name).read_text())
            self.assertEqual(read('data/superbwarfare/recipe/ak_47.json')['neoforge:conditions'], [{'type': 'neoforge:false'}])
            self.assertNotIn('neoforge:conditions', read('data/superbwarfare/recipe/rpg.json'))
            self.assertIn('neoforge:conditions', read('data/superbwarfare/recipe/attachment.json'))
            self.assertEqual(read('data/superbwarfare/tags/item/blueprint/rare.json')['values'],
                             ['superbwarfare:rpg_blueprint', '#superbwarfare:blueprint/nested'])
            self.assertEqual(read('data/superbwarfare/sbw/mob_guns/skeleton.json')['Probability'], 0)

    def test_content_and_recipe_policy(self):
        self.assertTrue(JAVA.exists(), 'Military policy is not implemented')
        harness = '''import com.atsuishio.superbwarfare.compat.MilitaryContentPolicy;
import com.google.gson.JsonParser;
public class MilitaryPolicyTest {
 static int cases;
 static void check(boolean condition,String name){
  if(!condition)throw new AssertionError(name); cases++; System.out.println("PASS "+name);
 }
 static boolean blocked(String id,String json){return MilitaryContentPolicy.blocksRecipe(id,JsonParser.parseString(json));}
 public static void main(String[] args){
  check(MilitaryContentPolicy.blocksItem("superbwarfare:ak_47"),"SBW rifle disabled");
  check(MilitaryContentPolicy.blocksItem("superbwarfare:rifle_ammo"),"SBW infantry ammo unavailable");
  check(!MilitaryContentPolicy.blocksItem("scguns:advanced_round"),"Scorched ammo preserved");
  for(String id:new String[]{"rpg","javelin","igla_9k38","repair_tool","vehicle_gun","empty_gun","rare_material_pack","ancient_cpu","monitor","tactical_terminal"})
   check(!MilitaryContentPolicy.blocksItem("superbwarfare:"+id),id+" preserved");
  check(blocked("other:rifle","{\\"result\\":{\\"id\\":\\"superbwarfare:ak_47\\"}}"),"foreign recipe cannot supply forbidden rifle");
  check(blocked("superbwarfare:test","{\\"ingredients\\":[{\\"item\\":\\"superbwarfare:iron_action\\"}],\\"result\\":{\\"id\\":\\"minecraft:iron_ingot\\"}}"),"dead SBW ingredient branch removed");
  check(!blocked("other:test","{\\"ingredients\\":[{\\"item\\":\\"superbwarfare:hammer\\"}],\\"result\\":{\\"id\\":\\"minecraft:iron_ingot\\"}}"),"foreign input recipe preserved");
  check(blocked("superbwarfare:ju_87","{\\"type\\":\\"superbwarfare:vehicle_assembling\\"}"),"blocked vehicle recipe removed");
  check(!blocked("superbwarfare:m_1a_2","{\\"result\\":\\"superbwarfare:m_1a_2\\"}"),"retained tank recipe preserved");
  check(blocked("other:batch","{\\"results\\":[{\\"id\\":\\"superbwarfare:rifle_ammo\\"}]}"),"processing recipe outputs filtered");
  check(!blocked("other:unknown","{\\"description\\":\\"superbwarfare:ak_47\\"}"),"unrelated metadata does not disable foreign recipes");
  check(MilitaryContentPolicy.blocksEntity("superbwarfare:prism_tank"),"existing vehicle blacklist retained");
  check(!MilitaryContentPolicy.blocksEntity("superbwarfare:drone"),"drone retained");
  System.out.println(cases+" policy cases passed");
 }
}'''
        with tempfile.TemporaryDirectory(prefix='military-policy-test-') as directory:
            temp = Path(directory)
            test = temp / 'MilitaryPolicyTest.java'
            test.write_text(harness, encoding='utf-8')
            subprocess.run(['javac', '--release', '21', '-proc:none', '-cp', GSON,
                            '-d', str(temp), str(JAVA), str(test)], check=True)
            subprocess.run(['java', '-cp', f'{temp};{RESOURCES};{GSON}', 'MilitaryPolicyTest'], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gson', required=True)
    args, rest = parser.parse_known_args()
    GSON = args.gson
    unittest.main(argv=[__file__, *rest])
