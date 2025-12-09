import unittest
from unittest import mock
import sys
import types

fake_vim = types.ModuleType("vim")
fake_vim.command = lambda x: ()
sys.modules["vim"] = fake_vim

from agdavim.response import sexpr

class TestSExpr(unittest.TestCase):
    def test_parse_sexpr(self):
        sexpr_str = "(agda2-exit-done)"
        self.assertEqual(sexpr.parse(sexpr_str), ['agda2-exit-done'])

    def test_parse_highlight_clear(self):
        sexpr_str = '(agda2-highlight-clear)'
        self.assertEqual(sexpr.parse(sexpr_str), ['agda2-highlight-clear'])

    def test_parse_status_action(self):
        sexpr_str = '(agda2-status-action "")'
        self.assertEqual(sexpr.parse(sexpr_str), ['agda2-status-action', '""'])

    def test_parse_info_action_empty(self):
        sexpr_str = '(agda2-info-action "*Type-checking*" "" nil)'
        self.assertEqual(
            sexpr.parse(sexpr_str),
            ['agda2-info-action', '"*Type-checking*"', '""', sexpr.NIL])
    
    def test_parse_info_action_checking(self):
        sexpr_str = '(agda2-info-action "*Type-checking*" "Checking Demo (/path/to/demo.agda).\n" t)'
        self.assertEqual(
            sexpr.parse(sexpr_str),
            ['agda2-info-action', '"*Type-checking*"', '"Checking Demo (/path/to/demo.agda).\n"', True])

    def test_parse_highlight_add_annotations(self):
        sexpr_str = "(agda2-highlight-add-annotations 'nil '(1 4 (symbol) t) '(5 12 (keyword) t) '(13 25 (pragma) t) '(26 29 (symbol) t) '(31 37 (keyword) t) '(57 62 (keyword) t) '(64 70 (keyword) t) '(79 80 (symbol) t) '(86 91 (keyword) t) '(94 99 (keyword) t) '(112 113 (symbol) t) '(119 123 (keyword) t) '(136 137 (symbol) t) '(157 158 (symbol) t) '(166 220 (comment) t) '(227 228 (symbol) t) '(237 238 (symbol) t) '(251 252 (symbol) t) '(264 318 (comment) t))"
        self.assertEqual(
            sexpr.parse(sexpr_str),
            ['agda2-highlight-add-annotations',
             ['quote', sexpr.NIL],
             ['quote', [1, 4, ['symbol'], True]],
             ['quote', [5, 12, ['keyword'], True]],
             ['quote', [13, 25, ['pragma'], True]],
             ['quote', [26, 29, ['symbol'], True]],
             ['quote', [31, 37, ['keyword'], True]],
             ['quote', [57, 62, ['keyword'], True]],
             ['quote', [64, 70, ['keyword'], True]],
             ['quote', [79, 80, ['symbol'], True]],
             ['quote', [86, 91, ['keyword'], True]],
             ['quote', [94, 99, ['keyword'], True]],
             ['quote', [112, 113, ['symbol'], True]],
             ['quote', [119, 123, ['keyword'], True]],
             ['quote', [136, 137, ['symbol'], True]],
             ['quote', [157, 158, ['symbol'], True]],
             ['quote', [166, 220, ['comment'], True]],
             ['quote', [227, 228, ['symbol'], True]],
             ['quote', [237, 238, ['symbol'], True]],
             ['quote', [251, 252, ['symbol'], True]],
             ['quote', [264, 318, ['comment'], True]]]
        )

if __name__ == '__main__':
    unittest.main()