#!/usr/bin/python

from ebscopy import *

session = Session()
results = session.search("blue")

results.pprint()

print 
print "Total Hits:"
print "---------------"
print results.stat_total_hits
print 
print "Available Facets:"
print "---------------"
print results.avail_facets_labels
print 

record = session.retrieve(results.record[0])

print
print "Simple Call for Record Info"
print "---------------"
record.pprint()
print

record = session.retrieve((results.records_simple[0]['DbId'], results.records_simple[0]['An']), highlight=["blue"])

print 
print "Record Info with Highlight"
print "---------------"
record.pprint()
print

record = session.retrieve((results.records_simple[0]['DbId'], results.records_simple[0]['An']))

print
print "Record Info without Highlight"
print "---------------"
record.pprint()
print

session.end()

# EOF
