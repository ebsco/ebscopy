#!/usr/bin/python

from ebscopy import ebscopy
import unittest
from requests import HTTPError

class ExplicitConnectionTests(unittest.TestCase):
  def setUp(self):
    self.old_os_env_user	= os.getenv("EDS_USER")
    os.environ["EDS_USER"]=	= ""


  def tearDown(self):
    os.environ["EDS_USER"]=	= self.old_os_enf_user

  def test_good_explicit_connection_works(self):
    user_id		= os.getenv("EDS_USER")
    password		= os.getenv("EDS_PASS")
    profile		= os.getenv("EDS_PROFILE")
    org			= os.getenv("EDS_ORG")
    guest		= os.getenv("EDS_GUEST")
    c			= ebscopy.Connection(user_id=user_id password=password, profile=profile, org=org, guest=guest)
    c.connect()
    info		= c.info_data
    c.disconnect()
    self.assertIsNotNone(info)

  def test_bad_explicit_connection_breaks(self):
    with self.assertRaises(HTTPError):
      c			= ebscopy.Connection(user_id="betternotwork", password="betternotwork", profile="betternotwork", org="betternotwork", guest="n")
      c.connect()

  def test_missing_user_explicit_connection_breaks(self):
    with self.assertRaises(HTTPError):
      c			= ebscopy.Connection(user_id="", password="", profile="", org="", guest="n")
      c.connect()

  def test_implict_connection_breaks(self):
    with self.assertRaises(HTTPError):
      c			= ebscopy.Connection()
      c.connect()

class ImplicitConnectionTests(unittest.TestCase):
  def test_implicit_connection_works(self):
    c			= ebscopy.Connection()
    c.connect()
    info		= c.info_data
    c.disconnect()
    self.assertIsNotNone(info)


   

#connection	= ebscopy.Connection()
#connection.connect()
#results = connection.search("blue")
#print "---------------"
#print "Search Results"
#print "---------------"
#results.pprint()
#print "---------------"
#print "Total Hits:"
#print results.stat_total_hits
#print "---------------"
#print "Available Facets:"
#print results.avail_facets_labels
#print "---------------"
#print 
#
#record = connection.retrieve(results.record[0])
#print "---------------"
#print "Simple Call for Record Info"
#print "---------------"
#record.pprint()
#print "---------------"
#
#record = connection.retrieve((results.simple_records[0]['DbId'], results.simple_records[0]['An']), highlight=["blue"])
#print "---------------"
#print "Record Info with Highlight"
#print "---------------"
#record.pprint()
#print "---------------"
#
#record = connection.retrieve((results.simple_records[0]['DbId'], results.simple_records[0]['An']))
#print "---------------"
#print "Record Info without Highlight"
#print "---------------"
#record.pprint()
#print "---------------"
#
#connection.disconnect()
#
##
