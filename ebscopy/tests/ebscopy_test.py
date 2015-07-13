#!/usr/bin/python
#
# Test suite for ebscopy
#
# TODO?
# Create second Session object with specific user/pass and no Connection object
# Do we need to test that an implicit connection with bad env variables doesn't work? I don't think so...
# 

from ebscopy import *
import unittest
from requests import HTTPError
import os
import re
import time
from datetime import datetime

# We need these ENV variables to exist for testing
class EnvironmentIsGoodTests(unittest.TestCase):
	def test_for_env_variables(self):
		self.assertGreater(len(os.environ['EDS_USER']), 0)
		self.assertGreater(len(os.environ['EDS_PASS']), 0)
		self.assertGreater(len(os.environ['EDS_PROFILE']), 0)
		self.assertGreater(len(os.environ['EDS_ORG']), 0)
		self.assertGreater(len(os.environ['EDS_GUEST']), 0)
# End of [EnvironmentIsGoodTests] class

# The simplest creation method
# While we're doing it, might as well get some basic two-session stuff out of the way
class CreateSessionsWithENV(unittest.TestCase):
	def test_basic_sessions(self):
		sess_1								= ebscopy.Session()
		self.assertIsInstance(sess_1, ebscopy.Session)
		info_1								= sess_1.info_data
		self.assertIsNotNone(info_1)
		sess_2								= ebscopy.Session()
		self.assertEqual(sess_1.connection, sess_2.connection)
		self.assertNotEqual(sess_1, sess_2)
		res_1_blue							= sess_1.search("blue")
		res_2_blue							= sess_2.search("blue")
		self.assertIsInstance(res_1_blue, ebscopy.Results)
		self.assertEqual(res_1_blue, res_2_blue)
		res_1_green							= sess_1.search("green")
		self.assertNotEqual(res_1_blue, res_1_green)
		sess_1.end()
		with self.assertRaises(SessionError):								# Explicitly ended, so don't try to recreate
			res_1_red						= sess_1.search("red")
		res_2_green							= sess_2.search("green")
		self.assertEqual(res_1_green, res_2_green)
		sess_2.end()
	# End of [test_basic_sessions] function
# End of [CreateSessionsWithENV] class

class CreateSessionsWithParameters(unittest.TestCase):
	# We want to strip out any environment variables so they don't get used
	def setUp(self):
		self.environ						= {}
		for env, value in os.environ.items():
			if re.match("EDS_", env):
				self.environ[env]			= value
				os.environ[env]				= ""

	# Gotta put them back!
	def tearDown(self):
		for env, value in self.environ.items():
			os.environ[env]					= value

	def test_good_explicit_connection_works(self):
		user_id								= self.environ.get("EDS_USER")
		password							= self.environ.get("EDS_PASS")
		profile								= self.environ.get("EDS_PROFILE")
		org									= self.environ.get("EDS_ORG")
		guest								= self.environ.get("EDS_GUEST")

		sess_1								= ebscopy.Session(user_id=user_id, password=password, profile=profile, org=org, guest=guest)
		self.assertIsInstance(sess_1, ebscopy.Session)
		info_1								= sess_1.info_data
		sess_1.end()
		self.assertIsNotNone(info_1)

	def test_bad_explicit_connection_breaks(self):
		with self.assertRaises(ebscopy.AuthenticationError):
			sess_1							= ebscopy.Session(user_id="betternotwork", password="betternotwork", profile="betternotwork", org="betternotwork", guest="n")

	def test_missing_user_explicit_connection_breaks(self):
		with self.assertRaises(ValueError):
			sess_1							= ebscopy.Session(user_id="", password="", profile="", org="", guest="n")

	def test_implict_connection_breaks(self):
		with self.assertRaises(ValueError):
			sess_1							= ebscopy.Session()
# End of [CreateSessionsWithParameters] class

class CreateConnectionFirst(unittest.TestCase):
	def test_sessions_via_connections(self):
		self.assertEqual(len(ebscopy.POOL), 0)								# Pool should start empty
		conn_a								= ebscopy.POOL.get()			# Can I get a new implicit connection from the pool?
		self.assertIsInstance(conn_a, ebscopy._Connection)			
		sess_1								= ebscopy.Session(connection=conn_a)	# Can I make a session with the object?
		self.assertIsInstance(sess_1, ebscopy.Session)
		info_1								= sess_1.info_data
		self.assertIsNotNone(info_1)
		sess_2								= ebscopy.Session(connection=conn_a)	# Can I make another session with the same object?
		self.assertNotEqual(sess_1, sess_2)									# These sessions should be different
		conn_b								= ebscopy.POOL.get()
		self.assertIsInstance(conn_b, ebscopy._Connection)
		self.assertEqual(len(ebscopy.POOL), 1)								# Pool should only have the one _Connection
		self.assertEqual(conn_a, conn_b)									# ConnectionPool should have given the existing _Connection
		sess_1.end()
		sess_2.end()
	# End of [test_sessions_via_connections] function
# End of [CreateConnectionFirst] class

class Search(unittest.TestCase):
	def test_search_results(self):
		sess								= ebscopy.Session()
		res									= sess.search("yellow")

		self.assertGreater(res.stat_total_hits, 0)
		self.assertGreater(res.stat_total_time, 0)
		self.assertGreater(len(res.avail_facets_labels), 0)
		self.assertIsInstance(res.record[0], tuple)

		rec									= sess.retrieve(res.record[0])

		self.assertIsInstance(rec, ebscopy.Record)
		self.assertIsInstance(rec.dbid, (unicode, str))
		self.assertIsInstance(rec.an, (unicode, str))
		self.assertIsInstance(rec.plink, (unicode, str))
		self.assertRegexpMatches(rec.plink, "^http://")
		
		sess.end()
# End of [SearchTests] class

class RecordTests(unittest.TestCase):
	def test_record_equality(self):
		sess								= ebscopy.Session()
		res									= sess.search("orange")

		rec_0								= sess.retrieve(res.record[0])
		rec_1_a								= sess.retrieve(res.record[1])
		rec_1_b								= sess.retrieve(res.record[1])
		rec_2								= sess.retrieve(res.record[2])

		self.assertEqual(rec_0, rec_0)									# Test identity
		self.assertEqual(rec_1_a, rec_1_b)								# Test two equal objects
		self.assertNotEqual(rec_0, rec_2)								# Test two different objects

		sess.end()
# End of [RecordTests] class

class TimeoutTests(unittest.TestCase):
	def test_auth_timeout(self):
		conn							= ebscopy.POOL.get()
		sess							= ebscopy.Session(connection=conn)
		res_purple						= sess.search("purple")

		timeout_time					= conn.auth_timeout_time
		sleeptime						= timeout_time - datetime.now()

		time.sleep(sleeptime.seconds)
		time.sleep(60)

		res_violet						= sess.search("violet")
		
# EOF
