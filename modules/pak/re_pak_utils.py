#Author: NSA Cloud
import os
from math import log,pow
import zstandard as zstd
import zlib
import time
import json
import sys
from multiprocessing import cpu_count
import subprocess
from io import BytesIO
import struct
timeFormat = "%d"


from ..gen_functions import progressBar,formatByteSize,read_ubyte,read_ushort,read_uint,read_uint64,write_ubyte,write_ushort,write_uint,write_uint64

from .file_re_pak import ReadPakTOC,PakFile,PakTOCEntry,writePak
from ..hashing.mmh3.pymmh3 import hashUTF16#TODO Replace with pypi mmh3 library, orders of magnitude faster
from ..hashing.mmh3.fastmmh3 import FastMMH3
from ..encryption.re_pak_encryption import decryptResource
from ..asset.re_asset_utils import loadGameInfo,getFileCRC,buildNativesPathFromObj,loadREAssetCatalogFile,buildNativesPathFromCatalogEntry
from ..rszmini.re_rsz_utils import getRSZResourcePaths
from ..mdf.file_re_mdf import MDFFile

STREAMING_FILE_TYPE_SET = frozenset([".mesh",".abcmesh",".stmesh",".tex",".sbnk",".bnk",".pck",".spck",".vsrc",".mov",".mpci"])

class CompressionTypes:
	COMPRESSION_TYPE_NONE = 0
	COMPRESSION_TYPE_DEFLATE = 1
	COMPRESSION_TYPE_ZSTD = 2

def concatInt(a, b):#Combines two uint values into a uint64 for hash lookups
	return (a << 32) | b

def getPakLookupTable(pakPath):
	return {concatInt(entry.hashNameLower,entry.hashNameUpper) : entry for entry in ReadPakTOC(pakPath)}


def pathToPakHash(path):
	path = path.replace(os.sep,"/").replace("\\","/")
	return concatInt(hashUTF16(path.lower()),hashUTF16(path.upper()))

def pathToPakHashFast(hasher,path):
	path = path.replace(os.sep,"/").replace("\\","/")#The overhead on this replace is about 400 ms total when hashing the wilds list
	return hasher.pakHash(path)

def readListFileSet(listPath):
	outPathSet = set()
	lowerPathSet = set()
	with open(listPath,"r",encoding = "utf-8") as file:
		for line in file.readlines():
			if "natives" in line:
				outPath = "natives" + line.strip().split("natives")[1]
				
				lowerOutPath = outPath.lower()
				
				#Prefer properly cased paths over lower cased paths if they exist
				if outPath != lowerOutPath:
					lowerPathSet.add(lowerOutPath)
					if lowerOutPath in outPathSet:
						outPathSet.remove(lowerOutPath)
					outPathSet.add(outPath)
				else:
					#If path is lower cased and an upper cased one hasn't been added yet, add it to list
					if lowerOutPath not in lowerPathSet:
						outPathSet.add(lowerOutPath)
						lowerPathSet.add(lowerOutPath)
					
	return outPathSet

def isModPak(pakPath):
	result = False
	if os.path.isfile(pakPath):
		with open(pakPath,"rb") as file:
			pakFile = PakFile()
			pakFile.header.read(file)
			result = pakFile.header.majorVersion == 4 and (pakFile.header.minorVersion == 0 or pakFile.header.minorVersion == 1) and pakFile.header.feature == 0 and pakFile.header.fingerprint == 0 and "sub_000.pak" in pakPath
	return result
def isEmptyPak(pakPath):#RE RT updates remove old patch paks and replace them with nulled files, causing errors
	return os.path.getsize(pakPath) == 0
def scanForPakFiles(gameDir):
	#Returns list of pak files in load order (Base Chunk > Patch Files > DLC)
	lowPriorityList = []
	midPriorityList = []
	highPriorityList = []
	
	
	for entry in os.scandir(gameDir):
		if entry.is_file() and entry.name.endswith(".pak"):
			fullPath = os.path.join(gameDir,entry.name)
			if "patch_" in entry.name:
				if not isEmptyPak(fullPath) and not isModPak(fullPath):
					midPriorityList.append(fullPath)
			else:
				if not isEmptyPak(fullPath) and not isModPak(fullPath):
					lowPriorityList.append(fullPath)
		elif entry.is_dir():
			#Scan first level of subdirectories for dlc paks
			dirPath = os.path.join(gameDir,entry)
			for subentry in os.scandir(dirPath):
				if subentry.is_file() and subentry.name.endswith(".pak"):
					fullPath = os.path.join(dirPath,subentry.name)
					if "re_dlc" in subentry.name:
						if not isEmptyPak(fullPath) and not isModPak(fullPath):
							highPriorityList.append(fullPath)
						
	pakPriorityList = []

	lowPriorityList.sort()
	midPriorityList.sort()
	highPriorityList.sort()

	#pakPriorityList.extend(highPriorityList)
	#pakPriorityList.extend(midPriorityList)
	#pakPriorityList.extend(lowPriorityList)
	
	pakPriorityList.extend(lowPriorityList)
	pakPriorityList.extend(midPriorityList)
	pakPriorityList.extend(highPriorityList)
	
	
	return pakPriorityList
PAK_CACHE_VERSION = 1	

def writeExtractInfo(extractInfoDict,outPath):#Used to determine if the game has been updated and paks need to be rescanned
	with open(outPath,"w") as outputFile:
		json.dump(extractInfoDict,outputFile,indent=4, sort_keys=False,
	                      separators=(',', ': '))
	print(f"Saved {os.path.split(outPath)[1]}")

def findPakMDFPathFromMeshPath(meshPath,lookupDict,mdfVersion,gameName = None):
	#TODO fix this to be less of a mess
	#Should use regex to do this
	split = meshPath.split(".mesh")
	fileRoot = split[0]
	mdfPath = f"{fileRoot}.mdf2.{mdfVersion}"
	lookupHash = pathToPakHash(mdfPath)
	if not lookupHash in lookupDict:
		mdfPath = f"{fileRoot}_Mat.mdf2.{mdfVersion}"
		lookupHash = pathToPakHash(mdfPath)
	if not lookupHash in lookupDict:
		mdfPath = f"{fileRoot}_v00.mdf2.{mdfVersion}"
		lookupHash = pathToPakHash(mdfPath)
	if not lookupHash in lookupDict:
		mdfPath = f"{fileRoot}_A.mdf2.{mdfVersion}"
		lookupHash = pathToPakHash(mdfPath)
	if not lookupHash in lookupDict and fileRoot.endswith("_f"):
		
		mdfPath = f"{fileRoot[:-1] + 'm'}.mdf2.{mdfVersion}"#DD2 female armor uses male mdf, so replace _f with _m
	
	if not lookupHash in lookupDict and os.path.split(fileRoot)[1].startswith("SM_"):
		split = os.path.split(fileRoot)
		mdfPath = f"{os.path.join(split[0],split[1][1::])}.mdf2.{mdfVersion}"#DR Stage meshes, SM_ to M_
		
	if not lookupHash in lookupDict and "wcs" in fileRoot:#SF6 world tour models
		split = os.path.split(fileRoot)
		mdfPath = os.path.join(split[0],"00",split[1]+f"_00_v00.mdf2.{mdfVersion}")
	
	
	try:
		if not lookupHash in lookupDict and gameName != None:
			split = os.path.split(meshPath)
			rootPath = split[0]
			fileName = split[1].split(".mesh")[0].lower()
			if gameName == "MHWILDS":
				mdfPath = os.path.join(rootPath,f"{fileName}_A.mdf2.{mdfVersion}")	
				
				if not lookupHash in lookupDict and fileName.startswith("ch"):
					dirSplit = rootPath.split("Character",1)
					
					if fileName.count("_") == 2 and len(dirSplit) == 2:#Some models use materials from other gender
						isMale = "_000_" in fileName
						
						if isMale:
							newDir = dirSplit[1].replace("000","001",1)
							newFileName = fileName.replace("_000_", "_001_")
						else:
							newDir = dirSplit[1].replace("001","000",1)
							newFileName = fileName.replace("_001_", "_000_")
						mdfPath = os.path.join(dirSplit[0]+"Character"+newDir,f"{newFileName}.mdf2.{mdfVersion}")
				if not lookupHash in lookupDict and fileName.startswith("mesh_") and "ui_mesh" in rootPath and fileName.count("_") == 3:
					#Minimap textures
					split = fileName.split("_")
					stageID = split[1]
					section = split[3]
					newDir = os.path.join(os.path.dirname(rootPath),f"{stageID}_a00").replace("ui_mesh","ui_material",1)
					newFileName = f"mat_{stageID}_{section}.mdf2.{mdfVersion}"
					mdfPath = os.path.join(newDir,newFileName)
					if not lookupHash in lookupDict:
						newFileName = f"mat_{stageID}_00.mdf2.{mdfVersion}"
						mdfPath = os.path.join(newDir,newFileName)
	except:
		pass
	if lookupHash not in lookupDict:
		print(f"Could not find {mdfPath}.")
		mdfPath = None
			
	return mdfPath

def getMDFReferences(mdfFile):
	fileSet = set()
	#Get all texture paths and file references from an MDF file
	for material in mdfFile.materialList:
		fileSet.add(material.mmtrPath)
		for texture in material.textureList:
			fileSet.add(texture.texturePath)
		for path in material.gpbfBufferPathList:
			fileSet.add(path.name)
		
	return fileSet
def createPakCacheFile(pakPriorityList,outPath):

	lookupDict = {}
	print("Creating new pak cache file...")
	for index,pakPath in enumerate(pakPriorityList):
		print(f"Scanning {pakPath}...")
		for entry in ReadPakTOC(pakPath):
			lookupHash = concatInt(entry.hashNameLower,entry.hashNameUpper)
			if lookupHash not in lookupDict:
				lookupDict[lookupHash] = {
					"offset":entry.offset,
					"compressedSize":entry.compressedSize,
					"compressionType":entry.compressionType,
					"encryptionType":entry.encryptionType,
					"pakIndex":index,
					}
	
	stringBuffer = bytearray()
	with open(outPath,"wb") as outFile:
		write_uint(outFile,PAK_CACHE_VERSION)
		write_uint(outFile,len(lookupDict))#entryCount
		write_ushort(outFile,len(pakPriorityList))#pakCount
		write_uint(outFile,0)#reserved
		write_uint64(outFile,int(time.time()))#time_t timestamp
		for pakPath in pakPriorityList:
			encodedString = pakPath.encode("utf-16le")
			write_uint(outFile,len(encodedString))
			outFile.write(encodedString)
		for key,value in lookupDict.items():
			write_uint64(outFile,key)
			write_uint64(outFile,value["offset"])
			write_uint64(outFile,value["compressedSize"])
			write_ubyte(outFile,value["compressionType"])
			write_ubyte(outFile,value["encryptionType"])
			write_ushort(outFile,value["pakIndex"])
		print(f"Saved {len(lookupDict)} entries.")
	print(f"Saved pak cache to {outPath}")



def readPakCache(pakCachePath):
	importTimeStart = time.time()
	with open(pakCachePath,"rb") as file:
		version = read_uint(file)
		if version > PAK_CACHE_VERSION:
			raise Exception("Pak cache was generated in a newer version, an update is required")
		
		entryCount = read_uint(file)
		#print(entryCount)
		pakCount = read_ushort(file)
		file.seek(12,1)
		#reserved = read_uint(file)
		#timestamp = read_uint(file)
		pakPathList = []
		for _ in range(0,pakCount):
			stringLength = read_uint(file)
			pakPathList.append(file.read(stringLength).decode("utf-16le"))
		
		#lookupDict = {}
		#print(file.tell())
		#print("entry Offset")
		
		#Old version
		"""
		for _ in range(0,entryCount):
			#print(file.tell())
			lookupHash = read_uint64(file)
			lookupDict[lookupHash] = {
				"offset":read_uint64(file),
				"compressedSize":read_uint64(file),
				"compressionType":read_ubyte(file),
				"encryptionType":read_ubyte(file),
				"pakIndex":read_ushort(file),
				}
		"""
		#About 4x faster
		entryStruct = struct.Struct("<QQQBBH")
		lookupDict = {
		    lookupHash: {
		        "offset": offset,
		        "compressedSize": compressedSize,
		        "compressionType": compressionType,
		        "encryptionType": encryptionType,
		        "pakIndex": pakIndex,
		    } for lookupHash, offset, compressedSize, compressionType, encryptionType, pakIndex in entryStruct.iter_unpack(file.read())
		}
		importTimeEnd = time.time()
		importTime =  importTimeEnd - importTimeStart
		print(f"Loaded {entryCount} entries.")
		print(f"Pak cache loaded in {timeFormat%(importTime * 1000)} ms.")
		return pakPathList,lookupDict
def getStreamingPath(filePath,platform,lookupDict):
	streamingPath = filePath.replace(f"natives/{platform}/",f"natives/{platform}/streaming/")
	lookupHash = pathToPakHash(streamingPath)
	if lookupHash not in lookupDict:
		streamingPath = None
	return streamingPath
def extractFilesFromPakCache(gameInfoPath,filePathList,extractInfoPath,pakCachePath,extractDependencies = True,blenderAssetObj = None):
	extractInfo = None
	try:
		with open(extractInfoPath,"r", encoding ="utf-8") as file:
			#extractInfoDict["exePath"] = exePath
			#extractInfoDict["exeDate"] = os.path.getmtime(exePath)
			#extractInfoDict["exeCRC"] = getFileCRC(exePath)
			#extractInfoDict["extractPath"] = newDirPath
			extractInfo = json.load(file)
			
	except:
		print(f"Failed to load {extractInfoPath}")
	gameInfo = loadGameInfo(gameInfoPath)
	
	
	if extractInfo != None:
		
		
		extractDir = extractInfo["extractPath"]
		exePath = extractInfo["exePath"]
		platform = extractInfo["platform"]
		if not os.path.isfile(exePath):
			raise Exception("EXE path is invalid")
		modifiedTime = os.path.getmtime(exePath)
		lastModifiedTime = extractInfo["exeDate"]
		
		if not os.path.isfile(pakCachePath):
			pakPriorityList = scanForPakFiles(os.path.split(exePath)[0])
			if len(pakPriorityList) != 0:
				pakPriorityList.reverse()#Reverse the list so that the newest paths are cached first
				createPakCacheFile(pakPriorityList,pakCachePath)
		
		if modifiedTime > lastModifiedTime:
			#Check CRC to verify it changed
			exeCRC = getFileCRC(exePath)
			if exeCRC != extractInfo["exeCRC"]:
				extractInfo["exeDate"] = modifiedTime
				extractInfo["exeCRC"] = exeCRC
				
				print("Game updated. Regenerating pak cache.")
				pakPriorityList = scanForPakFiles(os.path.split(exePath)[0])
				if len(pakPriorityList) != 0:
					pakPriorityList.reverse()#Reverse the list so that the newest paths are cached first
					createPakCacheFile(pakPriorityList,pakCachePath)
					with open(extractInfoPath,"w", encoding ="utf-8") as outFile:
						json.dump(extractInfo,outFile)
						print(f"Wrote {os.path.split(extractInfoPath)[1]}")

				else:
					raise Exception("No pak files were found in game directory. Cannot continue.")
		
		pakPathList,lookupDict = readPakCache(pakCachePath)
		
		pakExtractionList = [[] for x in range(len(pakPathList))]
		extractedFileSet = set()
		dependencySet = set()#Files referenced in extracted files
		adjacentFilesSet = set()
		if blenderAssetObj != None:#For imported asset library objects, can't get path before this because the platform is needed
			filePathList.append(buildNativesPathFromObj(blenderAssetObj,gameInfo,platform))
			print(f"Blender Asset Path: {buildNativesPathFromObj(blenderAssetObj,gameInfo,platform)}")
			if blenderAssetObj.get("assetType") == "MESH":
				#Find related MDF path by generating alternate MDF names and checking it's hash
				mdfPath = findPakMDFPathFromMeshPath(filePathList[-1], lookupDict, gameInfo["fileVersionDict"].get("MDF2_VERSION",999))
				if mdfPath != None and mdfPath not in adjacentFilesSet:
					#print(f"Detected MDF path: {mdfPath}")
					filePathList.append(mdfPath)
		#print(filePathList)
		fastMMH3Hasher = FastMMH3()
		for filePath in filePathList:
			lookupHash = pathToPakHashFast(fastMMH3Hasher,filePath)
			if lookupHash in lookupDict:
				fileInfo = lookupDict[lookupHash]
				fileInfo["filePath"] = filePath
				pakIndex = fileInfo["pakIndex"]
				extractedFileSet.add(filePath)
				extractedFileSet.add(filePath.lower())#Prevent extracting the same file twice if it's found as a dependency and has a different path case
				
				pakExtractionList[pakIndex].append(fileInfo)
				#print(f"{os.path.split(filePath)[1]} found in {os.path.split(pakPathList[pakIndex])[1]}")
				
				#Check for streaming path if applicable
				if os.path.splitext(os.path.splitext(filePath)[0])[1] in STREAMING_FILE_TYPE_SET:
					streamingPath = getStreamingPath(filePath,platform,lookupDict)
					if streamingPath != None:
						#print("Found streamed path")
						lookupHash = pathToPakHashFast(fastMMH3Hasher,streamingPath)
						if lookupHash in lookupDict:
							fileInfo = lookupDict[lookupHash]
							fileInfo["filePath"] = streamingPath
							pakIndex = fileInfo["pakIndex"]
							extractedFileSet.add(streamingPath)
							extractedFileSet.add(streamingPath.lower())#Prevent extracting the same file twice if it's found as a dependency and has a different path case
							pakExtractionList[pakIndex].append(fileInfo)
		for index,fileInfoList in enumerate(pakExtractionList):
			if len(fileInfoList) != 0:
				print(f"Extracting {len(fileInfoList)} file(s) from {pakPathList[index]}")
				dependencySet.update(extractPakFromFileInfo(fileInfoList, pakPathList[index], extractDir,extractDependencies=extractDependencies))
		
		newFilesSet = dependencySet.difference(extractedFileSet)
		if len(newFilesSet) != 0:
			#print(f"New files:{newFilesSet}")
			#Reset extraction list to run it again with new paths
			pakExtractionList = [[] for x in range(len(pakPathList))]
			for path in newFilesSet:
				fileVersion = gameInfo["fileVersionDict"].get(f"{os.path.splitext(path)[1][1::].upper()}_VERSION",999)
				filePath = f"natives/{platform}/{path}.{fileVersion}"
				lookupHash = pathToPakHashFast(fastMMH3Hasher,filePath)
				if lookupHash in lookupDict:
					fileInfo = lookupDict[lookupHash]
					fileInfo["filePath"] = filePath
					pakIndex = fileInfo["pakIndex"]
					extractedFileSet.add(filePath)
					extractedFileSet.add(filePath.lower())#Prevent extracting the same file twice if it's found as a dependency and has a different path case
					
					pakExtractionList[pakIndex].append(fileInfo)
					#print(f"{os.path.split(filePath)[1]} found in {os.path.split(pakPathList[pakIndex])[1]}")
					
					#Check for streaming path if applicable
					if os.path.splitext(os.path.splitext(filePath)[0])[1] in STREAMING_FILE_TYPE_SET:
						streamingPath = getStreamingPath(filePath,platform,lookupDict)
						if streamingPath != None:
							lookupHash = pathToPakHashFast(fastMMH3Hasher,streamingPath)
							if lookupHash in lookupDict:
								fileInfo = lookupDict[lookupHash]
								fileInfo["filePath"] = streamingPath
								pakIndex = fileInfo["pakIndex"]
								extractedFileSet.add(streamingPath)
								extractedFileSet.add(streamingPath.lower())#Prevent extracting the same file twice if it's found as a dependency and has a different path case
								pakExtractionList[pakIndex].append(fileInfo)
								
			print(f"Extracting dependencies...")
			for index,fileInfoList in enumerate(pakExtractionList):
				if len(fileInfoList) != 0:
					print(f"Extracting {len(fileInfoList)} file(s) from {pakPathList[index]}")
					dependencySet.update(extractPakFromFileInfo(fileInfoList, pakPathList[index], extractDir,extractDependencies=False))
		print("Finished extracting files.")
	else:
		print("ExtractInfo missing, couldn't extract.")
				
	return extractedFileSet

def extractPakFromFileInfo(fileInfoList,pakPath,outDir,extractDependencies = True):
	
	decompressorZSTD = zstd.ZstdDecompressor()
	#decompressorDeflate = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
	dependencySet = set()
	if os.path.isfile(pakPath):
		with open(pakPath,"rb") as pakStream:
			#for entry in progressBar(fileInfoList, prefix = 'Progress:', suffix = 'Complete', length = 50):
			for entry in fileInfoList:
				filePath = entry["filePath"]
				#print(f"Hash: {entry.hashNameLower}-{entry.hashNameUpper}\nCompression Type: {entry.compressionType}\nEncryption Type: {entry.encryptionType}\n")
				pakStream.seek(entry["offset"])
				fileData = pakStream.read(entry["compressedSize"])
				
				if entry["encryptionType"] > 0:
					#print(f"Encrypted file ({entry.encryptionType}):{filePath}]")
					fileData = decryptResource(fileData)
				
				match entry["compressionType"]:
					case CompressionTypes.COMPRESSION_TYPE_DEFLATE:
						#print("Deflate Compression")
						#fileData = decompressorDeflate.decompress(fileData)
						fileData = zlib.decompress(fileData,wbits=-zlib.MAX_WBITS)
					case CompressionTypes.COMPRESSION_TYPE_ZSTD:
						#print("ZSTD Compression")
						fileData = decompressorZSTD.decompress(fileData)
				
				
				
				outPath = os.path.join(outDir,filePath).replace("/",os.sep).replace("\\",os.sep)
				
				if extractDependencies:
					if ".mdf2." in filePath:
						try:
							version = int(os.path.splitext(filePath)[1].replace(".",""))
						except:
							version = 23
						try:
							with BytesIO(fileData) as tempStream:
								mdfFile = MDFFile()
								mdfFile.read(tempStream,version)
								dependencySet.update(getMDFReferences(mdfFile))
						except:
							print(f"Failed to read dependencies from {outPath}")
				os.makedirs(os.path.split(outPath)[0],exist_ok=True)
				with open(outPath,"wb") as outFile:
					outFile.write(fileData)
					#print(f"Extracted {outPath}")
			else:
				pass
				#print(f"File Not Found ({lookupHash}) {filePath}")
					
				
	else:
		raise Exception("Pak path does not exist.")
	return dependencySet

#Unused		
def extractFileList(filePathList,pakPath,outDir):
	
	decompressorZSTD = zstd.ZstdDecompressor()
	#decompressorDeflate = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
	
	if os.path.isfile(pakPath):
		lookupDict = getPakLookupTable(pakPath)
		print("Extracting files...")
		with open(pakPath,"rb") as pakStream:
			for filePath in progressBar(filePathList, prefix = 'Progress:', suffix = 'Complete', length = 50):
				lookupHash = pathToPakHash(filePath)
				if lookupHash in lookupDict:
					entry = lookupDict[lookupHash]
					#print(f"Hash: {entry.hashNameLower}-{entry.hashNameUpper}\nCompression Type: {entry.compressionType}\nEncryption Type: {entry.encryptionType}\n")
					pakStream.seek(entry.offset)
					size = entry.compressedSize if entry.compressedSize != 0 else entry.uncompressedSize
					fileData = pakStream.read(size)
					
					if entry.encryptionType > 0:
						#print(f"Encrypted file ({entry.encryptionType}):{filePath}]")
						fileData = decryptResource(fileData)
					
					match entry.compressionType:
						case CompressionTypes.COMPRESSION_TYPE_DEFLATE:
							#print("Deflate Compression")
							#fileData = decompressorDeflate.decompress(fileData)
							fileData = zlib.decompress(fileData,wbits=-zlib.MAX_WBITS)
						case CompressionTypes.COMPRESSION_TYPE_ZSTD:
							#print("ZSTD Compression")
							fileData = decompressorZSTD.decompress(fileData)
					
					outPath = os.path.join(outDir,filePath.replace("/",os.sep))
					os.makedirs(os.path.split(outPath)[0],exist_ok=True)
					with open(outPath,"wb") as outFile:
						outFile.write(fileData)
						
						#print(f"Extracted {outPath}")
				else:
					pass
					#print(f"File Not Found ({lookupHash}) {filePath}")
					
				
	else:
		raise Exception("Pak path does not exist.")


class PakCacheStream:#Opens a stream to all pak files for fetching file data directly from the paks via their file paths
	def __init__(self,libraryDir,gameName):
		self.pakStreamList = []
		self.decompressorZSTD = zstd.ZstdDecompressor()
		extractInfoPath = os.path.join(libraryDir,f"ExtractInfo_{gameName}.json")
		pakCachePath = os.path.join(libraryDir,f"PakCache_{gameName}.pakcache")	
		if not os.path.isfile(extractInfoPath):
			raise Exception("Extract info path is invalid")
		extractInfo = None
		try:
			with open(extractInfoPath,"r", encoding ="utf-8") as file:
				#extractInfoDict["exePath"] = exePath
				#extractInfoDict["exeDate"] = os.path.getmtime(exePath)
				#extractInfoDict["exeCRC"] = getFileCRC(exePath)
				#extractInfoDict["extractPath"] = newDirPath
				extractInfo = json.load(file)
				
		except:
			print(f"Failed to load {extractInfoPath}")
		
		
		if extractInfo != None:
			
			
			#extractDir = extractInfo["extractPath"]
			exePath = extractInfo["exePath"]
			platform = extractInfo["platform"]
			if not os.path.isfile(exePath):
				raise Exception("EXE path is invalid")
			modifiedTime = os.path.getmtime(exePath)
			lastModifiedTime = extractInfo["exeDate"]
			
			if not os.path.isfile(pakCachePath):
				pakPriorityList = scanForPakFiles(os.path.split(exePath)[0])
				if len(pakPriorityList) != 0:
					pakPriorityList.reverse()#Reverse the list so that the newest paths are cached first
					createPakCacheFile(pakPriorityList,pakCachePath)
			
			if modifiedTime > lastModifiedTime:
				#Check CRC to verify it changed
				exeCRC = getFileCRC(exePath)
				if exeCRC != extractInfo["exeCRC"]:
					extractInfo["exeDate"] = modifiedTime
					extractInfo["exeCRC"] = exeCRC
					
					print("Game updated. Regenerating pak cache.")
					pakPriorityList = scanForPakFiles(os.path.split(exePath)[0])
					if len(pakPriorityList) != 0:
						pakPriorityList.reverse()#Reverse the list so that the newest paths are cached first
						createPakCacheFile(pakPriorityList,pakCachePath)
						with open(extractInfoPath,"w", encoding ="utf-8") as outFile:
							json.dump(extractInfo,outFile)
							print(f"Wrote {os.path.split(extractInfoPath)[1]}")

					else:
						raise Exception("No pak files were found in game directory. Cannot continue.")
			
			self.pakPathList,self.lookupDict = readPakCache(pakCachePath)
			for pakPath in self.pakPathList:
				self.pakStreamList.append(open(pakPath,"rb"))
		
	def retrieveFileData(self,filePath):
		fileData = None
		#print(filePath)
		lookupHash = pathToPakHash(filePath)
		if lookupHash in self.lookupDict:
			#print(f"Found {filePath}")
			fileInfo = self.lookupDict[lookupHash]
			pakIndex = fileInfo["pakIndex"]
			pakStream = self.pakStreamList[pakIndex]
			pakStream.seek(fileInfo["offset"])
			fileData = pakStream.read(fileInfo["compressedSize"])
			
			if fileInfo["encryptionType"] > 0:
				#print(f"Encrypted file ({fileInfo.encryptionType}):{filePath}]")
				fileData = decryptResource(fileData)
			
			match fileInfo["compressionType"]:
				case CompressionTypes.COMPRESSION_TYPE_DEFLATE:
					#print("Deflate Compression")
					#fileData = decompressorDeflate.decompress(fileData)
					fileData = zlib.decompress(fileData,wbits=-zlib.MAX_WBITS)
				case CompressionTypes.COMPRESSION_TYPE_ZSTD:
					#print("ZSTD Compression")
					fileData = self.decompressorZSTD.decompress(fileData)
			#print(f"Returned {len(fileData)} bytes")
			return fileData
			
	
	def closeStreams(self):
		for stream in self.pakStreamList:
			stream.close()
#Generator function that iterates over all files in all paks, used for pulling strings from files
def debugDataIterator(pakPathList):
	extractCount = 0
	print("Extracting all files...")
	
	extractStartTime = time.time()
	for pakPath in pakPathList:
		print(f"Extracting {os.path.split(pakPath)[1]}")
		
		decompressorZSTD = zstd.ZstdDecompressor()
		#decompressorDeflate = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
		
		if os.path.isfile(pakPath):
			pakTOC = ReadPakTOC(pakPath)
			
			with open(pakPath,"rb") as pakStream:
				for entry in progressBar(pakTOC, prefix = 'Progress:', suffix = 'Complete', length = 50):
					
					#print(f"Hash: {entry.hashNameLower}-{entry.hashNameUpper}\nCompression Type: {entry.compressionType}\nEncryption Type: {entry.encryptionType}\n")
					pakStream.seek(entry.offset)
					#print(entry.__dict__)
					fileData = pakStream.read(entry.compressedSize)
					
					if entry.encryptionType > 0:
						#print(f"Encrypted file ({entry.encryptionType}):{filePath}]")
						fileData = decryptResource(fileData)
					
					match entry.compressionType:
						case CompressionTypes.COMPRESSION_TYPE_DEFLATE:
							#print("Deflate Compression")
							#fileData = decompressorDeflate.decompress(fileData)
							fileData = zlib.decompress(fileData,wbits=-zlib.MAX_WBITS)
	
						case CompressionTypes.COMPRESSION_TYPE_ZSTD:
							#print("ZSTD Compression")
							fileData = decompressorZSTD.decompress(fileData)
					
					yield fileData
					extractCount += 1
						#print(f"Extracted {outPath}")
						
					
		extractEndTime = time.time()
		extractTime =  extractEndTime - extractStartTime
		print(f"Extracted {extractCount} files.")
		print(f"Extracting all files took {timeFormat%(extractTime)} s.")		


					
#Unused	
def extractAll(filePathList,pakPath,outDir):
	print(f"Extracting {os.path.split(pakPath)[1]}")
	
	decompressorZSTD = zstd.ZstdDecompressor()
	#decompressorDeflate = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
	hashStartTime = time.time()
	filePathHashDict = dict()
	for filePath in filePathList:
		filePathHashDict[pathToPakHash(filePath)] = filePath
	hashEndTime = time.time()
	hashTime =  hashEndTime - hashStartTime
	print(f"Hashing file paths took {timeFormat%(hashTime * 1000)} ms.")
	if os.path.isfile(pakPath):
		pakTOC = ReadPakTOC(pakPath)
		
		print("Extracting all files...")
		extractStartTime = time.time()
		extractCount = 0
		with open(pakPath,"rb") as pakStream:
			for entry in progressBar(pakTOC, prefix = 'Progress:', suffix = 'Complete', length = 50):
				
				lookupHash = concatInt(entry.hashNameLower,entry.hashNameUpper)
				if lookupHash in filePathHashDict:
					filePath = filePathHashDict[lookupHash]
				else:
					filePath = os.path.join("UNKNOWN",f"{lookupHash}.bin")
				#print(f"Hash: {entry.hashNameLower}-{entry.hashNameUpper}\nCompression Type: {entry.compressionType}\nEncryption Type: {entry.encryptionType}\n")
				pakStream.seek(entry.offset)
				size = entry.compressedSize if entry.compressedSize != 0 else entry.uncompressedSize
				#print(entry.__dict__)
				fileData = pakStream.read(size)
				
				if entry.encryptionType > 0:
					#print(f"Encrypted file ({entry.encryptionType}):{filePath}]")
					fileData = decryptResource(fileData)
				
				match entry.compressionType:
					case CompressionTypes.COMPRESSION_TYPE_DEFLATE:
						#print("Deflate Compression")
						#fileData = decompressorDeflate.decompress(fileData)
						fileData = zlib.decompress(fileData,wbits=-zlib.MAX_WBITS)

					case CompressionTypes.COMPRESSION_TYPE_ZSTD:
						#print("ZSTD Compression")
						fileData = decompressorZSTD.decompress(fileData)
				
				outPath = os.path.join(outDir,filePath)
				os.makedirs(os.path.split(outPath)[0],exist_ok=True)
				with open(outPath,"wb") as outFile:
					outFile.write(fileData)
					extractCount += 1
					#print(f"Extracted {outPath}")
				
			
			extractEndTime = time.time()
			extractTime =  extractEndTime - extractStartTime
			print(f"Extracted {extractCount} files.")
			print(f"Extracting all files took {timeFormat%(extractTime)} s.")		
				
	else:
		raise Exception("Pak path does not exist.")
def chunkedList(list_data,chunk_size):
  for i in range(0,len(list_data),chunk_size):
      yield list_data[i:i + chunk_size]

#Multiprocessing version
#Setup has a lot of initial overhead but for large amounts of files, it is a lot faster than the single threaded version.
TEMPDIR = os.path.join(os.path.abspath(os.path.split(__file__)[0]),"TEMP")
JOB_JSON_NAME = os.path.join(TEMPDIR,"TEMP_PAK_EXTRACT_JOB.json")
def extractPakMP(filePathList,pakPathList,outDir,maxThreads = cpu_count()-1,skipUnknowns = True):
	print(f"Starting extraction of {len(pakPathList)} pak file(s).")
	adjustedMaxThreads = maxThreads
	if adjustedMaxThreads > cpu_count():
		adjustedMaxThreads = cpu_count() - 1
		
	if adjustedMaxThreads < 1:
		adjustedMaxThreads = 1
	extractStartTime = time.time()
	hashStartTime = time.time()
	print(f"Hashing {len(filePathList)} file paths...")
	filePathHashDict = dict()
	
	fastMMH3Hasher = FastMMH3()
	for filePath in filePathList:
		filePathHashDict[pathToPakHashFast(fastMMH3Hasher,filePath)] = filePath
	hashEndTime = time.time()
	hashTime =  hashEndTime - hashStartTime
	print(f"Hashing file paths took {timeFormat%(hashTime * 1000)} ms.")
	jobJSONDict = {"jobList":[],"maxThreads":adjustedMaxThreads}
	extractedFileSet = set()
	#TODO Scan dependencies
	totalSize = 0
	for pakPath in pakPathList:
		startJobIndex = len(jobJSONDict["jobList"])
		
			
		print(f"Reading {os.path.split(pakPath)[1]}")
		
		skipCount = 0
		if os.path.isfile(pakPath):
			pakTOC = ReadPakTOC(pakPath)
			
			print("Processing TOC...")
			
			extractJobList = []
			for entry in pakTOC:
				skip = False
				lookupHash = concatInt(entry.hashNameLower,entry.hashNameUpper)
				if lookupHash in filePathHashDict:
					filePath = filePathHashDict[lookupHash]
				else:
					if skipUnknowns:
						skip = True
						skipCount += 1
					filePath = os.path.join("UNKNOWN",f"{lookupHash}.bin")
				#extractJobEntry = entry.__dict__
				if not skip:
					extractJobEntry = {
					
					"offset": entry.offset,
					"compressedSize": entry.compressedSize,
					"encryptionType": entry.encryptionType,
					"compressionType": entry.compressionType,
					"filePath": filePath.replace("\\",os.sep)
					}
					totalSize += entry.decompressedSize
					extractJobList.append(extractJobEntry)
				
				
			if skipCount != 0:
				print(f"Skipped ({skipCount} / {len(pakTOC)}) files due to their path not being in the file list.")
			entryCount = len(extractJobList)
			if entryCount < adjustedMaxThreads:
				chunkSize = entryCount
			else:
				chunkSize = entryCount//adjustedMaxThreads
			
			if chunkSize > 2:
				chunkSize = chunkSize // 2#Split chunk size in half so threads that finish earlier have something to do
			
			if entryCount != 0:
				#print(f"Entry Count {len(extractJobList)}")
				for index,listChunk in enumerate(chunkedList(extractJobList, chunkSize)):
					#print(f"List chunk size {len(listChunk)}") 
					#print(f"Generate process {index}")
					
					jobDictEntry = {
						"jobIndex":startJobIndex+index,
						"pakPath":pakPath,
						"outDir":outDir,
						"fileEntries":listChunk,
						}
					jobJSONDict["jobList"].append(jobDictEntry)
			else:
				print("Nothing to extract.")
		else:
			print("Pak path does not exist.")
		
	if len(jobJSONDict["jobList"]) != 0:	
		try:
			os.makedirs(TEMPDIR,exist_ok=True)
		except Exception as err:
			raise Exception(f"Couldn't create TEMP directory at: {TEMPDIR} {str(err)}")
				
				
		with open(JOB_JSON_NAME,"w", encoding ="utf-8") as outFile:
			json.dump(jobJSONDict,outFile)
			print(f"Wrote {os.path.split(JOB_JSON_NAME)[1]}")
		#time.sleep(.5)
		
		pakExtractScriptPath = os.path.join(os.path.split(os.path.abspath(__file__))[0],"re_pak_extract_mp.py")
		#print(pythonPath)
		#print(pakExtractScriptPath)
		
		#Multiprocessing doesn't work well in a blender addon, so a subprocess is used to call a python script using Blender's python executable.
		#This makes it so that the multiprocessing is independent from Blender's python instance.
		
		print(f"Approximately {formatByteSize(totalSize)} to be extracted.\n(Actual size may vary)")		
		print("Starting extraction subprocess.")
		
		with subprocess.Popen([sys.executable,"-u",pakExtractScriptPath], stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as process:
			for line in process.stdout:
				print(line, end='') 

		try:
			os.remove(JOB_JSON_NAME)
		except:
			print("Failed to delete temp job file.")
		if process.returncode != 0:
			raise subprocess.CalledProcessError(process.returncode, process.args)

		extractEndTime = time.time()
		extractTime =  extractEndTime - extractStartTime
		print(f"\nExtracting all pak files took {timeFormat%(extractTime)} s.")
	else:
		print("\nCancelled extraction because there were no files to be extracted.")
				
	
	
def createPakPatch(pakDir,outPath,compress=True,buildManifest = True):
	fileTypeBlackList = set([".exe",".dll",".pak",".blend",".blend1"])
	noCompressionExtensions = set([".tex",".png",".jpg",".ini"])#Tex can't be compressed since it uses gdeflate already
	hasNatives = False
	for entry in os.scandir(pakDir):
		if entry.is_dir():
			if entry.name == "natives":
				hasNatives = True
	if hasNatives:
		print("\nCreating patch pak.")
		print(f"Source Directory: {pakDir}")
		print(f"Output Path: {outPath}")
		print("\nTo cancel, press CTRL + C.\n")
		pakFile = PakFile()
		#compressorZSTD = zstd.ZstdCompressor()
		fileList = []
		for root, dirs, files in os.walk(pakDir):
			for file in files:
				try:
					extension = os.path.splitext(file)[1]
				except:
					extension = None
				if extension != None and extension.lower() not in fileTypeBlackList and not file.endswith("MANIFEST.TXT"):#Ignore manifests, write a new one
					
					fullPath = os.path.join(root,file)
					fileList.append(os.path.join(root,file))
		
		fileList.sort()
		if compress:
			compressorZSTD = zstd.ZstdCompressor()
		fileCount = len(fileList)
		if buildManifest:
			fileCount += 1
		#Set pak header
		pakFile.header.majorVersion = 4
		pakFile.header.minorVersion = 0
		pakFile.header.entryCount = fileCount
		
		manifestList = []
		with open(outPath,"wb") as pakOut:
			#Calculate offsets
			pakFile.write(pakOut)
			#Skip over TOC, will be written later
			currentOffset = 16 + (48 * fileCount)
			pakOut.seek(currentOffset)
			for fullPath in fileList:
				assetPath = os.path.relpath(fullPath,start=pakDir).replace(os.path.sep,"/")
				pakEntry = PakTOCEntry()
				pakEntry.offset = pakOut.tell()
				fileName = os.path.split(assetPath)[1]
				pakEntry.hashNameLower = hashUTF16(assetPath.lower())
				pakEntry.hashNameUpper = hashUTF16(assetPath.upper())
				
				if fileName.startswith("#UNKN#"):#Override hashes for unknown files
					pakEntry.hashNameLower = int(fileName.split("#UNKN#")[1].split("-")[0])
					pakEntry.hashNameUpper = int(fileName.split("-")[1].split(".")[0])
				else:
					manifestList.append(assetPath)
				
				with open(fullPath,"rb") as file:
					fileData = file.read()
				
				isCompressed = False
				pakEntry.decompressedSize = len(fileData)
				if compress and not any(extension in assetPath.lower() for extension in noCompressionExtensions) and pakEntry.decompressedSize > 128:#Textures are already gdeflate compressed
					fileData = compressorZSTD.compress(fileData)
					pakEntry.compressionType = CompressionTypes.COMPRESSION_TYPE_ZSTD
					pakEntry.attributes = 2
					isCompressed = True
				pakEntry.compressedSize = len(fileData)
				pakOut.write(fileData)
				print(f"{assetPath} " + (f"(zstd) [{pakEntry.decompressedSize} > {pakEntry.compressedSize} bytes]" if isCompressed else f"(Uncompressed) [{pakEntry.decompressedSize} bytes]"))
				pakFile.toc.entryList.append(pakEntry)
			
			if buildManifest:
				assetPath = "__MANIFEST/MANIFEST.TXT"
				manifestList.append(assetPath)
				pakEntry = PakTOCEntry()
				pakEntry.offset = pakOut.tell()
				
				pakEntry.hashNameLower = hashUTF16(assetPath.lower())
				pakEntry.hashNameUpper = hashUTF16(assetPath.upper())
				
				manifest = BytesIO()
				for path in manifestList:
					manifest.write(str(path+"\n").encode("utf-8"))
				
				fileData = manifest.getbuffer()
				pakEntry.decompressedSize = len(fileData)
				if compress:
					fileData = compressorZSTD.compress(fileData)
					pakEntry.compressionType = CompressionTypes.COMPRESSION_TYPE_ZSTD
					pakEntry.attributes = 2
				pakEntry.compressedSize = len(fileData)
				pakOut.write(fileData)
				#print("Wrote manifest")
				print(f"{assetPath} " + (f"(zstd) [{pakEntry.decompressedSize} > {pakEntry.compressedSize} bytes]" if compress else f"(Uncompressed) [{pakEntry.decompressedSize} bytes]"))
				pakFile.toc.entryList.append(pakEntry)
			pakOut.seek(16)#Seek to end of header
			pakFile.toc.write(pakOut)
		
		
		
		#writePak(pakFile,outPath)
		print(f"Wrote {outPath}")
	else:
		print("ERROR: No natives folder in the provided directory. Nothing to pack.")

def getFileMagic(stream):
	magic = -1
	magic2 = -1
	stream.seek(0)
	try:
		magic = read_uint(stream)
		magic2 = read_uint(stream)#Some files have the version first, then magic
	except:
		pass
	stream.seek(0)
	return (magic,magic2)

RSZ_MAGIC_SET = {
	5129043,#SCN
	5395285,#USR
	4343376,#PFB
	5919570,#RSZ
	}
MDF_MAGIC = 4605005#MDF
CHAIN2_MAGIC = 846096483
KNOWN_MAGIC_DICT ={
	
	5395285:"user",
	#4605011:"csdf",
	850041:"gui",
	1196641607:"msg",
	4605005:"mdf2",
	4605011:"mmtr",
	5784916:"tex",
	1330201423:"ocioc",
	1480938578:"rtex",
	#1346980931:"ucurve",
	5457225:"ies",
	1213416781:"mesh",
	1413891155:"sdftex",
	1279870531:"cfil",
	#0:"rtmr",
	1380013139:"star",
	1280262989:"mcol",
	541934162:"rmesh",
	5129043:"scn",
	1818389620:"tmlbld",
	4998992:"poglst",
	4673360:"pog",
	1346980931:"clip",
	1413697613:"mpci",
	4343376:"pfb",
	3295086312:"prb",
	1112690766:"lprb",
	#0:"gpbf",
	1936614250:"jcns",
	846096483:"chain2",
	1802396269:"motbank",
	1953721453:"motlist",
	1885433194:"jmap",
	1734634602:"jointlodgroup",
	544501613:"mot",
	1852599155:"fbxskel",
	1347636291:"clsp",
	1330398023:"gpuc",
	1381320275:"sfur",
	1735943530:"jntexprgraph",
	#0:"vmap",
	#0:"zivacomb",
	1096173914:"ziva",
	4476748:"lod",
	5001030:"fol",
	944591955:"stmesh",
	1497648962:"rbs",
	#1497648962:"rdd",
	172774471:"gtl",
	541476931:"chf",
	538986056:"hf",
	5000519:"gml",
	1145983559:"grnd",
	1920493157:"efx",
	#3:"efcsv",
	1212959046:"abcmesh",
	1431720750:"uvs",
	1413699654:"fxct",
	1919772005:"eem",
	1918989941:"uvar",
	#4605011:"vsdf",
	1229738838:"vsdflist",
	1380991815:"gcp",
	1195787079:"gcf",
	1498698567:"gsty",
	1414288198:"fslt",
	1330004550:"oft",
	1414415945:"ift",
	1447904594:"mov",
	1128746052:"dlgcf",
	1279740996:"dlglist",
	4672580:"dlg",
	#1346980931:"dlgtml",
	1414940738:"fsmv2",
	1280262994:"rcol",
	846423668:"tmlfsm2",
	1953721443:"mcamlist",
	1347570755:"clrp",
	1413829443:"cset",
	1162104902:"fpolygon",
	1262633795:"ccbk",
	845966185:"iklookat2",
	1347242305:"ainvm",
	#1347242305:"ainvmmgr",
	1685547107:"chainwnd",
	5460819:"sss",
	1835098989:"motcam",
	1802396259:"mcambank",
	1936485225:"ikls",
	1819110249:"ikmulti",
	1936092009:"ikfs",
	2053925737:"iklizard",
	1802068582:"fbik",
	1684564841:"ikhd",
	1735879529:"ikwagon",
	845636972:"ikleg2",
	1735554162:"retargetrig",
	#1852599155:"skeleton",
	1637975441:"ord",
	2157998135:"rcf",
	3524345696:"ncf",
	1751347827:"vsrc",
	5919570:"amix",
	#5919570:"swms",
	1936483189:"ucurvelist",
	1145588546:"sbnk",
	1263553345:"spck",
	1095584065:"aimapattr",
	1178944579:"cdef",
	541476164:"def",
	1179535686:"finf",
	5461075:"sts",
	1480938568:"htex",
	1347375952:"psop",
	#4605011:"sdf",
	1179992647:"rcfg",
	
	} 

#Common non game files that may be included in the pak
extraPathList=[
	"modinfo.ini",
	"__MANIFEST/MANIFEST.TXT",
	"preview.png",
	"preview.jpg",
	"showcase.png",
	"showcase.jpg",]

def extractModPak(libDir,gameName,pakPath,outDir,looseFileDir = ""):
	#This will miss new paths with language and platform extensions, but I don't think it's worth hashing orders of magnitude more paths to find them.
	#It's unlikely that there'll be unknown paths with those anyway
	print(f"Extracting {pakPath}")
	print(f"Output Directory: {outDir}")
	extractInfoPath = os.path.join(libDir,f"ExtractInfo_{gameName}.json")
	if os.path.isfile(extractInfoPath):
		try:
			with open(extractInfoPath,"r", encoding ="utf-8") as file:
				extractInfo = json.load(file)
				platform = extractInfo["platform"]
		except:
			raise Exception(f"Failed to load {extractInfoPath}")
		
	else:
		raise Exception("Extract paths are not set.")
		return {'CANCELLED'}
	
	gameInfoPath = os.path.join(libDir,f"GameInfo_{gameName}.json")
	if not os.path.isfile(gameInfoPath):
		raise Exception(f"GameInfo_{gameName}.json is missing.")
	catalogPath = os.path.join(libDir,f"REAssetCatalog_{gameName}.tsv")
	print(f"Catalog Path: {catalogPath}")
	
	if not os.path.isfile(catalogPath):
		raise Exception(f"GameInfo_{gameName}.json is missing.")
	gameInfo = loadGameInfo(gameInfoPath)
	filePathList = []
	filePathList.extend(extraPathList)
	unpackStartTime = time.time()
	for row in [entry for entry in loadREAssetCatalogFile(catalogPath)]:
		nativesPath = buildNativesPathFromCatalogEntry(row, gameInfo["fileVersionDict"].get(f"{os.path.splitext(row[0])[1][1::].upper()}_VERSION","999"), platform)
		filePathList.append(nativesPath)
		#print(os.path.splitext(row[0])[1] in STREAMING_FILE_TYPE_SET)
		if os.path.splitext(row[0])[1] in STREAMING_FILE_TYPE_SET:
			#No need to verify if the path exists, that will be done when they're hashed
			streamingPath = nativesPath.replace(f"natives/{platform}/",f"natives/{platform}/streaming/")
			#print(streamingPath)
			filePathList.append(streamingPath)
	decompressorZSTD = zstd.ZstdDecompressor()
	#decompressorDeflate = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
	extractedFilesSet = set()
	
	mdfVersion = int(gameInfo["fileVersionDict"].get("MDF2_VERSION","999"))#For reading texture paths from mdfs
	magicExtensionDict = dict()
	for magic,extension in KNOWN_MAGIC_DICT.items():
		magicExtensionDict[magic] = f".{extension}."+gameInfo["fileVersionDict"].get(f"{extension.upper()}_VERSION","999")
	
	#print(magicExtensionDict)
	scannedPathSet = set()
	unknownCount = 0
	
	#Scan all files in provided loose files directory for paths
	if looseFileDir != "":
		if os.path.isdir(looseFileDir):
			print(f"Scanning files in {looseFileDir}")
			for root, dirs, files in os.walk(looseFileDir):
				for file in files:
					with open(os.path.join(root,file),"rb") as stream:
						magic,magic2 = getFileMagic(stream)
						#magic2 is unused for now
						
						if magic == MDF_MAGIC:
							try:
								#print(f"MDF magic found: {filePath}")
								mdfFile = MDFFile()
								mdfFile.read(stream,mdfVersion)
								scannedPathSet.update(getMDFReferences(mdfFile))
							except Exception as err:
								print(f"Failed to read MDF dependencies from {os.path.join(root,file)}:{str(err)}")
						elif magic in RSZ_MAGIC_SET:
							try:
								scannedPathSet.update(getRSZResourcePaths(stream))
							except Exception as err:
								print(f"Failed to read RSZ dependencies from {os.path.join(root,file)}:{str(err)}")
			print(f"Found {len(scannedPathSet)} paths.")
		else:
			raise Exception("Invalid loose files directory.")
	if os.path.isfile(pakPath):
		lookupDict = getPakLookupTable(pakPath)
		reverseLookupDict = dict()
		fastMMH3Hasher = FastMMH3()
		
		#Load manifest with all files contained in pak if present
		manifestPath = "__MANIFEST/MANIFEST.TXT"
		lookupHash = pathToPakHashFast(fastMMH3Hasher,manifestPath)
		newFilePathList = []#Paths from manifest
		skipFullHash = False
		if lookupHash in lookupDict:
			print("Manifest found.")
			newFilePathList = []
			with open(pakPath,"rb") as pakStream:
				reverseLookupDict[lookupHash] = manifestPath
				entry = lookupDict[lookupHash]
				pakStream.seek(entry.offset)
				size = entry.compressedSize if entry.compressedSize != 0 else entry.uncompressedSize
				fileData = pakStream.read(size)
				
				if entry.encryptionType > 0:
					#print(f"Encrypted file ({entry.encryptionType}):{filePath}]")
					fileData = decryptResource(fileData)
				
				match entry.compressionType:
					case CompressionTypes.COMPRESSION_TYPE_DEFLATE:
						#print("Deflate Compression")
						#fileData = decompressorDeflate.decompress(fileData)
						fileData = zlib.decompress(fileData,wbits=-zlib.MAX_WBITS)
					case CompressionTypes.COMPRESSION_TYPE_ZSTD:
						#print("ZSTD Compression")
						fileData = decompressorZSTD.decompress(fileData)
				
				
				with BytesIO(fileData) as tempStream:
					for line in tempStream.readlines():
						newFilePathList.append(line.decode("utf-8").strip())
						#print(newFilePathList[-1])
		else:
			print("No manifest found.")
		 
		if len(newFilePathList) == len(lookupDict):
			skipFullHash = True
			print(f"Loaded {len(newFilePathList)} paths from manifest.")
			
			for filePath in newFilePathList:#Determine if all paths in the manifest are correct
				lookupHash = pathToPakHashFast(fastMMH3Hasher,filePath)
				if lookupHash in lookupDict:
					reverseLookupDict[lookupHash] = filePath
				else:
					skipFullHash = False
					break

			
		if not skipFullHash:
			filePathList.extend(newFilePathList)
			print(f"Hashing {len(filePathList)} paths...")
			for filePath in progressBar(filePathList, prefix = 'Progress:', suffix = 'Complete', length = 50):
				lookupHash = pathToPakHashFast(fastMMH3Hasher,filePath)
				if lookupHash in lookupDict:
					reverseLookupDict[lookupHash] = filePath
		
		if gameName == "MHWILDS":#Hack fix for extracting older chain file versions if present
			for path in filePathList:
				if path.endswith(".chain2"):
					nativesPath = f"natives/{platform}/"+path.replace("@","")+".13"
					#print(nativesPath)
					lookupHash = pathToPakHashFast(fastMMH3Hasher,nativesPath)
					if lookupHash in lookupDict:
						reverseLookupDict[lookupHash] = nativesPath
						
		print(f"Extracting {len(reverseLookupDict)} known file paths...")
		with open(pakPath,"rb") as pakStream:
			for lookupHash in progressBar(lookupDict, prefix = 'Progress:', suffix = 'Complete', length = 50):
				entry = lookupDict[lookupHash]
				filePath = reverseLookupDict.get(lookupHash,None)
				#print(f"Hash: {entry.hashNameLower}-{entry.hashNameUpper}\nCompression Type: {entry.compressionType}\nEncryption Type: {entry.encryptionType}\n")
				pakStream.seek(entry.offset)
				size = entry.compressedSize if entry.compressedSize != 0 else entry.uncompressedSize
				fileData = pakStream.read(size)
				
				if entry.encryptionType > 0:
					#print(f"Encrypted file ({entry.encryptionType}):{filePath}]")
					fileData = decryptResource(fileData)
				
				match entry.compressionType:
					case CompressionTypes.COMPRESSION_TYPE_DEFLATE:
						#print("Deflate Compression")
						#fileData = decompressorDeflate.decompress(fileData)
						fileData = zlib.decompress(fileData,wbits=-zlib.MAX_WBITS)
					case CompressionTypes.COMPRESSION_TYPE_ZSTD:
						#print("ZSTD Compression")
						fileData = decompressorZSTD.decompress(fileData)
				
				
				with BytesIO(fileData) as tempStream:
					magic,magic2 = getFileMagic(tempStream)
					
					if magic == MDF_MAGIC:
						try:
							#print(f"MDF magic found: {filePath}")
							mdfFile = MDFFile()
							mdfFile.read(tempStream,mdfVersion)
							scannedPathSet.update(getMDFReferences(mdfFile))
						except Exception as err:
							print(f"Failed to read MDF dependencies from {filePath if filePath != None else str(lookupHash)} (Magic:{magic}):{str(err)}")
					elif magic in RSZ_MAGIC_SET:
						try:
							scannedPathSet.update(getRSZResourcePaths(tempStream))
						except Exception as err:
							print(f"Failed to read RSZ dependencies from {filePath if filePath != None else str(lookupHash)}:{str(err)}")

				if filePath != None:
					try:
						outPath = os.path.join(outDir,filePath.replace("/",os.sep))
						if len(outPath) > 260:
							print(f"WARNING: Path exceeds Windows size limit of 260 characters!\n{outPath}")
						os.makedirs(os.path.split(outPath)[0],exist_ok=True)
						with open(outPath,"wb") as outFile:
							outFile.write(fileData)
							extractedFilesSet.add(lookupHash)
					except Exception as err:
						print(f"Failed to extract {outPath}:{str(err)}")
					#print(f"Extracted {outPath}")
			
			#Once all known files have been extracted, scan for dependencies in remaining unknown files
			skippedHashSet = set(lookupDict.keys()) - extractedFilesSet	
			if len(skippedHashSet) != 0:
				print(f"{len(skippedHashSet)} unknown entries.")
				
				newPathSet = set()
				unresolvedPathSet = set()#Print out any paths that may potentially be files but weren't able to extract
				
				if gameName == "MHWILDS":#Hack fix for extracting older chain file versions if present
					for path in scannedPathSet:
						if path.endswith(".chain2"):
							nativesPath = f"natives/{platform}/"+path.replace("@","")+".13"
							#print(nativesPath)
							lookupHash = pathToPakHashFast(fastMMH3Hasher,nativesPath)
							if lookupHash in skippedHashSet:
								reverseLookupDict[lookupHash] = nativesPath
								newPathSet.add(nativesPath)
								
				for path in scannedPathSet:
					nativesPath = f"natives/{platform}/"+path.replace("@","")+"."+gameInfo["fileVersionDict"].get(f"{os.path.splitext(path)[1][1::].upper()}_VERSION","999")
					#print(nativesPath)
					lookupHash = pathToPakHashFast(fastMMH3Hasher,nativesPath)
					if lookupHash in skippedHashSet:
						reverseLookupDict[lookupHash] = nativesPath
						newPathSet.add(nativesPath)
						if os.path.splitext(nativesPath)[1] in STREAMING_FILE_TYPE_SET:
							streamingPath = getStreamingPath(filePath,platform,lookupDict)
							if streamingPath != None:
								#print("Found streamed path")
								lookupHash = pathToPakHashFast(fastMMH3Hasher,streamingPath)
								if lookupHash in skippedHashSet:
									reverseLookupDict[lookupHash] = streamingPath
									newPathSet.add(streamingPath)
					else:
						if lookupHash not in lookupDict:
							unresolvedPathSet.add(nativesPath)
					#print(path)
				print(f"New files found: {len(newPathSet)}")
				for path in newPathSet:
					print(path)
					
				
				print("Extracting remaining files...")
	
				for lookupHash in progressBar(skippedHashSet, prefix = 'Progress:', suffix = 'Complete', length = 50):
					if lookupHash in lookupDict:
						entry = lookupDict[lookupHash]
						filePath = reverseLookupDict.get(lookupHash,None)
						#print(f"Hash: {entry.hashNameLower}-{entry.hashNameUpper}\nCompression Type: {entry.compressionType}\nEncryption Type: {entry.encryptionType}\n")
						pakStream.seek(entry.offset)
						size = entry.compressedSize if entry.compressedSize != 0 else entry.uncompressedSize
						fileData = pakStream.read(size)
						
						if entry.encryptionType > 0:
							#print(f"Encrypted file ({entry.encryptionType}):{filePath}]")
							fileData = decryptResource(fileData)
						
						match entry.compressionType:
							case CompressionTypes.COMPRESSION_TYPE_DEFLATE:
								#print("Deflate Compression")
								#fileData = decompressorDeflate.decompress(fileData)
								fileData = zlib.decompress(fileData,wbits=-zlib.MAX_WBITS)
							case CompressionTypes.COMPRESSION_TYPE_ZSTD:
								#print("ZSTD Compression")
								fileData = decompressorZSTD.decompress(fileData)
						
						if filePath != None:
							try:
								outPath = os.path.join(outDir,filePath.replace("/",os.sep))
								if len(outPath) > 260:
									print(f"WARNING: Path exceeds Windows size limit of 260 characters!\n{outPath}")
								os.makedirs(os.path.split(outPath)[0],exist_ok=True)
								with open(outPath,"wb") as outFile:
									outFile.write(fileData)
									extractedFilesSet.add(lookupHash)
							except Exception as err:
								print(f"Failed to extract {outPath}:{str(err)}")
						else:
							with BytesIO(fileData) as tempStream:
								magic,magic2 = getFileMagic(tempStream)
							
							if magic in magicExtensionDict:
								extension = magicExtensionDict[magic]
							elif magic2 in magicExtensionDict:
								extension = magicExtensionDict[magic2]
							else:
								extension = ".bin.999"
							try:
								outPath = os.path.join(outDir,"UNKNOWN",f"#UNKN#{entry.hashNameLower}-{entry.hashNameUpper}{extension}")
								if len(outPath) > 260:
									print(f"WARNING: Path exceeds Windows size limit of 260 characters!\n{outPath}")
								os.makedirs(os.path.split(outPath)[0],exist_ok=True)
								
								with open(outPath,"wb") as outFile:
									outFile.write(fileData)
									unknownCount += 1
									extractedFilesSet.add(lookupHash)
							except Exception as err:
								print(f"Failed to extract {outPath}:{str(err)}")
				
				if len(unresolvedPathSet) != 0:
					print("\n\n\nAdditional potential file paths:")
					for entry in sorted(list(unresolvedPathSet)):
						print(entry)
				print(f"\nPak extracted to {outDir}")
				print(f"All files extracted, {unknownCount} unknown paths.")
				unpackEndTime = time.time()
				unpackTime =  unpackEndTime - unpackStartTime
				unpackTimeInt = int(unpackTime*1000)
				print(f"Unpacking took {unpackTimeInt} ms.")
				
	else:
		raise Exception("Pak path does not exist.")
