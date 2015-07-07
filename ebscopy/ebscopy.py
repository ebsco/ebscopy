# ebscopy.py

# To Do:
#	be able to use IP
#	close on destroy

import json					# Manage data
import os					# Get ENV variables with auth info
import requests					# Does the heavy HTTP lifting
from datetime import datetime, timedelta	# Monitor authentication timeout
import inspect					# For debugging
import logging					# Smart logging
import re					# Strip highlighting


# Take text with highlight tagging, remove the highlight tags but save the locations
# TODO: this assumes only one highlight in string; what if more?
def _parse_highlight(text):
  output["orig"]		= text
  output["clean"]		= ""
  output["start_pos"]		= 0
  output["end_pos"]		= 0

  start_tag			= "&lt;highlight&gt;"
  end_tag			= "&lt;\/highlight&gt;"
  
  start_match			= re.search(start_tag, output["orig"])
  if start_match:
    output["start_pos"]		= start_match.start()
    output["clean"]		= output["orig"][:start_match.start()] + output["orig"][start_match.end():]

  end_match			= re.search(end_tag, output["clean"])
  if end_match:
    output["end_pos"]		= end_match.start()
    output["clean"]		= output["clean"][:end_match.start()] + output["clean"][end_match.end():]

  return output
# End of [_parse_highlight] function


# Get the "Data" component of a named item from an arbitrarily sorted JSON list
def _get_item_data(items, name):
  dictionary			= next((item for item in items if item["Name"] == name), None)
  if dictionary:
    return dictionary["Data"]
  else:
    logging.warn("No match for %s in items!", name)
    return None
# End of [_get_item_data] function


# Connection object
# Don't use manually, is used by Session objects
# Create with credentials and settings, then call connect()
class Connection:

  # Initialize Connection object with blank values (mostly)
  def __init__(self):
    self.user_id		= ""
    self.password		= ""
    self.profile		= ""
    self.org			= ""
    self.guest			= ""
    #global __version__
    self.interface_id		= "ebscopy"
    #self.interface_id		= "ebscopy %s" % (__version__)
    self.connected		= False
  # End of [__init__] function

  # Internal method to generate an HTTP request 
  def request(self, session_token, method, data):
    valid_methods		= frozenset(["CreateSession", "Info", "Search", "Retrieve", "EndSession", "UIDAuth", "SearchCriteria"])
    if method not in valid_methods:
      raise ValueError("Unknown API method requested")

    data_json			= json.dumps(data)
    logging.debug("JSON data being sent: %s", data_json)
    base_host			= "https://eds-api.ebscohost.com"
    base_path			= ""
    base_url			= ""
    full_url			= ""

    if method == "UIDAuth":
      base_path			= "/authservice/rest/"
    else:
      base_path			= "/edsapi/rest/"

    full_url			= base_host + base_path + method
    logging.debug("Full URL: %s", full_url)

    headers			= {'Content-Type': 'application/json', 'Accept': 'application/json'}

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

    logging.debug("Request headers: %s", headers)

    r				= requests.post(full_url, data=data_json, headers=headers)
    logging.debug("Request response object: %s", r)

    code			= r.status_code
    if code is not 200:
      if code is 400 and method not in ("UIDAuth", "CreateSession"):
        logging.debug("Session died?!?!")
        #TODO: Probably a timeout issue, need to recover
  	# 400 error, invalid session token
  	#  Receive JSON:
  	#    {"DetailedErrorDescription":"Invalid Session Token. Please generate a new one.","ErrorDescription":"Session Token Invalid","ErrorNumber":"109"}
      else:
        logging.debug("Error text: %s", r.text)
        r.raise_for_status()

    # This should be a dict now...?
    return r.json()
  # End of [request] function

  # Actually connect to the API by doing an authorization
  def connect(self, user_id="", password="", profile="", org="", guest=""):
    self.user_id		= user_id
    self.password		= password
    self.profile		= profile
    self.org			= org
    self.guest			= guest

    if not self.user_id:
      if os.environ.get('EDS_USER'):
        self.user_id		= os.environ['EDS_USER']
      else:
        raise ValueError("Could not find value for user_id in passed parameters or OS environment")

    if not self.password:
      if os.environ.get('EDS_PASS'):
        self.password		= os.environ['EDS_PASS']
      else:
        raise ValueError("Could not find value for password in passed parameters or OS environment")

    if not self.profile:
      if os.environ.get('EDS_PROFILE'):
        self.profile		= os.environ['EDS_PROFILE']
      else:
        raise ValueError("Could not find value for profile in passed parameters or OS environment")

    if not self.org:
      if os.environ.get('EDS_ORG'):
        self.org		= os.environ['EDS_ORG']
      else:
        raise ValueError("Could not find value for org in passed parameters or OS environment")

    if not self.guest:
      if os.environ.get('EDS_GUEST'):
        self.guest		= os.environ['EDS_GUEST']
      else:
        self.guest		= "n"

    logging.debug("UserID: %s", self.user_id)
    logging.debug("Password: %s", self.password)
    logging.debug("Profile: %s", self.profile)
    logging.debug("Org: %s", self.org)
    logging.debug("Guest: %s", self.guest)

    # Do UIDAuth
    auth_data			= {
					"UserId":	self.user_id,
					"Password":	self.password,
					"InterfaceId":	self.interface_id
			  	}
    auth_response		= self.request("", "UIDAuth", auth_data)
    logging.debug("UIDAuth response: %s", auth_response)

    self.auth_token		= auth_response["AuthToken"]
    self.auth_timeout		= auth_response["AuthTimeout"]
    self.auth_timeout_time	= datetime.now() + timedelta(seconds=int(self.auth_timeout))

    if self.auth_token:
      self.connected		= True

    return
  # End of [connect] function

  # Create a Session by hitting the API and returning a session token
  def create_session(self, user_id="", password="", profile="", org="", guest="" ):
    create_data			= {
					"Profile":	self.profile,
					"Guest":	self.guest,
					"Org":		self.org
				}

    create_response		= self.request("", "CreateSession", create_data)
    logging.debug("CreateSession response: %s", create_response)

    return create_response["SessionToken"]
  # End of [create_session] function

# End of [Connection] class


class Session:
  def __init__(self, profile="", org="", guest="", user_id="", password=""):

    # Required for Session
    self.profile		= profile
    self.org			= org
    self.guest			= guest

    # Optional, could be handled by Connection
    self.user_id		= user_id
    self.password		= password

    global CONNECTION
    if not CONNECTION.connected:
      CONNECTION.connect(user_id, password)

    self.auth_token		= CONNECTION.auth_token
    self.connection		= CONNECTION.auth_token
    self.auth_timeout_time	= CONNECTION.auth_timeout_time

    self.session_token		= CONNECTION.create_session(profile, org, guest)

    # Get Info from API, just in case
    info_data			= {}

    info_response		= self.__request("Info", info_data)
    logging.debug("Info response: %s", info_response)
    self.info_data		= info_response
	# TODO: catch SessionTimeout?

  # End of [__init__] function

  def __request(self, method, data):
    return CONNECTION.request(self.session_token, method, data)
  # End of [__request] function

  def __eq__(self, other):
    if isinstance(other, Session):
      return self.session_token == other.session_token
    else:
      return NotImplemented
   # End of [__eq__] function

  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    else:
      return not result

  # Do a search
  def search(self, query, mode="all", sort="relevance", inc_facets="y", view="brief", rpp=20, page=1, highlight="y"):

    search_data			= {
					"SearchCriteria": {
						"Queries": [
								{
									"Term": query
								}
						],
						"SearchMode": mode,
						"IncludeFacets": inc_facets,
						"Sort": sort
					},
					"RetrievalCriteria": {
						"View": view,
						"ResultsPerPage": rpp,
						"PageNumber": page,
						"Highlight": highlight
					},
					"Actions": None
				}
		
    logging.debug("Search data: %s", search_data)

    search_response		= self.__request("Search", search_data)

    logging.debug("Search response: %s", search_response)

    results			= Results()
    results.load(search_response)

    return results
  # End of [search] function

  # Retrieve a record
  def retrieve(self, dbid_an_tup, highlight=None, ebook="ebook-pdf"):
    retrieve_data		= {
					"DbId": dbid_an_tup[0],
					"An": dbid_an_tup[1],
					"HighlightTerms": highlight,
					"EbookPreferredFormat": ebook
				}

    logging.debug("Retrieve data: %s", retrieve_data)

    retrieve_response		= self.__request("Retrieve", retrieve_data)

    logging.debug("Retrieve response: %s", retrieve_response)

    record			= Record()
    record.load(retrieve_response)

    return record
  # End of [retrieve] function

  # End the Session
  def end(self):
    end_data			= {
					"SessionToken": self.session_token
				  }
    end_response		= self.__request("EndSession", end_data)
    logging.debug("EndSession response: %s", end_response)
    return
  # End of [end] function
# End of [Session] class


# Results object returned by Search request
class Results:

  # Initialize 
  def __init__(self):
    self.stat_total_hits	= 0
    self.stat_total_time	= 0
    self.stat_databases_raw	= []
    self.avail_facets_raw	= []
    self.avail_facets_labels	= []
    self.avail_facets_ids	= []
    self.simple_records		= []		# List of dicts with keys: PLink, DbID, An, Title, Author?
    self.rec_format		= ""		# String straight from JSON
    self.records_raw		= []		# List of raw Records straight from JSON
    self.record			= []		# List of DbId/An tuples

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
    self.stat_total_hits	= data["SearchResult"]["Statistics"]["TotalHits"]
    self.stat_total_time	= data["SearchResult"]["Statistics"]["TotalSearchTime"]
    self.stat_databases_raw	= data["SearchResult"]["Statistics"]["Databases"]

    self.search_criteria	= data["SearchRequest"]["SearchCriteria"]

    self.avail_facets_raw	= data["SearchResult"]["AvailableFacets"]
    for facet in data["SearchResult"]["AvailableFacets"]:
      self.avail_facets_labels.append(facet["Label"])
      self.avail_facets_ids.append(facet["Id"])

    self.rec_format		= data["SearchResult"]["Data"]["RecordFormat"]
    self.records_raw		= data["SearchResult"]["Data"]["Records"]
    for record in data["SearchResult"]["Data"]["Records"]:
      simple_rec		= {}
      simple_rec["PLink"]	= record["PLink"]
      simple_rec["DbId"]	= record["Header"]["DbId"]
      simple_rec["An"]		= record["Header"]["An"]
      # TODO: are there other sources of titles?
      simple_rec["Title"]	= record["RecordInfo"]["BibRecord"]["BibEntity"]["Titles"][0]["TitleFull"]
      # TODO: add fulltext true/false
      self.simple_records.append(simple_rec)
      self.record.append((record["Header"]["DbId"], record["Header"]["An"])) 
    return
  # End of load function

  def pprint(self):
    for record in self.simple_records:
      print("Title: %s" % record["Title"])
      print("PLink: %s" % record["PLink"])
      print("DbId: %s" % record["DbId"])
      print("An: %s" % record["An"])
      print
    return
# End of Results class


# Record object returned by Retrieve request
class Record:
  def __init__(self):
    self.dbid			= ""
    self.an			= ""
    self.pubtype		= ""
    self.pubtype_id		= ""
    self.plink			= ""
    self.fulltext_avail		= False
    self.simple_title		= ""
    self.simple_author		= ""

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
    self.dbid			= data["Record"]["Header"]["DbId"]
    self.an			= data["Record"]["Header"]["An"]
    self.pubtype		= data["Record"]["Header"]["PubType"]
    self.pubtype_id		= data["Record"]["Header"]["PubTypeId"]
    self.plink			= data["Record"]["PLink"]
    # TODO, determine fulltext status
    #self.fulltext_avail		= False
    # TODO: generate simple values for all possiblities
    self.simple_title		= _get_item_data(data["Record"]["Items"], "Title")
    self.simple_author		= _get_item_data(data["Record"]["Items"], "Author")
    return

  def pprint(self):
    print("Title: %s"	% self.simple_title)
    print("Author: %s"	% self.simple_author)
    print("PLink: %s"	% self.plink)
    print("DbId: %s"	% self.dbid)
    print("An: %s"	% self.an)
    print
    return
# End of Record class

CONNECTION			= Connection()

#EOF
