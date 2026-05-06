import pytest

import sys

import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from mcfg_parser.grammar import (
    MCFGRuleElement,
    MCFGRuleElementInstance,
    MCFGRule
)

class TestMCFGRuleElement:

    def test_init_and_properties(self):
        # create an element NP(u, v)
        el = MCFGRuleElement("NP", (0,), (1,))
        
        # check variable name
        assert el.variable == "NP"
        # check stored string variables
        assert el.string_variables == ((0,), (1,))

    def test_str(self):
        # __str__ converts element into readable format
        el = MCFGRuleElement("NP", (0,), (1,))
        
        assert str(el) == "NP(0, 1)"

    def test_eq(self):
        # two identical elements should be equal
        el1 = MCFGRuleElement("NP", (0,), (1,))
        el2 = MCFGRuleElement("NP", (0,), (1,))
        # different variable -> not equal        
        el3 = MCFGRuleElement("VP", (0,), (1,))
        
        assert el1 == el2
        assert el1 != el3

    def test_to_tuple(self):
        # to_tuple() gives a hashable representation
        el = MCFGRuleElement("NP", (0,), (1,))
        
        assert el.to_tuple() == ("NP", ((0,), (1,)))

    def test_hash(self):
        # hash should be same for equal objects
        el1 = MCFGRuleElement("NP", (0,), (1,))
        el2 = MCFGRuleElement("NP", (0,), (1,))

        assert hash(el1) == hash(el2)

    def test_unique_string_variables(self):
        # collect all unique indices across tuples
        el = MCFGRuleElement("X", (0,1), (1,2))
        # {0,1,2} -> duplicates removed
        
        assert el.unique_string_variables == {0,1,2}

class TestMCFGRuleElementInstance:

    def test_init_and_properties(self):
        # represents NP covering span (0,2)
        inst = MCFGRuleElementInstance("NP", (0,2))

        assert inst.variable == "NP"
        assert inst.string_spans == ((0,2),)

    def test_eq(self):
        # equality checks both variable and spans
        i1 = MCFGRuleElementInstance("NP", (0,2))
        i2 = MCFGRuleElementInstance("NP", (0,2))
        i3 = MCFGRuleElementInstance("VP", (0,2))

        assert i1 == i2
        assert i1 != i3

    def test_to_tuple(self):
        # tuple representation for hashing/comparison
        inst = MCFGRuleElementInstance("NP", (0,2))
        
        assert inst.to_tuple() == ("NP", ((0,2),))

    def test_hash(self):
        # equal objects -> same hash
        i1 = MCFGRuleElementInstance("NP", (0,2))
        i2 = MCFGRuleElementInstance("NP", (0,2))

        assert hash(i1) == hash(i2)

    def test_str_and_repr(self):
        # should display spans nicely
        inst = MCFGRuleElementInstance("NP", (0,2))

        assert str(inst) == "NP([0, 2])"
        assert repr(inst) == "NP([0, 2])"

class TestMCFGRule:

    def test_init_and_properties(self):
        # parse rule from string
        rule = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")

        # check left side variable
        assert rule.left_side.variable == "S"

        # check number of RHS elements
        assert len(rule.right_side) == 2
        
    def test_to_tuple(self):
        # should return (left_side, right_side)
        rule = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")
        tup = rule.to_tuple()

        assert isinstance(tup, tuple)
        assert len(tup) == 2
        
    def test_hash(self):
        # equal rule -> same hash
        r1 = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")
        r2 = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")

        assert hash(r1) == hash(r2)    
            
    def test_str_and_repr(self):
        rule = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")
        
        assert "S" in str(rule)
        assert "<Rule:" in repr(rule)

    def test_eq(self):
        # same rule -> equal
        r1 = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")
        r2 = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")
        # different rule -> not equal
        r3 = MCFGRule.from_string("S(uv) -> NP(u) NP(v)")

        assert r1 == r2
        assert r1 != r3

    def test_validate_duplicate_variables_error(self):
        # RHS variables cannot share the same string variable
        with pytest.raises(ValueError):
            MCFGRule.from_string("S(uv) -> NP(u) VP(u)") 
    
    def test_validate_mismatched_variables_error(self):
        # left and right sides must reference the same set of string variables
        left = MCFGRuleElement("S", (0,), (1,))
        right = MCFGRuleElement("NP", (0,))

        with pytest.raises(ValueError):
            MCFGRule(left, right)   

    def test_is_epsilon(self):
        # terminal rule -> epsilon
        rule = MCFGRule.from_string("D(the)")

        assert rule.is_epsilon

    def test_unique_variables(self):
        rule = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")

        # should contain all variables used
        assert "S" in rule.unique_variables
        assert "NP" in rule.unique_variables
        assert "VP" in rule.unique_variables

    def test_build_span_map(self):
        # Rule: S(uv) -> NP(u) VP(v)
        rule = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")

        # instantiate NP and VP with spans
        np = MCFGRuleElementInstance("NP", (0,2))
        vp = MCFGRuleElementInstance("VP", (2,5))

        # map u -> (0,2), v -> (2,5)
        span_map = rule._build_span_map((np, vp))

        assert span_map == {0:(0,2), 1:(2,5)}

    def test_right_side_aligns(self):
        # correct alignment -> True
        rule = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")

        np = MCFGRuleElementInstance("NP", (0,2))
        vp = MCFGRuleElementInstance("VP", (2,5))

        assert rule._right_side_aligns((np, vp))

    def test_right_side_aligns_fail(self):
        # wrong variable -> should fail
        rule = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")
        wrong = MCFGRuleElementInstance("X", (0,2))
        vp = MCFGRuleElementInstance("VP", (2,5))

        assert not rule._right_side_aligns((wrong, vp))

    def test_instantiate_left_side_success(self):
        # combine NP(0,2) and VP(2,5) -> S(0,5)
        rule = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")

        np = MCFGRuleElementInstance("NP", (0,2))
        vp = MCFGRuleElementInstance("VP", (2,5))

        result = rule.instantiate_left_side(np, vp)

        assert result.variable == "S"
        assert result.string_spans == ((0,5),)

    def test_instantiate_left_side_fail_non_adjacent(self):
        # non-adjacent spans -> should raise error
        rule = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")

        np = MCFGRuleElementInstance("NP", (0,2))
        vp = MCFGRuleElementInstance("VP", (3,5))

        with pytest.raises(ValueError):
            rule.instantiate_left_side(np, vp)

    def test_from_string(self):
        # parsing rule string -> correct structure
        rule = MCFGRule.from_string("NP(uv) -> D(u) N(v)")

        assert rule.left_side.variable == "NP"
        assert len(rule.right_side) == 2

    def test_string_yield(self):
        # only works for epsilon rules
        rule = MCFGRule.from_string("D(the)")

        assert rule.string_yield() == "D"

    def test_string_yield_error(self):
        # non-epsilon -> should raise error
        rule = MCFGRule.from_string("S(uv) -> NP(u) VP(v)")

        with pytest.raises(ValueError):
            rule.string_yield()
    
class TestMultipleContextFreeGrammar:

    @pytest.fixture(scope="module")

    def grammar(self):

        literal_rules = [
            "S(uv) -> NP(u) VP(v)",
            "NP(uv) -> D(u) N(v)",
            "VP(uv) -> V(u) NP(v)",
            "D(the)",
            "N(human)",
            "N(greyhound)",
            "V(sees)",
        ]

        parsed_rules = {
            MCFGRule.from_string(r)
            for r in literal_rules
        }

        all_variables = {
            el
            for r in parsed_rules
            for el in (r.left_side, *r.right_side)
        }

        start_variables = {
            v
            for v in all_variables
            if v.variable == "S"
        }

        return MultipleContextFreeGrammar(
            rules=parsed_rules,
            parser_class=AgendaBasedParser,
            start_variables=start_variables,
        )