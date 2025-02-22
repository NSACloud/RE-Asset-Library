#Author: NSA Cloud

#Requires mmh3 library
#pip install mmh3

import mmh3

import os
from modules.pak.re_pak_utils import readPakCache,concatInt

PAK_CACHE_PATH = r"D:\EXTRACT\SF6_EXTRACT\DUMP\PakCache_SF6.pakcache"

PLATFORM = "STM"
MERGE_LISTS_DIR = r"D:\EXTRACT\SF6_EXTRACT\DUMP\mergeLists"

LIST_OUT_NAME = r"SF6_Pak_Release.list"



#--------------------
listOutPath = os.path.join(MERGE_LISTS_DIR,"output",LIST_OUT_NAME)
os.makedirs(os.path.split(listOutPath)[0],exist_ok=True)
outputPathSet = set()

def hashPakPathMMH3Lib(path):
	return concatInt(mmh3.hash(path.lower().encode("utf-16le"),seed=0xFFFFFFFF,signed=False),mmh3.hash(path.upper().encode("utf-16le"),seed=0xFFFFFFFF,signed=False))
 
 
pakPathList, lookupDict = readPakCache(PAK_CACHE_PATH)


addedPathSet = set()
print("Processing lists...")
for entry in os.scandir(MERGE_LISTS_DIR):
	if entry.is_file() and entry.name.endswith(".list"):
		with open(os.path.join(MERGE_LISTS_DIR,entry.name),"r",encoding = "utf-8") as dumpFile:
			print(f"Reading {os.path.join(MERGE_LISTS_DIR,entry.name)}")
			for line in dumpFile:
				path = line.strip().replace("@","")
				lookupHash = hashPakPathMMH3Lib(path)
				
				if path not in addedPathSet and lookupHash in lookupDict:
					outputPathSet.add(path)
					addedPathSet.add(path)
					addedPathSet.add(path.lower())

print(listOutPath)		
with open(listOutPath,"w",encoding="utf-8") as outFile:
	for entry in sorted(list(outputPathSet)):
		outFile.write(entry+"\n")
	print(f"Saved {listOutPath}")
	