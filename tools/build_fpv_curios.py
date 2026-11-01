"""Compile the compatibility class and overlay the pinned upstream release.

No downloads or changes to the upstream classes/bundled dependencies are needed.
The ordinary Gradle build also includes these same source/resource changes.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.8.9.2-techpenis.2'
BASE_SHA256 = 'c06b4da8258adbc7d623c5c8e36ffc642c28831ddf6c9aa9c05c10dd18997490'
MIXIN = 'com/atsuishio/superbwarfare/mixins/SbwDroneFpvGogglesMixin'
RESOURCES = [
    'mixins.superbwarfare.json',
    'data/curios/tags/item/fpv_googles.json',
    'data/superbwarfare/curios/entities/fpv_goggles.json',
    'data/techpenis/curios/slots/fpv_googles.json',
    'assets/techpenis/textures/slot/empty_fpv_googles_slot.png',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-jar', type=Path, required=True)
    parser.add_argument('--classpath', required=True, help=f'Java 21 compile classpath, separated by {os.pathsep!r}')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/release/superbwarfare-0.8.9.2-techpenis.2-mc1.21.1.jar')
    args = parser.parse_args()
    if args.base_jar.resolve() == args.output.resolve() or args.output.exists():
        parser.error('Output must be a new file, separate from the base JAR')
    if hashlib.sha256(args.base_jar.read_bytes()).hexdigest() != BASE_SHA256:
        parser.error('Base SHA256 does not match the pinned c22d98c2 release')
    with zipfile.ZipFile(args.base_jar) as original:
        metadata = original.read('META-INF/neoforge.mods.toml').decode()
        if 'version = "0.8.9.2"' not in metadata:
            parser.error('Expected the 0.8.9.2 mc1.21.1 c22d98c2 release')
        if original.testzip() is not None:
            parser.error('Corrupt base JAR')
        additions = {name: (ROOT / 'src/main/resources' / name).read_bytes() for name in RESOURCES}
        additions['META-INF/neoforge.mods.toml'] = metadata.replace(
            'version = "0.8.9.2"', f'version = "{VERSION}"', 1).encode()
        with tempfile.TemporaryDirectory(prefix='fpv-curios-build-') as directory:
            subprocess.run(['javac', '--release', '21', '-proc:none', '-encoding', 'UTF-8',
                            '-classpath', args.classpath, '-d', directory,
                            str(ROOT / 'src/main/java' / f'{MIXIN}.java')], check=True)
            additions[f'{MIXIN}.class'] = (Path(directory) / f'{MIXIN}.class').read_bytes()
        additions['META-INF/techpenis-fpv-curios.json'] = json.dumps({
            'version': VERSION,
            'upstream_commit': 'c22d98c232aeb8f6150799e16387ffa09b488681',
            'base_sha256': hashlib.sha256(args.base_jar.read_bytes()).hexdigest(),
            'compatibility': 'SBW Drone Warfare 1.0.6; Curios fpv_googles',
        }, indent=2).encode()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.output, 'x', compression=zipfile.ZIP_DEFLATED) as output:
            for entry in original.infolist():
                if entry.filename not in additions:
                    output.writestr(copy.copy(entry), original.read(entry.filename))
            for name, contents in additions.items():
                entry = zipfile.ZipInfo(name, (2026, 11, 2, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                output.writestr(entry, contents)
        with zipfile.ZipFile(args.output) as output:
            assert output.testzip() is None
            changed = {name for name in original.namelist() if original.read(name) != output.read(name)}
            assert changed == {'mixins.superbwarfare.json', 'META-INF/neoforge.mods.toml'}, changed
        print(f'Built {args.output}')
        print(f'SHA256 {hashlib.sha256(args.output.read_bytes()).hexdigest()}')
        print('Verified: all original classes and bundled dependencies are byte-identical')


if __name__ == '__main__':
    main()
