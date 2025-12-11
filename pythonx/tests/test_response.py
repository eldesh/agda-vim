import unittest
from unittest import mock
import sys
import types
from typing import Any

fake_vim = types.ModuleType("vim")
fake_vim.command = lambda x: ()
sys.modules["vim"] = fake_vim

from agdavim.response import *
import agdavim.log

class TestResponse(unittest.TestCase):
    def assert_response(self, cls: type[Any], str: str):
        self.assertEqual("%s" % cls.parse(str), str)

    def assert_response_general(self, cls: type[Any], str: str):
        res = parse_response(str)
        self.assertIsInstance(res, cls)
        self.assertEqual("%s" % res, str)

    def test_exit_done_response_roundtrip(self):
        self.assert_response(ExitDoneResponse, '(agda2-exit-done)')

    def test_abort_done_response_roundtrip(self):
        self.assert_response(AbortDoneResponse, '(agda2-abort-done)')

    def test_status_action_response_roundtrip(self):
        self.assert_response(StatusActionResponse, '(agda2-status-action "")')
        self.assert_response(StatusActionResponse, '(agda2-status-action "Checked")')
        self.assert_response(StatusActionResponse, '(agda2-status-action "Checked,ShowImplicit")')
        self.assert_response(StatusActionResponse, '(agda2-status-action "ShowImplicit")')
        self.assert_response(StatusActionResponse, '(agda2-status-action "ShowIrrelevant")')

    def test_highlight_clear_response_roundtrip(self):
        self.assert_response(HighlightClearResponse, '(agda2-highlight-clear)')

    def test_highlight_load_and_delete_action_response_roundtrip(self):
        self.assert_response(HighlightLoadAndDeleteActionResponse, '(agda2-highlight-load-and-delete-action)')

    def test_verbose_response_roundtrip(self):
        self.assert_response(VerboseResponse, '(agda2-verbose "Checked A.")')
        self.assert_response(VerboseResponse, '(agda2-verbose "Checked B.")')
        self.assert_response(VerboseResponse, '(agda2-verbose "Checking A.")')
        self.assert_response(VerboseResponse, '(agda2-verbose "Checking B.")')
        self.assert_response(VerboseResponse, '(agda2-verbose "Checking D.")')
        self.assert_response(VerboseResponse, '(agda2-verbose "Found interaction point ConcreteDef ?0 : (Pow I)")')
        self.assert_response(VerboseResponse, '(agda2-verbose "Positivity graph (completed): E=1")')
        self.assert_response(VerboseResponse, '(agda2-verbose "Positivity graph: N=2 E=1")')
        self.assert_response(VerboseResponse, '(agda2-verbose "parseVariables: current module = Issue7863 current section = clause context = (x₁ : Bool)")')
        self.assert_response(VerboseResponse, '(agda2-verbose "splitting clause: f = con context = (x : Bool) tel = (x : Bool) perm = x0 -> x0 ps = [x₁] ell = NoEllipsis type = Bool")')

    def test_give_action_response_roundtrip(self):
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "(lsuc lzero)")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "(m + ?)")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "(λ { (c ()) }) ?")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "10 !")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "5")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "? + x")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "? ∷ ?")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "H-Level.has-hlevel hl")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "Just ?")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "M.a")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "M.c")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "S₁ (S₅ _) (S₅ _)")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "[]")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "\\ x -> ?")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "a")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "b 0")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "black , nb a r r")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "c ? ?")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "c x")')
        self.assert_response(GiveActionResponse, '(agda2-give-action 0 "c")')

    def test_highlight_add_annotations_response_roundtrip(self):
        self.assert_response(HighlightAddAnnotationsResponse, "(agda2-highlight-add-annotations 'nil)")
        self.assert_response(HighlightAddAnnotationsResponse, "(agda2-highlight-add-annotations 'nil '(94 95 (function) nil nil (Issue4954-2.agda . 94)))")
        self.assert_response(HighlightAddAnnotationsResponse, "(agda2-highlight-add-annotations 'nil '(94 99 () t))")
        self.assert_response(HighlightAddAnnotationsResponse, "(agda2-highlight-add-annotations 'nil '(94 99 (typechecks)))")
        self.assert_response(HighlightAddAnnotationsResponse, "(agda2-highlight-add-annotations 'nil '(940 946 (keyword) t))")
        self.assert_response(HighlightAddAnnotationsResponse, "(agda2-highlight-add-annotations 'nil '(95 96 (datatype) nil nil (HighlightPositivity.agda . 95)))")
        self.assert_response(HighlightAddAnnotationsResponse, "(agda2-highlight-add-annotations 'nil '(97 98 (module) nil nil (Issue3010.agda . 25)))")
        self.assert_response(HighlightAddAnnotationsResponse, "(agda2-highlight-add-annotations 'nil '(4625 4627 (deadcode)) '(4686 4688 (deadcode)))")
        self.assert_response(HighlightAddAnnotationsResponse, "(agda2-highlight-add-annotations 'nil '(320 322 (unsolvedconstraint)) '(349 370 (unsolvedconstraint)))")
        self.assert_response(HighlightAddAnnotationsResponse, "(agda2-highlight-add-annotations 'remove '(1 27 (background) t))")
        self.assert_response(HighlightAddAnnotationsResponse, "(agda2-highlight-add-annotations 'remove '(1 7 (keyword) t))")
        self.assert_response(HighlightAddAnnotationsResponse, "(agda2-highlight-add-annotations 'remove '(1 27 (background) t) '(27 28 (background) t) '(28 39 (background) t) '(39 40 (background) t) '(40 52 (markup) t) '(53 62 (keyword) t) '(65 66 (symbol) t) '(71 81 (markup) t) '(81 82 (background) t))")
        self.assert_response(HighlightAddAnnotationsResponse, "(agda2-highlight-add-annotations 'nil '(37 38 (unsolvedmeta)) '(60 63 (error) nil \"Issue157.agda:8.9-12: error: [UnequalSorts] Set₁       │  != Set when checking that the expression Set has type Set\"))")

    def test_info_action_and_copy_response_roundtrip(self):
        self.assert_response(InfoActionAndCopyResponse, '''(agda2-info-action-and-copy "*Helper function*" "id' : ∀ {A} → A → A " nil)''')
        self.assert_response(InfoActionAndCopyResponse, '''(agda2-info-action-and-copy "*Helper function*" "g : ∀ A {B : A → Set} (a : A) → B a " nil)''')
        self.assert_response(InfoActionAndCopyResponse, '''(agda2-info-action-and-copy "*Helper function*" "id₂′ : ∀ {A} {B} (x : if true then A else B) → if false then B else A " nil)''')
        self.assert_response(InfoActionAndCopyResponse, '''(agda2-info-action-and-copy "*Helper function*" "aux : ∀ {A} → E → A ⇒ A " nil)''')
        self.assert_response(InfoActionAndCopyResponse, '''(agda2-info-action-and-copy "*Helper function*" "id' : K → K " nil)''')
        self.assert_response(InfoActionAndCopyResponse, '''(agda2-info-action-and-copy "*Helper function*" "id'' : ∀ {A} {k : A} → ? → A " nil)''')
        self.assert_response(InfoActionAndCopyResponse, '''(agda2-info-action-and-copy "*Helper function*" "id\''' : F → K → F " nil)''')
        self.assert_response(InfoActionAndCopyResponse, '''(agda2-info-action-and-copy "*Helper function*" "id\'\''' : (tm : T m) → Unit " nil)''')
        self.assert_response(InfoActionAndCopyResponse, '''(agda2-info-action-and-copy "*Helper function*" "id\'\'\''' : (x : Unit) → W c → Unit " nil)''')
        self.assert_response(InfoActionAndCopyResponse, '''(agda2-info-action-and-copy "*Helper function*" "helper : Σ ℕ T " nil)''')
        self.assert_response(InfoActionAndCopyResponse, '''(agda2-info-action-and-copy "*Helper function*" "Aux : T → T → Set → Set → Set " nil)''')
        self.assert_response(InfoActionAndCopyResponse, '''(agda2-info-action-and-copy "*Helper function*" "SuperBag-delete : (i : y ∈ ys) (sb : SuperBag xs ys) → SuperBag (delete ys i) ys → SuperBag (delete xs (reindex sb i)) ys " nil)''')

    def test_goals_action_response_roundtrip(self):
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '()))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1 2 3 4 5 6 7 8 9 10 11 12)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1 2 3 4 5 6 7 8 9 10 11)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1 2 3 4 5 6 7 8 9 10)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1 2 3 4 5 6 7 8 9)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1 2 3 4 5 6 7 8)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1 2 3 4 5 6 7)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1 2 3 4 5 6)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1 2 3 4 5)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1 2 3 4)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1 2 3)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1 2)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0 1)))")
        self.assert_response(GoalsActionResponse, "((last . 1) . (agda2-goals-action '(0)))")

    def test_make_case_action_response_roundtrip(self):
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("(- A) B = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("(A + B) C = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("(A nofun) B = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("... | [] = ?" "... | x ∷ foo-ls = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("... | [] = ?" "... | xs ∷ʳ′ x = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("... | c = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("... | c q = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("... | itt r = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("... | leaf = ?" "... | node n n₂ = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("... | tt = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("... | unit = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("... | x₁ ∷ zs = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("... | zero = ?" "... | suc n = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("... | zero = ?" "... | suc p = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("... | zero = ?" "... | suc x = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("... | ♭ = ?" "... | B' `→ B'' = ?")))''')
        self.assert_response(MakeCaseActionResponse, '''((last . 2) . (agda2-make-case-action '("32-cases true true true true true = ?" "32-cases true true true true false = ?" "32-cases true true true false true = ?" "32-cases true true true false false = ?" "32-cases true true false true true = ?" "32-cases true true false true false = ?" "32-cases true true false false true = ?" "32-cases true true false false false = ?" "32-cases true false true true true = ?" "32-cases true false true true false = ?" "32-cases true false true false true = ?" "32-cases true false true false false = ?" "32-cases true false false true true = ?" "32-cases true false false true false = ?" "32-cases true false false false true = ?" "32-cases true false false false false = ?" "32-cases false true true true true = ?" "32-cases false true true true false = ?" "32-cases false true true false true = ?" "32-cases false true true false false = ?" "32-cases false true false true true = ?" "32-cases false true false true false = ?" "32-cases false true false false true = ?" "32-cases false true false false false = ?" "32-cases false false true true true = ?" "32-cases false false true true false = ?" "32-cases false false true false true = ?" "32-cases false false true false false = ?" "32-cases false false false true true = ?" "32-cases false false false true false = ?" "32-cases false false false false true = ?" "32-cases false false false false false = ?")))''')

    def test_make_case_action_extendlam_response_roundtrip(self):
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '("()")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '(".Iso.inv ()")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '(".out false → ?" ".out true → ?")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '(".out x → ?")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '("a .proj₁ → ?" "a .proj₂ → ?")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '("record { π₁ = π₃ ; π₂ = π₄ } → ?")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '("refl → ?")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '("true z → ?" "false z → ?")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '("true {w} → ?" "false {w} → ?")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '("true → ?" "false → ?")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '("tt → ?")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '("x .proj₁ → ?" "x .proj₂ → ?")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '("x {m = zero} → ?" "x {m = suc m} → ?")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '("z {true} → ?" "z {false} → ?")))''')
        self.assert_response(MakeCaseActionExtendlamResponse, '''((last . 2) . (agda2-make-case-action-extendlam '("zero -> ?" "(suc n) -> ?")))''')

    def test_solveall_action_response_roundtrip(self):
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '()))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(0 "3" 1 "2 ∷ 1 ∷ 0 ∷ []")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(0 "3" 1 "reverse example")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(0 "? == ?")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(0 "_")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(0 "a ⊔ b ⊔ c")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(0 "length example" 1 "reverse example")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(0 "p .fst")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(0 "x")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(0 "∀ (m : ?) n → Id _ m n")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(1 "_ == _")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(1 "a")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(1 "not _" 3 "not _")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(3 "forall (m : ?) n -> m ≡ n")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(3 "true")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(3 "∀ (m : ?) n → m ≡ n")))''')
        self.assert_response(SolveAllActionResponse, '''((last . 2) . (agda2-solveAll-action '(5 "D z")))''')

    def test_maybe_goto_response_roundtrip(self):
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Error-in-imported-module/M.agda" . 88)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue1244a.agda" . 182)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue1326.agda" . 111)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue1339.agda" . 148)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue1365.agda" . 4948)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue157.agda" . 60)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue157b.agda" . 94)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue1925.agda" . 19)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue2096.agda" . 1752)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue2174a.agda" . 1)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue2181.agda" . 389)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue2239.agda" . 353)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue2286.agda" . 431)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue2291.agda" . 228)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue2447.agda" . 47)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue2447/Operator-error.agda" . 113)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue2447/Parse-error.agda" . 1)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue2447/Type-error.agda" . 82)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue2487/B.agda" . 50)))''')
        self.assert_response(MaybeGotoResponse, '''((last . 3) . (agda2-maybe-goto '("Issue2575/M.agda" . 39)))''')

    def test_general_response_roundtrip(self):
        self.assert_response_general(HighlightAddAnnotationsResponse, '''(agda2-highlight-add-annotations 'nil '(195 196 (error) nil "/path/to/file.agda:9,12-13\nCannot split into projections because the target type a == a is\nnot a record type\nwhen checking that the expression ? has tye a == a"))''')


if __name__ == '__main__':
    log.init_logging(level=logging.DEBUG)
    log.set_logging_level(logging.DEBUG)
    unittest.main()
