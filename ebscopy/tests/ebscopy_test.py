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
		#self.assertEqual(res_1_blue, res_2_blue)
		self.assertEqual(int(round(len(res_1_blue) - len(res_2_blue), -1)), 0)
		res_1_green							= sess_1.search("green")
		self.assertNotEqual(res_1_blue, res_1_green)
		sess_1.end()
		with self.assertRaises(SessionError):								# Explicitly ended, so don't try to recreate
			res_1_red						= sess_1.search("red")
		res_2_green							= sess_2.search("green")
		#self.assertEqual(res_1_green, res_2_green)
		self.assertEqual(int(round(len(res_1_green) - len(res_2_green), -1)), 0)
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
		#self.assertEqual(len(ebscopy.POOL), 0)										# Pool should start empty
		conn_a								= ebscopy.POOL.get()					# Can I get a new implicit connection from the pool?
		self.assertIsInstance(conn_a, ebscopy._Connection)			
		sess_1								= ebscopy.Session(connection=conn_a)	# Can I make a session with the object?
		self.assertIsInstance(sess_1, ebscopy.Session)
		info_1								= sess_1.info_data
		self.assertIsNotNone(info_1)
		sess_2								= ebscopy.Session(connection=conn_a)	# Can I make another session with the same object?
		self.assertNotEqual(sess_1, sess_2)											# These sessions should be different
		conn_b								= ebscopy.POOL.get()
		self.assertIsInstance(conn_b, ebscopy._Connection)
		self.assertEqual(len(ebscopy.POOL), 1)										# Pool should only have the one _Connection
		self.assertEqual(conn_a, conn_b)											# ConnectionPool should have given the existing _Connection
		sess_1.end()
		sess_2.end()
	# End of [test_sessions_via_connections] function
# End of [CreateConnectionFirst] class

class SearchTests(unittest.TestCase):
	def test_basic_search_results(self):
		sess								= ebscopy.Session()
		res_yellow							= sess.search("yellow")

		self.assertIsInstance(res_yellow, ebscopy.Results)
		self.assertGreater(res_yellow.stat_total_hits, 0)
		self.assertGreater(res_yellow.stat_total_time, 0)
		self.assertGreater(len(res_yellow.avail_facets_labels), 0)
		self.assertIsInstance(res_yellow.record[0], tuple)
		self.assertEqual(sess.current_page, 1)

		res_yellow_blue						= sess.search("yellow blue")
		self.assertGreater(res_yellow, res_yellow_blue)								# Does a one term search have more hits than a two term search?

		rec									= sess.retrieve(res_yellow.record[0])	# Can I retrieve a record from the results list?
		self.assertIsInstance(rec, ebscopy.Record)
		
		sess.end()
	# End of [test_basic_search_results] function

	def test_search_modes(self):
		sess								= ebscopy.Session()
		res_def								= sess.search("red green")
		res_any								= sess.search("red green", mode="any")
		res_bool							= sess.search("red AND green", mode="bool")

		self.assertEqual(sess.default_search_mode, res_def.search_criteria["SearchMode"])
		self.assertEqual("any", res_any.search_criteria["SearchMode"])
		self.assertEqual("bool", res_bool.search_criteria["SearchMode"])


		sess.end()
	# End of [test_search_modes] function

	def test_limiter_search_results(self):
		sess								= ebscopy.Session()
		res									= sess.search("volcano", limiters=["FT:Y", "RV:Y"])

		self.assertTrue(res)

		sess.end()

	def test_bad_limiters(self):
		sess								= ebscopy.Session()
		res									= sess.search("volcano", limiters=["JJ:Y", "XX:Y"])

		self.assertTrue(res)

		# In strict mode, it should raise a ValueError
		ebscopy._strict						= True
		with self.assertRaises(ValueError):
			res_error						= sess.search("earthquake", limiters=["JJ:Y", "XX:Y"])
		ebscopy._strict						= False

		sess.end()

	def test_dt1_limiter(self):
		sess								= ebscopy.Session()
		res_api_date						= sess.search("volcano", limiters=["DT1:2014-01/2014-12"])		# This is the form that API requires
		res_eds_date						= sess.search("volcano", limiters=["DT1:20140101-20141231"])	# This is the form that the EDS interface generates

		self.assertEqual(int(round(len(res_api_date) - len(res_eds_date), -1)), 0)	# Are the two result sets within 8 results of each other?

		res_eds_date_space					= sess.search("volcano", limiters=["DT1: 20140101-20141231"])	# A common form from EDS contains a space
		self.assertTrue(res_eds_date_space)
		self.assertEqual(res_eds_date, res_eds_date_space)

		res_api_date_space					= sess.search("volcano", limiters=["DT1: 2014-01/2014-12"])		# The space should be acceptable
		self.assertTrue(res_api_date_space)
		self.assertEqual(res_api_date, res_api_date_space)
		

		res_feb_31							= sess.search("magma", limiters=["DT1:19000101-19930231"])		# The EDS interface considers the 31st to be the last day of every month
		self.assertTrue(res_feb_31)

		
		# Date ranges can be open-ended
		res_only_start						= sess.search("magma", limiters=["DT1:19930131-"])
		res_only_start_space				= sess.search("magma", limiters=["DT1: 19930131-"])
		res_only_end						= sess.search("magma", limiters=["DT1:-19930131"])
		res_only_end_space					= sess.search("magma", limiters=["DT1: -19930131"])

		self.assertTrue(res_only_start)
		self.assertTrue(res_only_start_space)
		self.assertTrue(res_only_end)
		self.assertTrue(res_only_end_space)

		sess.end()
	
	def test_expander_search_results(self):
		sess								= ebscopy.Session()
		res									= sess.search("earthquake", expanders=["fakeexpander:Y", "fulltext:Y"])

		self.assertTrue(res)

		sess.end()
# End of [SearchTests] class

class BadResultTests(unittest.TestCase):
	def test_bad_date_value(self):
		sess								= ebscopy.Session()
		res									= sess.search("AN uoc.2743836", rpp=5)	# This item has a PubDate "M" value of "19"

		self.assertEqual(int(res.records_raw[0]["RecordInfo"]["BibRecord"]["BibRelationships"]["IsPartOfRelationships"][0]["BibEntity"]["Dates"][0]["M"]), 19)
		self.assertFalse(res.records_simple[0]["PubDate"])

		sess.end()
# End of [BadResultTests] class

class PageTests(unittest.TestCase):
	def test_basic_page_movement(self):
		sess								= ebscopy.Session()
		res_1								= sess.search("red yellow orange green indigo violet", rpp=5)
		res_2								= sess.next_page()						# Get the next page of results

		self.assertEqual(sess.current_page, 2)										# Is the session on the next page?
		self.assertEqual(res_2.page_number, 2)										# Are the results on the next page?
		self.assertEqual(sess.current_page, res_2.page_number)						# Does the session page match the latest results page? (Technically, this must be true, due to the transitive property of the last two tests)
		self.assertIsInstance(res_2, ebscopy.Results)								# Is the second page a Results object?
		self.assertGreater(res_2.stat_total_hits, 0)								# Are there still more than 0 hits?
		self.assertNotEqual(res_1, res_2)											# Are the two pages different?
		self.assertNotEqual(res_1.record[0], res_2.record[0])						# Is the first item of the 1st page different than the first item of the 2nd page?
		
		res_4								= sess + 2								# Does addition work?
		self.assertEqual(sess.current_page, 4)										# Is the session on the right page?
		self.assertEqual(res_4.page_number, 4)										# Are the results on the right page?

		res_3								= sess - 1								# Does subtraction work?
		self.assertEqual(sess.current_page, 3)										# Is the session on the right page?
		self.assertEqual(res_3.page_number, 3)										# Are the results on the right page?

		sess.end()

	def test_too_many_page_movement(self):
		sess								= ebscopy.Session()

		res_blue							= sess.search("blue", rpp=100)
		res_bad								= sess + 5

		self.assertFalse(res_bad)													# Does skipping too many pages give an empty result set?

		res_roygbiv							= []
		res_roygbiv.append(sess.search("red yellow orange green indigo violet", rpp=10))
		
		# Collect results until we get the same page twice
		for page in range(1,10):
			res								= sess.next_page()
			res_roygbiv.append(res)
			if not res:
				break
			
		self.assertTrue(res_roygbiv[0])
		self.assertTrue(res_roygbiv[1])
		self.assertFalse(res_roygbiv[-1])											# Is the last result page empty?
		
		sess.end()

	#@unittest.expectedFailure														#("This is currently broken by a bug in the API")
	@unittest.skip("This is currently broken by a bug in the API")
	def test_basic_long_page_movement(self):
		sess								= ebscopy.Session()

		for page in range(0, 50):
			if page == 0:
				res							= sess.search("green", rpp=100, view="detailed", highlight="n")
			else:
				res							= sess.next_page()

			if not res:
				break

		self.assertTrue(res)
		self.assertEqual(sess.current_page, res.page_number)						# Does the session page match the latest results page?
		self.assertEqual(res.page_number, 50)										# Does the results page number match the loop count?

		sess.end()

	#@unittest.expectedFailure														#("This is currently broken by a bug in the API")
	@unittest.skip("This is currently broken by a bug in the API")
	def test_facet_long_page_movement(self):
		sess								= ebscopy.Session()

		for page in range(0, 50):
			if page == 0:
				res							= sess.search("green", rpp=100, view="detailed", highlight="n")
				res							= sess.add_action("addfacetfilter(SourceType:Academic Journals)")
			else:
				res							= sess.next_page()

			if not res:
				break

		self.assertTrue(res)
		self.assertEqual(sess.current_page, res.page_number)						# Does the session page match the latest results page?
		self.assertEqual(res.page_number, 50)										# Does the results page number match the loop count?

		sess.end()
# End of [PageTests] class


class RecordTests(unittest.TestCase):
	def test_record_equality(self):
		sess								= ebscopy.Session()
		res									= sess.search("orange")

		rec_0								= sess.retrieve(res.record[0])
		rec_1_a								= sess.retrieve(res.record[1])
		rec_1_b								= sess.retrieve(res.record[1])
		rec_2								= sess.retrieve(res.record[2])

		self.assertIsInstance(rec_0, ebscopy.Record)
		self.assertIsInstance(rec_0.dbid, (unicode, str))
		self.assertIsInstance(rec_0.an, (unicode, str))
		self.assertIsInstance(rec_0.plink, (unicode, str))
		self.assertRegexpMatches(rec_0.plink, "^http://")

		self.assertEqual(rec_0, rec_0)									# Test identity
		self.assertEqual(rec_1_a, rec_1_b)								# Test two equal objects
		self.assertNotEqual(rec_0, rec_2)								# Test two different objects

		sess.end()
# End of [RecordTests] class

class TimeoutTests(unittest.TestCase):
	@unittest.skip("The timeout test takes too long.")
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
