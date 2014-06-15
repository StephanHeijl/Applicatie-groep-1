# Graph nodes test
from StringIO import StringIO
from ElegantAPI import *
from models import *
import networkx as nx
import re,sys, copy

class Graph():
	def __init__(self):
		self.nodeCollection = []
		self.edgeCollection = []
	
	def selectNodes(self, node, depth=0):
		n = Node().get(value=node).take(0)
		edges = Edge().get(source=n).collection
		edges += Edge().get(end=n).collection
		
		nodeCollection = [n]
		for edge in edges:
			if edge.source not in nodeCollection:
				nodeCollection.append(edge.source)
			if edge.end not in nodeCollection:
				nodeCollection.append(edge.end)
				
		nodeCollection = list(set(nodeCollection))
		edgeCollection = edges
		
		if depth > 0:
			thisLayer = copy.copy(nodeCollection)
			for node in thisLayer:
				print "Starting on node %s out of %s" % ( thisLayer.index(node), len(thisLayer))
				if node == n:
					continue
				nn, ne = self.selectNodes(str(node.value.value),depth=(depth-1))
				nodeCollection = list(set( nodeCollection + nn ))
				edgeCollection = list(set( edgeCollection + ne ))
			
			return nodeCollection, edgeCollection
		else:
			print "Done"
			return list(set(nodeCollection)), list(set(edgeCollection))
	
	def make(self, percentile=0, node=None, depth=-1):
		searchNodeType = NodeType().get(name="Search node").take(0)
		if node and depth > -1:
			try:
				nodeCollection, edgeCollection = self.selectNodes(node,depth)
			except IndexError:
				self.G=nx.Graph()
				self.G.add_node(	node,
									node_color=searchNodeType.color.value,
									node_id=-1,
									node_type=int(searchNodeType.id.value) )
				return False
		else:
			nodeCollection = Node().get().collection
			edgeCollection = Edge().get().collection

		edges = [(edge.source.value.value,edge.end.value.value) for edge in edgeCollection]
		scores = sorted([edge.score.value for edge in edgeCollection])

		self.G=nx.Graph()
	
		for n in nodeCollection:
			if n.value.value == node:
				self.G.add_node(	n.value.value, 
									node_color=searchNodeType.color.value, 
									node_id=int(n.id.value),
									node_type=int(searchNodeType.id.value)	)				
			else :
				self.G.add_node(	n.value.value, 
									node_color=n.type.color.value, 
									node_id=int(n.id.value),
									node_type=int(n.type.id.value)	)

		for edge in edgeCollection:	
			try:
				green_ratio = float(edge.positivescore.value) / float(edge.negativescore.value) * 128
			except ZeroDivisionError:
				green_ratio = 255
			red_ratio = 255 - green_ratio
			
			if green_ratio < 0:
				green_ratio, red_ratio = 0, 255
				
			if red_ratio < 0:
				green_ratio, red_ratio = 255,0
			
			
			red = re.sub( "[^\w\d]|0x", "", hex(int(red_ratio)))
			green = re.sub( "[^\w\d]|0x", "", hex(int(green_ratio)))
			color = "#" + red.ljust(2,"0") + green.ljust(2,"0") + "00"
			
				
			if edge.score.value > max(scores) * (float(percentile)/100):	
				self.G.add_edge(	edge.source.value.value,
									edge.end.value.value,
									Positive_Score=int(edge.positivescore.value),
									Negative_Score=int(edge.negativescore.value),
									Score=int(edge.score.value),
									edge_color=color	)
									
		return True
	
	def export(self):
		f = StringIO()
		nx.write_gexf(self.G,f)

		xml = f.getvalue()
		attrs = re.findall('<attribute .+? title="(\w+)"', xml)
		attrIds = re.findall('<attribute id="(\d+)?"', xml)
	
		for attr, attrId in zip(attrs, attrIds):
			xml = xml.replace('id="%s"' % attrId, 'id="%s"' % attr )
			xml = xml.replace('for="%s"' % attrId, 'for="%s"' % attr  )
			
		return xml
		
if __name__ == "__main__":
	graph = Graph()
	
	if len(sys.argv) > 1:
		print sys.argv[1:]
		xmlName = "graph.%s.%s.%s.xml" % tuple(sys.argv[1:])
		
		getGraph = GraphCache().get(name=xmlName)
		
		if not getGraph or len(getGraph.collection) == 0 or getGraph.collection[0].isExpired():
			graph.make(int(sys.argv[1]), sys.argv[2], int(sys.argv[3]) )
			xml = graph.export()
			
			gc = GraphCache ( name=xmlName, xml=xml )
			gc.save()
		else:	
			xml = getGraph.collection[0].xml.value
			print xml
			
	else:
		graph.make()
		gc = GraphCache()
	
	