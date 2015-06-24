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
#import urllib2
import requests					# Does the heavy HTTP lifting
from datetime import datetime, timedelta	# Monitor authentication timeout
from config import *


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

    if Mode.debug:
      print self.user_id
      print self.password
      print self.profile
      print self.org
      print self.guest

    
  # Internal method to generate an HTTP request 
  def __request(self, method, data):
    valid_methods		= frozenset(["CreateSession", "Info", "Search", "Retrieve", "EndSession", "UIDAuth", "SearchCriteria"])
    if method not in valid_methods:
      raise ValueError

    data_json			= json.dumps(data)
    base_host			= "https://eds-api.ebscohost.com"
    base_path			= ""
    base_url			= ""
    full_url			= ""

    if method == "UIDAuth":
      base_path			= "/authservice/rest/"
    else:
      base_path			= "/edsapi/rest/"

    full_url			= base_host + base_path + method

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

    r				= requests.post(full_url, data=data_json, headers=headers)
    code			= r.status_code
    if code is not "200":
      if code is "400" and method not in ("UIDAuth", "CreateSession"):
        if Mode.debug: print "Session died!?!"
        #TODO: Probably a timeout issue, need to recover
  	# 400 error, invalid session token
  	#  Receive JSON:
  	#    {"DetailedErrorDescription":"Invalid Session Token. Please generate a new one.","ErrorDescription":"Session Token Invalid","ErrorNumber":"109"}
      else:
        r.raise_for_status()

    # This should be a dict now...?
    return r.json()
  # End of __request


  def connect(self):
  # Do UIDAuth
  # POST /authservice/rest/UIDAuth Http/1.1
  # Headers:
  #   Content-Type: applicaton/json
  #   Accept: applicaton/json
  # Send JSON with:
  #  UserId
  #  Password
  #  InterfaceId
  # Receive JSON with:
  #  AuthToken
  #  AuthTimeout

    auth_data			= {
					"UserId":	self.user_id,
					"Password":	self.password,
					"InterfaceId":	self.interface_id
			  	}
    auth_response		= self.__request("UIDAuth", auth_data)
    if Mode.debug: print auth_response

    self.auth_token		= auth_response["AuthToken"]
    self.auth_timeout		= auth_response["AuthTimeout"]
    self.auth_timeout_time	= datetime.now() + timedelta(seconds=int(self.auth_timeout))

  # Do CreateSession
  # GET /edsapi/rest/CreateSession?profile=[PROFILE]&org=[ORG]&guest=[Y/N] Http/1.1
  # Headers:
  #   Content-Type: applicaton/json
  #   Accept: applicaton/json
  #   x-authenticationToken: [AuthToken]
  # Receive JSON with:
  #  SessionToken

    create_data			= {
					"Profile":	self.profile,
					"Guest":	self.guest,
					"Org":		self.org
				}

    create_response		= self.__request("CreateSession", create_data)
    if Mode.debug: print create_response

    self.session_token		= create_response["SessionToken"]


  # Do Info
  # GET /edsapi/rest/Info Http/1.1 
  # Headers:
  #   Content-Type: applicaton/json
  #   Accept: applicaton/json
  #   x-authenticationToken: [AuthToken]
  #   x-sessionToken: [SessionToken]
  # Receive JSON with:
  #  Lots of info

    info_data			= {}

    info_response		= self.__request("Info", info_data)
    if Mode.debug: print info_response
    self.info_data		= info_response
	# TODO: catch SessionTimeout?

  # End of connect

  # Do a search
  def search(self, query):

  # Pull in info needed:
  #  query(ies)
  #  searchmode
  #  resultsperpage
  #  pagenumber (maintain this state)?
  #  sort type
  #  highlighting?
  #  include facets?
  #  view
  #  expander

  # GET /edsapi/rest/Search?query=[QUERY]&searchmode=[bool|all|any|smart]&resultsperpage=20&pagenumber=1&sort=relevance&highlight=y&includefacets=y&view=brief&expander=fulltext Http/1.1 
    pass


  def disconnect(self):
    end_data			= {
					"SessionToken": self.session_token
				  }
    end_response		= self.__request("EndSession", end_data)
    if Mode.debug: print end_response
  # End of disconnect


#EOF
