## Agenda-Based Parser for Multiple Context-Free Grammars

This Python package implements an agenda-based parser for Multiple Context-Free Grammars (MCFGs), following the agenda-based parsing strategy in Shieber et al. (1995). MCFGs extend context-free grammars by allowing rules that can model mildly context-sensitive structures, making them useful for representing more complex linguistic phenomena.

The package is organized into three main components:

* grammar.py <br>
    Contains classes for representing MCFG rule elements, instantiated rule elements, grammar rules, and the full grammar itself. <br>
* parser.py <br>
    Implements an agenda-based parsing algorithm that builds larger constituents from lexical entries while storing intermediate results in a chart. <br>
* tree.py <br>
    Provides a tree data structure used for representing parse trees, including utilities for indexing, relabeling, and converting trees into string or tuple representations.