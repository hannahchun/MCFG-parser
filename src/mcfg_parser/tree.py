import pyparsing

from collections.abc import Hashable, Callable

DataType = Hashable
TreeList = list[str, list['TreeList'] | None]
TreeTuple = tuple[DataType, tuple['TreeTuple', ...] | None]

class Tree:
    """A tree data structure with parsing and search capabilities.

    Parameters
    ----------
    data : DataType
        The data stored at this node.
    children : list[Tree]
        The children of this node.
    """

    LPAR = pyparsing.Suppress('(')
    RPAR = pyparsing.Suppress(')')
    DATA = pyparsing.Regex(r'[^\(\)\s]+')

    PARSER = pyparsing.Forward()
    SUBTREE = pyparsing.ZeroOrMore(PARSER)
    PARSERLIST = pyparsing.Group(LPAR + DATA + SUBTREE + RPAR)
    PARSER <<= DATA | PARSERLIST
    
    def __init__(self, data: DataType, children: list['Tree'] = []):
        self._data = data
        self._children = children
        
        self._validate()
  
    def to_tuple(self) -> TreeTuple:
        """Convert this tree to a nested tuple representation.

        Returns
        -------
        TreeTuple
            Nested tuple of (data, children_tuples).
        """
        return self._data, tuple(c.to_tuple() for c in self._children)

    def __hash__(self) -> int:
        return hash(self.to_tuple())
    
    def __eq__(self, other: 'Tree') -> bool:
        return self.to_tuple() == other.to_tuple()

    def __str__(self) -> str:
        return ' '.join(self.terminals)
        
    def __repr__(self) -> str:
        return self.to_string()
     
    def to_string(self, depth=0) -> str:
        """Render this tree as an indented string.

        Parameters
        ----------
        depth : int
            Current depth for indentation.

        Returns
        -------
        str
            Indented string representation of the tree.
        """
        s = (depth - 1) * '  ' +\
            int(depth > 0) * '--' +\
            self._data + '\n'
        s += ''.join(c.to_string(depth+1)
                     for c in self._children)
        
        return s
    
    def __contains__(self, data: DataType) -> bool:
        # pre-order depth-first search
        if self._data == data:
            return True
        else:
            for child in self._children:
                if data in child:
                    return True
                
            return False
        
    def __getitem__(self, idx: int | tuple[int, ...]) -> 'Tree':
        if isinstance(idx, int):
            return self._children[idx]
        elif len(idx) == 1:
            return self._children[idx[0]]
        elif idx:
            return self._children[idx[0]].__getitem__(idx[1:])
        else:
            return self
        
    @property
    def data(self) -> DataType:
        """The data stored at this node."""
        return self._data 
    
    @property
    def children(self) -> list['Tree']:
        """The children of this node."""
        return self._children
     
    @property
    def terminals(self) -> list[str]:
        """The terminal (leaf) strings of this tree."""
        if self._children:
            return [w for c in self._children 
                    for w in c.terminals]
        else:
            return [str(self._data)]
        
    def _validate(self) -> None:
        try:
            assert all(isinstance(c, Tree)
                       for c in self._children)
        except AssertionError:
            msg = 'all children must be trees'
            raise TypeError(msg)
            
    def index(self, data: DataType, index_path: tuple[int, ...] = tuple()) -> list[tuple[int, ...]]:
        """Find all index paths to nodes matching the given data.

        Parameters
        ----------
        data : DataType
            The data to search for.
        index_path : tuple[int, ...]
            The current path prefix for recursive calls.

        Returns
        -------
        list[tuple[int, ...]]
            List of index paths to matching nodes.
        """
        indices = [index_path] if self._data==data else []
        root_path = [] if index_path == -1 else index_path
        
        indices += [j 
                    for i, c in enumerate(self._children) 
                    for j in c.index(data, root_path+(i,))]

        return indices
    
    def relabel(self, label_map: Callable[[DataType], DataType], 
                nonterminals_only: bool = False, terminals_only: bool = False) -> 'Tree':
        """Create a copy of this tree with relabeled nodes.

        Parameters
        ----------
        label_map : Callable[[DataType], DataType]
            Function to apply to each node's data.
        nonterminals_only : bool
            If True, only relabel nonterminal nodes.
        terminals_only : bool
            If True, only relabel terminal nodes.

        Returns
        -------
        Tree
            A new tree with relabeled nodes.
        """
        if not nonterminals_only and not terminals_only:
            data = label_map(self._data)
        elif nonterminals_only and self._children:
            data = label_map(self._data)
        elif terminals_only and not self._children:
            data = label_map(self._data)
        else:
            data = self._data
        
        children = [c.relabel(label_map, nonterminals_only, terminals_only) 
                    for c in self._children]
        
        return self.__class__(data, children)
    
    @classmethod
    def from_string(cls, treestr: str) -> 'Tree':
        """Parse a tree from a parenthesized string representation.

        Parameters
        ----------
        treestr : str
            The parenthesized string to parse.

        Returns
        -------
        Tree
            The parsed tree.
        """
        treelist = cls.PARSER.parse_string(treestr)[0]
        
        return cls.from_list(treelist)
    
    @classmethod
    def from_list(cls, treelist: TreeList) -> 'Tree':
        """Build a tree from a nested list representation.

        Parameters
        ----------
        treelist : TreeList
            The nested list to convert.

        Returns
        -------
        Tree
            The constructed tree.
        """
        if isinstance(treelist, str):
            return cls(treelist[0])
        elif isinstance(treelist[1], str):
            return cls(treelist[0], [cls(treelist[1])])
        else:
            return cls(treelist[0], [cls.from_list(l) for l in treelist[1:]])