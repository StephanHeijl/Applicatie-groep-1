import sys
sys.path.insert(0, "/home/owe8_pg1/public_html/Applicatie/BackEnd/" ) # Load Elegant Modules

from ElegantAPI import *
from models import *

from Bio import Entrez
import itertools, random, time, traceback, threading

# Analyseert & scoort artikelen
# Auteurs: Roel Beumers & Stephan Heijl
#
# Versies:
# v1: Originele functionaliteit, Roel Beumers
# v2: Aangepast voor server, API integratie

class Analyze(object):
	def __init__(self):
		self.__parseconfig()
		self.articles = []
		
	def rel(self, *x):
		return os.path.join(os.path.abspath(os.path.dirname(__file__)),*x)
		
	def __parseconfig(self, f="entrez.config"):
		conf = open(self.rel(f))
		config = {}
		for line in conf.read().split("\n"):
			if len(line) > 0 and line[0] != "#":
				try:
					key, val = line.split("=")
				except:
					continue
				
				config[key.strip()] = val.strip()
		self.config = config
	
	def __retreiveFromPubMed(self, idlist):
		articles = []
		for id in idlist:
			article = Entrez.efetch(db="pubmed", id=id, retmode="text", rettype="xml")
			try:
				art = self.__parse( Entrez.read( article )[0], id )
			except IndexError:
				art = self.__parse( Entrez.read( article ), id )
			articles.append(art)
			
		return articles
	
	def __parse(self, record, id):
		# Article title
		try:
			if 'BookDocument' in record:
				Title = record['BookDocument']['ArticleTitle']
			else:
				Title = record['MedlineCitation']['Article']['ArticleTitle']
		except KeyError:
			return
		
		# Article abstract
		try:
			if 'BookDocument' in record:
				Abstract = record['BookDocument']['Abstract']['AbstractText'][0]
			else:
				Abstract = record['MedlineCitation']['Article']['Abstract']['AbstractText'][0]
		
		except KeyError:
			Abstract = ""
		
		# Article authors
		Authors = []
		try:
			if 'BookDocument' in record:	
				AuthorsList = record['BookDocument']['AuthorList']
			else:
				AuthorsList = record['MedlineCitation']['Article']['AuthorList']
				
			for author in AuthorsList:
				try:
					Authors.append(author["ForeName"] + " " + author["LastName"])
				except:
					continue
		
			Authors = ", ".join(Authors)
			
		except KeyError, TypeError:
			Authors = ""
		
		# Article journal
		try:
			if 'BookDocument' in record:
				Journal = ""
			else:
				Journal =  record['MedlineCitation']['Article']['Journal']['Title']
			
		except KeyError:
			Journal = ""
		
		# Article keywords
		if 'BookDocument' in record:
			KeywordsList = record['BookDocument']['KeywordList']
		else:
			KeywordsList = record['MedlineCitation']['KeywordList']
			
		
		Keywords = []
		for listElement in KeywordsList:
			for kw in listElement:
				Keywords.append( unicode(kw) )
				
		# Article created
		try:
			if 'BookDocument' in record:
				DateCreatedDict = record['BookDocument']['DateRevised']
			else:
				DateCreatedDict = record['MedlineCitation']['DateCreated']
			
			DateCreated = "-".join([DateCreatedDict['Year'], DateCreatedDict['Month'], DateCreatedDict['Day']])
		except KeyError:
			DateCreated = "0000-00-00"
		
		# Output in markdown		
		article = Article(	id=int(id),
							title=unicode(Title), 
							authors=unicode(Authors), 
							journal=unicode(Journal), 
							publish_date=unicode(DateCreated), 
							abstract=unicode(Abstract) )
		article.save()
		return article
		
	
	def __retreiveFromDatabase(self, idlist):
		inQ = Query(id__in=idlist)
		savedArticles = Article().get(id=inQ).collection
		return savedArticles
	
			
	def score(self, onlyNew=True):
		if len(self.articles) == 0:
			print "Please start a search first"
			return 0
			
		titleScore 		= 10
		abstractScore 	= 5
		keywordScore 	= 15
		
		self.positiveScore 	= 0
		self.negativeScore 	= 0
		self.score			= 0
		
		checkWords = Keyword().get().collection
		for article in self.articles:
			if not article:
				continue
			for word in checkWords:
				try:
					titleCount = article.title.value.encode("utf-8","ignore").count(word.word.value)
					if titleCount > 0:
						self.positiveScore 	+= word.keyword_type.positive_score.value * titleCount
						self.negativeScore 	+= word.keyword_type.negative_score.value * titleCount
						self.score			+= titleCount * titleScore
						
					abstractCount = article.abstract.value.encode("utf-8","ignore").count(word.word.value)
					if abstractCount > 0:
						self.positiveScore 	+= word.keyword_type.positive_score.value * abstractCount
						self.negativeScore 	+= word.keyword_type.negative_score.value * abstractCount
						self.score			+= abstractCount * abstractScore
						
				except UnicodeDecodeError:
					continue
					
						
	def search(self, limit=-1, *terms):			
		self.terms = terms
				
		try:
			Entrez.email = self.config['email']
		except KeyError:
			print "No email has been added to the config file. Add it like so: email=john@example.org"
			return
			
		try:
			if limit<0:
				retreivelimit = int(self.config['retmax'])
			else:
				retreivelimit = int(min(self.config['retmax'],limit))
			
		except KeyError, ValueError:
			print "No retreival limit has been added to the config file. Add it like so: retmax=100"
			return
			
		handle	= Entrez.esearch(db="pubmed", term=" AND ".join(['"%s"' % t[0] for t in self.terms]),  retmax=retreivelimit)
		results	= Entrez.read(handle, validate=False)
		
		count 	= results['Count']
		idlist	= results['IdList']
		
		if len(idlist) == 0:
			print "No results"
			return False
		
		inDb = self.__retreiveFromDatabase(idlist)
		
		foundIds = [str(article.id.value) for article in inDb]
		print "Found %s articles. " % len(idlist)
		
		self.articles = inDb
		print "%s of these are already in the database. Downloading %s articles." % ( len(inDb), len(idlist)-len(inDb))
		remaining = list(set(idlist).difference(set(foundIds)))
		downloaded = self.__retreiveFromPubMed(remaining)
		
		self.downloaded = downloaded
		self.articles += downloaded
		
		return True
	
	def saveResults(self):
		if not self.score:
			print "Please score the search results first"
			return 
		
		nodes = {}
		for term in self.terms:			
			try:
				nodes[term] = Node().get(value=term[0]).take(0)
			except:
				try:
					Node(value=term[0], type=NodeType().get(id=term[1]).take(0)).save()
					nodes[term] = Node().get(value=term[0]).take(0)
				except:
					return
		
		for combination in itertools.combinations(self.terms, 2):
			e = Edge(	source=nodes[combination[0]], 
						end=nodes[combination[1]],
						positivescore=self.positiveScore,
						negativescore=self.negativeScore,
						score=self.score
					)
			e.save()
			
			for article in self.downloaded:
				EdgeArt(edge=e,article=article).save()
				

class initSearch(threading.Thread):
	def __init__(self, word):
		super(initSearch, self).__init__()
		self.word = word
		
		
	def run(self ):
		word = self.word
		tries = 1
		found = False
		while not found: 
			try:
				print word
				an = Analyze()
				if an.search(-1, word[0], word[1])			:
					an.score(onlyNew=False)
					an.saveResults()
					
				found = True
			except ValueError as e:
				found = True				
				continue
				
			except Exception as e:
				t = 5*tries
				print "No connection, waiting for %s seconds" % t
				print "-"*60
				print traceback.format_exc()
				time.sleep(t)
				tries+=1
				
		global currentThreads
		currentThreads-=1
					
				
if __name__ == "__main__":
	words = []
		
	print len(list(itertools.product( *[chemicals, pathways] )))
	print len(words)
	
	r = open(Analyze().rel("resumeAt.txt"), "rw")
	try:
		current = int(r.read())
	except:
		current = 0
	r.close()
	
	resume = current
	
	global currentThreads
	currentThreads = 0
	print "total words: %s\ncurrent index: %s\namount left: %s " % ( len(words), current, len(words)-current )
	
	previous = resume
	
	while resume < len(words):
		if currentThreads < 10:
			s = initSearch((words[resume][0], ("Dictyostelium",4))) # 
			s.setDaemon(True)
			s.start()
			
			r = open("resumeAt.txt","w")
			resume+=1
			r.write(str(resume))
			r.close()
			currentThreads+=1
		else:
			time.sleep(2)
				
		if resume-previous > 50:
			previous = resume
			print "*"*60
			print "total words: %s\ncurrent index: %s\namount left: %s " % ( len(words), resume, len(words)-resume )
			print "*"*60
			
	# Join all threads properly
	main_thread = threading.currentThread()
	for t in threading.enumerate():
		if t is main_thread:
			continue
		logging.debug('joining %s', t.getName())
		t.join()
	
