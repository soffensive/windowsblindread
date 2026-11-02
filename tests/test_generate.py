import importlib.util
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('generate', REPO / 'tools/generate.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class GenerationTests(unittest.TestCase):
    def test_distribution_preserves_original_coverage(self):
        paths = generator.generate()
        legacy = {generator.normalize(p) for p in (REPO / 'data/legacy-paths.txt').read_text().splitlines()}
        self.assertTrue(legacy.issubset(paths))
        self.assertGreater(len(paths), len(legacy))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual((REPO / 'windows-files.txt').read_text(), '\n'.join(paths) + '\n')
        self.assertFalse(any('{profile}' in path or path != path.strip() for path in paths))

    def test_known_missing_families(self):
        paths = generator.generate()
        for path in ['c:/programdata/ssh/sshd_config',
                     'c:/programdata/jenkins/.jenkins/config.xml',
                     'c:/programdata/docker/config/daemon.json',
                     'c:/program files/postgresql/17/data/pg_hba.conf',
                     'c:/inetpub/wwwroot/.env',
                     'c:/tomcat/conf/server.xml',
                     'c:/windows/ntds/ntds.dit',
                     'c:/programdata/anydesk/service.conf',
                     'c:/program files/uvnc bvba/ultravnc/ultravnc.ini',
                     'c:/users/administrator/appdata/roaming/mremoteng/confcons.xml',
                     'c:/program files/microsoft sql server/150/setup bootstrap/log/summary.txt']:
            self.assertIn(path, paths)

    def test_no_case_only_duplicates(self):
        paths = generator.generate()
        self.assertEqual(len(paths), len({path.casefold() for path in paths}))

    def test_custom_locations_and_case(self):
        paths = generator.generate(['tomcat'], ['c', 'd'], extra_roots=['tomcat=E:\\Apps\\Tomcat'])
        self.assertIn('d:/tomcat/conf/server.xml', paths)
        self.assertIn('E:/Apps/Tomcat/conf/server.xml', paths)
        self.assertFalse(any('/users/' in path for path in paths))

    def test_profiles_and_separators(self):
        paths = generator.generate(['profiles', 'legacy'], ['d'], ['Alice'], separator='\\')
        self.assertIn('d:\\users\\Alice\\.aws\\credentials', paths)
        self.assertIn('d:\\users\\Alice\\desktop\\proof.txt', paths)
        self.assertFalse(any('/' in path for path in paths))

    def test_invalid_input(self):
        for options in [dict(categories=['unknown']), dict(drives=['cc']),
                        dict(usernames=['../user']), dict(extra_roots=['tomcat=relative']),
                        dict(extra_roots=['unknown=c:/apps'])]:
            with self.assertRaises(ValueError):
                generator.generate(**options)


if __name__ == '__main__':
    unittest.main()
