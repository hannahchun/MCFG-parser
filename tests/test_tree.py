import pytest

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src",)))

from mcfg_parser.tree import Tree

class TestTree:

    @pytest.fixture
    def sample_tree(self):

        # S
        # ├── NP
        # │   └── John
        # └── VP
        #     └── runs

        return Tree("S",[Tree("NP",[Tree("John")]), Tree("VP",[Tree("runs")]),],)

    def test_init_and_properties(self, sample_tree):
        # tree should store root data and child nodes
        assert sample_tree.data == "S"
        assert len(sample_tree.children) == 2

    def test_to_tuple(self, sample_tree):
        # tree should convert into nested tuple representation
        expected = ("S",(("NP", (("John", ()),)), ("VP", (("runs", ()),)),),)

        assert sample_tree.to_tuple() == expected

    def test_hash(self, sample_tree):
        # structurally identical trees should have same hash
        other = Tree("S", [Tree("NP", [Tree("John")]), Tree("VP", [Tree("runs")]),],)
        
        assert hash(sample_tree) == hash(other)

    def test_eq(self, sample_tree):
        # equality should depend on recursive tree structure
        other = Tree("S",[Tree("NP",[Tree("John")]),Tree("VP", [Tree("runs")]),],)

        different = Tree("S",[Tree("X")],)

        assert sample_tree == other
        assert sample_tree != different

    def test_str(self, sample_tree):
        # __str__ should return terminal yield
        assert str(sample_tree) == "John runs"

    def test_repr(self, sample_tree):
        # __repr__ should return indented tree string
        
        assert "S" in repr(sample_tree)
        assert "--NP" in repr(sample_tree)

    def test_to_string(self, sample_tree):
        # tree string should contain hierarchical indentation
        tree_string = sample_tree.to_string()
        
        assert "S" in tree_string
        assert "--NP" in tree_string
        assert "--VP" in tree_string

    def test_contains(self, sample_tree):
        # membership uses pre-order depth-first traversal

        assert "NP" in sample_tree
        assert "runs" in sample_tree
        assert "XYZ" not in sample_tree

    def test_getitem_int(self, sample_tree):
        # integer indexing should access direct children

        assert sample_tree[0].data == "NP"
        assert sample_tree[1].data == "VP"

    def test_getitem_tuple(self, sample_tree):
        # tuple indexing should recursively traverse tree paths

        assert sample_tree[(0, 0)].data == "John"
        assert sample_tree[(1, 0)].data == "runs"

    def test_terminals(self, sample_tree):
        # terminals should return leaf-node yield in order
        assert sample_tree.terminals == ["John", "runs",]

    def test_validate_error(self):
        # all children must themselves be Tree objects

        with pytest.raises(TypeError):
            Tree("S", ["not_a_tree"])

    def test_index(self, sample_tree):
        # index() should return paths to matching nodes
        indices = sample_tree.index("runs")

        assert indices == [(1, 0)]

    def test_relabel_all(self, sample_tree):
        # relabel() should apply function to every node
        relabeled = sample_tree.relabel(str.lower)

        assert relabeled.data == "s"
        assert relabeled[(0, 0)].data == "john"

    def test_relabel_nonterminals_only(self, sample_tree):
        # only internal nodes should be relabeled

        relabeled = sample_tree.relabel(str.lower, nonterminals_only=True,)

        assert relabeled.data == "s"
        assert relabeled[(0, 0)].data == "John"

    def test_relabel_terminals_only(self, sample_tree):
        # only leaf nodes should be relabeled

        relabeled = sample_tree.relabel(str.upper,terminals_only=True,)

        assert relabeled.data == "S"
        assert relabeled[(0, 0)].data == "JOHN"

    def test_from_list(self):
        # nested list representation should reconstruct tree
        tree = Tree.from_list(
            [
                "S",
                [
                    "NP",
                    "John",
                ],
                [
                    "VP",
                    "runs",
                ],
            ]
        )

        assert tree.data == "S"
        assert tree[(0, 0)].data == "John"

    def test_from_string(self):
        # parenthesized string should parse into tree structure

        tree = Tree.from_string("(S (NP John) (VP runs))")

        assert tree.data == "S"
        assert tree[(1, 0)].data == "runs"