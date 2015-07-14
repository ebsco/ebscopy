# ebscopy.py

# TODO:
#	be able to use IP
#	close on destroy

import json																	# Manage data
import os																	# Get ENV variables with auth info
from requests import HTTPError, post										# Does the heavy HTTP lifting
from datetime import datetime, timedelta									# Monitor authentication timeout
import logging																# Smart logging
import re																	# Strip highlighting
from pkg_resources import get_distribution

### Helper Functions

# TODO: this assumes only one highlight in string; what if more?
def _parse_highlight(text):
	"""
	Parse out the API's ``<highlight>`` tags and return a dict including the clean text.

	:param string text: unprocessed text that may include ``<highlight>`` and ``</highlight>`` tags
	:rtype: dict
	:key: orig: the original text
	:key: clean: the stripped text
	:key: start_pos: integer representing the start of highlighting in ``clean``
	:key: end_pos: integer representing the end of highlighting in ``clean``
	
	"""
	output["orig"]							= text
	output["clean"]							= ""
	output["start_pos"]						= 0
	output["end_pos"]						= 0

	start_tag								= "&lt;highlight&gt;"
	end_tag									= "&lt;\/highlight&gt;"

	start_match								= re.search(start_tag, output["orig"])
	if start_match:
		output["start_pos"]					= start_match.start()
		output["clean"]						= output["orig"][:start_match.start()] + output["orig"][start_match.end():]

	end_match								= re.search(end_tag, output["clean"])
	if end_match:
		output["end_pos"]					= end_match.start()
		output["clean"]						= output["clean"][:end_match.start()] + output["clean"][end_match.end():]

	return output
# End of [_parse_highlight] function

# TODO: Do we need this? 
# TODO: Use group instead of name?
def _get_item_data(items, name):
	"""
	Return the ``Data`` component of item ``name`` from a list of dictionaries

	:param list items: a list of dictionaries, each of which contains ``Name`` and ``Data`` keys
	:param string name: the ``Name`` to find
	:rtype: dict
	"""
	dictionary								= next((item for item in items if item["Name"] == name), None)
	if dictionary:
		return dictionary["Data"]
	else:
		logging.warn("_get_item_data: No match for %s in items!", name)
		return None
# End of [_get_item_data] function

def _use_or_get(kind, value=""):
	"""
	Return the value passed or get it from the appropriate environment variable.

	:param string kind: type of value
	:param string value: content of value
	:rtype: string
	:raises ValueError: when value is empty and environemnt variable is not found
	"""
	kind_env_map							= {
												"user_id":		"EDS_USER",
												"password":		"EDS_PASS",
												"profile":		"EDS_PROFILE",
												"org":			"EDS_ORG",
												"guest":		"EDS_GUEST",
											}
	if not value:
		env									= kind_env_map[kind]
		if os.environ.get(env):
			value							= os.environ[env]
		elif kind == "guest":
			value							= "n"
		else:
			raise ValueError("Could not find value for %s in passed parameters or OS environment (%s)" % (kind, env))

	return value
# End of [_use_or_get] function


### Classes

class Borg:
	"""
	All objects of class share same state.

	Extended by ConnectionPool. Based on Alex Martelli's code:
	http://www.aleax.it/5ep.html
	"""
	_shared_state 							= {}
	def __init__(self):
		self.__dict__ 						= self._shared_state

class AuthenticationError(Exception):
	"""
	An error authenticating against the API.
	"""
	pass

class SessionError(Exception):
	"""
	An error creating a Session with the API.
	"""
	pass

class _Connection:
	"""
	A single connection to the API, shared by 1+ Sessions.

	Created and managed by the ConnectionPool object, POOL.
	"""

	# ConnectionPool should give us safe values when initializing
	def __init__(self, user_id, password):
		"""
		Initialize the _Connection object with user_id and password.

		:param string user_id: API user ID
		:param string passowrd: API password
		"""
		self.user_id						= user_id
		self.password						= password
		self.userpass						= (user_id, password)
		self.interface_id					= "ebscopy %s" % (_version)
	# End of [__init__] function

	# Internal method to generate an HTTP request 
	def request(self, method, data, session_token=None, attempt=0):
		"""
		Make a single HTTP request to the API server.

		If the request fails, try again twice.

		:param string method: valid API endpoint
		:param dict data: Data to be POSTed as JSON
		:param string session_token: optional Session Token to include in header
		:param int attempt: optional counter of request attempts
		:returns: response from API
		:rtype: dict
		"""
		valid_methods						= frozenset(["CreateSession", "Info", "Search", "Retrieve", "EndSession", "UIDAuth", "SearchCriteria"])
		if method not in valid_methods:
			raise ValueError("Unknown API method requested!")

		data_json							= json.dumps(data)
		logging.debug("_Connection.request: JSON data being sent: %s", data_json)
		base_host							= "https://eds-api.ebscohost.com"
		base_path							= ""
		base_url							= ""
		full_url							= ""

		attempt								+= 1
		if attempt > 2:
			raise HTTPError("Unable to acquire target lock!")

		if method == "UIDAuth":
			base_path						= "/authservice/rest/"
		else:
			base_path						= "/edsapi/rest/"

		full_url							= base_host + base_path + method
		logging.debug("_Connection.request: Full URL: %s", full_url)

		headers								= {'Content-Type': 'application/json', 'Accept': 'application/json'}

		try:
			headers['x-authenticationToken']	= self.auth_token
		except:
			if method is not "UIDAuth":
				raise ValueError("Missing Authentication Token!")

		try:
			headers['x-sessionToken']		= session_token
		except:
			if method not in ("UIDAuth", "CreateSession"):
				raise ValueError("Missing Session Token!")

		logging.debug("_Connection.request: Request headers: %s", headers)

		r									= post(full_url, data=data_json, headers=headers)

		try:
			r.raise_for_status()
		except:
			logging.debug("_Connection.request: Request attempt: %s", attempt)
			logging.debug("_Connection.request: Method: %s", method)
			logging.debug("_Connection.request: Code: %s", r.status_code)
			logging.debug("_Connection.request: Request response object: %s", r)
			logging.debug("_Connection.request: Error text: %s", r.text)

			if r.json().get("ErrorNumber") in ("104", "107"):							# Authentication Token Invalid or Missing
				logging.warn("_Connection.request: Bad AuthToken, trying to get another.")
				self.connect()
				logging.warn("_Connection.request: Rerunning original request.")
				return self.request(method, data, session_token, attempt)
			elif r.json().get("ErrorNumber") in ("108", "109"):							# Session Token Missing or Invalid
				logging.warn("_Connection.request: Bad Session, raising SessionError.")
				raise SessionError
			elif r.json().get("ErrorCode") == 1102:										# ErrorCode is an integer, not a string
				raise AuthenticationError("Invalid credentials!")
			elif r.json().get("ErrorCode") == 1103:										# ErrorCode is an integer, not a string
				raise AuthenticationError("No valid profiles found for customer/group combination.")
			else:
				raise HTTPError("Unexpected error from server!")
	
	
		return r.json()
	# End of [request] function

	def connect(self):
		"""
		Request an AuthToken from the API using the credentials from initilization.
		"""
	
		# I think this is okay. Safe for new connects, and no need for a reconnect wrapper function to do it.
		self.auth_token					= None

		logging.debug("_Connection.connect: UserID: %s", self.user_id)
		logging.debug("_Connection.connect: Password: %s", self.password)
		logging.debug("_Connection.connect: InterfaceId: %s", self.interface_id)

		# Do UIDAuth
		auth_data							= {
					"UserId":	self.user_id,
					"Password":	self.password,
					"InterfaceId":	self.interface_id
		}
		auth_response						= self.request("UIDAuth", auth_data)
		logging.debug("_Connection.connect: UIDAuth response: %s", auth_response)

		self.auth_token						= auth_response["AuthToken"]
		self.auth_timeout					= auth_response["AuthTimeout"]
		self.auth_timeout_time				= datetime.now() + timedelta(seconds=int(self.auth_timeout))

		if not self.auth_token:
			raise AuthenticationError("Didn't get AuthToken from API?!")

		return
	# End of [connect] function

	# Create a Session by hitting the API and returning a session token
	# The parameters should have been vetted by the Session object that called this
	def _create_session(self, profile="", org="", guest=""):
		"""
		Create a Session by requesting a Session Token from the API, using passed credentials.

		:param string profile: EDS profile to search
		:param string org: Arbitrary text for reporting 
		:param string guest: Treat the user as a guest or authenticated (n* | y)
		:returns: SessionToken
		:rtype: string
		"""
		create_data							= {
												"Profile":	profile,
												"Guest":	guest,
												"Org":		org
											}

		create_response						= self.request("CreateSession", create_data)
		logging.debug("_Connection._create_session: Response: %s", create_response)

		return create_response["SessionToken"]
	# End of [_create_session] function
# End of [_Connection] class

class ConnectionPool(Borg):
	"""
	Container for _Connection objects.
	"""
	def __init__(self):
		"""
		Initialize pool as a Borg.
		"""
		Borg.__init__(self)													# Share state with another ConnectionPool
		self.pool							= []							# The list of Connection objects

	def get(self, user_id="", password=""):
		"""
		Provide an existing or new connection based on credentials.
		
		If the credentials match an existing connection, return it; otherwise, return a new one.

		:param string user_id: API user_id
		:param string password: API password
		:returns: _Connection object
		:rtype: class:`ebscopy._Connection`

		"""
		self.new_user_id					= _use_or_get("user_id", user_id)
		self.new_password					= _use_or_get("password", password)
		connection							= _Connection(self.new_user_id, self.new_password)	# The Connection object

		for item in self.pool:
			logging.debug("ConnectionPool.get: Item: %s", item)
			if item.userpass == connection.userpass:
				logging.debug("ConnectionPool.get: Item Matched: %s", item)
				connection					= item
				break
		else: # no break
			logging.debug("ConnectionPool.get: No Items Matched!")
			connection.connect()
			self.pool.append(connection)

		return connection
	# End of [get] function

	def __len__(self):
		"""
		Return number of _Connection objects in the pool.
		"""
		return len(self.pool)
	# End of [len] function

# End of [ConnectionPool] class

class Session:
	"""
	A single user's API session object.
	"""
	def __init__(self, connection=None, profile="", org="", guest="", user_id="", password=""):
		"""
		Initialize Session object.

		Will get a _Connection from the POOL if necessary. Other parameters are taken from EDS_ environment variables as needed.

		:param connection: optional _Connection object to use
		:type connection: :class:`ebscopy._Connection` instance
		:param string profile: optional EDS profile to use
		:param string org: optional Org value for reporting
		:param string guest: Treat the user as a guest or authenticated (n* | y)
		:param string user_id: optional EDS user_id to use
		:param string password: optional EDS password to use
		"""

		if connection:
			self.connection					= connection
		else:
			self.connection					= POOL.get(user_id, password)

		# Required for Session
		self.profile						= _use_or_get("profile", profile)
		self.org							= _use_or_get("org", org)
		self.guest							= _use_or_get("guest", guest)

		self.session_token					= self.connection._create_session(self.profile, self.org, self.guest)
		if self.session_token:
			self.active							= True
		else:
			self.active							= False
			raise SessionError("No Session Token received from API!")


		# Get Info from API; used by tests
		# TODO: parse some of this out
		# TODO: catch SessionTimeout here?
		#	 "ApplicationSettings":{ "SessionTimeout":"480"
		info_response						= self._request("Info", {})
		self.info_data						= info_response
	# End of [__init__] function

	def _request(self, method, data):
		"""
		Use the _Connection.request function to make an API request.

		Will attempt to heal itself if SessionToken is expired.

		:param string method: API endpoint
		:param dict data: Request data to POST
		:returns: response from API
		:rtype: dict
		"""
		if not self.active:
			raise SessionError("This session is not active (probably explicitly closed)!")
		try:
			return self.connection.request(method, data, self.session_token)
		except SessionError:
			logging.warn("Session._request: Problem with Session, trying to start another!")
			self.session_token				= self.connection._create_session(self.profile, self.org, self.guest)
			return self.connection.request(method, data, self.session_token)
	# End of [_request] function

	def __eq__(self, other):
		"""
		Determine object equality based on SessionToken.

		:rtype: boolean
		"""
		if isinstance(other, Session):
			return self.session_token == other.session_token
		else:
			return NotImplemented
	# End of [__eq__] function

	def __ne__(self, other):
		"""
		Determine object inequality based on SessionToken.

		:rtype: boolean
		"""
		result = self.__eq__(other)
		if result is NotImplemented:
			return result
		else:
			return not result

	# Do a search
	def search(self, query, mode="all", sort="relevance", inc_facets="y", view="brief", rpp=20, page=1, highlight="y"):
		"""
		Perform a search with the EDS API.

		:param string mode: SearchMode, (all* | any | bool | smart) 
		:param string sort: sort mode, determined by API configuration
		:param string inc_facets: IncludeFacets, (y* | n)
		:param string view: level of record detail (brief* | title | detailed)
		:param int rpp: results per page (20)
		:param int page: page number to return (1)
		:param string highlight: wrap search terms in <highlight> tags (y* | n)
		:returns: Results object
		:rtype: class:`ebscopy.Results`

		"""

		search_data							=	{
												"SearchCriteria": 		{
													"Queries":		 		[
																				{
																					"Term": query
																				}
																			],
													"SearchMode":			mode,
													"IncludeFacets":		inc_facets,
													"Sort": 				sort
																		},
												"RetrievalCriteria":	{
													"View":					view,
													"ResultsPerPage":		rpp,
													"PageNumber":			page,
													"Highlight":			highlight
																		},
												"Actions":				None
												}

		logging.debug("Session.search: Request data: %s", search_data)

		search_response						= self._request("Search", search_data)

		logging.debug("Session.search: Response: %s", search_response)

		results								= Results()
		results.load(search_response)

		return results
	# End of [search] function

	# Retrieve a record
	def retrieve(self, dbid_an_tup, highlight=None, ebook="ebook-pdf"):
		"""
		Retrieve a single record by DbId and An values.

		:param tuple dbid_an_tup: DbId and An to make 
		:returns: Record object
		:rtype: class:`ebscopy.Record` 

		"""
		retrieve_data						= {
					"DbId": dbid_an_tup[0],
					"An": dbid_an_tup[1],
					"HighlightTerms": highlight,
					"EbookPreferredFormat": ebook
				}

		logging.debug("Session.retrieve: Request data: %s", retrieve_data)

		retrieve_response					= self._request("Retrieve", retrieve_data)

		logging.debug("Session.retrieve: Response: %s", retrieve_response)

		record								= Record()
		record.load(retrieve_response)

		return record
	# End of [retrieve] function

	# End the Session
	def end(self):
		"""
		End an active Session.
		"""
		end_data							= {
					"SessionToken": self.session_token
		}
		end_response						= self._request("EndSession", end_data)

		if end_response["IsSuccessful"] == "y": 
			self.active							= False
		else:
			logging.warn("Session.end: Unsuccessful! Response: %s", end_response)

		return
	# End of [end] function
# End of [Session] class


# Results object returned by Search request
class Results:

	# Initialize 
	def __init__(self):
		self.stat_total_hits				= 0
		self.stat_total_time				= 0
		self.stat_databases_raw				= []
		self.avail_facets_raw				= []
		self.avail_facets_labels			= []
		self.avail_facets_ids				= []
		self.simple_records					= []							# List of dicts w/ keys: PLink, DbID, An, Title, Author?
		self.rec_format						= ""							# String straight from JSON
		self.records_raw					= []							# List of raw Records straight from JSON
		self.record							= []							# List of DbId/An tuples

	def __eq__(self, other):
		if isinstance(other, Results):
			return self.search_criteria == other.search_criteria and self.stat_total_hits == other.stat_total_hits
		else:
			return NotImplemented
	# End of [__eq__] function

	def __ne__(self, other):
		result = self.__eq__(other)
		if result is NotImplemented:
			return result
		else:
			return not result

	# Load with dict
	def load(self, data):
		self.stat_total_hits				= data["SearchResult"]["Statistics"]["TotalHits"]
		self.stat_total_time				= data["SearchResult"]["Statistics"]["TotalSearchTime"]
		self.stat_databases_raw				= data["SearchResult"]["Statistics"]["Databases"]

		self.search_criteria				= data["SearchRequest"]["SearchCriteria"]

		self.avail_facets_raw				= data["SearchResult"]["AvailableFacets"]
		for facet in data["SearchResult"]["AvailableFacets"]:
			self.avail_facets_labels.append(facet["Label"])
			self.avail_facets_ids.append(facet["Id"])

		self.rec_format						= data["SearchResult"]["Data"]["RecordFormat"]
		self.records_raw					= data["SearchResult"]["Data"]["Records"]
		for record in data["SearchResult"]["Data"]["Records"]:
			simple_rec						= {}
			simple_rec["PLink"]				= record["PLink"]
			simple_rec["DbId"]				= record["Header"]["DbId"]
			simple_rec["An"]				= record["Header"]["An"]
			# TODO: are there other sources of titles?
			simple_rec["Title"]				= record["RecordInfo"]["BibRecord"]["BibEntity"]["Titles"][0]["TitleFull"]
			# TODO: add fulltext true/false
			self.simple_records.append(simple_rec)
			self.record.append((record["Header"]["DbId"], record["Header"]["An"])) 
		return
	# End of load function

	def pprint(self):
		print "Search Results"
		print "---------------"
		for record in self.simple_records:
			print("Title: %s" % record["Title"])
			print("PLink: %s" % record["PLink"])
			print("DbId: %s" % record["DbId"])
			print("An: %s" % record["An"])
			print
		print "---------------"
		return
# End of Results class


# Record object returned by Retrieve request
class Record:
	def __init__(self):
		self.dbid							= ""
		self.an								= ""
		self.pubtype						= ""
		self.pubtype_id						= ""
		self.plink							= ""
		self.fulltext_avail					= False
		self.simple_title					= ""
		self.simple_author					= ""

	def __eq__(self, other):
		if isinstance(other, Record):
			return self.an == other.an and self.dbid == other.dbid
		else:
			return NotImplemented
	# End of [__eq__] function

	def __ne__(self, other):
		result = self.__eq__(other)
		if result is NotImplemented:
			return result
		else:
			return not result

	def load(self, data):
		self.dbid							= data["Record"]["Header"]["DbId"]
		self.an								= data["Record"]["Header"]["An"]
		self.pubtype						= data["Record"]["Header"]["PubType"]
		self.pubtype_id						= data["Record"]["Header"]["PubTypeId"]
		self.plink							= data["Record"]["PLink"]
		# TODO, determine fulltext status
		#self.fulltext_avail				= False
		# TODO: generate simple values for all possiblities
		self.simple_title					= _get_item_data(data["Record"]["Items"], "Title")
		self.simple_author					= _get_item_data(data["Record"]["Items"], "Author")
		return

	def pprint(self):
		print("Title: %s"	% self.simple_title)
		print("Author: %s"	% self.simple_author)
		print("PLink: %s"	% self.plink)
		print("DbId: %s"	% self.dbid)
		print("An: %s"		% self.an)
		print
		return
# End of Record class

_version = get_distribution('ebscopy').version

# The shared Connection Pool
POOL										= ConnectionPool()

#EOF
