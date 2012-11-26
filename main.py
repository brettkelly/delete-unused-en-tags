#!/usr/bin/env python

# Copyright 2012 Evernote Corporation
# All rights reserved.

import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors

from time import sleep
import socket

EN_HOST = "www.evernote.com"
EN_URL = "https://%s" % EN_HOST
TESTING = False
MAX_TIMEOUTS = 5
MAX_DELETE = 2

def getUserStoreInstance(authToken):
	print "Getting UserStore instance..."
	userStoreUri = "%s/edam/user" % EN_URL
	userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
	userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
	userStore = UserStore.Client(userStoreProtocol)
	return userStore

def getNoteStoreInstance(authToken, userStore):
	print "Getting NoteStore instance..."
	try:
		noteStoreUrl = userStore.getNoteStoreUrl(authToken)
	except Errors.EDAMUserException, ue:
		print "Error: your dev token is probably wrong; double-check it."
		print ue
		return None

	noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
	noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
	noteStore = NoteStore.Client(noteStoreProtocol)
	return noteStore

def getNonEmptyUserInput(prompt):
	"""
	Prompt the user for input, disallowing empty responses
	"""
	uinput = raw_input(prompt)
	if uinput:
		return uinput
	print "This can't be empty. Try again."
	return getNonEmptyUserInput(prompt)

def getAllTags(authToken, noteStore):
	try:
		tags = noteStore.listTags(authToken)
		return [t.guid for t in tags]
	except Exception, e:
		print "Exception calling listTags"
		print type(e), e

def deleteTag(authToken, noteStore, tagGuid):
	try:
		tag = noteStore.getTag(authToken, tagGuid)
		noteStore.expungeTag(authToken, tag)
		print "Tag %s deleted." % tag.name
	except Exception, e:
		print "Exception when getting or deleting tag:"
		print type(e), e
		raise SystemExit

def getAllTagGuids(authToken, noteStore):
	tagguids = []
	timeouts = 0
	offset = 0
	chunk = 100
	rspec = NoteStore.NotesMetadataResultSpec()
	rspec.includeTagGuids = True
	nfilter = NoteStore.NoteFilter()
	moreNotes = True
	while moreNotes:
		try:
			print "Current offset: ", offset
			mdata = noteStore.findNotesMetadata(authToken, nfilter, offset, chunk, rspec)
		except socket.error, se:
			timeouts += 1
			if timeouts < MAX_TIMEOUTS:
				print "Timed out. Waiting briefly before attempting to reconnect."
				sleep(3)
				continue
			else:
				print "Maximum timeout threshold reached. Quitting"
				raise SystemExit

		except Exception, e:
			print "findNotesMetadata broke:"
			print type(e), e
			raise SystemExit

		for n in mdata.notes:
			if n.tagGuids:
				tagguids += n.tagGuids

		if len(mdata.notes) % chunk == 0:
			offset += chunk
		else:
			moreNotes = False

	# dedupe tag guid list
	tGuids = dict(map(None,tagguids,[])).keys()
	return tGuids


authToken = "" # bypass the dev token prompt by populating this variable.

if not authToken:
	authToken = getNonEmptyUserInput("Enter your dev token: ")

# Get initialized UserStore and NoteStore instances
userStore = getUserStoreInstance(authToken)
noteStore = getNoteStoreInstance(authToken, userStore)

##
# Retrieve all tags
##
print "Getting tags..."
allTags = getAllTags(authToken, noteStore)
if not allTags:
	print "No tags retrieved"
	raise SystemExit
print "Total tags: %d" % len(allTags)

##
# Retrieve all tags currently in use
##
print "Collecting used tags..."
tguids = getAllTagGuids(authToken, noteStore)
print "Total guids:", len(tguids)

##
# Compare the two lists, build a collection of unused tags
##
unusedTagGuids = []

for t in allTags:
	if t not in tguids:
		unusedTagGuids.append(t)

print "You have %d unused tags." % len(unusedTagGuids)

##
# If not testing, delete tags up to MAX_DELETE (if set)
##

if not TESTING:
	delCount = 0
	for tGuid in unusedTagGuids:
		deleteTag(authToken, noteStore, tGuid)
		delCount += 1
		if MAX_DELETE and delCount == MAX_DELETE:
			break
