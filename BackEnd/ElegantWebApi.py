# ElegantWebApi.py
# Functie: Hier worden alle ElegantApi elementen aan het web blootgesteld.
# Auteurs: Stephan Heijl & Roel Beumers
# Versie: 0.81
# Datum: 3/6/2013

from ElegantAPI import *
import models
from models import * 
from mod_python import apache

import json, os, threading, traceback

from mod_python import util

from Search import *

def rel(*x):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)),*x)
	
def index(req):
	req.content_type = "text/html"
	req.write("WebApi")

def data(req, model, **kwargs):
	req.content_type = "application/json"
	
	kwargs = dict([(key, value.split("||")) for key,value in kwargs.items()])
	
	model = getattr(models, model)()
	coll = model.get(flat=True, **kwargs).collection
	
	results = []
	
	for inst in coll:
		instResults = {}
		for key, value in inst.getFields().items():
			if key[0] != "_":
				if isinstance(value.value, datetime.date):
					instResults[key] = str(value.value)
				else:
					instResults[key] = value.value
		
		results.append(instResults)
	
	req.write(json.dumps(results))
	
def graph(req, threshold=0,  node=None, depth=0):
	from graph import Graph
	req.content_type = "text"	
	
	xmlName = "graph.%s.%s.%s.xml" % (threshold, node, depth)
	getGraph = GraphCache().get(name=xmlName)
	
	if not getGraph or len(getGraph.collection) == 0 or getGraph.collection[0].isExpired():
		graph = Graph()
		
		doSave = graph.make(int(threshold), node, int(depth))
		xml = graph.export()
		
		if doSave:
			gc = GraphCache ( name=xmlName, xml=xml )
			gc.save()
	else:
		xml = getGraph.collection[0].xml.value
		
	req.write(xml)
	
def search(req, start=0, limit=10, **kwargs):
	req.content_type = "application/json"
	
	where = []
	for key,value in kwargs.items():
		if len(value) == 0:
			continue 
			
		if ";" in value:
			where.append( (key, Query(**{"%s__in" % key: "%s" % value}) ) )
		else:
			try:
				if int(value) > 0:
					where.append( (key, Query(**{"%s__is" % key: "%s" % value}) ) )			
			except Exception as e:
				where.append( (key, Query(**{"%s__like" % key: ("%%%s%%" % value).replace("*","%") }) ) ) 
		
	where = dict(where)
	
	results = Node().get(	flat=True,
							limit="%s,%s" % (start,limit),
							**where)
	
	nodes = []
	for result in results.collection:
		nodes.append({ })
		for field in result.getFields():
			try:
				if field[0] != "_":
					nodes[-1][field] = getattr(result, field).value
			except:
				pass
	
	req.write( json.dumps(nodes) )

class newSearch(threading.Thread):
	def __init__(self, word, req):
		super(newSearch, self).__init__()
		self.word = word
		self.found = False
		self.req = req
		
	def run( self ):
		global currentThreads
		word = self.word
		tries = 1
		found = False
				
		while not found and tries < 5: 
			try:
				an = Analyze()
				
				if an.search(-1, word[0], word[1]):
					an.score(onlyNew=False)
					an.saveResults()
					
				found = True
				currentThreads -= 1
								
			except ValueError as e:
				found = True	
				continue
			
			except NotXMLError as e:
				found = True
				continue
			
			except Exception as e:
				t = 5*tries
				time.sleep(t)
				tries+=1

def new(req, term, type):	
	type = max(type) # Quick fix for a form bug 
	
	terms = [n.value.value for n in  Node().get(type=Query(type__not=type)).collection ]
	
	req.content_type = "text/html"
	
	t= 0
	global currentThreads
	currentThreads = 0
	
	bars = 100 
	total = len(terms)
	bar = total/bars
	c = 0
	
	req.write( "Percentage shown as an amount of bars (%s) \n" % bars )
	req.write( ( "_" * bars ) + "\n" )
	 
	while t < total:
		if currentThreads < 20:
			s = newSearch((terms[t], (term,int(type) )), req) # 
			s.setDaemon(True) 
			s.start()			
			
			t+=1
			c+=1
			if c == bar:
				c = 0
				req.write( "|" )
			
			currentThreads+=1 
		else:
			time.sleep(0.5)
	
	# Join all threads properly
	main_thread = threading.currentThread()
	for t in threading.enumerate():
		if t is main_thread:
			continue
		t.join()
	
	req.write(json.dumps({"Complete":"Succes", "Searches":len(terms) }) )
	
	req.write("<script> window.top.location.href='../../FrontEnd/success.psp?term=%s'; </script>" % term)
			
		