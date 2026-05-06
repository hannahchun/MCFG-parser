import re
from collections import defaultdict

StringVariables = tuple[int, ...]

class MCFGRuleElement:

    """A multiple context free grammar rule element.

    Parameters
    ----------
    variable : str
        The nonterminal variable name.
    string_variables : StringVariables
        Variable number of string variable tuples.

    Attributes
    ----------
    variable : str
        The nonterminal variable name.
    string_variables : tuple[StringVariables, ...]
        The string variable tuples.
    """

    def __init__(self, variable: str, *string_variables: StringVariables):
        self._variable = variable
        self._string_variables = string_variables

    def __str__(self) -> str:
        strvars = ', '.join(
            ''.join(str(v) for v in vtup)
            for vtup in self._string_variables
        )
        
        return f"{self._variable}({strvars})"

    def __eq__(self, other) -> bool:
        vareq = self._variable == other._variable
        strvareq = self._string_variables == other._string_variables
        
        return vareq and strvareq
        
    def to_tuple(self) -> tuple[str, tuple[StringVariables, ...]]:
        """Convert to a hashable tuple representation.

        Returns
        -------
        tuple[str, tuple[StringVariables, ...]]
            The (variable, string_variables) tuple.
        """
        return (self._variable, self._string_variables)

    def __hash__(self) -> int:
        return hash(self.to_tuple())
        
    @property
    def variable(self) -> str:
        """The nonterminal variable name."""
        return self._variable

    @property
    def string_variables(self) -> tuple[StringVariables, ...]:
        """The string variable tuples."""
        return self._string_variables

    @property    
    def unique_string_variables(self) -> set[int]:
        """The unique string variable indices across all tuples."""
        return {
            i
            for tup in self.string_variables
            for i in tup
        }
        
SpanIndices = tuple[int, ...]

class MCFGRuleElementInstance:
    """An instantiated multiple context free grammar rule element.

    Parameters
    ----------
    variable : str
        The nonterminal variable name.
    string_spans : SpanIndices
        Variable number of span index tuples.

    Attributes
    ----------
    variable : str
        The nonterminal variable name.
    string_spans : tuple[SpanIndices, ...]
        The span index tuples.
    """
    def __init__(self, variable: str, *string_spans: SpanIndices):
        self._variable = variable
        self._string_spans = string_spans

    def __eq__(self, other: 'MCFGRuleElementInstance') -> bool:
        vareq = self._variable == other._variable
        strspaneq = self._string_spans == other._string_spans
        
        return vareq and strspaneq
        
    def to_tuple(self) -> tuple[str, tuple[SpanIndices, ...]]:
        """Convert to a hashable tuple representation.

        Returns
        -------
        tuple[str, tuple[SpanIndices, ...]]
            The (variable, string_spans) tuple.
        """
        return (self._variable, self._string_spans)

    def __hash__(self) -> int:
        return hash(self.to_tuple())

    def __str__(self):
        strspans = ', '.join(
            str(list(stup))
            for stup in self._string_spans
        )
        
        return f"{self._variable}({strspans})"

    def __repr__(self) -> str:
        return self.__str__()
    
    @property
    def variable(self) -> str:
        """The nonterminal variable name."""
        return self._variable

    @property
    def string_spans(self) -> tuple[SpanIndices, ...]:
        """The span index tuples."""
        return self._string_spans
    
SpanMap = dict[int, SpanIndices]

class MCFGRule:
    """A linear multiple context free grammar rule.

    Parameters
    ----------
    left_side : MCFGRuleElement
        The left side of the rule.
    right_side : MCFGRuleElement
        Variable number of right side elements.

    Attributes
    ----------
    left_side : MCFGRuleElement
        The left side of the rule.
    right_side : tuple[MCFGRuleElement, ...]
        The right side elements.
    """

    def __init__(self, left_side: MCFGRuleElement, *right_side: MCFGRuleElement):
        self._left_side = left_side
        self._right_side = right_side

        self._validate()

    def to_tuple(self) -> tuple[MCFGRuleElement, tuple[MCFGRuleElement, ...]]:
        """Convert to a hashable tuple representation.

        Returns
        -------
        tuple[MCFGRuleElement, tuple[MCFGRuleElement, ...]]
            The (left_side, right_side) tuple.
        """
        return (self._left_side, self._right_side)

    def __hash__(self) -> int:
        return hash(self.to_tuple())
    
    def __repr__(self) -> str:
        return '<Rule: '+str(self)+'>'
        
    def __str__(self) -> str:
        if self.is_epsilon:
            return str(self._left_side)                

        else:
            return str(self._left_side) +\
                ' -> ' +\
                ' '.join(str(el) for el in self._right_side)

    def __eq__(self, other: 'MCFGRule') -> bool:
        left_side_equal = self._left_side == other._left_side
        right_side_equal = self._right_side == other._right_side

        return left_side_equal and right_side_equal

    def _validate(self):
        vs = [
            el.unique_string_variables
            for el in self.right_side
        ]
        sharing = any(
            vs1.intersection(vs2)
            for i, vs1 in enumerate(vs)
            for j, vs2 in enumerate(vs)
            if i < j
        )

        if sharing:
            raise ValueError(
                'right side variables cannot share '
                'string variables'
            )

        if not self.is_epsilon:
            left_vars = self.left_side.unique_string_variables
            right_vars = {
                var for el in self.right_side
                for var in el.unique_string_variables
            }
            if left_vars != right_vars:
                raise ValueError(
                    'number of arguments to instantiate must '
                    'be equal to number of unique string_variables'
                )
        
    @property
    def left_side(self) -> MCFGRuleElement:
        """The left side of the rule."""
        return self._left_side

    @property
    def right_side(self) -> tuple[MCFGRuleElement, ...]:
        """The right side elements."""
        return self._right_side

    @property
    def is_epsilon(self) -> bool:
        """Whether this is an epsilon (terminal) rule."""
        return len(self._right_side) == 0

    @property
    def unique_variables(self) -> set[str]:
        """The set of unique variable names across both sides."""
        return {
            el.variable
            for el in [self._left_side]+list(self._right_side)
        }

    def instantiate_left_side(self, *right_side: MCFGRuleElementInstance) -> MCFGRuleElementInstance:
        """Instantiate the left side of the rule given an instantiated right side.

        Parameters
        ----------
        right_side : MCFGRuleElementInstance
            The instantiated right side elements.

        Returns
        -------
        MCFGRuleElementInstance
            The instantiated left side element.

        Raises
        ------
        ValueError
            If spans are not adjacent as required by the rule.
        """
        
        if self.is_epsilon:
            strvars = tuple(v[0] for v in self._left_side.string_variables)
            strconst = tuple(el.variable for el in right_side)
            
            if strconst == strvars:
                return MCFGRuleElementInstance(
                    self._left_side.variable,
                    *[s for el in right_side for s in el.string_spans]
                )

        new_spans = []
        span_map = self._build_span_map(right_side)
        
        for vs in self._left_side.string_variables:
            for i in range(1,len(vs)):
                end_prev = span_map[vs[i-1]][1]
                begin_curr = span_map[vs[i]][0]

                if end_prev != begin_curr:
                    raise ValueError(
                        f"Spans {span_map[vs[i-1]]} and {span_map[vs[i]]} "
                        f"must be adjacent according to {self} but they "
                        "are not."
                    )
                
            begin_span = span_map[vs[0]][0]
            end_span = span_map[vs[-1]][1]

            new_spans.append((begin_span, end_span))

        return MCFGRuleElementInstance(
            self._left_side.variable, *new_spans
        )

    def _build_span_map(self, right_side: tuple[MCFGRuleElementInstance, ...]) -> SpanMap:
        """Construct a mapping from string variables to string spans.

        Parameters
        ----------
        right_side : tuple[MCFGRuleElementInstance, ...]
            The instantiated right side elements.

        Returns
        -------
        SpanMap
            Mapping from string variable indices to span tuples.

        Raises
        ------
        ValueError
            If the instantiated right side does not align with the rule.
        """
        
        if self._right_side_aligns(right_side):
            return {
                strvar[0]: strspan
                for elem, eleminst in zip(
                    self._right_side,
                    right_side
                )
                for strvar, strspan in zip(
                    elem.string_variables,
                    eleminst.string_spans
                )
            }
        else:
            raise ValueError(
                f"Instantiated right side {right_side} do not "
                f"align with rule's right side {self._right_side}"
            )

    def _right_side_aligns(self, right_side: tuple[MCFGRuleElementInstance, ...]) -> bool:
        """Check whether the instantiated right side aligns with the rule.

        Parameters
        ----------
        right_side : tuple[MCFGRuleElementInstance, ...]
            The instantiated right side elements.

        Returns
        -------
        bool
            Whether the right side aligns.
        """

        if len(right_side) == len(self._right_side):
            vars_match = all(
                elem.variable == eleminst.variable
                for elem, eleminst in zip(self._right_side, right_side)
            )
            strvars_match = all(
                len(elem.string_variables) == len(eleminst.string_spans)
                for elem, eleminst in zip(self._right_side, right_side)
            )

            return vars_match and strvars_match
        else:
            return False 

    @classmethod
    def from_string(cls, rule_string) -> 'MCFGRule':
        """Parse an MCFG rule from a string representation.

        Parameters
        ----------
        rule_string : str
            The rule string to parse, e.g. ``'A(uv) -> B(u) C(v)'``.

        Returns
        -------
        MCFGRule
            The parsed rule.
        """
        elem_strs = re.findall('(\w+)\(((?:\w+,? ?)+?)\)', rule_string)

        elem_tuples = [(var, [v.strip()
                              for v in svs.split(',')])
                       for var, svs in elem_strs]

        if len(elem_tuples) == 1:
            return cls(MCFGRuleElement(elem_tuples[0][0],
                                   tuple(w for w in elem_tuples[0][1])))

        else:
            strvars = [v for _, sv in elem_tuples[1:] for v in sv]

            # no duplicate string variables
            try:
                assert len(strvars) == len(set(strvars))
            except AssertionError:
                msg = 'variables duplicated on right side of '+rule_string
                raise ValueError(msg)

            
            elem_left = MCFGRuleElement(elem_tuples[0][0],
                                    *[tuple([strvars.index(v)
                                             for v in re.findall('('+'|'.join(strvars)+')', vs)])
                                      for vs in elem_tuples[0][1]])

            elems_right = [MCFGRuleElement(var, *[(strvars.index(sv),)
                                              for sv in svs])
                           for var, svs in elem_tuples[1:]]

            return cls(elem_left, *elems_right)
        
    def string_yield(self):
        """Get the string yield of an epsilon rule.

        Returns
        -------
        str
            The variable name of the left side.

        Raises
        ------
        ValueError
            If this is not an epsilon rule.
        """
        if self.is_epsilon:
            return self._left_side.variable
        else:
            raise ValueError(
                'string_yield is only implemented for epsilon rules'
            )

class MultipleContextFreeGrammar:

    """
    A multiple context free grammar (MCFG).

    This class stores a collection of MCFG rules and provides lookup utilities used by an agenda-based parser.
    
    Parameters
    ----------
    rules : set[MCFGRule]
        Set of grammar rules
    parser_class : type[Parser]
        Parser class used for recognition and parsing
    start_variables : set[MCFGRuleElement]
        Set of start symbols
    alphabet : set[str], optional
        Set of terminal symbols
    variables : set[MCFGRuleElement], optional
        Set of nonterminal symbols
    """
    
    def __init__(
        self,
        rules: set[MCFGRule],
        parser_class,
        start_variables: set[MCFGRuleElement],
        alphabet: set[str] | None = None,
        variables: set[MCFGRuleElement] | None = None,
    ):

        self._rules = rules
        self._start_variables = start_variables
        self._parser_class = parser_class

        # infer variables if not given
        if variables is None:
            self._variables = {
                el
                for r in self._rules
                for el in (r.left_side, *r.right_side)
            }

        else:
            self._variables = variables

        # infer alphabet from epsilon rules if not given
        if alphabet is None:
            self._alphabet = {
                rule.left_side.string_variables[0][0]
                for rule in self._rules
                if rule.is_epsilon
            }

        else:
            self._alphabet = alphabet
            
        # initialize parser
        self._parser = self._parser_class(self)

    def __call__(self, string, mode="recognize"):
        
        """
        Parse or recognize a string using the parser.

        Parameters
        ----------
        string : list[str] or str
        mode : str
        
        Returns
        -------
        depends on mode
        """

        if isinstance(string, str):
            string = string.split()

        return self._parser(string, mode=mode)

    def parse(self, string):
        
        """
        Parse a string and return parse trees.

        Parameters
        ----------
        string : str | list[str]

        Returns
        -------
        set[Tree]

        """
        
        return self(string, mode="parse")

    def recognize(self, string):
        
        """
        Check whether the grammar recognizes a string.

        Parameters
        ----------
        string : str | list[str]

        Returns
        -------
        bool
        """
        
        return self(string, mode="recognize")
    
    def rules(self, left_side: str | None = None) -> set[MCFGRule]:

        """
        Get rules with the specified left-side variable.

        Parameters
        ----------
        left_side : str or None

        Returns
        -------
        set[MCFGRule]
        """

        if left_side is None:
            return self._rules

        return {
            r for r in self._rules
            if r.left_side.variable == left_side
        }

    def parts_of_speech(self, word: str) -> set[MCFGRule]:

        """
        Return epsilon rules that produce this word.

        Parameters
        ----------
        word : str

        Returns
        -------
        set[MCFGRule]
        """

        return {
            r for r in self._rules
            if r.is_epsilon
            if r.left_side.string_variables[0][0] == word
        }

    def _partner_index(self) -> dict[str, set[str]]:
        
        """
        Build index of which variables co-occur in RHS.
        Used to limit combination candidates in agenda parser.
        
        Returns
        -------
        dict[str, set[str]]
            Mapping from a variable name to the set of variable names that appear alongside it in a rule right side
        """

        index = defaultdict(set)

        for rule in self._rules:
            if len(rule.right_side) == 2:
                a = rule.right_side[0].variable
                b = rule.right_side[1].variable
                index[a].add(b)
                index[b].add(a)

        return dict(index)     
    
    def get_partner_vars(self, var: str) -> set[str]:
        
        """
        Return variables that co-occur with the given variable on the right-hand side of grammar rules.

        Parameters
        ----------
        var : str
            Variable name

        Returns
        -------
        set[str]
            Variables that may combine with the given variable during agenda parsing
        """
        
        return self._partner_index().get(var, set())

    def reduce(self, left: MCFGRuleElementInstance, right: MCFGRuleElementInstance) -> set[MCFGRule]:

        """
        Find rules whose RHS matches (left, right).
        This is used by the agenda parser to combine constituents.

        Parameters
        ----------
        left : MCFGRuleElementInstance
            Left instantiated symbol
        right : MCFGRuleElementInstance
            Right instantiated symbol
            
        Returns
        -------
        set[MCFGRule]
            Rules whose right side matches the given pair of instantiated symbols
        """

        return {
            r for r in self._rules
            if r._right_side_aligns((left, right))
        }

    @property
    def alphabet(self):
        return self._alphabet

    @property
    def variables(self):
        return self._variables

    @property
    def start_variables(self):
        return self._start_variables
