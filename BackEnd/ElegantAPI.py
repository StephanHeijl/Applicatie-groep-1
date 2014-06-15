#!/usr/bin/python
# -*- coding: utf-8 -*-

# ################################################################################# #
#                                                                                   #
#                _____ _                        _      _    ____ ___                #
#               | ____| | ___  __ _  __ _ _ __ | |_   / \  |  _ \_ _|               #
#               |  _| | |/ _ \/ _` |/ _` | '_ \| __| / _ \ | |_) | |                #
#               | |___| |  __/ (_| | (_| | | | | |_ / ___ \|  __/| |                #
#               |_____|_|\___|\__, |\__,_|_| |_|\__/_/   \_\_|  |___|               #
#                             |___/                                                 #
#                                                                                   #
# ################################################################################# #
#                                                                                   #
# ElegantAPI                                                                        #
# ==========                                                                        #
# @author	Stephan Heijl                                                           #
# @date		23/05/2013                                                              #
# @version	0.91                                                                    #
#                                                                                   #
# ----------                                                                        #
# ElegantAPI is the Data backbone of the Elegant text mining application. It        #
# provides data management and abstraction to more easily integrate Python with     #
# MySQL by treating the data as Python-native objects and converting seamlessly     #
# between the two.                                                                  #
# ----------                                                                        #
# The software is provided "as is" and the author disclaims all warranties with     #
# regard to this software including all implied warranties of merchantability and   #
# fitness. In no event shall the author be liable for any special, direct,          #
# indirect, or consequential damages or any damages whatsoever resulting from loss  #
# of use, data or profits, whether in an action of contract, negligence or other    #
# tortious action, arising out of or in connection with the use or performance of   #
# this software.                                                                    #
# ----------                                                                        #
# You are not allowed to distribute this software without prior explicit permission #
# by the original author.                                                           #
# You are allowed to modify this software for your own personal projects.           #
#                                                                                   #
# ################################################################################# #

import MySQLdb
from decimal import *
import copy, os, re, datetime, json
from pprint import pprint as pp

from warnings import filterwarnings
import MySQLdb as Database
filterwarnings('ignore', category = Database.Warning)

# ElegantAPI class
# Direct communication with the database
# Models shouldn't handle this communication on their own, so they do this via ElegantAPI
# This class is instantiated once every time a model is instantiated, after which it is 
#    saved as a static variable to avoid opening to many connections
# Connects to the db, executes queries, commits them and returns the results
# Includes filesystem functions
# Handles configuration parsing

class ElegantAPI:
	def __init__(self):
		self.dbConfig = self.__parseconfig(f="db.config")
		self.apiConfig = self.__parseconfig(f="api.config")
		self.__connect()
	
	def rel(self, *x):
		return os.path.join(os.path.abspath(os.path.dirname(__file__)),*x)
		
	def __parseconfig(self, f="db.config"):
		conf = open(self.rel(f))
		config = {}
		for line in conf.read().split("\n"):
			if len(line) > 0 and line[0] != "#":
				try:
					key, val = line.split("=")
				except:
					continue
				
				config[key.strip()] = val.strip()
		return config
		
	def __connect(self):
		self.__connection	= MySQLdb.connect( **self.dbConfig )
		self.__cursor		= self.__connection.cursor()
		
	def query(self, q):
		#raise Exception, q
		try:
			self.__cursor.execute(q)
		except:
			raise Exception, q
		self.__connection.commit()		
		return self.__cursor.fetchall()
		
	def close(self):
		self.__connection.close()

# Query class
# Class that allows more advanced queries to take place
# The normal system only allows for normal equals and IN comparisons IE id=10, id=(10,20,30)
# To allow for more advanced comparisons (less than, greater than, etc) this class is used
# Ex:
# Query(id__lt=10) // ID < 10
# Query(value__between = [10,20] ) // value BETWEEN 10 AND 20

# Is passed to the object as a keyword argument for the field.
# Node().get(value=Query(...))
# Might be slightly buggy
		
class Query:
	def __init__(self, *args, **kwargs):
		self.kwargs = kwargs
		self.sql = ""
		
	def execute(self, model):
		bools = []
		
		for keyword, value in self.kwargs.items():
			if "__" in keyword:
				key, method = keyword.split("__")
				
				if key in dir(model):
					field = getattr(model, key)
					
				elif "_Query__" + method in dir(self):
					getattr( self, "_Query__"+method )(key, value)
					return
				
				#print dir(field.value)
				#print field.value
				
				if method in dir(field.value):
					method = getattr( field.value, method )
				elif "__"+method+"__" in dir(field.value):
					method = getattr( field.value, "__"+method+"__" )
				else:
					return "AIDS"
					
				bools.append( method(value) )
		
		return all(bools), bools
		
	def __in(self, key, value):
		self.sql = "IN (%s)" % ', '.join(value)
		
	def __notin(self, key, value):
		self.sql = "NOT IN (%s)" % ', '.join(value)
		
	def __lt(self, key, value):
		self.sql = "< %s" % value
		
	def __gt(self, key, value):
		self.sql = "> %s" % value
		
	def __lte(self, key, value):
		self.sql = "<= %s" % value
		
	def __gte(self, key, value):
		self.sql = ">= %s" % value
		
	def __not(self, key, value):
		self.sql = "!= %s" % value
		
	def __is(self, key, value):
		self.sql = "= %s" % value
		
	def __like(self, key, value):
		self.sql = "LIKE '%s'" % value
		
	def __between(self, key, value):
		self.sql = "BETWEEN %s AND %s" % (value[0], value[1])
		
	def __gt(self, key, value):
		self.sql = "> %s" % value
		
	def getSQL(self):
		return self.sql

# Field class
# Designated class to contain variables
# Is a specified type (see Model.types)
# Can only contain variables according to its constraints (length, type, etc.)
# Can accept multiple type constraints
# Can accept one type constraint and convert it to another type internally
# Contains internal constraint checkers to catch exceptions before they are passed to the database.
		
class Field(object):
	def __init__(self, typeConstraint, lengthConstraint, name="GenericField", convertTo=False, showlength=False):
		self.value = None		
		self.name = name
		self.model = None
		
		self.blank	= False
		self.null	= False
		self.unique	= False
		self.autoIncrement = False
		
		self.showlength = showlength
		
		self.typeConstraint = typeConstraint
		self.lengthConstraint = lengthConstraint
		
		self.primaryKey = False
		self.foreignKey = False
		
		self.convertTo = convertTo
		
	def setValue(self, value):		
		if self.__checkConstraint(value):
			if self.convertTo:
				try:
					value = self.convertTo(value)
				except ValueError:
					raise TypeError, "Could not set this '%s' field to this value, as the type is invalid. (Conversion error)" % self.name
			
			self.value = value
					
	def __checkConstraint(self, value):
		if value == None and not self.null:
			raise ValueError, "This field cannot be null."
		elif value == None and self.null:
			return True
	
		if isinstance(self.typeConstraint, tuple):
			matched = False
			for typeConstraint in self.typeConstraint:
				if isinstance(value, typeConstraint): 
					matched = True
			
			if not matched:
				raise TypeError, "Could not set this '%s' field to value '%s', as the type '%s' is invalid." % (self.name, str(type(value)), value) 
			
		else:
			if not isinstance(value, self.typeConstraint):
				raise TypeError, "Could not set this '%s' field to value '%s', as the type '%s' is invalid." % (self.name, str(type(value)), value) 
		
		if self.lengthConstraint == -1:
			raise AttributeError, "Could not set this '%s' field to this value, as the length of this field has not been set." % self.name
			
			
		if self.lengthConstraint == -2:
			return True
		
		try:
			if len(value) > self.lengthConstraint:
				raise ValueError, "Could not set this '%s' field to this value, as it is longer than %s." % (self.name, self.lengthConstraint)
				
		except TypeError: # This type does not have a length ( it is a number of sorts)
			if value > self.lengthConstraint:
				raise ValueError, "Could not set this '%s' field to this value, as it is too large." % self.name
				return False
		
		return True	
		
	def __call__(self, blank=False, null=False, unique=False, primary=False, length=-1, auto_increment=False):
		if length > 0:
			self.lengthConstraint = length
			
		self.blank	= blank
		self.null	= null
		self.unique = unique
		self.primaryKey = primary
		self.autoIncrement = auto_increment
				
		return copy.deepcopy(self)
		
	def __str__(self):
		return "%s field with value: %s" % ( self.name, self.value )	

# Model class
# Center of the API, allows storage and retreival of objects in the database
# Should be subclassed with specific variables.
# Generates SQL for its own table creation, storage and retreival.
# Examples of subclassing are exhibited in models.py
# Allows for foreign relationships, recursively returning other objects instead of hard values when specified.
# 
		
class Model(object):
	internalCounter = 0
	eAPI = 0
	
	def __init__(self, **fields):
		self.definedFields = self.getFields()
		self.collection = []
								
		for field, value in fields.items():
			if "_" + field not in self.definedFields:
				raise AttributeError, "This model does not have a '%s' attribute. " % field
			
			if isinstance( value, Model):
				try:
					val = getattr(value, value.getPrimary() )
				except Exception as e: 
					# The id has not been set, this is a bad thing, as it means the object has not been saved
					# We can not reliably determine the id it will have, so we will force a save
					id = self.__getMaxID()+1
					
					primaryCopy = copy.copy(getattr(value, "_"+value.getPrimary()))
					primaryCopy.setValue(id)
					
					setattr(value, value.getPrimary(), primaryCopy)
					val = getattr(value, value.getPrimary() )
					
				if val.primaryKey and val.autoIncrement:
					if val.value == None:
						self.definedFields["_"+field].setValue(value.internalCounter)
						value.internalCounter+=1
					else:
						self.definedFields["_"+field].setValue(val.value)
						value.internalCounter+=1
					self.definedFields["_"+field].model = value.__class__
					setattr(self,field,copy.deepcopy(self.definedFields["_"+field]))
					
				elif val.primaryKey and not val.autoIncrement:
					self.definedFields["_"+field].setValue(val.value)
					self.definedFields["_"+field].model = value.__class__
					setattr(self,field,copy.deepcopy(self.definedFields["_"+field]))
										
			else:
				if self.definedFields["_"+field].autoIncrement:
					self.definedFields["_"+field].setValue(self.internalCounter)
					self.internalCounter+=1
				else:
					self.definedFields["_"+field].setValue(value)
				setattr(self,field,copy.deepcopy(self.definedFields["_"+field]))
					
	def getFields(self):
		definedFields = {}
		
		for field in dir(self):
			fieldInst = getattr(self, field)
			
			if isinstance( fieldInst, Field):
				definedFields[field] = fieldInst
			
			if isinstance( fieldInst, Model):				
				for key, val in fieldInst.getFields().items():
					if val.primaryKey:
						v = copy.deepcopy(val)
						v.primaryKey = False
						v.foreignKey = True
						v.model = fieldInst.__class__
						definedFields[field] = v
						
		return definedFields
	
	def getPrimary(self):
		for key, val in self.getFields().items():
			if val.primaryKey:
				return key[1:] if key[0] == "_" else key
	
	def __generateMaxIdSQL(self):
		if self.getPrimary():
			sql = "SELECT MAX(`%s`) FROM %s " % (self.getPrimary(), self.__class__.__name__)
			return sql
		return False
	
	def __generateCreateSQL(self):
	
		sql = "CREATE TABLE `%s` (\n" % self.__class__.__name__
		
		for field, fieldInst in self.getFields().items():
		
			field = field[1:] if field.startswith("_") else field
			
			fieldSql = ["\t`%s` %s" % (field, fieldInst.name)]
			if fieldInst.showlength:
				fieldSql.append("(%s)" % fieldInst.lengthConstraint)
			
			if not fieldInst.null:
				fieldSql.append("NOT NULL")	
			
			if fieldInst.autoIncrement and fieldInst.primaryKey:
				fieldSql.append("AUTO_INCREMENT")
			
			fieldSql.append( ",\n" )
			if fieldInst.primaryKey:
				fieldSql.append("\tPRIMARY KEY (%s)" % field)
				fieldSql.append( ",\n" )
				
			if fieldInst.foreignKey:
				fieldSql.append("\tFOREIGN KEY (%s) REFERENCES %s(%s)" % (field,fieldInst.model.__name__,fieldInst.model().getPrimary()))				
				fieldSql.append( ",\n" )
				
			if fieldInst.unique:
				fieldSql.append("\tUNIQUE (%s)" % field)
				fieldSql.append( ",\n" )
				
			if(fieldSql[-1] != ",\n" ):
				fieldSql.append( ",\n" )
				
			sql += " ".join(fieldSql)
				
		sql = sql[:-2] + "\n)"
		
		return sql
		
	def __generateNewRowSQL(self):
		sql = "REPLACE `%s` (" % self.__class__.__name__
		values = []
		keys = []
		
		for field, fieldInst in self.getFields().items():
			v = fieldInst.value
			
			if v == None:
				continue
					
			keys.append(field)
			pattern = "([\\|\'\"])"
			
			if isinstance(v,str):
				values.append( "'%s'" % re.sub(pattern, "\$1", (v.decode("utf-8", "ignore"))))
			elif isinstance(v,unicode):
				values.append( "'%s'" % re.sub(pattern, "\$1", unicode(v)))
			else:
				values.append( re.sub(pattern, "\$1", unicode(v) ) )
		
		key = 0
		while key < len(keys):
			if keys[key].startswith("_"):
				if keys[key][1:] in keys:
					del keys[key]
					del values[key]
				else:
					keys[key] = keys[key][1:]
					key+=1
			else:
				key+=1
				
		
		sql += ", ".join(keys)
			
		sql = sql + ")\nVALUES (%s)" % ",".join(values)
		
		return sql
	
	def __generateGetRowSQL(self, limit=False, flat=False, *columns, **where):
		sql = "SELECT %s FROM %s" % ( ",".join([ '`col`' for col in columns ]) if len(columns) > 0 else "*", self.__class__.__name__)
		conditions = []
		if len(where) > 0:
			sql += "\nWHERE "			
			
			for col, val in where.items():
				if isinstance(val, list):
					conditions.append("`%s` IN (%s)" % (col, ", ".join([ str(v) if not isinstance(v,str) else '"%s"' % v for v in val ])))
					
				elif isinstance(val, tuple) and len(val) > 1:
					for v in val:
						if isinstance(v, Query):
							v.execute(self)
							conditions.append("`%s` %s" % (col, v.getSQL()))
						else:
							conditions.append("`%s` = %s" % (col, str(v) if not isinstance(v, str) else '"%s"' % v))
				elif isinstance(val, tuple) and len(val) == 1:
					val = val[0]
				else:
					if isinstance(val, Query):
						val.execute(self)
						conditions.append("`%s` %s" % (col, val.getSQL()))
					else:
						conditions.append("`%s` = %s" % (col, str(val) if not isinstance(val, str) else '"%s"' % val))
		
		
		sql += " AND ".join(conditions)
		if limit != False:
			if isinstance(limit, list):
				sql+= " LIMIT %s " % int(limit[0])
			else:
				sql+= " LIMIT %s " % limit
			
		return sql 
	
	def create(self):
		sql = self.__generateCreateSQL() + ";"
		if not self.eAPI:
			eAPI = ElegantAPI()
		eAPI.query(sql)
	
	def save(self):
		sql = self.__generateNewRowSQL() + ";"
 		
		if not self.eAPI:
			eAPI = ElegantAPI()
		eAPI.query(sql)
		
		if self.getPrimary():
			try:
				getattr(self, self.getPrimary())
			except:
				newId = self.__getMaxID()
				primaryCopy = copy.copy(getattr(self, "_"+self.getPrimary()))
				primaryCopy.setValue(newId)
				
				setattr(self, self.getPrimary(), primaryCopy)
	
	def take(self,n):
		return self.collection[n]
	
	def __getMaxID(self):
		sql = self.__generateMaxIdSQL()
		
		if not sql:
			return 0
		
		if not self.eAPI:
			eAPI = ElegantAPI()
			
		results = eAPI.query(sql)
		if results[0][0] == None:
			return 0
		else:
			return results[0][0]
	
	def get(self, *columns, **where):
		self.collection = []
		special = ["limit","flat"]
		
		allFields = self.getFields()
		for col in columns:
			if "_"+col not in allFields and col not in special:
				raise AttributeError, "This Model does not have attribute '%s'." % col
		
		for col,val in where.items():
			if "_"+col not in allFields and col not in special:
				raise AttributeError, "This Model does not have attribute '%s'." % col
			if isinstance(val, Model):
				where[col] = getattr(val, val.getPrimary() ).value
		
		sql = self.__generateGetRowSQL(*columns, **where) + ";"
		
		if not self.eAPI:
			eAPI = ElegantAPI()
		results = eAPI.query(sql)

		batchGet = {}
		
		for result in results:
			kwresult = zip([ (field[1:], type) for field,type in self.definedFields.items()], result) # Merge the field names, types and results
			newModel = object.__new__(self.__class__)
			
			for key, val in kwresult:
				type = key[1]
				
				if type.foreignKey and type.model and "flat" not in where:
					
					fkey = dict([(type.model().getPrimary(),val)])
					
					if type.model not in batchGet:
						batchGet[type.model] = {}
					
					batchGet[type.model][(newModel,key[0])] = fkey
	
					#v = type.model().get( **fkey ).take(0)
					#setattr(newModel, key[0], v)
				elif "flat" in where and where["flat"]:
					nVal = copy.copy(type)
					nVal.setValue(val)
					setattr(newModel, key[0], nVal)
				else:
					nVal = copy.copy(type)
					nVal.setValue(val)
					setattr(newModel, key[0], nVal)
			
			self.collection.append(newModel)
		
		
		for model,requirements in batchGet.items():
			needed = {}		
			
			for req in requirements.values():
				need = req.items()
				for n in need:
					if n[0] not in needed:
						needed[n[0]] = []
					if n[1] not in needed[n[0]]:
						needed[n[0]].append(n[1])
				
			results = model().get(**needed).collection
			
			for nm, req in requirements.items():
				for result in results:
					found = True
					for r,v in req.items():
						if getattr(result, r).value != v:
							found = False
							break
					
					if found:
						setattr(self.collection[self.collection.index(nm[0])], nm[1], result)
			
		return self
	
	# types class, includes static fields with prededined types and constraints
	# these conform to the types in MySQL and will be parsed as such
	
	class types:
		# Numeric types
		SmallInteger	= Field( (int,long), 65535 , name="smallint" )
		Integer			= Field( (int,long), 4294967295, name="int" )
		SmallIntegerS	= Field( (int,long), 32767, name="smallint" ) # Signed small integer (with negative values)
		IntegerS		= Field( (int,long), 2147483647, name="smallint" ) # Signed integer (with negative values)
		Long			= Field( int, 4294967295, name="long", convertTo=long)
		
		Float			= Field( float,  3.402823466**38, name="float" )
		Double			= Field( Decimal,  1.7976931348623157**308, name="double" )
		
		# Text types
		VarChar			= Field( (str,unicode), -1, name="varchar", showlength=True )
		Blob			= Field( (str,unicode), 1024*1024*64, name="blob")
		Text			= Field( (str,unicode),  65535, name="text" )
		MediumText		= Field( (str,unicode),  16777215, name="mediumtext" )
		
		Date			= Field( (str,unicode, datetime.date), -2, name="date" )
		Boolean			= Field( bool, 1, name="tinyint", convertTo=int )

# CachedObject is a subclass of model that allows interfacing with the filesystem
# It stores all its cached data in the models directory that is specified in the api.config
# The 

class CachedObject(Model):
	_name = Model.types.VarChar(length=200, primary=True) # We always need a filename
	_created = Model.types.Date() # And an age
	_expires = Model.types.Date() # And an expiry date
	
	def __init__(self, **kwargs):
		super(CachedObject, self).__init__(**kwargs)
		self.created = datetime.datetime.now()
		self.API = ElegantAPI()
	
	def save(self):
		name = getattr(self, self.getPrimary()).value
		fname = os.path.join( self.API.apiConfig['models'], name)
		
		try:
			file = open(fname, "w")
		except IOError as e:
			raise AttributeError, "Could not access file %s for some reason... %s" % (fname,e)
			
		contents = {}	
			
		for field in self.getFields():
			if not "_" in field:
				v = getattr(self, field).value
				contents[field] = v

		contents = json.dumps(contents)
		file.write(contents)
		file.close()
		
		
	def get(self, name):
		self.collection = []
		try:
			fname = os.path.join( self.API.apiConfig['models'], name)
			file = open(fname, "r")
						
			vars = json.loads(file.read())
			file.close()

			new = copy.copy(self)
			new.__init__(**vars)
			
			self.collection.append( new	)
			return self
			
		except Exception as err:
			print err 
			return False
	
	def isExpired(self):
		if "expired" not in self.getFields():
			self.expired = self.created + datetime.timedelta(hours=1)
			self.save()
		
		if self.expired < datetime.datetime.now():
			return True
		else:
			return False
			
	def take(self, n):
		return self.collection(n)
	
	def create(self):
		pass

		