"""Prepare an isolated military integration server; launch only with explicit --run.

Only selected mod/config files are copied. Production libraries are read through a
directory junction; production saves, mods, and running processes are untouched.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'build/military-smoke'
MAIN = Path(r'D:\Minecraft Server\TechPenis-Server')
DEFAULT_SBW = ROOT / 'build/libs/superbwarfare-0.8.9.2-techpenis.3-mc1.21.1.jar'
DEFAULT_SCGUNS = ROOT.parent / 'scorched-guns-techpenis/build/libs/ScorchedGuns-TechPenis-1.5-techpenis.11.jar'
DEPENDENCIES = ['kotlinforforge-*.jar', 'curios-neoforge-*.jar', 'geckolib-neoforge-*.jar',
                'framework-neoforge-*.jar', 'create-1.21.1-*.jar', 'SBW-Drone-Warfare-*.jar', 'rhino-*.jar']
CONFIGS = ['superbwarfare-common.toml', 'superbwarfare-server.toml',
           'scguns-common.toml', 'scguns-server.toml', 'sbwdroneconfig-common.toml']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_directory(value):
    directory = value.resolve()
    directory.relative_to(RUNS.resolve())
    if directory == RUNS.resolve():
        raise ValueError('Use a dedicated child directory under build/military-smoke')
    return directory


def junction(path, target):
    target = target.resolve(strict=True)
    if path.exists():
        if path.resolve() != target:
            raise ValueError(f'Unexpected libraries junction target: {path.resolve()}')
        return
    if os.name == 'nt':
        # Native PowerShell creates only this junction; no shell deletion/moving.
        quote = lambda text: "'" + str(text).replace("'", "''") + "'"
        command = f'New-Item -ItemType Junction -Path {quote(path)} -Target {quote(target)} | Out-Null'
        subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', command], check=True)
    else:
        path.symlink_to(target, target_is_directory=True)


def copy(source, destination, manifest):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    manifest.append({'source': str(source.resolve()), 'destination': str(destination), 'sha256': digest(destination)})


def prepare(args):
    directory = checked_directory(args.directory or RUNS / (
        datetime.now().strftime('%Y%m%d-%H%M%S-') + secrets.token_hex(3)))
    directory.mkdir(parents=True, exist_ok=True)
    if any((directory / name).is_symlink() for name in ['mods', 'config', 'defaultconfigs', 'smoke-world']):
        raise ValueError('Smoke output directories must not be links')
    junction(directory / 'libraries', args.main / 'libraries')
    manifest = []
    for pattern in DEPENDENCIES:
        matches = list((args.main / 'mods').glob(pattern))
        if len(matches) != 1:
            raise ValueError(f'Expected exactly one installed dependency {pattern}: {matches}')
        copy(matches[0], directory / 'mods' / matches[0].name, manifest)
    for name in CONFIGS:
        source = args.main / 'config' / name
        if source.exists():
            copy(source, directory / 'config' / name, manifest)
            if name.endswith('-server.toml'):
                copy(source, directory / 'defaultconfigs' / name, manifest)
    missing = []
    for artifact in [args.sbw_jar, args.scguns_jar]:
        if artifact.exists():
            copy(artifact, directory / 'mods' / artifact.name, manifest)
        else:
            missing.append(str(artifact))
    expected_mods = {Path(entry['destination']).name for entry in manifest
                     if Path(entry['destination']).parent == directory / 'mods'}
    unexpected_mods = {path.name for path in (directory / 'mods').glob('*.jar')} - expected_mods - {
        'techpenis-military-smoke-fixture.jar'}
    if unexpected_mods:
        raise ValueError(f'Unexpected staged mods {sorted(unexpected_mods)}; prepare a new directory')
    with socket.socket() as port_socket:
        port_socket.bind(('127.0.0.1', 0))
        port = port_socket.getsockname()[1]
    (directory / 'eula.txt').write_text('eula=true\n', encoding='utf-8')
    (directory / 'server.properties').write_text(
        f'server-ip=127.0.0.1\nserver-port={port}\nonline-mode=false\nmax-players=1\n'
        'level-name=smoke-world\nlevel-type=minecraft:flat\ngenerate-structures=false\n'
        'view-distance=2\nsimulation-distance=2\nspawn-protection=0\n'
        'enable-query=false\nenable-rcon=false\nallow-flight=true\n'
        'sync-chunk-writes=false\nmax-tick-time=60000\n', encoding='utf-8')
    metadata = {'main_server_read_only': str(args.main.resolve()), 'directory': str(directory),
                'copied_files': manifest, 'pending_artifacts': missing,
                'launch_requested': args.run, 'fixture': str(ROOT / 'tools/smoke/MilitarySmoke.java')}
    (directory / 'smoke-manifest.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    return directory, missing


def compile_fixture(args, directory):
    original = args.classpath.read_text(encoding='utf-8').strip().split(os.pathsep)
    # Explicit upcoming full builds precede old classpath artifacts.
    classpath = os.pathsep.join([str(args.sbw_jar.resolve()), str(args.scguns_jar.resolve()),
                                *(entry for entry in original if Path(entry).exists())])
    classes = directory / 'fixture-classes'
    classes.mkdir(exist_ok=True)
    subprocess.run(['javac', '--release', '21', '-proc:none', '-encoding', 'UTF-8',
                    '-classpath', classpath, '-d', str(classes),
                    str(ROOT / 'tools/smoke/MilitarySmoke.java')], check=True)
    fixture = directory / 'mods/techpenis-military-smoke-fixture.jar'
    with zipfile.ZipFile(fixture, 'w', zipfile.ZIP_DEFLATED) as output:
        for path in classes.rglob('*.class'):
            output.write(path, path.relative_to(classes).as_posix())
        output.write(ROOT / 'tools/smoke/neoforge.mods.toml', 'META-INF/neoforge.mods.toml')
    return fixture


def launch(args, directory):
    run_bat = (args.main / 'run.bat').read_text(encoding='utf-8')
    match = re.search(r'@libraries/net/neoforged/neoforge/([^/\s]+)/win_args\.txt', run_bat)
    if not match:
        raise ValueError('Cannot identify installed NeoForge launcher from run.bat')
    launch_args = f'libraries/net/neoforged/neoforge/{match.group(1)}/win_args.txt'
    if not (directory / launch_args).is_file():
        raise ValueError(f'Missing launcher arguments: {launch_args}')
    result_path = directory / 'smoke-result.txt'
    # A previously completed result must never count as this launch's acceptance.
    if result_path.exists():
        raise ValueError('Completed smoke directory already has a result; prepare a new isolated run')
    with (directory / 'console.log').open('w', encoding='utf-8') as log:
        process = subprocess.Popen([args.java, '-Xms512M', '-Xmx3G', '@' + launch_args, 'nogui'],
                                   cwd=directory, stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT,
                                   text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        print(f'SMOKE_PID {process.pid}', flush=True)
        try:
            return_code = process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            try:
                process.communicate('stop\n', timeout=30)
            except subprocess.TimeoutExpired:
                # This is solely the child process launched above, never a discovered server.
                process.kill()
                process.wait(timeout=10)
            raise RuntimeError(f'Isolated smoke server exceeded {args.timeout}s; stop requested')
    if not result_path.exists():
        raise RuntimeError(f'Smoke server exited {return_code} without fixture result; inspect {directory / "console.log"}')
    result = result_path.read_text(encoding='utf-8').strip()
    print(result)
    if return_code != 0 or not result.startswith('MILITARY_SMOKE_PASS '):
        raise RuntimeError(f'Smoke server failed: exit={return_code}, {result}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', type=Path, default=MAIN)
    parser.add_argument('--sbw-jar', type=Path, default=DEFAULT_SBW)
    parser.add_argument('--scguns-jar', type=Path, default=DEFAULT_SCGUNS)
    parser.add_argument('--classpath', type=Path, default=ROOT / 'build/compat-scguns-test/direct-classpath.txt')
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--java', default='java')
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--run', action='store_true', help='Explicitly launch the isolated test server')
    args = parser.parse_args()
    directory, missing = prepare(args)
    print(f'SMOKE_DIRECTORY {directory}', flush=True)
    if missing:
        print('PENDING_ARTIFACTS ' + json.dumps(missing))
        if args.run:
            raise FileNotFoundError('Build the full source artifacts before --run')
        print('PREPARED_NOT_LAUNCHED')
        return
    fixture = compile_fixture(args, directory)
    print(f'FIXTURE_COMPILED {fixture}')
    if args.run:
        launch(args, directory)
    else:
        print('PREPARED_NOT_LAUNCHED')


if __name__ == '__main__':
    main()
