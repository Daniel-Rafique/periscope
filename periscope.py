#!/usr/bin/python
# -*- coding: utf-8 -*-

#   This file is part of periscope.
#
#    periscope is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    periscope is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import mimetypes
from optparse import OptionParser
import logging
import periscope

SUPPORTED_FORMATS = 'video/x-msvideo', 'video/quicktime'

def main():
	'''Download subtitles'''
	# parse command line options
	parser = OptionParser("usage: %prog [options] file1 file2")
	parser.add_option("-l", "--language", action="append", dest="langs", help="wanted language (ISO 639-1 two chars) for the subtitles (fr, en, ja, ...). If none is specified will download a subtitle in any language. This option can be used multiple times like %prog -l fr -l en file1 will try to download in french and then in english if no french subtitles are found.")
	parser.add_option("-q", "--query", action="append", dest="queries", help="query to send to the subtitles website")
	parser.add_option("--debug", action="store_true", dest="debug", help="set the logging level to debug")
	(options, args) = parser.parse_args()

	if not args:
		print parser.print_help()
		exit()

	# process args
	if options.debug:
		logging.basicConfig(level=logging.DEBUG)
		print "setting logging level to debug"
			
	if options.queries: args += options.queries
	videos = []
	for arg in args:
		videos += recursive_search(arg)

	for arg in videos:
		periscope_client = periscope.Periscope()
		if not options.langs: #Look into the config
			logging.info("No lang given, looking into config file")
			langs = periscope_client.preferedLanguages
		else:
			langs = options.langs
		sub = periscope_client.downloadSubtitle(arg, langs)

def recursive_search(entry):
	'''searches files in the dir'''
	files = []
	if os.path.isdir(entry):
		for e in os.listdir(entry):
			files += recursive_search(os.path.join(entry, e))
	elif os.path.isfile(entry):
		mimetype = mimetypes.guess_type(entry)[0]
		if mimetype in SUPPORTED_FORMATS:
			files.append(os.path.normpath(entry))
		else :
			logger.warn("%s mimetype i '%s' which is not supported (%s)" %(entry, mimetype, SUPPORTED_FORMATS))
	return files
	
if __name__ == "__main__":
	main()
