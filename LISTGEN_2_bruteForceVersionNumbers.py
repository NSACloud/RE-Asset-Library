#Author: NSA Cloud

#Requires mmh3 library
#pip install mmh3

import mmh3

import os
import sys
import json
from multiprocessing import Pool, cpu_count
from modules.pak.re_pak_utils import scanForPakFiles,createPakCacheFile,readPakCache,concatInt

STRING_DUMP_PATH = r"D:\EXTRACT\SF6_EXTRACT\DUMP\pathStringDump_SF6.txt"

FILE_VERSIONS_OUT_PATH = r"D:\EXTRACT\SF6_EXTRACT\DUMP\fileVersions_SF6.json"

#If there's a generated list of versions for a different game, you can start brute forcing upwards from their versions,making it much quicker
STARTING_FILE_VERSIONS_PATH = r"D:\EXTRACT\SF6_EXTRACT\DUMP\fileVersions_SF6Old.json"

#STARTING_FILE_VERSIONS_PATH = None#Uncomment to not load starting file and start from 0

GAME_DIR = r"J:\SteamLibrary\steamapps\common\Street Fighter 6"

PAK_CACHE_OUT_PATH = r"D:\EXTRACT\SF6_EXTRACT\DUMP\PakCache_SF6.pakcache"

PLATFORM = "STM"

STARTING_SAMPLE_NUM = 1#Increase this to hash using a different file path

MAX_SAMPLES = 5#Test hashes against x amount of file paths in case one of them doesn't exist

negativeVersionFileTypes = set([".lmap"])


#--------------
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
platformExtList = [
	"",
	".x64",
	".STM",
	".MSG",
	".NSW",
	]

#BLOCK_SIZE = 1000000000#Process hashes in batches of x per thread
BLOCK_SIZE = 2000000


#MAX_VALUE = 4294967295
MAX_VALUE = 2147483647#Versions seem to be a signed int
def hashPakPathMMH3Lib(path):
	return concatInt(mmh3.hash(path.lower().encode("utf-16le"),seed=0xFFFFFFFF,signed=False),mmh3.hash(path.upper().encode("utf-16le"),seed=0xFFFFFFFF,signed=False))

def writeJSON(path,knownVersionDict):
	with open(path,"w",encoding="utf-8") as outputFile:
		json.dump(knownVersionDict,outputFile,indent=4, sort_keys=True,
	                      separators=(',', ': '))	


"""
for extension in extensionDict:
	if extension in knownVersionDict and knownVersionDict[extension] == 0:
		print(f"Brute forcing {extension}:")
		currentVersionNum = 0
		
		
		
		rootPath = f"natives/{PLATFORM}/{extensionDict[extension][SAMPLE_NUM]}."
		newPath = f"{rootPath}{currentVersionNum}"
		
		lookupHash = hashPakPathMMH3Lib(newPath)
		while lookupHash not in lookupDict:
			currentVersionNum += 1
			newPath = f"{rootPath}{currentVersionNum}"
			lookupHash = hashPakPathMMH3Lib(newPath)
			if currentVersionNum % 1000000 == 0:
				print(f"Current Version Number {currentVersionNum}")
			#print(newPath)
		print("Found version number for {extension}")
		knownVersionDict[extension] = currentVersionNum
		writeJSON(FILE_VERSIONS_OUT_PATH, knownVersionDict)
		
"""
def bruteForceHash(jobDict):
	jobIndex = jobDict["jobIndex"]
	resultVersion = 0
	
	
	hashSet = jobDict["hashSet"]
	rootPath = jobDict["path"]
	newPath = rootPath+"0"
	#print(jobIndex)
	#print(newPath)
	for i in range(jobDict["startRange"],jobDict["endRange"]):
		newPath = rootPath+str(i)
		if "bnk" not in newPath and "pck" not in newPath:
			lookupHash = hashPakPathMMH3Lib(newPath)
			#lookupHash = hashPakPathMMH3LibPreEncode(lowerPathBytes+str(i).encode("utf-16le"),upperPathBytes+str(i).encode("utf-16le"))
			if lookupHash in hashSet:
				resultVersion = i
				break
		else:
			for platExt in platformExtList:
				for langExt in langExtList:
					newPath = f"{rootPath}{i}{platExt}{langExt}"
					#print(newPath)
					lookupHash = hashPakPathMMH3Lib(newPath)
					if lookupHash in hashSet:
						resultVersion = i
						break
						break
	return resultVersion

def runBruteForceJob():
	global BLOCK_SIZE
	extensionDict = dict()
	#Get 3 samples of every file type
	with open(STRING_DUMP_PATH,"r") as file:
		for line in file.readlines():
			path = line.strip()
			extension = os.path.splitext(path)[1]
			if extension in extensionDict:
				if len(extensionDict[extension]) < MAX_SAMPLES:
					extensionDict[extension].append(path)
			else:
				extensionDict[extension] = [path]
				
	if not os.path.isfile(PAK_CACHE_OUT_PATH):			
		createPakCacheFile(scanForPakFiles(GAME_DIR),PAK_CACHE_OUT_PATH)

	_,lookupDict = readPakCache(PAK_CACHE_OUT_PATH)

	if os.path.isfile(FILE_VERSIONS_OUT_PATH):
		with open(FILE_VERSIONS_OUT_PATH,"r") as jsonFile:	
			knownVersionDict = json.load(jsonFile)
	else:
		knownVersionDict = {extension: 0 for extension in extensionDict}
		writeJSON(FILE_VERSIONS_OUT_PATH, knownVersionDict)
	for extension in extensionDict:
		if extension not in knownVersionDict:
			knownVersionDict[extension] = 0
	writeJSON(FILE_VERSIONS_OUT_PATH, knownVersionDict)
	startingVersionDict = dict()
	if STARTING_FILE_VERSIONS_PATH != None and os.path.isfile(STARTING_FILE_VERSIONS_PATH):
		with open(STARTING_FILE_VERSIONS_PATH,"r") as jsonFile:	
			startingVersionDict = json.load(jsonFile)
			print(f"Loaded starting version dict {STARTING_FILE_VERSIONS_PATH}")
	
	hashSet = set(lookupDict.keys())
	for extension in extensionDict:
		if extension in knownVersionDict and knownVersionDict[extension] == 0:
			hashFound = False
			for sample in extensionDict[extension][STARTING_SAMPLE_NUM::]:
				print(f"Brute forcing {extension}:")
				if extension in startingVersionDict:
					currentVersionNum = startingVersionDict[extension]
					print(f"Starting at {currentVersionNum}")
				else:
					currentVersionNum = 0
				
				hashFound = False
				startRange = currentVersionNum
				isNegative = extension in negativeVersionFileTypes
				if isNegative:
					print("Negative version number file type")
				if isNegative and BLOCK_SIZE > 0:
					BLOCK_SIZE *= -1
				elif not isNegative and BLOCK_SIZE < 0:
					BLOCK_SIZE *= -1
				
				#basePath = f"natives/{PLATFORM}/{extensionDict[extension][SAMPLE_NUM]}."
				basePath = f"natives/{PLATFORM}/{sample}."
				print(basePath)
				while not hashFound:
					if abs(startRange) > abs(MAX_VALUE):
						break
					jobList = []
					
					
					print(f"{extension} Current Range {startRange} - {startRange + (BLOCK_SIZE * cpu_count())}")
					for i in range(cpu_count()):
						
						
						endRange = startRange + BLOCK_SIZE
						jobEntry = {
							"jobIndex":i,
							"startRange":startRange,
							"endRange":endRange,
							"path":basePath,
							"hashSet":hashSet,
							}
						jobList.append(jobEntry)
						startRange = endRange
					jobCount = len(jobList)	
					
					with Pool(processes=cpu_count()) as pool:
						#print(jobJSONDict["jobList"])
						results = pool.imap_unordered(func=bruteForceHash, iterable = jobList,chunksize = 1)
						for i, results in enumerate(results):
							sys.stdout.write(f"(Finished {i+1} of {jobCount})\n")
							sys.stdout.flush()
							if results != 0:
								hashFound = True
								currentVersionNum = results
								knownVersionDict[extension] = currentVersionNum
								writeJSON(FILE_VERSIONS_OUT_PATH, knownVersionDict)
								print(f"Found {extension} version {results}")
								break
								
				if hashFound:
					break
			if not hashFound:
				print(f"Skipped {extension} because it's version could not be found")				
						
		
	
	print("Done")
if __name__ == '__main__':
	print("Process started.")
	
	runBruteForceJob()