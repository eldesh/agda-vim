import unittest
from unittest import mock
import sys
import types

fake_vim = types.ModuleType("vim")
fake_vim.command = lambda x: ()
sys.modules["vim"] = fake_vim

from agdavim.agda_version import AgdaVersion

class TestAgdaVersion(unittest.TestCase):
    def test_parse_version(self):
        version_str = "Agda version 2.6.8.1"
        self.assertEqual(AgdaVersion.parse(version_str).__str__(), version_str)

    def test_parse_prerelease_version(self):
        version_str = "Agda version 2.6.8.1-beta"
        self.assertEqual(AgdaVersion.parse(version_str).__str__(), version_str)


if __name__ == '__main__':
    unittest.main()