import unittest
from unittest import mock
import sys
import types

fake_vim = types.ModuleType("vim")
fake_vim.command = lambda x: ()
sys.modules["vim"] = fake_vim

from agdavim.response import sexpr
Symbol = sexpr.Symbol
QUOTE = sexpr.QUOTE

class TestSExpr(unittest.TestCase):
    def test_parse_sexpr(self):
        sexpr_str = "(agda2-exit-done)"
        self.assertEqual(sexpr.parse(sexpr_str), [Symbol('agda2-exit-done')])

    def test_parse_highlight_clear(self):
        sexpr_str = '(agda2-highlight-clear)'
        self.assertEqual(sexpr.parse(sexpr_str), [Symbol('agda2-highlight-clear')])

    def test_parse_status_action(self):
        sexpr_str = '(agda2-status-action "")'
        self.assertEqual(sexpr.parse(sexpr_str), [Symbol('agda2-status-action'), ''])

    def test_parse_info_action_empty(self):
        sexpr_str = '(agda2-info-action "*Type-checking*" "" nil)'
        self.assertEqual(
            sexpr.parse(sexpr_str),
            [Symbol('agda2-info-action'), '*Type-checking*', '', sexpr.NIL])
    
    def test_parse_info_action_checking(self):
        sexpr_str = '(agda2-info-action "*Type-checking*" "Checking Demo (/path/to/demo.agda).\n" t)'
        self.assertEqual(
            sexpr.parse(sexpr_str),
            [Symbol('agda2-info-action'), '*Type-checking*', 'Checking Demo (/path/to/demo.agda).\n', True])

    def test_parse_highlight_add_annotations(self):
        sexpr_str = "(agda2-highlight-add-annotations 'nil '(1 4 (symbol) t) '(5 12 (keyword) t) '(13 25 (pragma) t) '(26 29 (symbol) t) '(31 37 (keyword) t) '(57 62 (keyword) t) '(64 70 (keyword) t) '(79 80 (symbol) t) '(86 91 (keyword) t) '(94 99 (keyword) t) '(112 113 (symbol) t) '(119 123 (keyword) t) '(136 137 (symbol) t) '(157 158 (symbol) t) '(166 220 (comment) t) '(227 228 (symbol) t) '(237 238 (symbol) t) '(251 252 (symbol) t) '(264 318 (comment) t))"
        self.assertEqual(
            sexpr.parse(sexpr_str),
            [Symbol('agda2-highlight-add-annotations'),
             [QUOTE, sexpr.NIL],
             [QUOTE, [1, 4, [Symbol('symbol')], True]],
             [QUOTE, [5, 12, [Symbol('keyword')], True]],
             [QUOTE, [13, 25, [Symbol('pragma')], True]],
             [QUOTE, [26, 29, [Symbol('symbol')], True]],
             [QUOTE, [31, 37, [Symbol('keyword')], True]],
             [QUOTE, [57, 62, [Symbol('keyword')], True]],
             [QUOTE, [64, 70, [Symbol('keyword')], True]],
             [QUOTE, [79, 80, [Symbol('symbol')], True]],
             [QUOTE, [86, 91, [Symbol('keyword')], True]],
             [QUOTE, [94, 99, [Symbol('keyword')], True]],
             [QUOTE, [112, 113, [Symbol('symbol')], True]],
             [QUOTE, [119, 123, [Symbol('keyword')], True]],
             [QUOTE, [136, 137, [Symbol('symbol')], True]],
             [QUOTE, [157, 158, [Symbol('symbol')], True]],
             [QUOTE, [166, 220, [Symbol('comment')], True]],
             [QUOTE, [227, 228, [Symbol('symbol')], True]],
             [QUOTE, [237, 238, [Symbol('symbol')], True]],
             [QUOTE, [251, 252, [Symbol('symbol')], True]],
             [QUOTE, [264, 318, [Symbol('comment')], True]]]
        )

if __name__ == '__main__':
    unittest.main()