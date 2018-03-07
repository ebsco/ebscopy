# ebscopy.py
#
# This is the primary source file for the EBSCO Discovery Service API Python Module
# 
# Location of assignment equal sign:
#											=

# TODO:
#	be able to use IP authentication
#	close on destroy

from pkg_resources import get_distribution									# Automates version setting for autodocs
import logging																# Smart logging
import os																	# Get ENV variables with auth info
import json																	# Manage data
from requests import HTTPError, post										# Does the heavy HTTP lifting
from lxml import html														# Strip HTML
from datetime import date, datetime, timedelta								# Monitor authentication timeout
import dateutil.parser														# Parse text to date
import re																	# Strip highlighting
#import warnings															# Allow warnings

## Work-in-Progress
## Create logger
#logger										= logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
#fh = logging.FileHandler('/tmp/jjj-ebscopy.log')
#fh.setLevel(logging.DEBUG)
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#fh.setFormatter(formatter)
#logger.addHandler(fh)
#
#logger.debug("Starting ebscopy! (debug)")
#logger.info("Starting ebscopy! (info)")
#logger.warn("Starting ebscopy! (warn)")
#logger.error("Starting ebscopy! (error)")
#logger.critical("Starting ebscopy! (critical)")

### Utility Functions
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
def _get_item_data(items, key, value):
	"""
	Return the ``Data`` component of a dict with the ``key`` of ``value`` from a list of dicts

	:param list items: a list of dicts, each of which contains keys, inlcuding ``Data``
	:param string key: the key to search
	:param string value: the value to search for
	:rtype: string
	"""
	data									= next((item for item in items if item.get(key) == value), None)
	if data:
		return data["Data"]
	else:
		logging.warn("_get_item_data: No match for %s:%s in items!", key, value)
		return None
# End of [_get_item_data] function

def _get_item_data_by_name(items, name):
	"""
	Check a list of dicts for a dict with a key, ``Name``, that has the value, ``name``, and get the value of the key, ``Data``

	:param list items: a list of dicts, each of which contains keys, inlcuding ``Data``
	:param string name: the value of the ``Name`` key to search
	:rtype: string
	"""
	return _get_item_data(items, "Name", name)
# End of [_get_item_data_by_name] function
	
def _get_item_data_by_group(items, group):
	"""
	Check a list of dicts for a dict with a key, ``Group``, that has the value, ``group``, and get the value of the key, ``Data``

	:param list items: a list of dicts, each of which contains keys, inlcuding ``Data``
	:param string group: the value of the ``Group`` key to search
	:rtype: string
	"""
	return _get_item_data(items, "Group", group)
# End of [_get_item_data_by_group] function

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
			raise ValueError("Could not find value for %s in passed parameter or OS environment (%s)" % (kind, env))

	return value
# End of [_use_or_get] function

def _get_or_use(kind, value=""):
	"""
	Get the a value from the appropriate environment variable or return the value passed.

	:param string kind: type of value
	:param string value: content of value
	:rtype: string
	:raises ValueError: when  environemnt variable is not found and value is empty
	"""
	kind_env_map							= {
												"base_host":	"EDS_BASE_HOST",
											}

	env										= kind_env_map[kind]

	if os.environ.get(env):
		return os.environ[env]
	elif value:
		return value
	else:
		raise ValueError("Could not find value for %s in OS environment (%s) or passed parameter" % (kind, env))
# End of [_get_or_use] function


def _uniq(seq):
	"""
	Return a unique list of items
	See: https://www.peterbe.com/plog/uniqifiers-benchmark

	:param list seq: list of items to dedupe
	:rtype: list
	"""

	seen = set()
	return [x for x in seq if x not in seen and not seen.add(x)]
# End of [_uniq] function

def _parse_bib_date(dt):
	"""
	Return a date parsed from values in a dict

	:param dict dt: dictionary with keys that represent a date
	:rtype: class:`datetime.date`
	"""
	
	try:																		# Lots of stuff can go wrong with date parsing
		if "Y" in dt and "M" in dt and "D" in dt:
			return date(int(dt["Y"]), int(dt["M"]), int(dt["D"])) 
		elif "Text" in dt:
			parsed			= dateutil.parser.parse(dt["Text"])
			return date(parsed.year, parsed.month, parsed.day)
	except ValueError:
		return None
# End of [_parse_bib_date] function

def _parse_date_string_from_eds(d):
	"""
	Parses a date string, e.g. "19930231", generated from the EDS interface's date slider and Advanced Search dropdowns. Specifically, EDS considers the day, "31", to be the last day of any month, which is confusing to other date parsers. This function tries to catch and fix those.

	:param str d: string containing an 8-digit date in the format "YYYYMMDD"
	:rtype: class:`datetime.date`
	"""

	if isinstance(d, datetime):
		return d
	elif isinstance(d, str):
		try:
			date				= datetime.strptime(d, "%Y%m%d")
		except ValueError as e:
			if e.message != "day is out of range for month":						# Error message generated by strptime when a month doesn't have that many days
				raise																# Something else went wrong, so let it bubble up
			else:																	# This is what we can fix
				if re.match("\d{6}(?:29|30|31)", d):								# We have an otherwise valid date string with a day of 29-31
					logging.info("Trying to fix date string: %s", d)
					return _parse_date_string_from_eds(str(int(d)-1))				# I feel equally horrible and awesome for this use of recursion
				else:
					raise
		return date
	else:
		raise ValueError("Expecting a datetime or a string, got neither!")

# End of [_parse_date_string_from_eds] function


def _change_eds_date_limiter_to_api(l):
	"""
	Fixes the DT1 limiter syntax from EDS/EBSCOhost

	:param dict l: dictionary with containing limiter in the form {"Id": "DT1", "Values": ["19780515-20171231"]}
	:rtype: dict
	"""

	# The date range can have a start, end, or both dates: 19780515-, -20161205, or 19780515-20161205
	# This regex does a look-ahead to make sure there is at least one date string, and then looks for optional start and end
	# It should *not* match the following:
	# 19780515		(no dash)
	# -				(just a dash)
	# 1-19780515	(bad start)
	# 19780515-1	(bad end)
	#
	if l["Id"] != "DT1" or not re.search("\A\s*(?=-?\d{8})(?:\d{8})?-(?:\d{8})?\Z", l["Values"][0]):
		return l

	logging.info("_change_eds_date_limiter_to_api: DT1 Limiter Was: %s", l["Values"][0])

	api_string								= "/"
	(start_str, end_str)					= l["Values"][0].split("-")

	if len(start_str.strip()) == 8:
		api_string							= _parse_date_string_from_eds(start_str.strip()).strftime("%Y-%m") + api_string

	if len(end_str.strip()) == 8:
		api_string							= api_string + _parse_date_string_from_eds(end_str.strip()).strftime("%Y-%m")

	l["Values"][0]							= api_string

	logging.info("_change_eds_date_limiter_to_api: DT1 Limiter Now: %s", l["Values"][0])

	return l
# End of [_change_eds_date_limiter_to_api] function

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

class RetrievalError(Exception):
	"""
	An error retrieving informatino from the API.
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
		self.valid_methods					= frozenset(["CreateSession", "Info", "Search", "Retrieve", "EndSession", "UIDAuth", "SearchCriteria"])
		self.user_id						= user_id
		self.password						= password
		self.userpass						= (self.user_id, self.password)
		self.interface_id					= "ebscopy %s" % (_version)
		self.auth_token						= ""
		self.active							= False
	# End of [__init__] function

	def __repr__(self):
		return self.__class__.__name__ + "(user_id=%r, password=%r, active=%r)" % (self.user_id, self.password, self.active)

	def __str__(self):
		if self.active:
			return "Active Connection using %s/%s" % (self.user_id, self.password)
		else:
			return "Inactive Connection"

	def __int__(self):
		return POOL.pool.index(self)

	def __eq__(self, other):
		if isinstance(other, _Connection):
			return self.userpass == other.userpass
		else:
			return NotImplemented

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
		if method not in self.valid_methods:
			raise ValueError("Unknown API method requested!")

		data_json							= json.dumps(data)
		logging.debug("_Connection.request: JSON data being sent: %s", data_json)

		#base_host							= "https://eds-api-a.ebscohost.com"
		#base_host							= "https://eds-api.ebscohost.com"
		base_host							= _get_or_use("base_host", "https://eds-api.ebscohost.com")
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
			logging.error("_Connection.request: Request attempt: %s", attempt)
			logging.error("_Connection.request: Method: %s", method)
			logging.error("_Connection.request: Code: %s", r.status_code)
			logging.error("_Connection.request: Error text: %s", r.text)
			#logging.error("_Connection.request: JSON Object: %s", r.json())

			if r.json().get("ErrorNumber"):
				# ErrorNumbers come in as strings
				error_num					= r.json()["ErrorNumber"]
				logging.error("_Connection.request: ErrorNumber: %s", error_num )

				if error_num in ("104", "107"):										# Authentication Token Invalid or Missing
					logging.warn("_Connection.request: Bad AuthToken, trying to get another.")
					self.active				= False
					self.connect()
					logging.warn("_Connection.request: Rerunning original request.")
					return self.request(method, data, session_token, attempt)
				elif error_num in ("108", "109"):									# Session Token Missing or Invalid
					logging.error("_Connection.request: Bad session %s", session_token)
					raise SessionError("Bad Session!")
				elif error_num == "144":											# Account/Profile mismatch
					raise ValueError("Account/Profile mismatch!")
				elif error_num == "138":											# Max Record Retrieval Exceeded
					raise RetrievalError("Max Record Retrieval Exceeded!")
				else:
					raise HTTPError("Unexpected ErrorNumber from server (%s)!" % error_num)

			elif r.json().get("ErrorCode"):
				# ErrorCodes come in as integers
				error_code					= r.json()["ErrorCode"]
				logging.error("_Connection.request: ErrorCode: %s", error_code )

				if error_code == 1102:												# Invalid Credentials
					raise AuthenticationError("Invalid credentials!")
				elif error_code == 1103:											# No Profile
					raise AuthenticationError("No valid profiles found for customer/group combination.")
				else:
					raise HTTPError("Unexpected ErrorCode from server (%s)!" % error_code)
			else:
				raise HTTPError("Completely unexpected error from server!")
	
		return r.json()
	# End of [request] function

	def connect(self):
		"""
		Request an AuthToken from the API using the credentials from initilization.
		"""
	
		# I think this is okay. Safe for new connects, and no need for a reconnect wrapper function to do it.
		self.auth_token						= ""

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

		if self.auth_token:
			self.active						= True
		else:
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

	def __repr__(self):
		return self.__class__.__name__ + "(pool=%r)" % (self.pool)

	def __str__(self):
		return "Connection Pool with %d Connections" % len(self)

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

		:returns: size of pool
		:rtype: int
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
		self.active							= False	
		self.last_search					= {}
		self.next_search					= {}
		self.current_page					= 0

		if connection:
			self.connection					= connection
		else:
			self.connection					= POOL.get(user_id, password)

		# Required for API call
		self.profile						= _use_or_get("profile", profile)
		self.org							= _use_or_get("org", org)
		self.guest							= _use_or_get("guest", guest)

		self.session_token					= self.connection._create_session(self.profile, self.org, self.guest)
		if self.session_token:
			self.active						= True
		else:
			raise SessionError("No Session Token received from API!")

		# Get Info from API; used by tests and sets some defaults
		# TODO: parse some of this out
		# TODO: catch SessionTimeout here?
		#	 "ApplicationSettings":{ "SessionTimeout":"480"
		self.info_data						= self._request("Info", {})

		self.valid_sorts					= set()
		for sort in self.info_data.get("AvailableSearchCriteria", {}).get("AvailableSorts", []):
			self.valid_sorts.add(sort.get("Id"))

		self.valid_search_fields			= set()
		for field in self.info_data.get("AvailableSearchCriteria", {}).get("AvailableSearchFields", []):
			self.valid_search_fields.add(field.get("FieldCode"))

		self.valid_expanders				= set()
		for expander in self.info_data.get("AvailableSearchCriteria", {}).get("AvailableExpanders", []):
			self.valid_expanders.add(expander.get("Id"))

		self.valid_limiters					= set()
		for limiter in self.info_data.get("AvailableSearchCriteria", {}).get("AvailableLimiters", []):
			self.valid_limiters.add(limiter.get("Id"))

		self.valid_search_modes				= set()
		for mode in self.info_data.get("AvailableSearchCriteria", {}).get("AvailableSearchModes", []):
			self.valid_search_modes.add(mode.get("Mode"))
			if mode.get("DefaultOn") == "y":
				self.default_search_mode	= mode.get("Mode")

		self.valid_dym_options				= set()
		for dym in self.info_data.get("AvailableSearchCriteria", {}).get("AvailableDidYouMeanOptions", []):
			self.valid_dym_options.add(dym.get("Id"))

		self.session_timeout				= int(self.info_data.get("ApplicationSettings", {}).get("SessionTimeout", "900"))
		self.max_record_jump				= int(self.info_data.get("ApiSettings", {}).get("MaxRecordJumpAhead", "250"))

		self.include_image_quick_view		= bool()
		if self.info_data.get("ViewResultSettings", {}).get("IncludeImageQuickView", {}).get("DefaultOn", "n") == "y":
			self.include_image_quick_view	= True
			


		# TODO: Do more here


	# End of [__init__] function

	def __repr__(self):
		return self.__class__.__name__ + "(connection=%r, profile=%r, org=%r, guest=%r, active=%r)" % (self.connection, self.profile, self.org, self.guest, self.active)
	# End of [__repr__] function

	def __str__(self):
		if self.active:
			return "Active Session to %s on %s" % (self.profile, self.connection)
		else:
			return "Inactive Session"
	# End of [__str__] function

	def __nonzero__(self):
		"""
		Determine boolean value based on self.active.

		:rtype: boolean
		"""
		return self.active
	# End of [__nonzero__] function

	def __len__(self):
		"""
		Determine length value based on self.active.

		:rtype: int
		"""
		return int(self.active)
	# End of [__len__] function

	def __eq__(self, other):
		"""
		Determine object equality based on SessionToken.

		:returns: equality
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

		:returns: inequality
		:rtype: boolean
		"""
		result = self.__eq__(other)
		if result is NotImplemented:
			return result
		else:
			return not result
	# End of [__ne__] function

	def __add__(self, other):
		"""
		Get results for higher page number.

		:returns: Results object
		:rtype: class:`ebscopy.Results`
		"""
		if isinstance(other, int):
			new_page						= self.current_page + other
			return self.get_page(new_page)
		else:
			return NotImplemented
	# End of [__add__] function

	def __sub__(self, other):
		"""
		Get results for lower page number.

		:returns: Results object
		:rtype: class:`ebscopy.Results`
		"""
		if isinstance(other, int):
			new_page						= max(1, self.current_page - other)
			return self.get_page(new_page)
		else:
			return NotImplemented
	# End of [__sub__] function

#	def __del__(self):
#		if self.active:
#			self.end()

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
		#except RetrievalError:
			#logging.error("Session._request: Whoa, error with retrieving results!")
			#return
		except SessionError:
			logging.warn("Session._request: Problem with Session (%s), trying to start another!", self.session_token)
			self.session_token				= self.connection._create_session(self.profile, self.org, self.guest)
			logging.info("Session._request: Started new Session (%s)!", self.session_token)
			new_req							= self.connection.request(method, data, self.session_token)
			logging.info("Session._request: Made new %s request!", method)
			return new_req
	# End of [_request] function

	# Internal function for actually calling the API Search 
	def _search(self, search_data={}, expect_page=None):
		"""
		Internal search function for new and modified searches

		:param dict search_data: dict of search POST data
		:returns: Results object
		:rtype: class:`ebscopy.Results`
		"""
		if not search_data:
			raise ValueError("No search data in search_data!")
		
		results								= Results()
		logging.debug("Session.search: Request data: %s", search_data)

		try:
			search_response					= self._request("Search", search_data)
		except RetrievalError as e:
			logging.warn("Session._search: Unable to retrieve results; Results object will be empty! Error: %s", e)
			return results

		logging.debug("Session.search: Response: %s", search_response)

		self.last_search					= search_data
		self.next_search					= search_data

		if search_response["SearchRequest"]["SearchCriteria"].get("FacetFilters"):
			self.next_search["SearchCriteria"]["FacetFilters"]	= search_response["SearchRequest"]["SearchCriteria"]["FacetFilters"]
		if search_response["SearchRequest"]["SearchCriteria"].get("Limiters"):
			self.next_search["SearchCriteria"]["Limiters"]		= search_response["SearchRequest"]["SearchCriteria"]["Limiters"]

		self.current_page					= int(search_response["SearchRequest"]["RetrievalCriteria"].get("PageNumber", 1))
		self.next_search["RetrievalCriteria"]["PageNumber"]		= self.current_page
		
		if not expect_page or expect_page == self.current_page:
			results.load(search_response)
		else:
			logging.warn("Session._search: Expected page %s but got page %s; Results object will be empty!" % (expect_page, self.current_page))
		
		return results
	# End of [_search] function

	# Do a search
	def search(self, query, mode=None, sort="relevance", view="brief", rpp=20, page=1, highlight="y", suggest="n", iqv="n", expanders=[], limiters=[]):
		"""
		Perform a search with the EDS API.

		:param string mode: SearchMode, (all* | any | bool | smart) 
		:param string sort: sort mode, determined by API configuration
		:param string view: level of record detail (brief* | title | detailed)
		:param int rpp: results per page (20)
		:param int page: page number to return (1)
		:param string highlight: wrap search terms in <highlight> tags (y* | n)
		:param string suggest: return search suggestions (y | n*)
		:param string iqv: return image quick view results (y | n*)
		:param list expanders: expanders to apply; each list item can be in the form "fulltext:Y" (string) or "fulltext" (string)
		:param list limiters: limiters to apply; each list item can be in the form "LA99:English" (string), ["LA99", "English"] (list), or {"Id": "LA99", "Values": ["English", "Spanish"]} (dict)
		:returns: Results object
		:rtype: class:`ebscopy.Results`
		"""

		if mode == None:
			mode = self.default_search_mode

		if mode not in self.valid_search_modes:
			if _strict:
				raise ValueError("Search Mode \"%s\" is not valid!" % (mode))
			else:
				logging.warn("Session.search: Ignoring invalid mode \"%s\", using \"all\"!", mode)
				mode						= "all"

		#valid_expanders					= frozenset(["thesaurus", "fulltext", "relatedsubjects"])
		expanders_to_check					= []
		for expander in expanders:
			expander						= expander.replace("enhancedsubjectprecision", "relatedsubjects")
			if ":Y" in expander:
				expanders_to_check.append(expander.split(":")[0])
			else:
				expanders_to_check.append(expander)
		expanders_to_use					= list(self.valid_expanders.intersection(expanders_to_check))

		limiters_to_use						= []
		for limiter in limiters:
			entry							= {"Id": "", "Values": [""]}
			to_append						= True

			if isinstance(limiter, str):
				entry["Id"], entry["Values"][0]	= limiter.split(":")
			elif isinstance(limiter, list) and len(limiter) == 2:
				entry["Id"]					= limiter[0]
				entry["Values"][0]			= limiter[1]
			elif isinstance(limiter, dict) and isinstance(limiter.get("Id"), str) and isinstance(limiter.get("Values"), list):
				entry						= limiter
			else:
				to_append					= False
				logging.warn("Session.search: Could not parse limiter \"%s\"!", limiter)

			if to_append:
				if entry["Id"] not in self.valid_limiters:
					if _strict:
						raise ValueError("Limiter ID %s is not in list of available IDs!" % (entry["Id"]))
					else:
						logging.warn("Session.search: Ignoring invalid limiter \"%s\"!", entry["Id"])
						continue

				# Try to fix DT1 format in case it's coming from EDS
				if entry["Id"] == "DT1":
					entry					= _change_eds_date_limiter_to_api(entry)

				limiters_to_use.append(entry)
			# End of to_append check

		search_data							=	{
												"SearchCriteria": 		{
													"Queries":		 		[
																				{
																					"Term": query
																				}
																			],
													"SearchMode":			mode,
													"IncludeFacets":		"y",
													"AutoSuggest":			suggest,
													"Sort": 				sort
																		},
												"RetrievalCriteria":	{
													"View":					view,
													"ResultsPerPage":		max(1, min(rpp, 100)),
													"PageNumber":			page,
													"Highlight":			highlight
																		},
												"Actions":				[],
												}

		if self.include_image_quick_view and iqv == "y":
			search_data["RetrievalCriteria"]["IncludeImageQuickView"]	= "y"

		if expanders_to_use:
			search_data["SearchCriteria"]["Expanders"]	= expanders_to_use

		if limiters_to_use:
			search_data["SearchCriteria"]["Limiters"]	= limiters_to_use

		return self._search(search_data)
	# End of [search] function

	def add_action(self, action, expect_page=None):
		"""
		Add an Action to an existing search.

		:param list action: List of EDS API Action(s)
		:returns: Results object
		:rtype: class:`ebscopy.Results`
		"""

		return self.add_actions([action], expect_page)
	# End of [add_action] function

	def add_actions(self, actions, expect_page=None):
		"""
		Add an Action or Actions to an existing search.

		:param list action: List of EDS API Action(s)
		:returns: Results object
		:rtype: class:`ebscopy.Results`
		"""
		if self.next_search:
			search_data						= self.next_search
			search_data["Actions"]			= actions
			return self._search(search_data, expect_page=expect_page)
		else:
			logging.warn("Session.add_actions: No previous search found when setting action(s): \"%s\"!", actions)
			return Results()
	# End of [add_actions] function

	def get_page(self, page=1):
		"""
		Get a page of results.

		:param int page: page to request
		:returns: Results object
		:rtype: class:`ebscopy.Results`
		"""
		return self.add_actions(["GoToPage(%d)" % page], expect_page=page)
	# End of [get_page] function

	def next_page(self):
		"""
		Get the next page of results.

		:returns: Results object
		:rtype: class:`ebscopy.Results`
		"""
		page								= self.current_page + 1
		return self.get_page(page)
	# End of [next_page] function

	# Get the previous page of results (not below 1)
	def prev_page(self):
		"""
		Get the previous page of results.

		:returns: Results object
		:rtype: class:`ebscopy.Results`
		"""
		page								= max(1, self.current_page - 1)
		return self.get_page(page)
	# End of [prev_page] function

	def auto_suggest(self, term=""):
		"""
		Request just automatic suggestions.

		:returns: list of suggestions
		:rtype: list
		"""
		
		results								= self.search(term, rpp=1, highlight="n", suggest="y")
		return results.auto_suggestions
	# End of [auto_suggest] function

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

		if not self.active:
			logging.warn("Session.end: Attempt to end inactive Session!")
			return

		end_data							= {
												"SessionToken": self.session_token
											}
		end_response						= self._request("EndSession", end_data)

		if end_response["IsSuccessful"] == "y": 
			self.active						= False
		else:
			logging.warn("Session.end: Unsuccessful! Response: %s", end_response)

		return
	# End of [end] function
# End of [Session] class


class Results:
	"""
	Results object returned by an API Search request.
	"""

	# Initialize 
	def __init__(self):
		#self.query_string					= ""							# String straight from JSON
	
		self.search_queries					= []
		self.stat_total_hits				= 0
		self.stat_total_time				= 0
		self.page_number					= 0
		self.rec_format						= ""							# String straight from JSON
		self.stat_databases_raw				= []
		self.avail_facets_raw				= []
		self.avail_facets_labels			= []
		self.avail_facets_ids				= []
		self.avail_facets_by_id				= {}
		self.actions_addable				= []
		self.actions_removable				= []
		self.auto_suggestions				= []							# List of automatic suggestions
		self.records_simple					= []							# List of dicts w/ keys: PLink, DbID, An, Title, Author, etc.
		self.records_raw					= []							# List of raw Records straight from JSON
		self.record							= []							# List of DbId/An tuples

	## Internal helper functions
	# Representation function
	def __repr__(self):
		return self.__class__.__name__ + "(queries=%r, hits=%r, page=%r)" % (self.search_queries, self.stat_total_hits, self.page_number)

	# Stringify function
	def __str__(self):
		string								= "Page %d of Results for \"" % self.page_number
		for q in self.search_queries:
			string							+= q.get("Term")
		string += "\""
		return string
	# End of [__str__] function

	def __bool__(self):
		"""
		Determine boolean value based on number of hits (Python 3).

		:rtype: boolean
		"""
		return bool(self.stat_total_hits)
	# End of [__bool__] function

	def __nonzero__(self):
		"""
		Determine boolean value based on number of hits (Python 2).

		:rtype: boolean
		"""
		return self.__bool__()
	# End of [__nonzero__] function

	def __len__(self):
		"""
		Determine length value based on number of hits.

		:rtype: int
		"""
		return self.stat_total_hits
	# End of [__len__] function

	# Equality function
	def __eq__(self, other):
		if isinstance(other, Results):
			return self.search_criteria == other.search_criteria and self.stat_total_hits == other.stat_total_hits and self.page_number == other.page_number
		elif isinstance(other, int):
			return self.stat_total_hits == other
		else:
			return NotImplemented
	# End of [__eq__] function

	# Not-Equal function
	def __ne__(self, other):
		result = self.__eq__(other)
		if result is NotImplemented:
			return result
		else:
			return not result
	# End of [__ne__] function
	
	# Less Than function
 	def __lt__(self, other):
		if isinstance(other, Results):
			return self.stat_total_hits < other.stat_total_hits
		elif isinstance(other, int):
			return self.stat_total_hits < other
		else:
			return NotImplemented
	# End of [__lt__] function

	# Less Than or Equal function
 	def __le__(self, other):
		if isinstance(other, Results):
			return self.stat_total_hits <= other.stat_total_hits
		elif isinstance(other, int):
			return self.stat_total_hits <= other
		else:
			return NotImplemented
	# End of [__le__] function

	# Greater Than function
 	def __gt__(self, other):
		if isinstance(other, Results):
			return self.stat_total_hits > other.stat_total_hits
		elif isinstance(other, int):
			return self.stat_total_hits > other
		else:
			return NotImplemented
	# End of [__gt__] function

	# Greater Than or Equal function
 	def __ge__(self, other):
		if isinstance(other, Results):
			return self.stat_total_hits >= other.stat_total_hits
		elif isinstance(other, int):
			return self.stat_total_hits >= other
		else:
			return NotImplemented
	# End of [__ge__] function

	# Load with dict
	def load(self, data):
		"""
		Load and process the response from an API Search request.

		:param dict data: Dict containing the API response from a Search request
		"""
		self.stat_total_hits				= data["SearchResult"]["Statistics"]["TotalHits"]
		self.stat_total_time				= data["SearchResult"]["Statistics"]["TotalSearchTime"]
		self.auto_suggestions				= data["SearchResult"].get("AutoSuggestedTerms", [])
		self.stat_databases_raw				= data["SearchResult"]["Statistics"]["Databases"]

		self.search_criteria				= data["SearchRequest"]["SearchCriteria"]
		self.search_queries					= data["SearchRequest"]["SearchCriteria"]["Queries"]
		self.page_number					= data["SearchRequest"]["RetrievalCriteria"].get("PageNumber", 1)
		self.rpp							= data["SearchRequest"]["RetrievalCriteria"]["ResultsPerPage"]

		for qwa in data["SearchRequest"]["SearchCriteriaWithActions"].get("QueriesWithAction", []):
			self.actions_removable.append( qwa["RemoveAction"] )

		for ffwa in data["SearchRequest"]["SearchCriteriaWithActions"].get("FacetFiltersWithAction", []):
			self.actions_removable.append( ffwa["RemoveAction"] )
			for fvwa in ffwa["FacetValuesWithAction"]:
				self.actions_removable.append( fvwa["RemoveAction"] )

		for lwa in data["SearchRequest"]["SearchCriteriaWithActions"].get("LimitersWithAction", []):
			self.actions_removable.append( lwa["RemoveAction"] )
			for lvwa in lwa["LimiterValuesWithAction"]:
				self.actions_removable.append( lvwa["RemoveAction"] )

		if self.stat_total_hits > 0:
			self.avail_facets_raw			= data.get("SearchResult",{}).get("AvailableFacets",[])
			for facet in self.avail_facets_raw:
				self.avail_facets_labels.append(facet["Label"])
				self.avail_facets_ids.append(facet["Id"])
				self.avail_facets_by_id[facet["Id"]]	= facet["AvailableFacetValues"]
				for value in facet["AvailableFacetValues"]:
					self.actions_addable.append(value["AddAction"])

			#TODO: add available criteria. here? or outside the if hits>0?
	
			self.rec_format					= data["SearchResult"]["Data"]["RecordFormat"]
			self.records_raw				= data["SearchResult"]["Data"]["Records"]
			for record in data["SearchResult"]["Data"]["Records"]:
				# Internal variables with default values
				simple_rec					= {}
				has_source					= False
				identifiers					= []
				authors         			= []
				isbns						= []
				issns						= []
				subjects					= []
				#image_quick_views			= []

				# Start loading simple record data
				simple_rec["ResultId"]		= record["ResultId"]
				simple_rec["DbId"]			= record["Header"]["DbId"]
				simple_rec["DbLabel"]		= record["Header"].get("DbLabel", None)
				simple_rec["An"]			= record["Header"]["An"]
				simple_rec["Score"]			= record["Header"].get("RelevancyScore", None)
				simple_rec["PubType"]		= record["Header"].get("PubType", None)
				simple_rec["PubTypeId"]		= record["Header"].get("PubTypeId", None)
				simple_rec["PLink"]			= record["PLink"]
				simple_rec["FTAvail"]		= (False, True)[int(record["FullText"]["Text"]["Availability"])]
				# Alternate method of setting FTAvail
				#if record["FullText"]["Text"]["Availability"] > 0:
				#	simple_rec["FTAvail"]	= True

				# Troll through Items for good stuff
				# Items often contain markup, so most things are better found elsewhere
				# Abstracts are only found in Items (and only when detailed results are requested)
				for item in record.get("Items", []):
					if item["Group"] == "Src":
						has_source			= True
					elif item["Group"] == "Ab" and item["Label"] == "Abstract":
						simple_rec["AbstractRaw"]	= item["Data"]
						# Clean up the HTML in the abstract
						simple_rec["Abstract"]        = html.fromstring(simple_rec["AbstractRaw"]).text_content()

				# Collect any Identifiers from the main BibEntity
				identifiers.extend(record["RecordInfo"]["BibRecord"]["BibEntity"].get("Identifiers", []))

				# Collect any Pagination info (PageCount and StartPage) from the main BibEntity
				if record["RecordInfo"]["BibRecord"]["BibEntity"].get("PhysicalDescription"):
					if record["RecordInfo"]["BibRecord"]["BibEntity"]["PhysicalDescription"].get("Pagination"):
						if record["RecordInfo"]["BibRecord"]["BibEntity"]["PhysicalDescription"]["Pagination"].get("PageCount"):
							simple_rec["PageCount"]	= record["RecordInfo"]["BibRecord"]["BibEntity"]["PhysicalDescription"]["Pagination"]["PageCount"]
						if record["RecordInfo"]["BibRecord"]["BibEntity"]["PhysicalDescription"]["Pagination"].get("StartPage"):
							simple_rec["StartPage"]	= record["RecordInfo"]["BibRecord"]["BibEntity"]["PhysicalDescription"]["Pagination"]["StartPage"]
					
				# Collect any Subjects
				for subs in record["RecordInfo"]["BibRecord"]["BibEntity"].get("Subjects", []):
					subjects.append(subs.get("SubjectFull", None))

				# Get the main, unadorned Title, if it exists
				if record["RecordInfo"]["BibRecord"]["BibEntity"].get("Titles") and len(record["RecordInfo"]["BibRecord"]["BibEntity"]["Titles"]) > 0:
					simple_rec["Title"]		= record["RecordInfo"]["BibRecord"]["BibEntity"]["Titles"][0].get("TitleFull")

				# Collect any Authors
				for contribs in record["RecordInfo"]["BibRecord"].get("BibRelationships", {}).get("HasContributorRelationships", []):
					if contribs["PersonEntity"]["Name"]["NameFull"]:
						authors.append(contribs["PersonEntity"]["Name"]["NameFull"]) 


				# According to the documentation: 
				# "Currently, the IsPartOfRelationships element will contain only one IsPartOf element."
				# http://edswiki.ebscohost.com/EBSCO_Discovery_Service_API_User_Guide_Appendix
				bib_entity					= record["RecordInfo"]["BibRecord"].get("BibRelationships", {}).get("IsPartOfRelationships", [{}])[0].get("BibEntity", {})

				if has_source:
					for ttl in bib_entity.get("Titles", []):
						if ttl["Type"] == "main":
							simple_rec["Source"]	= ttl["TitleFull"]

				# Collect any Numbering values
				for num in bib_entity.get("Numbering", []):
					if num["Type"] == "volume":
						simple_rec["Volume"]	= num["Value"]
					elif num["Type"] == "issue": 
						simple_rec["Issue"]	= num["Value"]
				
				# Collect any Date values, regardless of format
				for dt in bib_entity.get("Dates", []):
					if dt["Type"] == "published":
						simple_rec["PubDate"]	= _parse_bib_date(dt)
					elif dt["Type"] == "created": 
						simple_rec["CreateDate"]= _parse_bib_date(dt)
					else:
						simple_rec["OtherDate"]	= _parse_bib_date(dt)
				
				# Set "Date" to the best Date value available
				if simple_rec.get("PubDate"):
					simple_rec["Date"]		= simple_rec["PubDate"]
				elif simple_rec.get("CreateDate"):
					simple_rec["Date"]		= simple_rec["CreateDate"]
				elif simple_rec.get("OtherDate"):
					simple_rec["Date"]		= simple_rec["OtherDate"]

				# Collect any Identifiers from the IsPartOf BibEntity
				identifiers.extend(bib_entity.get("Identifiers", []))

				for ident in identifiers:
					if ident["Type"] == "doi":
						simple_rec["Doi"]	= ident["Value"]
					elif ident["Type"].startswith("isbn"):
						isbns.append(ident["Value"])
					elif ident["Type"].startswith("issn"):
						issns.append(ident["Value"])

				simple_rec["ImageQuickViews"]		= []
				simple_rec["ImageQuickViewThumbs"]	= []
				# Collect any ImageQuickView items
				for item in record.get("ImageQuickViewItems", []):
					#image_quick_views.append(item)
					simple_rec["ImageQuickViews"].append((item["DbId"], item["An"]))
					simple_rec["ImageQuickViewThumbs"].append(item["Url"])

				# Assign previously collected collections
				subjects					= _uniq(subjects)
				simple_rec["Subjects"]		= subjects
				simple_rec["Subject"]		= "; ".join(subjects)

				authors						= _uniq(authors)
				simple_rec["Authors"]		= authors
				simple_rec["Author"]		= "; ".join(authors)

				issns						= _uniq(issns)
				simple_rec["Issns"]			= issns
				simple_rec["Issn"]			= "; ".join(issns)

				isbns						= _uniq(isbns)
				simple_rec["Isbns"]			= isbns
				simple_rec["Isbn"]			= "; ".join(isbns)

				self.records_simple.append(simple_rec)
				self.record.append((record["Header"]["DbId"], record["Header"]["An"])) 
			# End of for loop of records
		return
	# End of load function

	def pprint(self):
		"""
		Print the list of results in a not displeasing manner.
		"""
		print "Search Results"
		print "--------------------"
		print repr(self)
		print "--------------------"
		for record in self.records_simple:
			print("DbId: %s" % record.get("DbId"))
			print("An: %s" % record.get("An"))
			print("Title: %s" % record.get("Title"))
			print("Author: %s" % record.get("Author"))
			print("PLink: %s" % record.get("PLink"))
			print("Subject: %s" % record.get("Subject"))
			print("DOI: %s" % record.get("Doi"))
			print("Isbn: %s" % record.get("Isbn"))
			print("Issn: %s" % record.get("Issn"))
			print("Abstract: %s" % record.get("Abstract"))
			print "----------"
			print
		print "--------------------"
		return
# End of Results class


class Record:
	"""
	Single Record object returned by Retrieve request
	"""
	def __init__(self):
		self.raw							= {}
		self.dbid							= ""
		self.an								= ""
		self.pubtype						= ""
		self.pubtype_id						= ""
		self.plink							= ""
		self.fulltext_avail					= False
		self.simple_title					= ""
		self.simple_author					= ""
		self.is_image_quick_view			= False
		self.best_image_url					= ""
		self.images							= []
	# End of [__init__] function

	def __repr__(self):
		return self.__class__.__name__ + "(dbid=%r, an=%r)" % (self.dbid, self.an)
	# End of [__repr__] function

	def __str__(self):
		return "Record for %s by %s)" % (self.simple_title, self.simple_author)
	# End of [__str__] function

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
	# End of [__ne__] function

	def load(self, data):
		"""
		Load and process the response from an API Retrieve request.

		:param dict data: Dict containing the API response from a Retrieve request
		"""
		self.raw							= data
		self.dbid							= data["Record"]["Header"]["DbId"]
		self.an								= data["Record"]["Header"]["An"]
		self.pubtype						= data["Record"]["Header"]["PubType"]
		self.pubtype_id						= data["Record"]["Header"]["PubTypeId"]
		self.plink							= data["Record"]["PLink"]
		# TODO, determine fulltext status
		#self.fulltext_avail				= False
		# TODO: generate simple values for all possiblities
		self.simple_title					= _get_item_data_by_group(data["Record"]["Items"], "Ti")
		self.simple_author					= _get_item_data_by_group(data["Record"]["Items"], "Au")
		self.simple_subject					= _get_item_data_by_group(data["Record"]["Items"], "Su")

		# TODO: Maybe don't even try to get title, author, and subject by group (above) for IQVs?
		if self.dbid == "iqv":
			self.is_image_quick_view		= True
			self.images						= data["Record"].get("IllustrationInfo", {}).get("Images", [])

			# Sort the list of dictionaries by size, based on the order of size_sort list
			size_sort						= ["orig", "full", "large", "small"]
			self.images.sort(key=lambda x: size_sort.index(x["Size"]))

			# Populate best_image_url with the url from the first item of the sorted list
			self.best_image_url				= self.images[0]["Target"]
		# End of iqv check

		return
	# End of [load] function

	def pprint(self):
		"""
		Print the list of results in a not displeasing manner.
		"""
		print("DbId: %s"	% self.dbid)
		print("An: %s"		% self.an)
		print("Title: %s"	% self.simple_title)
		print("Author: %s"	% self.simple_author)
		print("PLink: %s"	% self.plink)
		print
		return
	# End of [print] function
# End of Record class


# Set version
_version = get_distribution('ebscopy').version

# _strict controls the behavior of the ebscopy when dealing with bad input
# True: Pythonic, throws errors when input is bad
# False: Forgiving, ignores bad input whenever possible (default)
_strict										= False

# The shared Connection Pool
POOL										= ConnectionPool()

#EOF
