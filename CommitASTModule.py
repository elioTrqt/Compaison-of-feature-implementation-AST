import requests
import json
import re
import base64
import javalang
from GoodNode import *
from your_token import token

#------------------------------REQUESTS SETTINGS--------------------------------#

user = "BroadleafCommerce"
repo = "BroadleafCommerce"
headers = {"Accept": "application/vnd.github+json", "Authorization" : f"Token {token}"}
baseURL = f"https://api.github.com/repos/{user}/{repo}"


#------------------------------DISPLAY FUNCTIONS--------------------------------#

def printJson(myJson):
    print(json.dumps(myJson, indent=4))

    
def print_javalang_tree(node, depth=0):
    """print a javalang AST in a readable way

    Args:
        node (Node): The node of the AST to start the print from
        depth (int, optional): indicator for the indentation. Defaults to 0.
    """
    if isinstance(node, javalang.tree.Node):
        line = node.position.line if node.position is not None else "no"
        print(line, "|     " * depth, type(node))
        print_javalang_tree(node.children, depth + 1)
    elif issubclass(type(node), list):
        for child in node:
            print_javalang_tree(child, depth)
    else:
        print("no", "|     " * depth, type(node))


#------------------------------GET COMMITS--------------------------------#

def get_commits_for_file(path):
    """Get all commits informations for a given file

    Args:
        path (str): the path of the file in the repository

    Returns:
        List[Dict[str, any]]: a list of commits informations for the given file (each returned by extract_commit_infos)
    """
    pathParams = {"path" : path}
    req_commits = requests.get(f"{baseURL}/commits", params=pathParams, headers=headers)
    if req_commits.status_code != 200:
        print(f"Error: {req_commits.status_code}")
        return None
    commits = req_commits.json()
    
    files = []
    for c in commits:
        commit = requests.get(c["url"], headers=headers).json()
        if "files" in commit:
            for file in commit["files"]:
                if file["filename"] == path:
                    files.append(extract_commit_infos(file, commit["sha"]))
    
    return files


#------------------------------EXTRACT INFORMATIONS FROM COMMIT FILE--------------------------------#

patch_pattern = "@@ -(\d+),(\d+) \+(\d+),(\d+) @@"
def extract_patch_lines(patch):
    """Extract first and last line of a commit modifications

    Args:
        patch (str): Commits informations situated in the "patch" field of a file in a commit

    Returns:
        Tuple[int, int, int, int]: tuple containing the modifications lines (new_start_line, new_end_line, old_start_line, old_end_line)
    """
    patch_first_line = patch.split("\n")[0]
    match = re.match(patch_pattern, patch_first_line)
    if match:
        old_start = int(match.group(1))
        old_end = old_start + int(match.group(2))
        new_start = int(match.group(3))
        new_end = new_start + int(match.group(4)) 
        return (new_start, new_end, old_start, old_end)
    
def extract_commit_infos(file, commit_ref):
    """Extract usefules informations from a file in a commit

    Args:
        file (Dict[str, Any]): file informations situated in an element of the "files" field of a commit
        commit_ref (str): commit reference (sha field of a commit request)

    Returns:
        Dict[str, any]: dictionary containing : the file status, the file infos given by the api, the modifications lines, the commit reference and the file name
    """
    filename = file["filename"]
    if file["status"] == "removed":
        current_file = None
        patch = None

    elif file["status"] == "added":
        current_file = requests.get(file["contents_url"], params={"ref" : commit_ref}, headers=headers).json()
        patch = None

    elif file["status"] == "modified":
        current_file = requests.get(file["contents_url"], params={"ref" : commit_ref}, headers=headers).json()
        patch = extract_patch_lines(file["patch"])

    return {"commit_ref" : commit_ref, "statut" : file["status"], "patch_lines" : patch, "file_infos" : current_file}


#------------------------------BUILD JAVALANG AST FROM COMMIT--------------------------------#

def build_commit_ast(commit, path):
    """Build the AST of a file before and after a commit

    Args:
        commit (str): id of the commit (sha field of a commit request)
        path (str): path of the file in the repository

    Returns:
        Tuple(javalang.ast.Node, javalang.ast.Node): tuple containing the AST of the file before and after the commit
    """    
    current_ref = commit["sha"]
    previous_ref = commit["parents"][0]["sha"]

    current_file = requests.get(f"{baseURL}/contents/{path}", params={"ref" : current_ref}, headers=headers).json()
    previous_file = requests.get(f"{baseURL}/contents/{path}", params={"ref" : previous_ref}, headers=headers).json()

    current_AST = javalang.parse.parse(base64.b64decode(current_file['content']).decode("utf-8"))
    previous_AST = javalang.parse.parse(base64.b64decode(previous_file['content']).decode("utf-8"))

    return (current_AST, previous_AST)


#------------------------------SEARCH IN GOODNODE AST--------------------------------#

default_types = [javalang.tree.ClassDeclaration, javalang.tree.MethodDeclaration, javalang.tree.InterfaceDeclaration, javalang.tree.EnumDeclaration, javalang.tree.AnnotationDeclaration, javalang.tree.CompilationUnit]
def find_node_at_line(good_tree, line):
    """Find the node at a given line in a GoodNode tree

    Args:
        good_tree (GoodNode): Node to start the search from (usually the root)
        line (int): line to find

    Returns:
        GoodNode: the node at the given line
    """
    if good_tree.children == []:
        return good_tree
    elif good_tree.line == line:
        return good_tree
    else:
        for i in range(len(good_tree.children)):
            if i == len(good_tree.children) - 1 or  good_tree.children[i + 1].line > line or good_tree.children[i].line == 0:
                return find_node_at_line(good_tree.children[i], line)
        
def nearest_common_parent(node1, node2, types=default_types):
    """Find the nearest common parent of two nodes

    Args:
        node1 (GoodNode): first node
        node2 (GoodNode): second node
        types (List[Type], optional): list of types to consider as common parents. Defaults to default_types.

    Returns:
        GoodNode: The nearest common parent of node1 and node2
    """
    if node1.depth > node2.depth:
        return nearest_common_parent(node1.parentNode, node2)
    elif node2.depth > node1.depth:
        return nearest_common_parent(node1, node2.parentNode)
    else:
        if node1.parentNode == node2.parentNode and node1.parentNode.type in types:
            return node1.parentNode
        else:
            return nearest_common_parent(node1.parentNode, node2.parentNode)
        
def find_commit_node(commit_infos):
    """Find the parent node of a commit modifications

    Args:
        commit_infos (Dict[str, any]): dictionary containing informations a modified file  (returned by extract_commit_infos())

    Returns:
        GoodNode: the parent node of the commit modifications
    """
    content = base64.b64decode(commit_infos["file_infos"]['content']).decode("utf-8")

    javalang_tree = javalang.parse.parse(content)

    if commit_infos["statut"] == "added":
        return javalang_tree
    elif commit_infos["statut"] == "removed":
        return None
    good_tree = GoodNode(type(javalang_tree), 0, 0, javalang_tree)
    build_good_tree(javalang_tree, good_tree)

    start = find_node_at_line(good_tree, commit_infos["patch_lines"][0])
    end = find_node_at_line(good_tree, commit_infos["patch_lines"][1])

    return nearest_common_parent(start, end)


#------------------------------SORT COMMITS--------------------------------#

def sort_commits(commits_infos):
    """Sort a list of commits by the files and the elements they modified

    Args:
        commits_infos (List[Dict[str, any]]): list of commits informations (returned by extract_commit_infos())

    Returns:
        Dict[str, Dict[str, any]]: dictionary containing the commits sorted by files and the elements they modified
    """
    sorted = {}
    default = {"other": [], "class": {}, "method": {}, "interface": {}, "enum": {}, "annotation": {}}
    current = {}
    for commit in commits_infos:
        if commit["statut"] == "modified":
            filename = commit["file_infos"]["name"]
            if not filename in sorted:
                sorted[filename] = default
            current = sorted[filename]

            node = find_commit_node(commit).javaNode
            if isinstance(node, javalang.tree.ClassDeclaration):
                add_to_dict(current["class"], node.name, commit["commit_ref"])

            elif isinstance(node, javalang.tree.MethodDeclaration):
                add_to_dict(current["method"], node.name, commit["commit_ref"])

            elif isinstance(node, javalang.tree.InterfaceDeclaration):
                add_to_dict(current["interface"], node.name, commit["commit_ref"])

            elif isinstance(node, javalang.tree.EnumDeclaration):
                add_to_dict(current["enum"], node.name, commit["commit_ref"])

            elif isinstance(node, javalang.tree.AnnotationDeclaration):
                add_to_dict(current["annotation"], node.name, commit["commit_ref"])

            elif isinstance(node, javalang.tree.CompilationUnit):
                current["other"].append(commit["commit_ref"])
                
    return sorted

def add_to_dict(dict, key, value):
    """Ajoute une valeur à une clé d'un dictionnaire, si la clé n'existe pas, elle est créée

    Args:
        dict (Dict[S, List[T]]): dictionary to add the value to
        key (S): key to add the value to
        value (T): value to add to the key
    """
    if key in dict:
        dict[key].append(value)
    else:
        dict[key] = [value]


#------------------------------COMPARE AST----------------------------------#

# WARNING !!! Don't work yet because of the my_node_equals() function

def compare_AST(previous_AST, current_AST):
    """Find the modifications added to a file in a commit

    Args:
        previous_AST (GoodNode): The ast before the commit
        current_AST (GoodNode): The ast after the commit

    Returns:
        List[GoodNodes]: List of nodes presents in the current tree but not in the previous one
    """
    current_tree = GoodNode(type(current_AST.types), 0, 0, current_AST.types)
    previous_tree = GoodNode(type(previous_AST.types), 0, 0, previous_AST.types)

    build_good_tree(current_AST, current_tree)
    build_good_tree(previous_AST, previous_tree)

    res = []
    find_diffs(previous_tree, current_tree, res)
    return res


def find_diffs(previous_tree, current_tree, result_tab):
    """Put all the new nodes of the current tree in the result_tab

    Args:
        previous_tree (GoodNode): The ast before the commit
        current_tree (GoodNode): The ast after the commit
        result_tab (List[GoodNodes]): All the new nodes of the current tree
    """
    for child in current_tree.children:
        twin = find_twin(child, previous_tree.children)
        if twin:
            find_diffs(twin, child, result_tab)
        else:
            result_tab.append(child)
        

def find_twin(node_to_find, tab):
    """find a node in a list of nodes

    Args:
        node_to_find (GoodNode): the node to find
        tab (List[GoodNode]): the list of nodes to search in

    Returns:
        GoodNode: return the node if it is found, None otherwise
    """
    for node in tab:
        if my_node_equals(node_to_find.javaNode, node.javaNode):
            return node
    return None


# TODO : find a better way to compare nodes

def my_node_equals(n1, n2):
    """compare two javalang nodes

    Args:
        n1 (javalang.ast.Node): first Node
        n2 (javalang.ast.Node): second Node

    Returns:
        bool: True if the nodes are equals, False otherwise
    """
    if type(n1) is not type(n2):
        return False

    for attr in n1.attrs:
        if attr in ["name", "label", "condition", "control", "value", "case", "method"] and getattr(n1, attr) != getattr(n2, attr):
            return False

    return True