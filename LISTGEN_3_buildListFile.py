#Author: NSA Cloud

#Requires mmh3 library
#pip install mmh3

import mmh3

import os
import sys
import json
from multiprocessing import Pool, cpu_count
from modules.pak.re_pak_utils import readPakCache,concatInt

STRING_DUMP_PATH = r"D:\EXTRACT\SF6_EXTRACT\DUMP\pathStringDump_SF6.txt"

FILE_VERSIONS_PATH = r"D:\EXTRACT\SF6_EXTRACT\DUMP\fileVersions_SF6.json"

PAK_CACHE_PATH = r"D:\EXTRACT\SF6_EXTRACT\DUMP\PakCache_SF6.pakcache"

PLATFORM = "STM"

LIST_OUT_PATH = r"D:\EXTRACT\SF6_EXTRACT\DUMP\SF6_Pak_Release.list"



#--------------------

langExtList = [
"",
".ja",
".en",
".fr",
".it",
".de",
".es",
".ru",
".pl",
".nl",
".pt",
".ptbr",
".ko",
".zhtw",
".zhcn",
".fi",
".sv",
".da",
".no",
".cs",
".hu",
".sk",
".ar",
".tr",
".bg",
".el",
".ro",
".th",
".ua",
".vi",
".id",
".fc",
".hi",
".es419",
]
platformExtList = {
	"",
	".x64",
	".STM",
	".MSG",
	".NSW",
	}

outputPathSet = set()

def hashPakPathMMH3Lib(path):
	return concatInt(mmh3.hash(path.lower().encode("utf-16le"),seed=0xFFFFFFFF,signed=False),mmh3.hash(path.upper().encode("utf-16le"),seed=0xFFFFFFFF,signed=False))
 
 
pakPathList, lookupDict = readPakCache(PAK_CACHE_PATH)

missedPathSet = set()

with open(FILE_VERSIONS_PATH,"r",encoding = "utf-8") as verFile:
	fileVersionDict = json.load(verFile)

print("Processing paths...")
with open(STRING_DUMP_PATH,"r",encoding = "utf-8") as dumpFile:
	for line in dumpFile:
		
		path = line.strip().replace("@","")
		try:
			fileExtension = fileVersionDict[os.path.splitext(line)[1].strip()]
		except:
			fileExtension = 0
			print(f"Unknown extension on path {path}")
		nativesPath = f"natives/{PLATFORM}/{path}.{fileExtension}"
		foundHash = False
		lookupHash = hashPakPathMMH3Lib(nativesPath)
		if lookupHash in lookupDict:
			foundHash = True
			outputPathSet.add(nativesPath)
		else:
			for platExt in platformExtList:
				for langExt in langExtList:
					newPath = f"{nativesPath}{platExt}{langExt}"
					lookupHash = hashPakPathMMH3Lib(newPath)
					if lookupHash in lookupDict:
						foundHash = True
						outputPathSet.add(newPath)
		if not foundHash:
			missedPathSet.add(path)
			
		streamingPath = f"natives/{PLATFORM}/streaming/{path}.{fileExtension}"
		foundHash = False
		lookupHash = hashPakPathMMH3Lib(streamingPath)
		if lookupHash in lookupDict:
			foundHash = True
			outputPathSet.add(streamingPath)
		else:
			for platExt in platformExtList:
				for langExt in langExtList:
					newPath = f"{streamingPath}{platExt}{langExt}"
					lookupHash = hashPakPathMMH3Lib(newPath)
					if lookupHash in lookupDict:
						outputPathSet.add(newPath)
with open(LIST_OUT_PATH,"w",encoding="utf-8") as outFile:
	for entry in sorted(list(outputPathSet)):
		outFile.write(entry+"\n")
	print(f"Saved {LIST_OUT_PATH}")
	
print("Missed paths:")
for path in sorted(list(missedPathSet)):
	print(path)