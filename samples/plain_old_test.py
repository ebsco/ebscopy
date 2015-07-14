#!/usr/bin/python

from ebscopy import *

connection = POOL.get()
session = Session(connection)
results = session.search("blue")
print "---------------"
print "Search Results"
print "---------------"
results.pprint()
print "---------------"
print "Total Hits:"
print results.stat_total_hits
print "---------------"
print "Available Facets:"
print results.avail_facets_labels
print "---------------"
print 

record = session.retrieve(results.record[0])
print "---------------"
print "Simple Call for Record Info"
print "---------------"
record.pprint()
print "---------------"

record = session.retrieve((results.simple_records[0]['DbId'], results.simple_records[0]['An']), highlight=["blue"])
print "---------------"
print "Record Info with Highlight"
print "---------------"
record.pprint()
print "---------------"

record = session.retrieve((results.simple_records[0]['DbId'], results.simple_records[0]['An']))
print "---------------"
print "Record Info without Highlight"
print "---------------"
record.pprint()
print "---------------"

session.end()

# EOF
