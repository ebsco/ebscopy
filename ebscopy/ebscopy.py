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

import json		# Need this for managing input and output
import os		# Need this to get ENV variables with auth info
import urllib2
import requests
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

    pass
    
  # Internal method to generate an HTTP request 
  def __request(self, method, data):
    valid_methods		= frozenset(CreateSession, Info, Search, Retrieve, EndSession, UIDAuth, SearchCriteria)
    if method not in valid_methods:
      raise ValueError

    base_host			= "https://eds-api.ebscohost.com"
    base_path			= ""
    base_url			= ""
    full_url			= ""

    if method == "UIDAuth":
      base_path			= "/authservice/rest/"
    else:
      base_path			= "/edsapi/rest/"

    full_url			= base_host + base_path + method

    headers			= {'Content-Type'='application/json', 'Accept'='application/json'}

    if self.auth_token:
      headers['x-authenticationToken']	= self.auth_token
    elif method is not "UIDAuth":
      raise ValueError
      
    if self.session_token:
      headers['x-sessionToken']		= self.session_token
    elif method not in ("UIDAuth", "CreateSession"):
      raise ValueError

    r				= requests.post(full_url, data=data, headers=headers)
    code			= r.status_code
    if code is not "200":
      if code is "400" and method not in ("UIDAuth", "CreateSession"):
        #TODO: Probably a timeout issue, need to recover
  	# 400 error, invalid session token
  	#  Receive JSON:
  	#    {"DetailedErrorDescription":"Invalid Session Token. Please generate a new one.","ErrorDescription":"Session Token Invalid","ErrorNumber":"109"}
      else
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

  # Save AuthToken
  #auth_token = valueof('AuthToken')
  # Save Timeout time
  #auth_timeout_time = valueof('AuthTimeout') + date.now

  # Do CreateSession
  # GET /edsapi/rest/CreateSession?profile=[PROFILE]&org=[ORG]&guest=[Y/N] Http/1.1
  # Headers:
  #   Content-Type: applicaton/json
  #   Accept: applicaton/json
  #   x-authenticationToken: [AuthToken]
  # Receive JSON with:
  #  SessionToken

  # Save SessionToken
  #session_token = valueof('SessionToken')

  # Do Info
  # GET /edsapi/rest/Info Http/1.1 
  # Headers:
  #   Content-Type: applicaton/json
  #   Accept: applicaton/json
  #   x-authenticationToken: [AuthToken]
  #   x-sessionToken: [SessionToken]
  # Receive JSON with:
  #  Lots of info
  # Need it to do searches correctly?
    pass

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





#EOF
