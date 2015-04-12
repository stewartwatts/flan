import re
import pydot

# ----- globals ----- #
datatypes = [
    "int", "real", "vector", "row_vector", "matrix",
    "positive_ordered", "simplex", "unit_vector", "cov_matrix",
    "corr_matrix", "cholesky_factor_cov", "cholesky_factor_corr"
]
declaration_re = re.compile("(%s)(<[\w,\s=]+>){0,1}(\[[\w\s,\-\+\*\/]+\]){0,1}\s+([\w]+)(\[[\w\s,\+\-\*\/]+\]){0,1}" % "|".join(datatypes))
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
shapes = {
    # (block, deterministic)
    ("data", False): "rect",
    ("transformed data", False): "rect",
    ("parameters", False): "circle",
    ("parameters", True): "doublecircle",
    ("transformed parameters", False): "circle",
    ("transformed parameters", True): "doublecircle",
    ("generated quantities", True): "doubleoctagon",
    ("generated quantities", False): "doubleoctagon",
}

# ----- graph logic ----- #
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
        self.include = False          # change while parsing edges if node is involved in "~" or "<-"

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

    data -> gray filled rects
    params -> white circles
    deterministic -> double bordered
    """
    def __init__(self, nodes, edges, graph_name=None):
        self.nodes = nodes
        self.edges = edges
        self.graph_name = graph_name if graph_name else "Stan Graph"
        self.dims = list(set([node.dims for node in self.nodes if node.dims]))
        # flat list of dim names so we can exclude them from the graph
        self.flat_dims = [dim for dim_tuple in self.dims for dim in dim_tuple]
        self.clusters = {repr(dim): pydot.Cluster(str(i), 
                                                  label='%s' % repr(dim).replace("'", ""), 
                                                  fontsize=18,
                                                  labeljust="l",
                                                  labelloc="b") for i, dim in enumerate(self.dims)}
        self.graph = pydot.Dot(graph_type="digraph", label='"%s"' % graph_name)
        self.edge_pairs = []

        for node in self.nodes:
            # we don't need to plot nodes corresponding only to vector / array dims
            if node.name in self.flat_dims:
                continue
            if node.dims and node.include:
                self.clusters[repr(node.dims)].add_node(pydot.Node(node.name, 
                                                        label='"%s"' % node.name, 
                                                        style="filled",
                                                        fillcolor=fillcolors[node.block],
                                                        shape=shapes[(node.block, node.deterministic)]))
            elif node.include:
                self.graph.add_node(pydot.Node('%s' % node.name, label='"%s"' % node.name))

        for dims in self.clusters:
            self.graph.add_subgraph(self.clusters[dims])

        for edge in self.edges:
            if edge.from_name in self.flat_dims or edge.to_name in self.flat_dims:
                continue
            edge_pair = (edge.from_name, edge.to_name)
            if edge_pair not in self.edge_pairs:
                self.graph.add_edge(pydot.Edge(*edge_pair))
                self.edge_pairs.append(edge_pair)

    def write_png(self, filepath):
        self.graph.write_png(filepath)

    def to_string(self):
        # debugging
        self.graph.to_string()


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

# -- nodes -- #
def process_dims(dim, array_dim):
    dim = dim.replace("[", "").replace("]", "").replace(" ", "").split(",") if dim else []
    array_dim = array_dim.replace("[", "").replace("]", "").replace(" ", "").split(",") if array_dim else []
    dims = dim + array_dim  # sort?
    return tuple(dims) if len(dims) > 0 else None
 
def build_nodes(blocks, debug=False):
    """
    Parse code lines to create Node instances, via variable declarations.
    The model block contains no variable declarations.
    """
    block_names = ["data", "transformed data", "parameters", "transformed parameters", "generated quantities"]
    nodes_dict = {}
    for block_name in block_names:
        lines = blocks.get(block_name)
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
                    nodes_dict[name] = Node(name, datatype, constraint, process_dims(dim, array_dim), block_name)
                except:
                    if debug:
                        print "no match"
    return nodes_dict

# -- edges -- #
def collapse_multiline(lines):
    for i, line in enumerate(lines):
        if ("~" in line or "<-" in line) and line[-1] != ";":
            print "line:", line, "   last char: < %s >" % line[-1]
            raw_input("--> ")
            return collapse_multiline(lines[:i] + ["".join(lines[i:i+2])] + lines[i+2:])
    return lines

def build_edges(blocks, nodes_dict, debug=True):
    """
    Parse the blocks where we do assignment and distribution declarations for edges.
    For assignments, set the `deterministic` attribute of the assigned node to be True.
    """
    node_names = nodes_dict.keys()
    nodes_re = re.compile("|".join(node_names))
    block_names = ["transformed data", "transformed parameters", "model", "generated quantities"]
    edges = []
    for block_name in block_names:
        lines = blocks.get(block_name)
        if lines:
            lines = collapse_multiline(lines)
            lines = filter(lambda line: "~" in line or "<-" in line, lines)
            for line in lines:
                line = re.sub("\s+", "", line)
                deterministic = "<-" in line
                to_str, from_str = line.split("<-" if deterministic else "~")
                to_node = re.findall(nodes_re, to_str)[0]
                from_nodes = re.findall(from_nodes_re, from_str)
                # filter out instances where a variable name is *contained* in another variable name
                from_nodes = [n for n in from_nodes if re.search("\W%s\W" % n, ";" + from_str)]

                # save state on the nodes
                nodes_dict[to_node].include = True
                # note that this node is deterministic
                if deterministic:
                    nodes_dict[to_node].deterministic = True
                for from_node in from_nodes:
                    nodes_dict[from_node].include = True
                    edges.append(Edge(from_node, to_node))
    return edges

def parse_stan(code, graph_name=None, debug=False):
    blocks = get_blocks(code)
    if debug:
        for name in blocks:
            print name
            for line in blocks[name]:
                print "  ", line
    nodes_dict = build_nodes(blocks)
    edges = build_edges(blocks, nodes_dict)
    nodes = nodes_dict.values()
    return DAG(nodes, edges, graph_name)

