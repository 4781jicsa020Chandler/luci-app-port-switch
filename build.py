#!/usr/bin/env python3
"""Build an architecture-independent OpenWrt 21.02 ipk without an SDK."""
import argparse
import gzip
import io
import pathlib
import tarfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
NAME = 'luci-app-port-switch_1.0.0_all.ipk'
SOURCE_FILES = {'README.md', 'LICENSE', 'build.py', '.gitignore'}
SOURCE_DIRS = {'control', 'root', 'tests', '.github'}

def archive(files):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w', format=tarfile.GNU_FORMAT) as tar:
        directories = set()
        for name, _, _ in files:
            for parent in pathlib.PurePosixPath(name).parents:
                if str(parent) != '.':
                    directories.add(str(parent))
        for name in sorted(directories, key=lambda path: (path.count('/'), path)):
            item = tarfile.TarInfo('./' + name + '/')
            item.type = tarfile.DIRTYPE
            item.mode = 0o755
            item.uid = item.gid = 0
            item.uname = item.gname = 'root'
            item.mtime = 0
            tar.addfile(item)
        for name, content, mode in sorted(files):
            item = tarfile.TarInfo('./' + name)
            item.size = len(content)
            item.mode = mode
            item.uid = item.gid = 0
            item.uname = item.gname = 'root'
            item.mtime = 0
            tar.addfile(item, io.BytesIO(content))
    return gzip.compress(output.getvalue(), mtime=0)

def collect(folder):
    files = []
    for path in sorted(folder.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(folder).as_posix()
        executable = relative.startswith('usr/libexec/') or relative.startswith('etc/init.d/') or relative in ('postinst', 'prerm')
        files.append((relative, path.read_bytes(), 0o755 if executable else 0o644))
    return files

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=pathlib.Path, default=ROOT / 'dist')
    OUTPUTS = parser.parse_args().output_dir.expanduser().resolve()
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    data = archive(collect(ROOT / 'root'))
    controls = collect(ROOT / 'control')
    installed_size = sum(len(content) for _, content, _ in collect(ROOT / 'root'))
    controls = [(name, content + ('Installed-Size: %d\n' % installed_size).encode() if name == 'control' else content, mode) for name, content, mode in controls]
    control = archive(controls)
    package = archive([('debian-binary', b'2.0\n', 0o644), ('control.tar.gz', control, 0o644), ('data.tar.gz', data, 0o644)])
    destination = OUTPUTS / NAME
    destination.write_bytes(package)
    with zipfile.ZipFile(OUTPUTS / 'openwrt-port-switch-source.zip', 'w', zipfile.ZIP_DEFLATED) as source:
        for path in sorted(ROOT.rglob('*')):
            relative = path.relative_to(ROOT)
            allowed = relative.as_posix() in SOURCE_FILES or relative.parts[0] in SOURCE_DIRS
            excluded = any(part in {'.git', '__pycache__', '.DS_Store'} for part in relative.parts)
            if path.is_file() and allowed and not excluded and OUTPUTS not in path.resolve().parents:
                source.write(path, 'openwrt-port-switch/' + path.relative_to(ROOT).as_posix())
    print(destination)

if __name__ == '__main__':
    main()
