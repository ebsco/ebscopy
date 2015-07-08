#!/usr/bin/python

from ebscopy import ebscopy
import unittest
from requests import HTTPError
import os
import re

class EnvironmentIsGoodTests(unittest.TestCase):
  def test_for_env_variables(self):
    self.assertGreater(len(os.environ['EDS_USER']), 0)
    self.assertGreater(len(os.environ['EDS_PASS']), 0)
    self.assertGreater(len(os.environ['EDS_PROFILE']), 0)
    self.assertGreater(len(os.environ['EDS_ORG']), 0)
    self.assertGreater(len(os.environ['EDS_GUEST']), 0)
# End of [EnvironmentIsGoodTests] class

# TODO: Types of connections...
#
# Create first Session object with env var user/pass and no Connection object
# Create first Session object with specific user/pass and no Connection object
#
# Create second Session object with env var user/pass and no Connection object
# Create second Session object with specific user/pass and no Connection object
#
# Manually get a Connection object...
#
# Create first Session object with passed Connection object
# 
# Create second Session object with passed Connection object
# 
#####
# sess	= Session()
# sess	= Session(profile, etc)
# sess	= Session(user, password, profile)
# sess	= Session(Connection, profile)

# TODO: Do we need to test that an implicit connection with bad env variables doesn't work? I don't think so...

# The simplest creation method
# While we're doing it, might as well get some basic two-session stuff out of the way
class CreateSessionsWithENV(unittest.TestCase):
  def test_basic_sessions(self):
    sess_1		= ebscopy.Session()
    self.assertIsInstance(sess_1, ebscopy.Session)
    info_1		= sess_1.info_data
    self.assertIsNotNone(info_1)
    sess_2		= ebscopy.Session()
    self.assertEqual(sess_1.connection, sess_2.connection)
    self.assertNotEqual(sess_1, sess_2)
    res_1_blue		= sess_1.search("blue")
    res_2_blue		= sess_2.search("blue")
    self.assertIsInstance(res_1_blue, ebscopy.Results)
    self.assertEqual(res_1_blue, res_2_blue)
    res_1_green		= sess_1.search("green")
    self.assertNotEqual(res_1_blue, res_1_green)
    sess_1.end()
    with self.assertRaises(HTTPError):
      res_1_red		= sess_1.search("red")
    res_2_green		= sess_2.search("green")
    self.assertEqual(res_1_green, res_2_green)
    sess_2.end()
  # End of [test_basic_sessions] function
# End of [CreateSessionsWithENV] class

class CreateSessionsWithParameters(unittest.TestCase):
  # We want to strip out any environment variables so they don't get used
  def setUp(self):
    self.environ		= {}
    for env, value in os.environ.items():
       if re.match("EDS_", env):
         self.environ[env]	= value
         os.environ[env]	= ""

  # Gotta put them back!
  def tearDown(self):
    for env, value in self.environ.items():
      os.environ[env]		= value

  def test_good_explicit_connection_works(self):
    user_id		= self.environ.get("EDS_USER")
    password		= self.environ.get("EDS_PASS")
    profile		= self.environ.get("EDS_PROFILE")
    org			= self.environ.get("EDS_ORG")
    guest		= self.environ.get("EDS_GUEST")

    sess_1		= ebscopy.Session(user_id=user_id, password=password, profile=profile, org=org, guest=guest)
    self.assertIsInstance(sess_1, ebscopy.Session)
    info_1		= sess_1.info_data
    sess_1.end()
    self.assertIsNotNone(info_1)

  def test_bad_explicit_connection_breaks(self):
    with self.assertRaises(HTTPError):
      sess_1		= ebscopy.Session(user_id="betternotwork", password="betternotwork", profile="betternotwork", org="betternotwork", guest="n")

  def test_missing_user_explicit_connection_breaks(self):
    with self.assertRaises(ValueError):
      sess_1		= ebscopy.Session(user_id="", password="", profile="", org="", guest="n")

  def test_implict_connection_breaks(self):
    with self.assertRaises(ValueError):
      sess_1		= ebscopy.Session()
# End of [CreateSessionsWithParameters] class


class SearchTests(unittest.TestCase):
  def test_search_results(self):
    sess		= ebscopy.Session()
    res			= sess.search("yellow")

    self.assertGreater(res.stat_total_hits, 0)
    self.assertGreater(res.stat_total_time, 0)
    self.assertGreater(len(res.avail_facets_labels), 0)
    self.assertIsInstance(res.record[0], tuple)

    rec			= sess.retrieve(res.record[0])

    self.assertIsInstance(rec, ebscopy.Record)
    self.assertIsInstance(rec.dbid, (unicode, str))
    self.assertIsInstance(rec.an, (unicode, str))
    self.assertIsInstance(rec.plink, (unicode, str))
    self.assertRegexpMatches(rec.plink, "^http://")
    
    sess.end()
# End of [SearchTests] class


class RecordTests(unittest.TestCase):
  def test_record_equality(self):
    sess		= ebscopy.Session()
    res			= sess.search("orange")

    rec_0		= sess.retrieve(res.record[0])
    rec_1_a		= sess.retrieve(res.record[1])
    rec_1_b		= sess.retrieve(res.record[1])
    rec_2		= sess.retrieve(res.record[2])

    self.assertEqual(rec_0, rec_0)				# Test identity
    self.assertEqual(rec_1_a, rec_1_b)				# Test two equal objects
    self.assertNotEqual(rec_0, rec_2)				# Test two different objects

    sess.end()
# End of [RecordTests] class

# EOF
