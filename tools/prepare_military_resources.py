"""Apply the imported policy to a full source build's copied resources."""
import argparse
import json
from pathlib import Path


def prepare(resources):
    profile = json.loads((resources / 'techpenis/military_profile.json').read_text(encoding='utf-8'))
    blocked = set(profile['blocked_items'])
    tags = set(profile['blocked_item_tags'])

    def forbidden(value):
        if isinstance(value, str):
            return value in blocked or value.startswith('#') and value[1:] in tags
        if isinstance(value, list):
            return any(forbidden(entry) for entry in value)
        if isinstance(value, dict):
            return value.get('tag') in tags or any(forbidden(entry) for entry in value.values())
        return False

    disabled_recipes = 0
    recipe_root = resources / 'data/superbwarfare/recipe'
    for path in recipe_root.rglob('*.json'):
        recipe = json.loads(path.read_text(encoding='utf-8'))
        identifier = 'superbwarfare:' + path.relative_to(recipe_root).with_suffix('').as_posix()
        if forbidden(recipe) or identifier in profile['blocked_recipe_ids']:
            recipe['neoforge:conditions'] = [{'type': 'neoforge:false'}]
            path.write_text(json.dumps(recipe, indent=2) + '\n', encoding='utf-8')
            disabled_recipes += 1
    removed_tag_entries = 0
    for path in (resources / 'data/superbwarfare/tags/item').rglob('*.json'):
        tag = json.loads(path.read_text(encoding='utf-8'))
        values = tag.get('values', [])
        allowed = [entry for entry in values if (entry if isinstance(entry, str) else entry.get('id')) not in blocked]
        if len(allowed) != len(values):
            removed_tag_entries += len(values) - len(allowed)
            tag['values'] = allowed
            path.write_text(json.dumps(tag, indent=2) + '\n', encoding='utf-8')
    for path in (resources / 'data/superbwarfare/sbw/mob_guns').rglob('*.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        if forbidden(data):
            data['Probability'] = 0
            path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(f'Military profile: disabled {disabled_recipes} recipes; removed {removed_tag_entries} tag entries')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('resources', type=Path)
    args = parser.parse_args()
    prepare(args.resources)
