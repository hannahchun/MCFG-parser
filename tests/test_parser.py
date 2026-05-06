import sys

import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest

from mcfg_parser.grammar import (
    MCFGRuleElement,
    MCFGRuleElementInstance,
    MCFGRule,
    MultipleContextFreeGrammar
)

from mcfg_parser.parser import (
    AgendaEntry,
    AgendaBasedParser
)

from mcfg_parser.tree import Tree

class TestAgendaEntry:

    def setup_method(self):
        # create one reusable agenda entry for testing
        self.entry = AgendaEntry(
            symbol=MCFGRuleElementInstance("VP", (2, 5)),
            entry_id=7,
            backpointers=((3, "Vpres"), (4, "NP"),)
        )

    def test_init(self):
        # test whether attributes are stored correctly
        assert self.entry.symbol == MCFGRuleElementInstance("VP", (2, 5))
        assert self.entry.entry_id == 7
        assert self.entry.backpointers == ((3, "Vpres"), (4, "NP"),)

    def test_repr(self):
        # test string representation
        assert "VP" in repr(self.entry)

    def test_hash(self):
        # equal entries should have equal hashes
        other = AgendaEntry(
            symbol=MCFGRuleElementInstance("VP",(2, 5)),
            entry_id=100,
        )
        assert hash(self.entry) == hash(other)

    def test_eq(self):
        # equality ignores entry IDs and uses symbol identity
        other = AgendaEntry(
            symbol=MCFGRuleElementInstance("VP", (2, 5)),
            entry_id=999,
        )

        different = AgendaEntry(
            symbol=MCFGRuleElementInstance("NP", (2, 5)),
            entry_id=999,
        )

        assert self.entry == other
        assert self.entry != different

# AgendaBasedParser tests
class TestAgendaBasedParser:

    @pytest.fixture(scope="module")
    def grammar(self):
        literal_rules = [
            "S(uv) -> NP(u) VP(v)",
            "S(uv) -> NPwh(u) VP(v)",
            "S(vuw) -> Aux(u) Swhmain(v, w)",
            "S(uwv) -> NPdisloc(u, v) VP(w)",
            "S(uwv) -> NPwhdisloc(u, v) VP(w)",
            "Sbar(uv) -> C(u) S(v)",
            "Sbarwh(v, uw) -> C(u) Swhemb(v, w)",
            "Sbarwh(u, v) -> NPwh(u) VP(v)",
            "Swhmain(v, uw) -> NP(u) VPwhmain(v, w)",
            "Swhmain(w, uxv) -> NPdisloc(u, v) VPwhmain(w, x)",
            "Swhemb(v, uw) -> NP(u) VPwhemb(v, w)",
            "Swhemb(w, uxv) -> NPdisloc(u, v) VPwhemb(w, x)",
            "Src(v, uw) -> NP(u) VPrc(v, w)",
            "Src(w, uxv) -> NPdisloc(u, v) VPrc(w, x)",
            "Src(u, v) -> N(u) VP(v)",
            "Swhrc(u, v) -> Nwh(u) VP(v)",
            "Swhrc(v, uw) -> NP(u) VPwhrc(v, w)",
            "Sbarwhrc(v, uw) -> C(u) Swhrc(v, w)",
            "VP(uv) -> Vpres(u) NP(v)",
            "VP(uv) -> Vpres(u) Sbar(v)",
            "VPwhmain(u, v) -> NPwh(u) Vroot(v)",
            "VPwhmain(u, wv) -> NPwhdisloc(u, v) Vroot(w)",
            "VPwhmain(v, uw) -> Vroot(u) Sbarwh(v, w)",
            "VPwhemb(u, v) -> NPwh(u) Vpres(v)",
            "VPwhemb(u, wv) -> NPwhdisloc(u, v) Vpres(w)",
            "VPwhemb(v, uw) -> Vpres(u) Sbarwh(v, w)",
            "VPrc(u, v) -> N(u) Vpres(v)",
            "VPrc(v, uw) -> Vpres(u) Nrc(v, w)",
            "VPwhrc(u, v) -> Nwh(u) Vpres(v)",
            "VPwhrc(v, uw) -> Vpres(u) Sbarwhrc(v, w)",
            "NP(uv) -> D(u) N(v)",
            "NP(uvw) -> D(u) Nrc(v, w)",
            "NPdisloc(uv, w) -> D(u) Nrc(v, w)",
            "NPwh(uv) -> Dwh(u) N(v)",
            "NPwh(uvw) -> Dwh(u) Nrc(v, w)",
            "NPwhdisloc(uv, w) -> Dwh(u) Nrc(v, w)",
            "Nrc(v, uw) -> C(u) Src(v, w)",
            "Nrc(u, vw) -> N(u) Swhrc(v, w)",
            "Nrc(u, vwx) -> Nrc(u, v) Swhrc(w, x)",
            "Dwh(which)",
            "Nwh(who)",
            "D(the)",
            "D(a)",
            "N(greyhound)",
            "N(human)",
            "Vpres(believes)",
            "Vroot(believe)",
            "Aux(does)",
            "C(that)",
        ]

        parsed_rules = {MCFGRule.from_string(r) for r in literal_rules}
        all_variables = {el for r in parsed_rules for el in (r.left_side, *r.right_side)}
        start_variables = {v for v in all_variables if v.variable == "S"}

        return MultipleContextFreeGrammar(
            rules=parsed_rules,
            parser_class=AgendaBasedParser,
            start_variables=start_variables,
        )

    @pytest.fixture(scope="module")
    def parser(self, grammar):
        return AgendaBasedParser(grammar)

    def test_init(self, parser, grammar):
        assert parser.grammar == grammar

    def test_recognize_valid(self, parser):
        sentence = [ "the", "human", "believes", "the", "greyhound"]
        assert parser(sentence, mode="recognize") is True

    def test_recognize_invalid(self, parser):
        sentence = ["human", "the", "believes"]
        assert parser(sentence, mode="recognize") is False

    def test_fill_chart_returns_entries(self, parser):
        # agenda-based parsing should populate the chart with derived AgendaEntry objects
        sentence = ["the", "human", "believes", "the", "greyhound"]
        chart = parser._fill_chart(sentence)
        assert len(chart) > 0
        assert all(
            isinstance(entry, AgendaEntry)
            for entry in chart
        )
        
    def test_parse_returns_tree_set(self, parser):
        # parse mode should reconstruct at least one parse tree from completed chart entries
        sentence = ["the", "human", "believes", "the", "greyhound"]
        parses = parser(sentence, mode="parse")

        assert isinstance(parses, set)
        assert len(parses) >= 1

    def test_combine_in_order(self, parser):
        # D + N should combine into NP under the rule:
        # NP(uv) -> D(u) N(v)
        left = AgendaEntry(MCFGRuleElementInstance("D", (0, 1)), 0)
        right = AgendaEntry(MCFGRuleElementInstance("N", (1, 2)), 1)

        results = parser._combine_in_order(left, right, 2,)

        assert len(results) >= 1
        assert any(r.symbol.variable == "NP" for r in results)

    def test_is_start_entry(self, parser):
        # start entries must use a start symbol and span the full sentence
        entry = AgendaEntry(MCFGRuleElementInstance("S", (0, 5)), 0)

        assert parser._is_start_entry(entry, 5)

    def test_get_entry_by_id(self, parser):
        chart = [AgendaEntry(MCFGRuleElementInstance("NP", (0, 2)), 3)]
        result = parser._get_entry_by_id(chart, 3)

        assert result.entry_id == 3

    def test_construct_tree_terminal(self, parser):
        # lexical entries with no backpointers should become terminal tree nodes
        chart = []
        entry = AgendaEntry(MCFGRuleElementInstance("D", (0, 1)), 0)
        tree = parser._construct_tree(chart, ["the"], entry)

        assert "D(the)" in repr(tree)