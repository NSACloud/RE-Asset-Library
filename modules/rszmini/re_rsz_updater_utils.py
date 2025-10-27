#Author: NSA Cloud
import os
import json
from io import BytesIO
from ..gen_functions import raiseWarning
from ..hashing.mmh3.pymmh3 import hashUTF8
from ..gen_functions import progressBar
from ..rszmini.re_rsz_utils import getRSZInstanceTypeIDs,getRSZCRCs,ReadRSZAutoDetectType,WriteRSZFile
from ..pak.re_pak_utils import PakCacheStream
from ..asset.re_asset_utils import loadGameInfo,loadREAssetCatalogFile
from shutil import copyfile


def generateRSZCRCCompendium(libraryDir,gameName):
	gameInfoPath = os.path.join(libraryDir,f"GameInfo_{gameName}.json")
	catalogPath = os.path.join(libraryDir,f"REAssetCatalog_{gameName}.tsv")
	extractInfoPath = os.path.join(libraryDir,f"ExtractInfo_{gameName}.json")
	compendiumOutPath = os.path.join(libraryDir,f"CRCCompendium_{gameName}.json")
	if os.path.isfile(gameInfoPath):
		gameInfo = loadGameInfo(gameInfoPath)
		assetEntryList = loadREAssetCatalogFile(catalogPath)
		extractPath = None
		with open(extractInfoPath,"r", encoding ="utf-8") as file:
			extractInfo = json.load(file)
			
		pakStream = PakCacheStream(libraryDir,gameName)
		rszFileTypes = {"user","pfb","scn"}
		rszFileList = [entry[0]+"."+gameInfo["fileVersionDict"][entry[0].split(".")[1].upper()+"_VERSION"] for entry in assetEntryList if entry[0].split(".")[1] in rszFileTypes]
		
		print(f"Processing {len(rszFileList)} RSZ files")
		
		typeIDDict = {}
		addedTypesSet = set()
		
		for path in progressBar(rszFileList, prefix = 'Progress:', suffix = 'Complete', length = 50):
			fullPath = os.path.join("natives",extractInfo["platform"],path)
			fileData = pakStream.retrieveFileData(fullPath)
			if fileData != None:
				try:
					with BytesIO(fileData) as file:
						newTypes = getRSZInstanceTypeIDs(file).difference(addedTypesSet)
						
						addedTypesSet.update(newTypes)
						for typeHash in newTypes:
							typeIDDict[typeHash] = path
						#print(len(addedTypesSet))
				except Exception as err:
					print(f"Failed to read ({path}:{str(err)})")
		sortedDict = {k: v for k, v in sorted(typeIDDict.items(), key=lambda item: item[0])}
		with open(compendiumOutPath,"w", encoding ="utf-8") as outFile:
			json.dump(sortedDict,outFile,sort_keys=False,indent=4)
			print(f"Wrote {os.path.split(compendiumOutPath)[1]}")
		print(f"{len(sortedDict)} CRC entries written")
		pakStream.closeStreams()
		del pakStream

def makeRSZBackup(rszPath):
	bakIndex = 0
	bakPath = f"{rszPath}.bak{bakIndex}"
	if os.path.isfile(rszPath):
		while(os.path.isfile(bakPath)):
			bakIndex += 1
			bakPath = f"{rszPath}.bak{bakIndex}"
		try:
			copyfile(rszPath,bakPath)
		except Exception as err:
			print(f"Failed to create backup of {rszPath} - {str(err)}")

def batchUpdateRSZFiles(modDirectory,libraryDir,gameName,searchSubdirectories,createBackups):
	print(f"Updating RSZ files in: {modDirectory}")
	rszList = []
	for root, dirs, files in os.walk(modDirectory):
		for fileName in files:
			if ".user." in fileName.lower() or ".pfb." in fileName.lower() or ".scn." in fileName.lower() and ".bak" not in fileName:#not fileName.endswith(".bak"):
				rszList.append(os.path.join(root,fileName))
		
		if not searchSubdirectories:
			break
	
	gameInfoPath = os.path.join(libraryDir,f"GameInfo_{gameName}.json")
	catalogPath = os.path.join(libraryDir,f"REAssetCatalog_{gameName}.tsv")
	extractInfoPath = os.path.join(libraryDir,f"ExtractInfo_{gameName}.json")
	compendiumPath = os.path.join(libraryDir,f"CRCCompendium_{gameName}.json")
	if os.path.isfile(compendiumPath):
		with open(compendiumPath,"r", encoding ="utf-8") as file:
			crcCompendium = json.load(file)
	else:
		raise Exception(f"CRC Compendium for {gameName} not found.")
	if os.path.isfile(gameInfoPath):
		
		gameInfo = loadGameInfo(gameInfoPath)
		assetEntryList = loadREAssetCatalogFile(catalogPath)
		extractPath = None
		with open(extractInfoPath,"r", encoding ="utf-8") as file:
			extractInfo = json.load(file)
			
		pakStream = PakCacheStream(libraryDir,gameName)
		
		rszFileTypes = {".user.",".pfb.",".scn."}
		rszFileList = []
		for root, dirs, files in os.walk(modDirectory):
			for fileName in files:
				if any(fileType in fileName for fileType in rszFileTypes) and ".bak" not in fileName:#not fileName.endswith(".bak"):
					rszFileList.append(os.path.join(root,fileName))
					#print(f"Added {fileName}")
			
			if not searchSubdirectories:
				break
		
		print(f"Prechecking {len(rszFileList)} file(s)...")
		usedTypeIDSet = set()
		for path in rszFileList:
			#print(path)
			with open(path,"rb") as file:
				usedTypeIDSet.update(getRSZInstanceTypeIDs(file))
		
		
		typeIDDict = {}
		addedTypesSet = set()
		print(f"Retrieving latest CRCs from {len(usedTypeIDSet)} files...")
		if len(usedTypeIDSet) > 0:
			for requiredTypeID in progressBar(usedTypeIDSet, prefix = 'Progress:', suffix = 'Complete', length = 50):
				if requiredTypeID not in typeIDDict:
					filePath = crcCompendium.get(str(requiredTypeID),"MISSING_TYPE_ID")
					#print(filePath)
					fullPath = os.path.join("natives",extractInfo["platform"],filePath)
					fileData = pakStream.retrieveFileData(fullPath)
					if fileData != None:
						try:
							with BytesIO(fileData) as file:
								crcDict = getRSZCRCs(file)
								#print(len(addedTypesSet))
						except Exception as err:
							crcDict = dict()
							print(f"Failed to read ({path}:{str(err)})")
						newTypes = set(crcDict.keys()).difference(addedTypesSet)
						
						addedTypesSet.update(newTypes)
						for typeHash in newTypes:
							typeIDDict[typeHash] = crcDict[typeHash]
	
	pakStream.closeStreams()
	del pakStream
	#print(typeIDDict)
	
	missingTypeIDs = usedTypeIDSet.difference(addedTypesSet)
	if len(missingTypeIDs) != 0:
		raiseWarning(f"{len(missingTypeIDs)} Type IDs are missing from the compendium.\n{str(missingTypeIDs)}")
	print(f"Processing {len(rszFileList)} RSZ file(s)")
	mmtrMaterialCache = dict()
	
	updatedFileCount = 0
	
	for path in rszFileList:
		print(f"Checking {path}")
		requiresUpdate = False
		try:
			with open(path,"rb") as file:
				rszFile = ReadRSZAutoDetectType(file)
				if rszFile.Header.magic == 5919570:#Check if it's embedded RSZ:
					instanceInfoList = rszFile.InstanceInfoList
				else:
					instanceInfoList = rszFile.rsz.InstanceInfoList
				for index, instanceInfo in enumerate(instanceInfoList):
					if instanceInfo.typeIDHash in typeIDDict:
						if typeIDDict[instanceInfo.typeIDHash] != instanceInfo.CRC:
							requiresUpdate = True
							print(f"Updated CRC for Instance {index}, ID: {instanceInfo.typeIDHash}")
							instanceInfo.CRC = typeIDDict[instanceInfo.typeIDHash]
				if requiresUpdate:
					if createBackups:
						makeRSZBackup(path)
					WriteRSZFile(rszFile, path)
					updatedFileCount += 1
					print("Update completed.")
				else:
					print("No update required.")
					
							#print(samplePath)
				#print(mdfPath)
		except Exception as err:
			print(f"Failed to read {path}: {str(err)}")
	return updatedFileCount