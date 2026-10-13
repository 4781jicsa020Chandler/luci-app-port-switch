import io
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='port-switch-package-', dir=ROOT.parent)
        cls.folder = pathlib.Path(cls.temp.name)
        cls.source = cls.folder / 'source'
        shutil.copytree(ROOT, cls.source, ignore=shutil.ignore_patterns('.git', 'dist', '__pycache__'))
        (cls.source / '.git').mkdir()
        (cls.source / '.git' / 'config').write_text('excluded metadata fixture')
        (cls.source / 'dist').mkdir()
        (cls.source / 'dist' / 'old.ipk').write_text('excluded previous build fixture')
        (cls.source / 'private-notes.txt').write_text('excluded unrelated fixture')
        cls.output = cls.folder / 'artifacts'
        subprocess.run([sys.executable, str(cls.source / 'build.py'), '--output-dir', str(cls.output)], check=True, stdout=subprocess.DEVNULL)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def package(self):
        return tarfile.open(self.output / 'luci-app-port-switch_1.0.0_all.ipk', 'r:gz')

    def test_opkg_container_and_required_payload(self):
        with self.package() as outer:
            self.assertEqual(outer.extractfile('./debian-binary').read(), b'2.0\n')
            with tarfile.open(fileobj=io.BytesIO(outer.extractfile('./data.tar.gz').read()), mode='r:gz') as data:
                for path in ('./usr/libexec/port-switch', './usr/lib/lua/luci/controller/port_switch.lua', './usr/lib/lua/luci/view/port-switch/index.htm', './etc/init.d/port-switch'):
                    self.assertTrue(data.getmember(path).isfile(), path)
                self.assertTrue(data.getmember('./usr/lib/lua/luci/view/port-switch').isdir())
                self.assertEqual(data.getmember('./usr/libexec/port-switch').mode, 0o755)
                self.assertEqual(data.getmember('./etc/init.d/port-switch').mode, 0o755)
                for member in data.getmembers():
                    self.assertEqual((member.uid, member.gid), (0, 0))

    def test_control_scripts_and_dependencies(self):
        with self.package() as outer:
            with tarfile.open(fileobj=io.BytesIO(outer.extractfile('./control.tar.gz').read()), mode='r:gz') as control:
                description = control.extractfile('./control').read().decode()
                self.assertIn('Package: luci-app-port-switch\n', description)
                self.assertIn('Architecture: all\n', description)
                self.assertIn('Depends: luci-base, jshn, jsonfilter, uci\n', description)
                for path in ('./postinst', './prerm'):
                    self.assertEqual(control.getmember(path).mode, 0o755)

    def test_source_archive_excludes_git_stale_builds_and_unrelated_files(self):
        with zipfile.ZipFile(self.output / 'openwrt-port-switch-source.zip') as source:
            names = source.namelist()
            self.assertIn('openwrt-port-switch/LICENSE', names)
            self.assertIn('openwrt-port-switch/build.py', names)
            self.assertFalse(any('/.git/' in name or '/dist/' in name or 'private-notes' in name for name in names))

    def test_package_build_is_repeatable(self):
        second = self.folder / 'second'
        subprocess.run([sys.executable, str(self.source / 'build.py'), '--output-dir', str(second)], check=True, stdout=subprocess.DEVNULL)
        name = 'luci-app-port-switch_1.0.0_all.ipk'
        self.assertEqual((self.output / name).read_bytes(), (second / name).read_bytes())


if __name__ == '__main__':
    unittest.main()
