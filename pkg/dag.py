import re
import pydot

# ----- temp ----- #
fn = "/home/stewartwatts/flan/pkg/models/example/eight_schools_001/model.stan"
code = open(fn).read()

# ----- globals ----- #
datatypes = [
    "int", "real", "vector", "row_vector", "matrix",
    "positive_ordered", "simplex", "unit_vector", "cov_matrix",
    "corr_matrix", "cholesky_factor_cov", "cholesky_factor_corr"
]
declaration_re = re.compile("(%s)(<[\w,=]+>){0,1}(\[[\w,\-\+\*\/]\]){0,1} ([\w_]+)(\[[\w,\+\-\*\/]+\]){0,1}" % "|".join(datatypes))
# regexs to pull out code blocks
regexs = [
    ("data", re.compile("data\s*{")),
    ("transformed data", re.compile("transformed data\s*{")),
    ("parameters", re.compile("parameters\s*{")),
    ("transformed parameters", re.compile("transformed parameters\s*{")),
    ("model", re.compile("model\s*{")),
    ("generated quantities", re.compile("generated quantities\s*{")),
]
fillcolors = {
    "data": "slategray",
    "transformed data": "slategray", 
    "parameters": "white",
    "transformed parameters": "white",
    "generated quantities": "deepskyblue2",
}

# data -> gray filled rects
# params -> white circles
# deterministic -> double bordered
# plates for iteration/vectorization (by unique index)


class Node(object):
    """
    `name`: Stan variable name
    `datatype`: int, real, vector, etc
    `dims`: tuple of the dimensions that index the variable, or None for scalar params
      matrix[N,M] real[2,2] -> ("N", "M", "2", "2")
    `block`: block where defined
    `deterministic`: True if defined "<-"; False if defined by "~"
    """
    def __init__(self, name, datatype, constraint, dims, block):
        self.name = name
        self.datatype = datatype
        self.constraint = constraint
        self.dims = dims
        self.block = block
        self.deterministic = False    # change while parsing edges if deterministic

class Edge(object):
    def __init__(self, from_name, to_name):
        self.from_name = from_name
        self.to_name = to_name

class DAG(object):
    """
    Drawing overlapping plates is not possible with Graphviz's Dot framework.
    Plates, pydot.Cluster instances, correspond to uniquely-indexed Stan variables.
    This splits up plates that should actually be drawn together.
    It should remain somewhat easy to follow what is going on. 
    """
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges
        self.dims = list(set([node.dim for node in self.nodes if node.dim]))
        self.clusters = {repr(dim): pydot.Cluster(repr(dim), label=repr(dim), fontsize=20) for dim in self.dims}
        self.graph = pydot.Dot(graph_type="digraph")

        for node in self.nodes:
            if node.dim:
                self.clusters[repr(node.dim)].add_node(pydot.Node(node.name, 
                                                       label=node.name, 
                                                       style="filled",
                                                       fillcolor=fillcolors[node.block]))
            else:
                self.graph.add_node(pydot.Node(node.name, label=node.name))

        for cluster in self.clusters:
            self.graph.add_subgraph(cluster)

        for edge in self.edges:
            self.graph.add_edge(pydot.Edge(edge.from_name, edge.to_name))

    def write_graph(self, filepath):
        self.graph.write_png(filepath)


# ----- parsing logic ----- #
def preprocess_code(code):
    # strip comments and leading/trailing whitespace
    code = re.sub("/\*.*?\*/", "", code)
    lines = [re.sub("//.*$", "", line).strip() for line in code.split("\n")]
    code = "\n".join(lines)
    return code

def get_block(code, regex):
    # return list of lines for a block
    i, depth = None, None
    m = regex.search(code)
    if m:
        s = ""
        i = m.end()
        depth = 1
        while depth > 0:
            if code[i] == "}":
                depth -= 1
            elif code[i] == "{":
                depth += 1
            if depth > 0:
                s += code[i]
            i += 1
        s = s.strip()
        return s.split("\n")
    else:
        return None

def get_blocks(code):
    # blocks: name -> list of lines
    code = preprocess_code(code)
    blocks = {}
    for name, regex in regexs:
        block = get_block(code, regex)
        if block:
            blocks[name] = block
    return blocks

def process_dims(dim, array_dim):
    dim = dim.replace("[", "").replace("]", "").split(",") if dim else []
    array_dim = array_dim.replace("[", "").replace("]", "").split(",") if array_dim else []
    dims = dim + array_dim  # sort?
    return dims if len(dims) > 0 else None
 
def build_nodes(blocks, debug=False):
    """
    Parse code lines to create Node instances, via variable declarations.
    The model block contains no variable declarations.
    """
    block_names = ["data", "transformed data", "parameters", "transformed parameters", "generated quantities"]
    nodes = {}
    for block_name in block_names:
        lines = blocks.get(name)
        if lines:
            for line in lines:
                try:
                    datatype, constraint, dim, name, array_dim = declaration_re.match(line).groups()
                    if debug:
                        print "\n\n", line
                        print "datatype:", datatype 
                        print "constraint:", constraint
                        print "dim:", dim
                        print "name:", name
                        print "array_dim:", array_dim
                    nodes[name] = Node(name, datatype, constraint, process_dims(dim, array_dim), block_name)
                except:
                    if debug:
                        print "no match"
    return nodes

def build_edges(blocks, nodes):
    """
    Parse the blocks where we do assignment and distribution declarations for edges.
    For assignments, set the `deterministic` attribute of the assigned node to be True.
    """
    node_names = nodes.keys()
    block_names = ["transformed data", "transformed parameters", "model", "generated quantities"]

    return edges

def parse_stan(code):
    blocks = get_blocks(code)

    # temp
    for name in blocks:
        print name
        for line in blocks[name]:
            print "  ", line




