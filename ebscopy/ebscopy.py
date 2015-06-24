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
from config import Mode


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
    
  # Internal method to generate a URL
  def __build_url(self, **kwargs):
  # /edsapi/rest/
  # /authservice/rest/UIDAuth 
    pass

  # Internal method to actually connect and get data
  def __get(self, url, data):
  # Check for timeout, reinit if needed

  # Handle error, reinit if needed
  # 400 error, invalid session token
  #  Receive JSON:
  #    {"DetailedErrorDescription":"Invalid Session Token. Please generate a new one.","ErrorDescription":"Session Token Invalid","ErrorNumber":"109"}
    pass

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
