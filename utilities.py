### TSV files

def parseTSV(filename,*args):
	f = open(filename)
	
	result = []
	for l in [l for l in f if (not l.startswith("#")) and (not l.strip()=="")]:
		
		l = l.replace("\n","").split("#")[0]
		data = list(filter(None,l.split("\t"))) # Multiple tabs are okay, we don't accept empty fields unless trailing
		entry = [] * len(args)
		for i in range(len(args)):
			if args[i]=="list":
				try:
					entry.append(data[i].split("␟"))
				except:
					entry.append([])
			elif args[i]=="string":
				try:
					entry.append(data[i])
				except:
					entry.append("")
			elif args[i]=="int":
				try:
					entry.append(int(data[i]))
				except:
					entry.append(0)
			elif args[i]=="bool":
				try:
					entry.append((data[i].lower() in ["true","yes","1","y"]))
				except:
					entry.append(False)
				
		result.append(entry)
		
	f.close()
	return result
	
def checksumTSV(folder):
	import hashlib
	import os
	
	sums = ""
	
	for f in os.listdir(folder + "/"):
		if (f.endswith(".tsv")):
			f = open(folder + "/" + f,"rb")
			sums += hashlib.md5(f.read()).hexdigest() + "\n"
			f.close()
			
	return sums
	
# returns whether checksums match and sets the checksum to invalid if they don't (or sets the new one if no previous one exists)
def combineChecksums(filename,checksums):
	import os
	
	if os.path.exists(filename + ".rulestate"):
		f = open(filename + ".rulestate","r")
		oldchecksums = f.read()
		f.close()
		if oldchecksums == checksums:
		# the new checksum given by the calling db server represents the rule state that all current unsaved scrobbles were created under
		# if this is the same as the existing one, we're all good
			return True
		elif (oldchecksums != "INVALID"):
			#if not, the file is not consistent to any single rule state (some scrobbles were created with an old ruleset, some not)
			f = open(filename + ".rulestate","w")
			f.write("INVALID") # this will never match any sha256sum
			f.close()
			return False
		else:
			#if the file already says invalid, no need to open it and rewrite
			return False
	else:
		f = open(filename + ".rulestate","w")
		f.write(checksums)
		f.close()
		return True
	
# checks ALL files for their rule state. if they are all the same as the current loaded one, the entire database can be assumed to be consistent with the current ruleset
# in any other case, get out
def consistentRulestate(folder,checksums):
	import os
	
	result = []
	for scrobblefile in os.listdir(folder + "/"):
		
		if (scrobblefile.endswith(".tsv")):
		
			try:
				f = open(folder + "/" + scrobblefile + ".rulestate","r")
				if f.read() != checksums:
					return False
			
			except:
				return False
			finally:
				f.close()
	
	return True
	
	
def parseAllTSV(path,*args):
	
	import os
	
	result = []
	for f in os.listdir(path + "/"):
		
		if (".tsv" in f):
			
			result += parseTSV(path + "/" + f,*args)
			
	return result
	
def createTSV(filename):
	import os
	
	if not os.path.exists(filename):
		open(filename,"w").close()

def addEntry(filename,a):

	createTSV(filename)
	
	line = "\t".join(a)
	with open(filename,"a") as f:
		f.write(line + "\n")

def addEntries(filename,al):
	
	with open(filename,"a") as f:
		for a in al:
			line = "\t".join(a)
			f.write(line + "\n")
		
		
### Logging
		
def log(msg):
	print(msg)
	# best function ever	
	

### Media info

def getArtistInfo(artist):
	import re
	import os
	import urllib
	import json
	import _thread
	
	
	filename = re.sub("[^a-zA-Z0-9]","",artist)
	filepath = "info/artists/" + filename
	filepath_cache = "info/artists_cache/" + filename
	
	# check if custom image exists
	if os.path.exists(filepath + ".png"):
		imgurl = "/" + filepath + ".png"
	elif os.path.exists(filepath + ".jpg"):
		imgurl = "/" + filepath + ".jpg"
	elif os.path.exists(filepath + ".jpeg"):
		imgurl = "/" + filepath + ".jpeg"
	
	#check if cached image exists	
	elif os.path.exists(filepath_cache + ".png"):
		imgurl = "/" + filepath_cache + ".png"
	elif os.path.exists(filepath_cache + ".jpg"):
		imgurl = "/" + filepath_cache + ".jpg"
	elif os.path.exists(filepath_cache + ".jpeg"):
		imgurl = "/" + filepath_cache + ".jpeg"
		
		
	# check if custom desc exists
	if os.path.exists(filepath + ".txt"):
		with open(filepath + ".txt","r") as descfile:
			desc = descfile.read().replace("\n","")
	
	#check if cached desc exists	
	elif os.path.exists(filepath_cache + ".txt"):
		with open(filepath_cache + ".txt","r") as descfile:
			desc = descfile.read().replace("\n","")
			
	try:
		return {"image":imgurl,"info":desc}
	except NameError:
		pass
	#is this pythonic?
	
	
	# if we neither have a custom image nor a cached version, we return the address from lastfm, but cache that image for later use	
	with open("apikey","r") as keyfile:
		apikey = keyfile.read().replace("\n","")
	
	
	try:	
		url = "https://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist=" + urllib.parse.quote(artist) + "&api_key=" + apikey + "&format=json"
		response = urllib.request.urlopen(url)
		lastfm_data = json.loads(response.read())
		try:
			imgurl
		except NameError:
			imgurl = lastfm_data["artist"]["image"][2]["#text"]
			if imgurl == "":
				imgurl = "/info/artists/default.jpg"
			else:
				_thread.start_new_thread(cacheImage,(imgurl,"info/artists_cache",filename))
		try:
			desc
		except NameError:
			desc = lastfm_data["artist"]["bio"]["summary"].split("(1) ")[-1]
			with open(filepath_cache + ".txt","w") as descfile:
				descfile.write(desc)
		# this feels so dirty
		
		
		return {"image":imgurl,"info":desc}
	except:
		return {"image":"/info/artists/default.jpg","info":"No information available"}
		
	
	
def cacheImage(url,path,filename):
	import urllib.request
	response = urllib.request.urlopen(url)
	target = path + "/" + filename + "." + response.info().get_content_subtype()	
	urllib.request.urlretrieve(url,target)
	
def artistLink(name):
	import urllib
	return "<a href='/artist?artist=" + urllib.parse.quote(name) + "'>" + name + "</a>"

# necessary because urllib.parse.urlencode doesnt handle multidicts
def keysToUrl(keys):
	import urllib
	st = ""
	for k in removeIdentical(keys):
		values = keys.getall(k)
		st += "&".join([urllib.parse.urlencode({k:v}) for v in values])
		st += "&"
	return st
	
def removeIdentical(keys):
	from bottle import FormsDict
	
	new = FormsDict()
	for k in keys:
		values = set(keys.getall(k))
		for v in values:
			new.append(k,v)
			
	return new
	
def getTimeDesc(timestamp):
	import datetime
	tim = datetime.datetime.utcfromtimestamp(timestamp)
	return tim.strftime("%d. %b %Y %I:%M %p")