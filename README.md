# Compaison of feature implementation AST

The aim of this project is to compare java AST corresponding to features implementation and determine a relation between them.  
The source code of [BroadleafCommerce](https://github.com/BroadleafCommerce/BroadleafCommerce/) was choosen as a study case.  

------------------------------------------------------------------------------------------------------

## Prerequisites:

- A jupyter environment with python 3.11.4
- Librairies of the requirements.txt file
- A Github access Token

------------------------------------------------------------------------------------------------------

## Initialization:
1. Install the requirements.txt
2. Replace the token in the file "your_token.py" with your own token
3. Ready to go !

------------------------------------------------------------------------------------------------------
### GoodNode.py:
This module define the class GoodNode, in opposition to BadNode because of my frustration using javalang librairy. Indeed the javalang module define a tree wich is strange to run through in my case :
- the children of a node is a list containing node and/or list of nodes
- not all the nodes have a line number
- nodes don't know their parent

To create a GoodNode tree from a javalang tree:
1) create the root with the constructor
2) use the build_good_tree method

### CommitASTModule.py:
This module define the main functions I used to create the commits ASTs and Analyse them:
- generating files ASTs before and after a commit
- generating the commit AST (Parent node of the modifications)
- sorting a list of commits by the modified file and element (method, class, variable, etc.)

**Note :** most of the functions are made for GoodNode ASTs (details are documented in the code)

work in progress:
- comparing AST more precisely to determine each nodes that have been added by a commit
(the idea is detailed in the [last section](#idea-for-comparaison-algorithm))

**Demo :** the file CommitModuleDemo.ipynb is a demo of the module

### IntersectingModule.py:
Because the aim is to find the relation between differents features, I created this program wich search for couples of features implemented in the same file

## Idea for comparaison algorithm:

Here is an algoritm I tried to implements in CommitASTModule.py in the section "COMPARE AST" (but I didn't manage to finish it)

```
NAME : FindNewNodes(previousAST, currentAST, resultList)
PARAMETERS :
    - previousAST : AST of the file before the commit
    - currentAST : AST of the file after the commit
    - resultList : a list to store the new nodes
RETURN :
    At the end, resultList should contains all the new nodes added by the commit

BEGIN
    FOR each node in currentAST
        twin <- search corresponding node in previousAST
        IF twin is None
            add node to resultList
        ELSE
            FindNewNodes(twin, node, resultList)
        END IF
    END FOR
END
```

**Difficulties :** the comparaison of two javalang node is not easy because of the way the nodes are defined : most of the node attributes also represent the node children.  
Because of a lack of time (due to the first misuntderstanding of the aim of the project), I couldn't manage to compare Nodes correctly.

```
