"""Import the server's existing managed policy; does not write pack files."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ITEM_LISTS = ['SMALL_ARMS', 'INFANTRY_AMMO', 'SMALL_ARMS_BLUEPRINTS',
              'REMOVED_VEHICLE_BLUEPRINTS', 'GUN_SUPPORT_ITEMS', 'JUNK_ITEMS', 'TOOL_CLUTTER']


def generate(script, base):
    text = script.read_text(encoding='utf-8-sig')

    def ids(name):
        match = re.search(r'const TP_SBW_' + name + r'\s*=\s*\[(.*?)\]', text, re.S)
        if not match:
            raise ValueError(f'Missing policy list {name}')
        # Comments must not become policy entries.
        body = re.sub(r'//[^\n]*', '', match[1])
        return set(re.findall(r"['\"](#?superbwarfare:[a-z0-9_./]+)['\"]", body))

    blocked = set().union(*(ids(name) for name in ITEM_LISTS))
    tags = ids('REMOVE_TAGS')
    vehicles = ids('BLOCKED_VEHICLES')
    entities = ids('BLOCKED_ENTITIES') | vehicles
    with zipfile.ZipFile(base) as release:
        visited = set()

        def expand(tag):
            if tag in visited:
                return
            visited.add(tag)
            namespace, name = tag.lstrip('#').split(':', 1)
            path = f'data/{namespace}/tags/item/{name}.json'
            if path not in release.namelist():
                return
            for entry in json.loads(release.read(path))['values']:
                value = entry if isinstance(entry, str) else entry['id']
                if value.startswith('#'):
                    expand(value)
                else:
                    blocked.add(value)

        for tag in tags:
            expand(tag)
    # Pin all registered handheld guns, even if a script list missed a new one.
    items = (ROOT / 'src/main/kotlin/com/atsuishio/superbwarfare/init/ModItems.kt').read_text()
    retained = {'rpg', 'javelin', 'igla_9k38', 'repair_tool', 'vehicle_gun', 'empty_gun'}
    blocked.update('superbwarfare:' + item for item in re.findall(r'registerGun\("([a-z0-9_]+)"', items)
                   if item not in retained)
    profile = {
        'source': 'TechPenis server military_ecosystem.js',
        'source_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
        'blocked_items': sorted(blocked),
        'blocked_item_tags': sorted(tag.lstrip('#') for tag in tags),
        'blocked_entities': sorted(entities),
        'blocked_recipe_ids': sorted(vehicles),
        'retained_launchers': ['superbwarfare:rpg', 'superbwarfare:javelin', 'superbwarfare:igla_9k38'],
    }
    destination = ROOT / 'src/main/resources/techpenis/military_profile.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(profile, indent=2) + '\n', encoding='utf-8')
    print(f'Imported {len(blocked)} item IDs, {len(tags)} tags, {len(entities)} entities')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--script', type=Path, required=True)
    parser.add_argument('--base-jar', type=Path, required=True)
    args = parser.parse_args()
    generate(args.script, args.base_jar)
