from enum import Enum
from abc import ABC

from .grammar import MCFGRuleElementInstance
from .tree import Tree

from collections import defaultdict, deque

class NormalForm(Enum):
    """Normal form types for parsers."""
    
    CNF = 0
    BNF = 1
    GNF = 2


class Parser(ABC):
    """
    A general parser class

    Parameters
    ----------
    grammar
    """

    normal_form = NormalForm.CNF

    def __init__(self, grammar):
        self._grammar = grammar

    def __call__(self, string, mode="recognize"):
        """Parse or recognize a string.

        Parameters
        ----------
        string : str | list[str]
            The string to process.
        mode : str
            Whether to "recognize" or "parse".

        Returns
        -------
        bool | set[Tree]
            Boolean for recognize, set of parse trees for parse.
        """
        if mode == "recognize":
            return self._recognize(string)
        elif mode == "parse":
            return self._parse(string)            
        else:
            msg = 'mode must be "parse" or "recognize"'
            raise ValueError(msg)
    
    @property
    def grammar(self):
        return self._grammar

BackPointer = tuple[int, str]

class AgendaEntry:

    """A chart entry for agenda-based parsing

    Parameters
    ----------
    symbol : MCFGRuleElementInstance
        The instantiated grammar symbol
    entry_id : int
        Unique identifier for this entry
    backpointers : tuple[BackPointer, ...] | None
        Child entries used to construct this entry
    """

    def __init__(
        self,
        symbol: MCFGRuleElementInstance,
        entry_id: int,
        backpointers: tuple[BackPointer, ...] | None = None,
    ):

        self._symbol = symbol
        self._entry_id = entry_id
        self._backpointers = backpointers or tuple()

    def key(self):
        return self._symbol.to_tuple()

    def __hash__(self) -> int:
        return hash(self.key())

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AgendaEntry) and self.key() == other.key()

    def __repr__(self) -> str:
        return f"{self._entry_id}: {self._symbol}"

    @property
    def symbol(self) -> MCFGRuleElementInstance:
        return self._symbol

    @property
    def entry_id(self) -> int:
        return self._entry_id

    @property
    def backpointers(self) -> tuple[BackPointer, ...]:
        return self._backpointers

class AgendaBasedParser(Parser):
    """
    Agenda-based parser for multiple context free grammars.
    
    The parser initializes lexical entries from terminal rules,
    stores them in an agenda, and repeatedly combines entries to build larger constituents until no new entries can be added.
    """
    
    normal_form = NormalForm.CNF

    def _recognize(self, string: list[str]) -> bool:
        # return True if the grammar recognizes the sentence
        chart = self._fill_chart(string)
        return any(self._is_start_entry(entry, len(string)) for entry in chart)

    def _parse(self, string: list[str]) -> set[Tree]:
        # return parse trees for the sentence.
        chart = self._fill_chart(string)
        start_entries = [
            entry
            for entry in chart
            if self._is_start_entry(entry, len(string))
        ]

        return {
            self._construct_tree(chart, string, entry)
            for entry in start_entries
        }

    def _fill_chart(self, string: list[str]) -> list[AgendaEntry]:

        """
        Construct a chart using agenda-based parsing.
        
        The parser begins with lexical entries generated from terminal rules 
        and repeatedly combines compatible chart entries until no new constituents can be derived.
        
        Parameters
        ----------
        string : list[str]
            Tokenized input sentence

        Returns
        -------
        list[AgendaEntry]
            Completed chart entries
        """
        
        # agenda stores entries that still need to be processed
        # newly created constituents are first added here before storing in the chart
        agenda: deque[AgendaEntry] = deque()

        # finalized chart entries
        chart: list[AgendaEntry] = []

        # used to avoid adding duplicate chart entries
        seen_keys = set()

        # map variable names to chart entries with that variable to avoid trying every possible pair
        # e.g., NP -> [NP([0,2]), NP([3,5])]
        chart_by_variable = defaultdict(list)

        # Unique ID assigned to each chart entry
        next_id = 0

        # 1. initialize lexical entries
        # word = "the" at span (0, 1)
        # rule = D(the)
        # instantiated constituent = D([0, 1])
        for i, word in enumerate(string):
            terminal = MCFGRuleElementInstance(word, (i, i + 1))
            for rule in self.grammar.parts_of_speech(word):
                try:
                    symbol = rule.instantiate_left_side(terminal)
                except ValueError:
                    continue

                agenda.append(
                    AgendaEntry(
                        symbol=symbol,
                        entry_id=next_id,
                        backpointers=tuple(),
                    )
                )
                next_id += 1
                
        # 2. main agenda loop
        # continue processing until no unexplored entries remain
        while agenda:
            current = agenda.popleft()
            # if the same instantiated symbol already exists in the chart, skip it to prevent duplicate work
            if current.key() in seen_keys:
                continue

            # add newly accepted constituent to the chart
            chart.append(current)
            seen_keys.add(current.key())
            chart_by_variable[current.symbol.variable].append(current)

            # 3. find possible partner entries
            # only retrieve entries whose variables can legally co-occur with the current variable in some rule RHS
            # e.g., if grammar contains: S -> NP VP and current variable is NP, then only VP entries are considered
            partner_vars = self.grammar.get_partner_vars(current.symbol.variable)

            if partner_vars:
                candidates = [
                    entry
                    for var in partner_vars
                    for entry in chart_by_variable.get(var, [])
                ]

            else:
                # if no partner index exists, try combining with all chart entries
                candidates = chart

            # 4. attempt binary combinations
            for other in candidates:
                # skip self-combination.
                if other is current:
                    continue
                
                # MCFG rules are order-sensitive, so attempt both: (current, other), (other, current)
                new_entries = self._combine_both_orders(current, other, next_id,)

                for new_entry in new_entries:
                    next_id += 1
                    # only unexplored constituents are pushed back onto the agenda
                    if new_entry.key() not in seen_keys:
                        agenda.append(new_entry)

        return chart

    def _combine_both_orders(self, first: AgendaEntry, second: AgendaEntry, next_id: int,) -> list[AgendaEntry]:
        
        """
        Attempt to combine two agenda entries in both possible orders.
        Since MCFG production rules are order-sensitive, both (A, B) and (B, A) must be tested separately.
        
        Parameters
        ----------
        first : AgendaEntry
            First chart entry.
        second : AgendaEntry
            Second chart entry.
        next_id : int
            Starting ID assigned to newly created entries.

        Returns
        -------
        list[AgendaEntry]
            Newly derived agenda entries.
        """        

        # try combining two entries in both orders
        results: list[AgendaEntry] = []

        # try first, second
        results.extend(self._combine_in_order(first, second, next_id + len(results),))

        # try second, first
        results.extend(self._combine_in_order(second, first, next_id + len(results),))

        return results

    def _combine_in_order(self, left: AgendaEntry, right: AgendaEntry, next_id: int,) -> list[AgendaEntry]:
        """

        Attempt to combine two entries in a fixed order.
        This checks whether the pair of instantiated symbols matches the right-hand side of any grammar rule.

        Parameters
        ----------
        left : AgendaEntry
            Left chart entry.
        right : AgendaEntry
            Right chart entry.
        next_id : int
            Starting ID assigned to newly created entries.

        Returns
        -------
        list[AgendaEntry]
            Newly derived agenda entries.
            
        """
        # try to combine two entries in a fixed order to check whether there is a grammar rule whose right side matches the two instantiated symbols
        results: list[AgendaEntry] = []

        # grammar.reduce(left, right) should return rules whose RHS aligns with these two instantiated symbols
        # e.g., S(uv) -> NP(u) VP(v) matches NP([0,2]), VP([2,5])
        for rule in self.grammar.reduce(left.symbol, right.symbol):
            try:
                # instantiate the parent constituent by combining child spans according to the MCFG rule
                parent_symbol = rule.instantiate_left_side(left.symbol, right.symbol,)

            except ValueError:
                # when spans do not satisfy the rule constraints
                continue

            results.append(
                AgendaEntry(symbol=parent_symbol, entry_id=next_id + len(results),
                    # store derivational history so parse trees can later be reconstructed from the chart
                    backpointers=((left.entry_id, left.symbol.variable), (right.entry_id, right.symbol.variable),),
                )
            )

        return results

    def _is_start_entry(self, entry: AgendaEntry, n: int) -> bool:
            
        """

        Check whether an entry represents a complete parse.

        A valid parse must use a start symbol and span the entire input sentence

        Parameters
        ----------
        entry : AgendaEntry
            Chart entry to test.
        n : int
            Length of the input sentence.

        Returns
        -------
        bool
            Whether the entry is a complete parse.

        """
        
        # check whether an entry is a complete start-symbol parse
        start_names = {start.variable for start in self.grammar.start_variables}

        return (entry.symbol.variable in start_names and entry.symbol.string_spans == ((0, n),))

    def _get_entry_by_id(self, chart: list[AgendaEntry], entry_id: int,) -> AgendaEntry:
        """

        Retrieve a chart entry by its ID.

        Parameters
        ----------
        chart : list[AgendaEntry]
            Completed parser chart.
        entry_id : int
            Entry ID to retrieve.

        Returns
        -------
        AgendaEntry
            Matching chart entry.

        Raises
        ------
        ValueError
            If no matching entry exists.
            
        """
        
        # find an entry in the chart by ID
        for entry in chart:
            if entry.entry_id == entry_id:
                return entry

        raise ValueError(f"No chart entry found with id {entry_id}")

    def _construct_tree(self, chart: list[AgendaEntry], string: list[str], entry: AgendaEntry,) -> Tree:
        """

        Recursively reconstruct a parse tree from chart backpointers.

        Parameters
        ----------
        chart : list[AgendaEntry]
            Completed parser chart.
        string : list[str]
            Input sentence.
        entry : AgendaEntry
            Root entry for reconstruction.

        Returns
        -------
        Tree
            Reconstructed parse tree.

        """
        
        # lexical entries have no backpointers because they are introduced directly from terminal rules
        # e.g., D(the) becomes Tree("D(the)")
        if not entry.backpointers:
            span = entry.symbol.string_spans[0]
            terminal = " ".join(string[span[0]:span[1]])
            return Tree(f"{entry.symbol.variable}({terminal})")

        children = []

        # recursively reconstruct child subtrees from stored backpointer IDs
        # backpointers encode the derivational history created during agenda-based parsing
        for child_id, _ in entry.backpointers:
            child_entry = self._get_entry_by_id(chart, child_id)
            children.append(self._construct_tree(chart, string, child_entry))
        return Tree(entry.symbol.variable, children)