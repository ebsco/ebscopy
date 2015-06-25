# ebscopy.py

# Version 0.0.1
#
# To Do:
# define connection object
#	be able to accept credentials
#	be able to use IP
#	log in, create session
#	keep open
#	close on destroy
#	
# 
# Reference:
# EDS API
#	GET CreateSession  info
#	POST CreateSession  info
#
#	GET Info  info
#	POST Info  info
#
#	GET Search  info
#	POST Search  info
#
#	GET Retrieve  info
#	POST Retrieve  info
#
#	GET EndSession  info
#	POST EndSession  info
#
# Authentication
#	POST UIDAuth  info
#
# Publication API
#	GET Search  info
#	POST Search  info
#
#	GET Retrieve  info
#	POST Retrieve  info
#
#	GET SearchCriteria  info
#	POST SearchCriteria  info
#

import json					# Manage data
import os					# Get ENV variables with auth info
import requests					# Does the heavy HTTP lifting
from datetime import datetime, timedelta	# Monitor authentication timeout
import inspect					# For debugging
import logging					# Smart logging
import pprint
from config import Mode				# ebscopy config settings


# Connection object
class Connection:

  # Initialize Connection object with auth and config info
  def __init__(self, user_id="", password="", profile="", org="", guest="" ):
    self.user_id		= user_id
    self.password		= password
    self.profile		= profile
    self.org			= org
    self.guest			= guest
    self.interface_id		= 'ebscopy'

    if not self.user_id:
      if os.environ.get('EDS_USER'):
        self.user_id		= os.environ['EDS_USER']
      else:
        raise ValueError

    if not self.password:
      if os.environ.get('EDS_PASS'):
        self.password		= os.environ['EDS_PASS']
      else:
        raise ValueError

    if not self.profile:
      if os.environ.get('EDS_PROFILE'):
        self.profile		= os.environ['EDS_PROFILE']
      else:
        raise ValueError

    if not self.org:
      if os.environ.get('EDS_ORG'):
        self.org		= os.environ['EDS_ORG']
      else:
        raise ValueError

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

  # Internal method to generate an HTTP request 
  def __request(self, method, data):
    valid_methods		= frozenset(["CreateSession", "Info", "Search", "Retrieve", "EndSession", "UIDAuth", "SearchCriteria"])
    if method not in valid_methods:
      raise ValueError

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

    #if self.auth_token:
    try:
      headers['x-authenticationToken']	= self.auth_token
    #elif method is not "UIDAuth":
    except:
      if method is not "UIDAuth":
        raise ValueError
      
    #if self.session_token:
    try:
      headers['x-sessionToken']		= self.session_token
    except:
      if method not in ("UIDAuth", "CreateSession"):
        raise ValueError

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
  # End of __request


  def connect(self):
    # Do UIDAuth
    auth_data			= {
					"UserId":	self.user_id,
					"Password":	self.password,
					"InterfaceId":	self.interface_id
			  	}
    auth_response		= self.__request("UIDAuth", auth_data)
    logging.debug("UIDAuth response: %s", auth_response)

    self.auth_token		= auth_response["AuthToken"]
    self.auth_timeout		= auth_response["AuthTimeout"]
    self.auth_timeout_time	= datetime.now() + timedelta(seconds=int(self.auth_timeout))

    # Do CreateSession
    create_data			= {
					"Profile":	self.profile,
					"Guest":	self.guest,
					"Org":		self.org
				}

    create_response		= self.__request("CreateSession", create_data)
    logging.debug("CreateSession response: %s", create_response)

    self.session_token		= create_response["SessionToken"]


    # Do Info
    info_data			= {}

    info_response		= self.__request("Info", info_data)
    logging.debug("Info response: %s", info_response)
    self.info_data		= info_response
	# TODO: catch SessionTimeout?

    return 
  # End of connect

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
  # End of search

  def disconnect(self):
    end_data			= {
					"SessionToken": self.session_token
				  }
    end_response		= self.__request("EndSession", end_data)
    logging.debug("EndSession response: %s", end_response)
    return
  # End of disconnect function

# End of Connection class

class Results:

  # Initialize 
  def __init__(self):
    pass

  # Load with dict
  def load(self, data):
    self.stat_total_hits	= data["SearchResult"]["Statistics"]["TotalHits"]
    self.stat_total_time	= data["SearchResult"]["Statistics"]["TotalSearchTime"]
    self.stat_databases		= data["SearchResult"]["Statistics"]["Databases"]

    self.avail_facets		= data["SearchResult"]["AvailableFacets"]
    self.avail_facets_labels	= []
    self.avail_facets_ids	= []
    for facet in data["SearchResult"]["AvailableFacets"]:
      self.avail_facets_labels.append(facet["Label"])
      self.avail_facets_ids.append(facet["Id"])

    self.rec_format		= data["SearchResult"]["Data"]["RecordFormat"]
    self.records		= data["SearchResult"]["Data"]["Records"]
    self.simple_records		= []
    for record in data["SearchResult"]["Data"]["Records"]:
      simple_rec		= {}
      simple_rec["PLink"]	= record["PLink"]
      simple_rec["DbId"]	= record["Header"]["DbId"]
      simple_rec["An"]		= record["Header"]["An"]
      simple_rec["Title"]	= record["RecordInfo"]["BibRecord"]["BibEntity"]["Titles"][0]["TitleFull"]
      self.simple_records.append(simple_rec)
  # End of load function

  def pretty_print(self):
    for record in self.simple_records:
      print("Title: %s" % record["Title"])
      print("PLink: %s" % record["PLink"])
      print("DbId: %s" % record["DbId"])
      print("An: %s" % record["An"])
      print("------------")
    #pprint.pprint(self.simple_records)
    
    

# End of Results class


class Record:
  pass

# End of Record class


#EOF
