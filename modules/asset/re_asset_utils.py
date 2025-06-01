#Author: NSA Cloud
from zlib import crc32
import os
import csv
import json
from ..mdf.file_re_mdf import readMDF
from ..hashing.mmh3.pymmh3 import hashUTF8
#TODO move more functions from operators file into here


def loadGameInfo(gameInfoPath):
	GAMEINFO_VERSION = 1
	try:
		with open(gameInfoPath,"r", encoding ="utf-8") as file:
			gameInfo = json.load(file)
	except:
		raise Exception(f"Failed to load {gameInfoPath}")
		
	if gameInfo["GameInfoVersion"] > GAMEINFO_VERSION:
		raise Exception("GameInfo version is newer than the currently installed version.\nUpdate the RE-Asset-Library addon from the addon preferences.")
	return gameInfo

def getFileCRC(filePath):
	size = 1024*1024*10  # 10 MiB chunks
	with open(filePath, 'rb') as f:
	    crcval = 0
	    while chunk := f.read(size):
	        crcval = crc32(chunk, crcval)
	return crcval

def buildNativesPathFromCatalogEntry(row,fileVersion,platform):
	return os.path.join("natives",platform,f"{row[0]}.{fileVersion}"+(f".{row[4]}".replace("STM",platform) if row[4] != "" else "")+(f".{row[5]}" if row[5] != "" else "")).replace(os.sep,"/")

def buildNativesPathFromObj(obj,gameInfo,platform):
	assetPath = obj.get("assetPath","UNKN_ASSET_PATH.file.1")
	fileVersion = gameInfo["fileVersionDict"].get(obj.get("assetType","UNKN")+"_VERSION","999")
	platExt = obj.get("platExt","")
	langExt = obj.get("langExt","")
	return os.path.join("natives",platform,f"{assetPath}.{fileVersion}"+(f".{platExt}".replace("STM",platform) if platExt != "" else "")+(f".{langExt}" if langExt != "" else "")).replace(os.sep,"/")

def loadREAssetCatalogFile(tsvPath,fileTypeWhiteListSet = set()):
	assetEntryList = []
	with open(tsvPath,encoding = "utf-8") as fd:
		try:
			gameName = tsvPath.split("Catalog_")[1].split("_")[0]
		except:
			raise Exception(f"Invalid catalog name, cannot load: {os.path.split(tsvPath)[1]}")
		rd = csv.reader(fd, delimiter="\t", quotechar='"')
		next(rd)#Skip header
		
		
		loadAll = len(fileTypeWhiteListSet) == 0
		 
		for row in rd:
			
			#Check if file extension is in the whitelist
			if loadAll or os.path.splitext(row[0])[1][1:].lower() in fileTypeWhiteListSet:
				assetEntryList.append(row)
	return assetEntryList

def catalogGetAllFilesInDir(catalogPath,dirPath,gameInfo,platform = "STM"):
	filePathSet = set()
	with open(catalogPath,"r") as file:
		reader = csv.reader(file, delimiter="\t", quotechar='"')
		for row in reader:
			if row[0].startswith(dirPath):
				ext = os.path.splitext(row[0])[1]
				fileVersion = gameInfo["fileVersionDict"].get(f"{ext[1::].upper()}_VERSION","999999")
				filePathSet.add(buildNativesPathFromCatalogEntry(row,fileVersion,platform))
					
	return filePathSet

def generateMaterialCompendium(libraryDir,gameName):
	gameInfoPath = os.path.join(libraryDir,f"GameInfo_{gameName}.json")
	catalogPath = os.path.join(libraryDir,f"REAssetCatalog_{gameName}.tsv")
	extractInfoPath = os.path.join(libraryDir,f"ExtractInfo_{gameName}.json")
	compendiumOutPath = os.path.join(libraryDir,f"MaterialCompendium_{gameName}.json")
	if os.path.isfile(gameInfoPath):
		gameInfo = loadGameInfo(gameInfoPath)
		assetEntryList = loadREAssetCatalogFile(catalogPath)
		extractPath = None
		with open(extractInfoPath,"r", encoding ="utf-8") as file:
			extractInfo = json.load(file)
			extractPath = extractInfo["extractPath"].replace("/",os.sep)
		mdfFileList = [entry[0]+"."+gameInfo["fileVersionDict"]["MDF2_VERSION"] for entry in assetEntryList if entry[0].endswith(".mdf2")]
		print(f"Processing {len(mdfFileList)} MDF files")
		
		mmtrUsageDict = {}
		for path in mdfFileList:
			
			fullPath = os.path.join(extractPath,"natives","STM",path.replace("/",os.sep))
			#print(fullPath)
			if os.path.isfile(fullPath):
				try:
					mdfFile = readMDF(fullPath)
				
					for material in mdfFile.materialList:
						mmtrLowerPathHash = hashUTF8(material.mmtrPath.lower())
						if mmtrLowerPathHash not in mmtrUsageDict:
							mmtrUsageDict[mmtrLowerPathHash] = {"name":os.path.splitext(os.path.split(material.mmtrPath)[1])[0],"mdfPath":path,"matNameHash":material.matNameHash}
				except Exception as err:
					print(f"Failed to read ({fullPath}:{str(err)})")
		sortedDict = {k: v for k, v in sorted(mmtrUsageDict.items(), key=lambda item: item[1]["name"])}
		with open(compendiumOutPath,"w", encoding ="utf-8") as outFile:
			json.dump(sortedDict,outFile,sort_keys=False,indent=4)
			print(f"Wrote {os.path.split(compendiumOutPath)[1]}")
		print(f"{len(sortedDict)} shader entries written")	
		#print(mdfFileList)