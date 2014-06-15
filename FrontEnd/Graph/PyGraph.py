# GEFX Generator

class Node():
    def __init__(self, name):
        self.name = name
        self.starts = []
        self.ends = []

    def get_connected(self):
        return self.starts + self.ends

    def __str__(self):
        return "Node: %s" % self.name


class Edge():
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __str__(self):
        return "Edge: %s => %s " %( start.name, end.name)

class PyGraph():
    def __init__(self):
        self.node_count = 0
        self.edge_count = 0
        self.nodes = {}
        self.edges = []
    
    def add_node(self, name=""):
        if len(name) == 0:
            name = self.node_count

        node = Node(name)

        self.nodes[name] = node
        self.node_count += 1

        return node

    def add_edge(self, start, end):
        if not isinstance(start, Node):
            try:
                start = self.nodes[start]
            except KeyError:
                raise Exception, "Start node '%s' not specified." % start
        if not isinstance(end, Node):
            try:
                end = self.nodes[end]
            except KeyError:
                raise Exception, "End node '%s' not specified." % end

        edge = Edge(start, end)
        self.edges.append(edge)
        start.starts.append( end )
        end.ends.append( start )

    def get_node(self, name):
        try:
            self.nodes[name]
        except KeyError:
            raise Exception, "Node '%s' not specified." % name

    def get_nodes(self):
        return self.nodes.values()

    def get_gefx(self):
        gefx = []
        return "\n".join(gefx)


if __name__ == "__main__":
    PG = PyGraph()
    PG.add_node("John")
    PG.add_node("Mary")
    PG.add_node("Judy")
    PG.add_node("Jenny")
    PG.add_node("Marc")
    
    PG.add_edge("John","Mary")
    PG.add_edge("Mary","Jenny")
    PG.add_edge("Marc","Mary")
    PG.add_edge("Judy","Jenny")

    for node in PG.get_nodes():
        print node, "- Connected to: "
        
        for n in node.get_connected():
            print "\t", n

    
