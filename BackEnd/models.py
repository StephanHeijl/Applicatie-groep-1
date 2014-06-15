from ElegantAPI import *

class UserLevel(Model):
	_id = Model.types.SmallInteger(primary=True)
	_name = Model.types.VarChar(length=10)

class User(Model):
	_id = Model.types.Integer(primary=True, auto_increment=True)
	_firstName = Model.types.VarChar(length=20)
	_lastName = Model.types.VarChar(length=30)
	_email = Model.types.VarChar(length=64)
	_password = Model.types.VarChar(length=64)
	_level = UserLevel()

class Article(Model):
	_id = Model.types.Integer(primary=True)
	_title = Model.types.VarChar(length=768)
	_authors = Model.types.Text(null=True)
	_journal = Model.types.VarChar(length=768,null=True)
	_publish_date = Model.types.Date(null=True)
	_abstract = Model.types.Text(null=True)
	
class NodeType(Model):
	_id = Model.types.Integer(primary=True, auto_increment=True)
	_name = Model.types.VarChar(length=100, unique=True)
	_color = Model.types.VarChar(length=20, unique=True)

class Node(Model):
	_id = Model.types.Integer(primary=True, auto_increment=True)
	_value = Model.types.VarChar(length=100, unique=True)
	_type = NodeType()
	
class Edge(Model):
	_id = Model.types.Integer(primary=True, auto_increment=True)
	_positivescore = Model.types.Integer(null=True)
	_score = Model.types.Integer(null=True)
	_negativescore = Model.types.Integer(null=True)
	_source = Node()
	_end = Node()

class EdgeArt(Model):
	_edge = Edge()
	_article = Article()

class KeywordType(Model):
	_id = Model.types.Integer(primary=True, auto_increment=True)
	_type = Model.types.VarChar(64)
	_positive_score = Model.types.SmallInteger()
	_negative_score = Model.types.SmallInteger()

class Keyword(Model):
	_id = Model.types.Integer(primary=True, auto_increment=True)
	_word = Model.types.VarChar(length=96)
	_keyword_type = KeywordType()

class GraphCache(CachedObject): 
	_xml = Model.types.MediumText()
