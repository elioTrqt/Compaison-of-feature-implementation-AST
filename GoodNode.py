import javalang

class GoodNode:
    """A class to get through the AST in an easier way than with javalang.\n
    The main difference are :
    - The children are stored in a list instead of a generator
    - Positionless nodes are not stored
    - The depth of the node is stored
    - The parent node is stored
    - The corresponding javalang node is stored

    Attributes:
        _parentNode (GoodNode): The parent node
        _children (List[GoodNode]): The children nodes
        _type (type): The type of the javalang node
        _depth (int): The depth of the node in the tree
        _line (int): The line of the node in the file
        _javaNode (javalang.tree.Node): The corresponding javalang node
    """ 
    def __init__(self, type, line, depth, javaNode, parent=None):
        self._parentNode = parent
        self._children = []
        self._type = type
        self._depth = depth
        self._line = line
        self._javaNode = javaNode
    
    # Getter for parentNode
    @property
    def parentNode(self):
        return self._parentNode

    # Setter for parentNode
    @parentNode.setter
    def parentNode(self, parent):
        self._parentNode = parent

    # Getter for line
    @property
    def line(self):
        return self._line

    # Setter for line
    @line.setter
    def line(self, line):
        self._line = line

     # Getter for javaNode
    @property
    def javaNode(self):
        return self._javaNode

    # Setter for javaNode
    @javaNode.setter
    def javaNode(self, javaNode):
        self._javaNode = javaNode

    # Getter for children
    @property
    def children(self):
        return self._children

    # Setter for children
    @children.setter
    def children(self, children_list):
        self._children = children_list

    # Method to add a child to children
    def add_child(self, child):
        self._children.append(child)
        child.parentNode = self

    # Getter for type
    @property
    def type(self):
        return self._type

    # Setter for type
    @type.setter
    def type(self, node_type):
        self._type = node_type

    # Getter for depth
    @property
    def depth(self):
        return self._depth

    # Setter for depth
    @depth.setter
    def depth(self, new_depth):
        self._depth = new_depth

def build_good_tree(node, parent, depth=0):
    """Build a GoodNode tree from a javalang tree

    Args:
        node (javalang.tree.Node): the javalang node to start the build from
        parent (GoodNode): the parent node of the node to build (usually start with the root)
        depth (int, optional): depth of the current node. Defaults to 0.
    """    
    if isinstance(node, javalang.tree.Node):
        if node.position is not None:
            new_node = GoodNode(type(node), node.position.line, depth, node)
            parent.add_child(new_node)
            build_good_tree(node.children, new_node, depth + 1)
        else:
            build_good_tree(node.children, parent, depth + 1)
    elif issubclass(type(node), list):
        for child in node:
            build_good_tree(child, parent, depth)

def print_good_tree(node):
    """Print a GoodNode tree in a readable way

    Args:
        node (GoodNode): The node to start the print from (usually the root)
    """    
    print(node.line, "|     " * node.depth, node.type)
    for child in node.children:
        print_good_tree(child)