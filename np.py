# coding=utf-8

import configparser
import hexchat
import requests
import html
import os
import sys

# http://stackoverflow.com/a/10077069 (fixed for python 3)
from collections import defaultdict
from xml.etree import cElementTree as ET


def etree_to_dict(t):
	d = {t.tag: {} if t.attrib else None}
	children = list(t)
	if children:
		dd = defaultdict(list)
		for dc in map(etree_to_dict, children):
			for k, v in dc.items():
				dd[k].append(v)
		d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.items()}}
	if t.attrib:
		d[t.tag].update(("@" + k, v) for k, v in t.attrib.items())
	if t.text:
		text = t.text.strip()
		if children or t.attrib:
			if text:
			  d[t.tag]["#text"] = text
		else:
			d[t.tag] = text
	return d


__module_name__ = "vlcnp"
__module_author__ = "albert--"
__module_version__ = "1.0"
__module_description__ = "HexChat 'now playing' script for VLC media player"
config = configparser.ConfigParser()
try:
	config.read(os.getenv('HOME') + '/.config/nowplay.ini')
	password = config['DEFAULT']['password']
except:
	password = 'password'

def np_cb(word, word_eol, userdata):
	if len(word) > 1:
		f = open("C:\\Users\\Albert\\AppData\\Roaming\\foobar2000\\np.txt", "r").read()
		cmd = "me " + f
	else:
		r = requests.get("http://localhost:8080/requests/status.xml", auth=("", password))
		e = ET.XML(r.text)
		xml = etree_to_dict(e)

		infos = {}
		try:
			xmlinfo = xml["root"]["information"]["category"][0]["info"]
		except KeyError:
			# filename = infos["filename"]
			cmd = "me is now playing an unknown song"
			hexchat.command(html.unescape(cmd))
			return hexchat.EAT_ALL


		def lookup(info, field):
			try:
				if isinstance(info, dict) and (field not in info):
					text = ''
				else:
					text = info[field]
			except TypeError:
				text = info[0][field]
			except KeyError:
				try:
					text = info[0][field]
				except KeyError:
					print('info=', info, file=sys.stderr)
					assert 0
			return text


		if len(xmlinfo) > 2:
			for info in xmlinfo:
				infos[lookup(info, "@name")] = lookup(info, "#text")
		else:
			infos["filename"] = lookup(xmlinfo, "#text")

		try:
			album = infos["album"]
			artist = infos["artist"]
			title = infos["title"]
			m, s = divmod(int(xml["root"]["length"]), 60)
			length = "%02d:%02d" % (m, s)
			cmd = "me is now playing: \002\00311{}\017 - \002\00311{}\017 (\002\00311{}\017) [\002\00307{}\017]".format(artist, title, album, length)
		except KeyError:
			m, s = divmod(int(xml["root"]["time"]), 60)
			time = "%02d:%02d" % (m, s)
			m, s = divmod(int(xml["root"]["length"]), 60)
			length = "%02d:%02d" % (m, s)
			try:
				title = infos["title"]
				cmd = "me is now playing: \002\00311{}\017 [\00308{}\017/\002\00307{}\017]".format(title, time, length)
			except:
				filename = infos["filename"]
				cmd = "me is now playing: \002\00311{}\017 [{}/\002\00307{}\017]".format(filename.encode(encoding='iso8859-1').decode(encoding='utf-8'), time, length)

	hexchat.command(html.unescape(cmd))
	return hexchat.EAT_ALL

def unload_cb(userdata):
	print(__module_name__, "version", __module_version__, "unloaded.")

hexchat.hook_command("np", np_cb)
hexchat.hook_unload(unload_cb)
