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

import getopt
import sys
import os
import threading
import logging
from Queue import Queue

import traceback
import ConfigParser

try:
	import xdg.BaseDirectory as bd
	is_local = True
except ImportError:
	is_local = False

import plugins

SUPPORTED_FORMATS = 'video/x-msvideo', 'video/quicktime', 'video/x-matroska', 'video/mp4'
VERSION = "0.1.6"

class Periscope:
	''' Main Periscope class'''
	
	def __init__(self):
		self.config = ConfigParser.SafeConfigParser({"lang": "en"})
		if is_local:
			self.config_file = os.path.join(bd.xdg_config_home, "periscope", "config")
			if not os.path.exists(self.config_file):
				folder = os.path.dirname(self.config_file)
				if not os.path.exists(folder):
					logging.info("Creating folder %s" %folder)
					os.mkdir(folder)
				logging.info("Creating config file")
				configfile = open(self.config_file, "w")
				self.config.write(configfile)
				configfile.close()

		self.pluginNames = self.listExistingPlugins()
		self._preferedLanguages = None

	def get_preferedLanguages(self):
		lang = self.config.get("DEFAULT", "lang")
		logging.info("lang read from config: " + lang)
		if lang == "":
			return None
		else:
			return lang.split(",")

	def set_preferedLanguages(self, langs):
		self.config.set("DEFAULT", "lang", ",".join(langs))
		configfile = open(self.config_file, "w")
		self.config.write(configfile)
		configfile.close()

	preferedLanguages = property(get_preferedLanguages, set_preferedLanguages)

	
	def deactivatePlugin(self, pluginName):
		self.pluginNames - pluginName
		
	def activatePlugin(self, pluginName):
		if pluginName not in self.listExistingPlugins():
			raise ImportError("No plugin with the name %s exists" %pluginName)
		self.pluginNames + pluginName
		
	def listActivePlugins(self):
		return self.pluginNames
		
	def listExistingPlugins(self):
		return plugins.SubtitleDatabase.SubtitleDB.__subclasses__()
	
	def listSubtitles(self, filename, langs=None):
		'''Searches subtitles within the plugins and returns all found matching subtitles ordered by language then by plugin.'''
		#if not os.path.isfile(filename):
			#raise InvalidFileException(filename, "does not exist")
	
		logging.info("Searching subtitles for %s with langs %s" %(filename, langs))
		subtitles = []
		q = Queue()
		for name in self.pluginNames:
			plugin = name()
			logging.info("Searching on %s " %plugin.__class__.__name__)
			thread = threading.Thread(target=plugin.searchInThread, args=(q, filename, langs))
			thread.start()

		# Get data from the queue and wait till we have a result
		for name in self.pluginNames:
			subs = q.get(True)
			if subs and len(subs) > 0:
				if not langs:
					subtitles += subs
				else:
					for sub in subs:
						if sub["lang"] in langs:
							subtitles += [sub] # Add an array with just that sub
			
		if len(subtitles) == 0:
			return []
		return subtitles
	
	
	def selectBestSubtitle(self, subtitles, langs=None):
		'''Searches subtitles from plugins and returns the best subtitles from all candidates'''
		if not subtitles:
			return None

		if not langs: # No preferred language => return the first
				return subtitles[0]
		
		subtitles = self.__orderSubtitles__(subtitles)
		for l in langs:
			if subtitles.has_key(l) and len(subtitles[l]):
				return subtitles[l][0]

		return None #Could not find subtitles

	def downloadSubtitle(self, filename, langs=None):
		''' Takes a filename and a language and creates ONE subtitle through plugins'''
		subtitles = self.listSubtitles(filename, langs)
		if subtitles:
			logging.debug("All subtitles: ")
			logging.debug(subtitles)	
			return attemptDownloadSubtitle(subtitles, langs)
		else:
			return None
		
		
	def attemptDownloadSubtitle(self, subtitles, langs):
		subtitle = self.selectBestSubtitle(subtitles, langs)
		if subtitle:
			logging.debug("Trying to download subtitle: ")
			logging.debug(subtitle)
			#Download the subtitle
			try:
				subpath = subtitle["plugin"].createFile(subtitle["link"], filename)			
				subtitle["subtitlepath"] = subpath
				return subtitle
			except :
				# Could not download that subtitle, remove it
				logging.info("Subtitle %s could not be downloaded, trying the next on the list" %subtitle['link'])
				subtitles = subtitles - subtitle
				self.attemptDownloadSubtitle(subtitles, langs)
		else :
			logging.error("No subtitles could be chosen.")
			return Exception("No subtitle was chosen from the list of subtitles")
		
		
	def __orderSubtitles__(self, subs):
		'''reorders the subtitles according to the languages then the website'''
		try:
			from collections import defaultdict
			subtitles = defaultdict(list) #Order matters (order of plugin and result from plugins)
			for s in subs:
				subtitles[s["lang"]].append(s)
			return subtitles
		except ImportError, e: #Don't use Python 2.5
			subtitles = {}
			for s in subs:
				# return subtitles[s["lang"]], if it does not exist, set it to [] and return it, then append the subtitle
				subtitles.setdefault(s["lang"], []).append(s)
			return subtitles

class Subtitle:
	''' Attributes and method characterizing a subtitle'''
	def __init__(self, filename, lang=None, link=None, downloadmethod=None):
		self.filename = filename
		self.lang = lang
		self.link = link
		self.downloadmethod = downloadmethod
		
	def download(self):
		self.downloadmethod(self.link, self.filename)
		


