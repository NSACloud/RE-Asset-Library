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
