#Author: NSA Cloud
import bpy
import os

import subprocess
import json
import uuid
import csv
from datetime import datetime, UTC
import zstandard as zstd
import zipfile
from zlib import crc32
import re
from io import StringIO
import requests
import glob

from bpy.types import Operator
from ..gen_functions import splitNativesPath,wildCardFileSearch,progressBar,formatByteSize
from .blender_re_asset import getChunkPathList
from ..blender_utils import showMessageBox
from ..mdf.re_mdf_updater_utils import generateMaterialCompendium
from ..rszmini.re_rsz_updater_utils import generateRSZCRCCompendium
from ..gen_functions import openFolder


CRC_INFO_VERSION = 1

#IMAGE_FORMAT = ".png"
IMAGE_FORMAT = ".jp2"

def REToolListFileToREAssetCatalogAndGameInfo(listPath,outputCatalogPath,outputGameInfoPath,fileTypeWhiteList = ["mesh","chain","chain2"]):
	GAMEINFO_VERSION = 1#For determining when changes are made to the structure of gameinfo files

	langDict = {
    "ja":"Japanese",
    "en":"English",
    "fr":"French",
    "it":"Italian",
    "de":"German",
    "es":"Spanish",
    "ru":"Russian",
    "pl":"Polish",
    "nl":"Dutch",
    "pt":"Portuguese",
    "ptbr":"PortugueseBr",
    "ko":"Korean",
    "zhtw":"TransitionalChinese",
    "zhcn":"SimplelifiedChinese",
    "fi":"Finnish",
    "sv":"Swedish",
    "da":"Danish",
    "no":"Norwegian",
    "cs":"Czech",
    "hu":"Hungarian",
    "sk":"Slovak",
    "ar":"Arabic",
    "tr":"Turkish",
    "bg":"Bulgarian",
    "el":"Greek",
    "ro":"Romanian",
    "th":"Thai",
    "ua":"Ukrainian",
    "vi":"Vietnamese",
    "id":"Indonesian",
	"fc":"Fiction",
    "hi":"Hindi",
    "es419":"LatinAmericanSpanish",
	}
	platformDict = {
		"x64":"PC",
		"stm":"Steam",
		"msg":"GamePass"
		}
	
	#Used for automatic category names for unmarked files
	fileTypeDisplayNameDict = {
		"mesh":"Mesh Files",
		"chain":"Chain Files",
		"chain2":"Chain2 Files",
		"efx":"EFX Files",
		"pfb":"Prefab Files",
		"user":"UserData Files",
		"scn":"Scene Files",
		"fbxskel":"FBXSkel Files",
		
		}
	#Having these be in separate categories doesn't make much sense since they're needed together
	excludeBaseCategorySet = set([
		"mesh",
		"chain",
		"chain2",
		"fbxskel",
		])
	fileExtensionSet = set()
	gameInfoDict = dict()
	gameName = outputGameInfoPath.split("GameInfo_")[1].split(".json")[0]
	gameInfoDict["GameName"] = gameName
	gameInfoDict["GameInfoVersion"] = GAMEINFO_VERSION
	gameInfoDict["fileTypeWhiteList"] = fileTypeWhiteList
	gameInfoDict["fileVersionDict"] = dict()
	
	readLineSet = set()
	with open(listPath,"r") as file:
		meshEntries = set()
		lines = file.readlines()
	with open(outputCatalogPath,"w",encoding = "utf-8") as outputFile:
		outputFile.write("File Path\tDisplay Name\tCategory (Forward Slash Separated)\tTags (Comma Separated)\tPlatform Extension\tLanguage Extension\n")#Write header line
		for line in sorted(lines):
			
			if "streaming" not in line.lower() and line.lower() not in readLineSet and os.path.split(line)[1].count(".") > 1:#Prevent duplicate entries
				readLineSet.add(line.lower())
				
				split = os.path.split(line.strip())[1].split(".")
				fileName = split[0]
				fileType = split[1]
				fileExtensionSet.add(fileType)
				#if fileType.lower() in fileTypeWhiteList:
				versionNum = split[2]
				gameInfoDict["fileVersionDict"][f"{fileType.upper()}_VERSION"] = versionNum
				
				
				if fileType not in excludeBaseCategorySet:
					category = fileTypeDisplayNameDict.get(fileType,fileType.upper()+" Files")
				else:
					category = ""
				tags = f"{fileName}.{fileType}"
				platformExtension = ""
				langExtension = ""
				#print(len(split))
				#print(split)
				
				#TODO
				#Many list files contain extra paths for files in each language.
				#This results in a ton of extra entries for assets that don't really exist.
				#Need to add verification that the file exists in the pak

				if len(split) == 4:
					if split[3].lower() in langDict:
						langExtension = split[3]
					elif split[3].lower() in platformDict:
						platformExtension = split[3]
				elif len(split) == 5:
					platformExtension = split[3]
					langExtension = split[4]
				filePath = os.path.join(splitNativesPath(os.path.split(line)[0])[1],f"{fileName}.{fileType}").replace("\\","/").replace(os.sep,"/")
				displayName = fileName+"."+fileType
				
				if platformExtension != "":
					 displayName += f" ({platformDict[platformExtension.lower()]})"
				if langExtension != "":
					 displayName += f" ({langDict[langExtension.lower()]})"
				outputFile.write(f"{filePath}\t{displayName}\t{category}\t{tags}\t{platformExtension}\t{langExtension}\n")
				
	with open(outputGameInfoPath,"w",encoding = "utf-8") as outputFile:
		json.dump(gameInfoDict,outputFile,indent=4, sort_keys=False,
	                      separators=(',', ': '))	
	print(f"Generated {os.path.split(outputGameInfoPath)[1]}")

def compressFileZSTD(inputPath, outputPath):
	with open(inputPath, 'rb') as inputFile:
		with open(outputPath, 'wb') as outputFile:
			compressor = zstd.ZstdCompressor()
			data = compressor.compress(inputFile.read())
			outputFile.write(data)

def decompressFileZSTD(inputPath, outputPath):
	with open(inputPath, 'rb') as inputFile:
		with open(outputPath, 'wb') as outputFile:
			decompressor = zstd.ZstdDecompressor()
			decompressedData = decompressor.decompress(inputFile.read())
			outputFile.write(decompressedData)
            
def decompressFileZSTD_Bytes(inputPath):#Returns bytes
	decompressedData = None
	with open(inputPath, 'rb') as inputFile:
		decompressor = zstd.ZstdDecompressor()
		decompressedData = decompressor.decompress(inputFile.read())
	return decompressedData

def getFileCRC(filePath):
	size = 1024*1024*10  # 10 MiB chunks
	with open(filePath, 'rb') as f:
	    crcval = 0
	    while chunk := f.read(size):
	        crcval = crc32(chunk, crcval)
	return crcval

def zipLibrary(blendDir,gameName):
	
	print("Preparing to package asset library")
	print(f"Game Name:{gameName}")
	
	if not re.match("^[a-zA-Z0-9_]+$",gameName):
		print("Invalid characters in game name.")
		return False
	uncompressedSize = 0
	gameInfoPath = os.path.join(blendDir,f"GameInfo_{gameName}.json")
	print(f"Game Info Path:{gameInfoPath}")
	assetCatalogPath = os.path.join(blendDir,f"REAssetCatalog_{gameName}.tsv")
	print(f"Asset Catalog Path:{assetCatalogPath}")
	thumbnailDir = os.path.join(blendDir,f"REAssetLibrary_{gameName}_thumbnails")
	print(f"Thumbnail Directory:{thumbnailDir}")
	materialCompendiumPath = os.path.join(blendDir,f"MaterialCompendium_{gameName}.json")
	crcCompendiumPath = os.path.join(blendDir,f"CRCCompendium_{gameName}.json")
	
	
	outputPath = os.path.join(blendDir,f"{gameName}.reassetlib")
	
	blendFilePath = os.path.join(blendDir,f"REAssetLibrary_{gameName}.blend")
	
	if os.path.isfile(gameInfoPath) and os.path.isfile(assetCatalogPath) and os.path.isdir(thumbnailDir):
		packedAssetCatalogPath = os.path.join(blendDir,f"packedAssetCat_{gameName}.zst")
		
		#Compressing this for the sole reason of preventing people from messing with it and causing problems for themselves.
		#Used to check for differences between original downloaded asset catalog and any modifications the user makes to it.
		compressFileZSTD(assetCatalogPath,packedAssetCatalogPath)
		#print("Generating CRC Info...")
		#CRCInfoDict = {"CRCInfo_Version":CRC_INFO_VERSION,"imageCRCDict":{}}
		#CRCInfoPath = os.path.join(blendDir,f"CRCInfo_{gameName}.json")
		uncompressedSize += os.path.getsize(packedAssetCatalogPath)
		uncompressedSize += os.path.getsize(gameInfoPath)
		uncompressedSize += os.path.getsize(assetCatalogPath)
		if os.path.isfile(blendFilePath):
			uncompressedSize += os.path.getsize(blendFilePath)
		else:
			print("Unknown blend file path, unable to get size. Uncompressed size will be wrong.")
		timestamp = str(datetime.now(UTC)).split(".")[0]
		packageInfoPath = os.path.join(blendDir,f"packageInfo_{gameName}.json")#Used to check if a newer version of a library is available on the repo
		packageInfoDict = dict()
		packageInfoDict["timestamp"] = timestamp
		with open(packageInfoPath,"w",encoding = "utf-8") as outputFile:
			json.dump(packageInfoDict,outputFile,indent=4, sort_keys=False,separators=(',', ': '))
		
		print("Compressing files...")
		with zipfile.ZipFile(outputPath, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
		    
			zf.write(gameInfoPath, arcname=f"{gameName}\GameInfo_{gameName}.json")
			zf.write(assetCatalogPath, arcname=f"{gameName}\REAssetCatalog_{gameName}.tsv")
			zf.write(packedAssetCatalogPath, arcname=f"{gameName}\packedAssetCat_{gameName}.zst")
			zf.write(packageInfoPath, arcname=f"{gameName}\packageInfo_{gameName}.json")
			if os.path.isfile(materialCompendiumPath):
				zf.write(materialCompendiumPath, arcname=f"{gameName}\MaterialCompendium_{gameName}.json")
				if os.path.isfile(crcCompendiumPath):
					zf.write(crcCompendiumPath, arcname=f"{gameName}\CRCCompendium_{gameName}.json")
			for file in os.scandir(thumbnailDir):
		        
				if file.name.endswith(IMAGE_FORMAT):
					uncompressedSize += os.path.getsize(os.path.join(thumbnailDir,file.name))
					#CRCInfoDict["imageCRCDict"][file.name]=getFileCRC(os.path.join(thumbnailDir,file.name))
					#print(file.name)
					zf.write(os.path.join(thumbnailDir,file.name), arcname=f"{gameName}\REAssetLibrary_{gameName}_thumbnails/{file.name}")
			#json.dump(CRCInfoDict,CRCInfoPath,indent=4, sort_keys=False,
		    #                  separators=(',', ': '))
			#zf.write(CRCInfoPath, arcname=f"{gameName}\CRCInfo_{gameName}.json")
		
		
		print(f"Saved packed library at {outputPath}")
		
		
		#Print out asset lib info as json for adding to the repo
		
		compressedSize = os.path.getsize(outputPath)
		crc = getFileCRC(outputPath)
		
		
		jsonDict = dict()
		jsonDict["libraryList"] = []
		
		libEntry = dict()
		libEntry["displayName"] = gameName#To be changed later
		libEntry["gameName"] = gameName
		libEntry["timestamp"] = timestamp
		libEntry["CRC"] = crc
		libEntry["compressedSize"] = compressedSize
		libEntry["uncompressedSize"] = uncompressedSize
		libEntry["URL"] = r"https://raw.githubusercontent.com/NSACloud/RE-Asset-Library-Collection/main/"+f"{gameName}.reassetlib"
		jsonDict["libraryList"].append(libEntry)
		print(json.dumps(jsonDict,indent=4, sort_keys=False,
	                      separators=(',', ': ')))
		#print(f"{os.path.split(outputPath)[1]} CRC:{crc}")
		return True
	else:
		print("One or more of the above paths are invalid. Cannot package library.")
		return False
	
def unzipLibrary(extractDir,zipPath):
	print(f"Extracting {zipPath}...")
	gameName = None
	with zipfile.ZipFile(zipPath, 'r') as zf:
		for name in zf.namelist():
			if "GameInfo_" in name:
				gameName = name.split("GameInfo_")[1].split(".json")[0]
				break
		zf.extractall(path = extractDir)
	
	print(f"Finished extracting {os.path.split(zipPath)[1]}")
	return gameName

def downloadFileContent(url,timeout = 30):

	r = requests.get(url, timeout=timeout)
	if r.ok:
	    print(f"Downloaded {url}")
	    return r.content
	else:
	    print(r)
	    print(r.text)
	    return None

def downloadREAssetLibDirectory(timeout = 30):
	url = r"https://raw.githubusercontent.com/NSACloud/RE-Asset-Library-Collection/main/REAssetLib_directory.json"
	content = downloadFileContent(url,timeout)
	jsonDict = None
	if content != None:
		#print(content)
		jsonDict = json.loads(content.decode("utf-8"))
	else:
		print(f"Failed to download {url}")
	return jsonDict

class WM_OT_RenderREAssets(Operator):
	bl_label = "Render RE Asset Thumbnails"
	bl_idname = "re_asset.render_re_asset_thumbnails"
	bl_description = "Renders thumbnails for all RE assets of a supported type.\nThis will open a new blend file and will take a long time.\nOnly assets without existing thumbnails will be rendered.\nA lot of storage space will be used for cached textures. Consider clearing RE Mesh Editor's texture cache folder after rendering"
	bl_options = {'INTERNAL'}
	def execute(self, context):
		addonDir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
		hdriPath = os.path.join(addonDir,"Resources","HDRI","thumbnailRenderEnvTexture.hdr")
		blendDir = os.path.split(bpy.context.blend_data.filepath)[0]
		rendererBlendPath = os.path.join(addonDir,"Resources","Blend","assetRenderer.blend")#This may seem pointless, it's a blank blend file. However, if blender's default startup is used, it'll cause textures to show up pink in the render for whatever reason.
		scriptPath = os.path.join(addonDir,"Resources","Scripts","renderAssets.py")
		try:
			gameName = os.path.split(bpy.context.blend_data.filepath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
		except:
			gameName = "UNKN"
		print(f"Game Name:{gameName}")
		renderJobPath = os.path.join(blendDir,f"RenderJob_{gameName}.json")
		gameInfoPath = os.path.join(blendDir,f"GameInfo_{gameName}.json")
		
		if os.path.isfile(gameInfoPath):
			gameInfo = loadGameInfo(gameInfoPath)
				
		else:
			print(f"RE Asset Library - Missing GameInfo:{gameInfoPath}")
		gameName = gameInfo["GameName"]
		meshVersion = "."+gameInfo["fileVersionDict"]["MESH_VERSION"]
		#Generate render job json
		renderJobDict = dict()
		meshPathList = []
		meshPathSet = set()
		print("Generating RenderJob file.")
		foundAssets = False
		if bpy.context.scene.get("isREAssetLibrary"):
			
			renderJobDict["GAME"] = gameName
			thumbnailDirectory = os.path.join(os.path.split(bpy.context.blend_data.filepath)[0],f"REAssetLibrary_{gameName}_thumbnails")
			#print(thumbnailDirectory)
			os.makedirs(thumbnailDirectory,exist_ok = True)
			renderJobDict["Output Path"] = thumbnailDirectory
			renderJobDict["HDRI Path"] = hdriPath
			
			for obj in bpy.data.objects:
				if obj.get("~TYPE") == "RE_ASSET_LIBRARY_ASSET":
					assetType = obj.get("assetType")
					
					match assetType:
						case "MESH":
							
							hashedPath = str(crc32(str(obj["assetPath"].lower()).encode("utf-8")))+IMAGE_FORMAT
							#print(hashedPath)
							fullThumbnailPath = os.path.join(thumbnailDirectory,hashedPath)
							#print(fullThumbnailPath)
							if (not os.path.exists(fullThumbnailPath) or not os.path.isfile(fullThumbnailPath)):# and not skipExistingThumbnails:
								chunkPathList = getChunkPathList(gameName)
								for chunkPath in chunkPathList:
									fullMeshPath = os.path.join(chunkPath,obj["assetPath"]+meshVersion)
									#print(fullMeshPath)
									if os.path.exists(fullMeshPath):
										if obj["assetPath"] not in meshPathSet:
											entry = dict()
											entry["path"] = fullMeshPath
											entry["outputName"] = os.path.split(obj["assetPath"].lower())[1]+"-"+hashedPath
											meshPathSet.add(obj["assetPath"])
											meshPathList.append(entry)
											break
			if len(meshPathList) != 0:
				foundAssets = True
			#meshPathList.sort(key = lambda item: item["path"])
			meshPathList.sort(key = lambda item: item["outputName"])
			renderJobDict["entryList"] = meshPathList
			with open(renderJobPath,"w",encoding = "utf-8") as outputFile:
				json.dump(renderJobDict,outputFile,indent=4,separators=(',', ': '))
			print(f"Generated {renderJobPath}")
		
		
		if os.path.isfile(scriptPath) and os.path.isfile(renderJobPath) and foundAssets:
			subprocess.Popen([bpy.app.binary_path, "--python", scriptPath,"--",renderJobPath])
			self.report({"INFO"},"Started asset render job.")
		else:
			if not os.path.isfile(renderJobPath):
				print("RenderJob json file was not generated. cannot render.")
				
			if not foundAssets:
				print("No renderable files found. This may mean that the chunk path is not correct.\nIf files in the library can not be found in any chunk paths, they can't be rendered.")
			if not os.path.isfile(scriptPath):
				print(f"{scriptPath} is missing.")
			self.report({"ERROR"},"Could not start asset render job. See console. (Window > Toggle System Console)")
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None

class WM_OT_FetchREAssetThumbnails(Operator):
	bl_label = "Fetch RE Asset Thumbnails"
	bl_idname = "re_asset.fetch_re_asset_thumbnails"
	bl_description = "Sets asset browser thumbnails to thumbnails created by the Render RE Asset button.\nThis may take a minute. Blender will freeze temporarily while assets are being assigned thumbnails"
	bl_options = {'INTERNAL'}
	
	forceReload : bpy.props.BoolProperty(
	   name = "Force Reload All",
	   description = "Discards all saved thumbnail info and reloads it.",
	   default = False)
	def execute(self, context):
		if bpy.context.scene.get("isREAssetLibrary"):
			try:
				gameName = os.path.split(bpy.context.blend_data.filepath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
			except:
				gameName = "UNKN"
			print(f"Game Name:{gameName}")
			print("\nFetching RE Asset Thumbnails...")
			addonThumbnailDir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Resources","Icons")
			blendDir = os.path.split(bpy.path.abspath(bpy.context.blend_data.filepath))[0]
			thumbnailDirectory = os.path.join(blendDir,f"REAssetLibrary_{gameName}_thumbnails")
			#currentThumbnailIndex = 0
			assetCollection = bpy.data.collections.get("RE Assets")
			if os.path.isdir(thumbnailDirectory) and assetCollection != None:
				try:
					bpy.ops.wm.console_toggle()
				except:
					pass
				
				assetCount = len(assetCollection.objects)
				CRCInfoPath = os.path.join(blendDir,f"CRCInfo_{gameName}.json")
				if os.path.isfile(CRCInfoPath) and not self.forceReload:
					try:
						with open(CRCInfoPath,"r", encoding ="utf-8") as file:
							CRCInfoDict = json.load(file)
					except:
						print(f"Failed to load {CRCInfoPath}, generating as new.")
						CRCInfoDict = {"CRCInfo_Version":CRC_INFO_VERSION,"imageCRCDict":{}}
				else:
					CRCInfoDict = {"CRCInfo_Version":CRC_INFO_VERSION,"imageCRCDict":{}}
				for obj in progressBar(assetCollection.objects, prefix = 'Progress:', suffix = 'Complete', length = 50):
					if obj.get("~TYPE") == "RE_ASSET_LIBRARY_ASSET":
						assetType = obj.get("assetType")
						
						hashedPath = os.path.split(obj["assetPath"].lower())[1]+"-" + str(crc32(str(obj["assetPath"].lower()).encode("utf-8")))+IMAGE_FORMAT
						#print(hashedPath)
						fullThumbnailPath = os.path.join(thumbnailDirectory,hashedPath)
						
						
						#Fallback file type thumbnail
						if not os.path.isfile(fullThumbnailPath):# and preferences.useFallBack == True TODO
							fullThumbnailPath = os.path.join(addonThumbnailDir,f"thumbnail_filetype_{assetType.lower()}{IMAGE_FORMAT}")
							
							
						if os.path.isfile(fullThumbnailPath):
							crc = getFileCRC(fullThumbnailPath)
							#print(f"{hashedPath}:{crc}")
							if not hashedPath in CRCInfoDict["imageCRCDict"] or (hashedPath in CRCInfoDict["imageCRCDict"] and CRCInfoDict["imageCRCDict"][hashedPath] != crc ):
								CRCInfoDict["imageCRCDict"][hashedPath] = crc
								with bpy.context.temp_override(id=obj):
									bpy.ops.ed.lib_id_load_custom_preview(filepath=fullThumbnailPath,check_existing=True)
							#currentThumbnailIndex += 1
							#if currentThumbnailIndex % 25 == 0:
								#print(f"Current Thumbnail Number {currentThumbnailIndex}")
				with open(CRCInfoPath,"w",encoding = "utf-8") as outputFile:
					json.dump(CRCInfoDict,outputFile,indent=4, sort_keys=False,
				                      separators=(',', ': '))
				print(f"Saved {CRCInfoPath}")
				try:
					bpy.ops.wm.console_toggle()
				except:
					pass
			else:
				self.report({"INFO"},"RE Asset thumbnails have not been rendered. Cannot retrieve.")
				return {'CANCELLED'}
			
		self.report({"INFO"},"Fetched RE Asset thumbnails.")
		return {'FINISHED'}
	def draw(self,context):
		layout = self.layout
		layout.label(text="Reload all new or changed asset thumbnails?")
		layout.prop(self,"forceReload")
	def invoke(self,context,event):
		return context.window_manager.invoke_props_dialog(self)
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None



def createBlenderCatalog(categoryNames, blender_assets_cat_path,makeNew = False):#Appends if already exists

	catalog_file_path = os.path.join(blender_assets_cat_path,"blender_assets.cats.txt")
	
	catalogEntrySet = set()#For checking exact matches without including uuid
	catalogEntryList = []#For final list of entries including uuid
	catalogIDDict = dict()
	if os.path.isfile(catalog_file_path) and not makeNew:
		with open(catalog_file_path, "r", encoding="utf-8") as file:
			lines = file.readlines()
		   
			for line in lines:
				if line.strip() != "" and not line.startswith("#") and "VERSION " not in line:
					uuidString = line.split(":")[0]
					full_catalog_name = line.split(":")[1].split(":")[0].strip()
					simple_catalog_name = line.split(":")[2].strip()
					catalog_entry = f"{full_catalog_name}:{simple_catalog_name}"
					#print(catalog_entry)
					
					if catalog_entry not in catalogEntrySet:
						catalogEntryList.append(f"{uuidString}:{catalog_entry}")
						catalogEntrySet.add(catalog_entry)
						catalogIDDict[full_catalog_name] = uuidString
					
	for name in categoryNames:
		full_catalog_name = name
		simple_catalog_name = name.replace("/","-")
		catalog_entry = f"{full_catalog_name}:{simple_catalog_name}"

		# Check if the full catalog name is already listed to avoid duplicates
		if catalog_entry not in catalogEntrySet and name != "":
			uuidString = str(uuid.uuid4())
			catalogEntryList.append(f"{uuidString}:{catalog_entry}")
			catalogEntrySet.add(catalog_entry)
			catalogIDDict[full_catalog_name] = uuidString
				
	with open(catalog_file_path, "w", encoding="utf-8") as file:
		file.write(  
"""# This is an Asset Catalog Definition file for Blender.
#
# Empty lines and lines starting with `#` will be ignored.
# The first non-ignored line should be the version indicator.
# Other lines are of the format "UUID:catalog/path/for/assets:simple catalog name"

# Generated by RE Asset Library

VERSION 1

"""
		)

		for entry in catalogEntryList:
			file.write(f"{entry}\n")

		return catalogIDDict

def getCatalogUUIDDict(blender_assets_cat_filepath):# Key: catalogUUID, Value:Category String
	catalogEntrySet = set()#For checking exact matches without including uuid
	catalogEntryList = []#For final list of entries including uuid
	catalogIDDict = dict()
	if os.path.isfile(blender_assets_cat_filepath):
		with open(blender_assets_cat_filepath, "r", encoding="utf-8") as file:
			lines = file.readlines()
		   
			for line in lines:
				if line.strip() != "" and not line.startswith("#") and "VERSION " not in line:
					uuidString = line.split(":")[0]
					full_catalog_name = line.split(":")[1].split(":")[0].strip()
					simple_catalog_name = line.split(":")[2].strip()
					catalog_entry = f"{full_catalog_name}:{simple_catalog_name}"
					#print(catalog_entry)
					
					if catalog_entry not in catalogEntrySet:
						catalogEntryList.append(f"{uuidString}:{catalog_entry}")
						catalogEntrySet.add(catalog_entry)
						catalogIDDict[uuidString] = full_catalog_name
	return catalogIDDict
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
def loadREAssetCatalogData(tsvData,fileTypeWhiteListSet = set()):
	assetEntryList = []
	
	file = StringIO(tsvData.decode("utf-8"))  # Convert the decompressed bytes to a file-like object
	rd = csv.reader(file, delimiter="\t", quotechar='"')
	next(rd)#Skip header
	loadAll = len(fileTypeWhiteListSet) == 0
	 
	for row in rd:
		#Check if file extension is in the whitelist
		if os.path.splitext(row[0])[1][1:].lower() in fileTypeWhiteListSet or loadAll:
			assetEntryList.append(row)
			
	return assetEntryList
	
def getCollection(collectionName,parentCollection = None,makeNew = False):
	if makeNew or not bpy.data.collections.get(collectionName):
		collection = bpy.data.collections.new(collectionName)
		collectionName = collection.name
		if parentCollection != None:
			parentCollection.children.link(collection)
		else:
			bpy.context.scene.collection.children.link(collection)
	return bpy.data.collections[collectionName]

def createEmpty(name,propertyList,parent = None,collection = None):
	obj = bpy.data.objects.new( name, None )
	obj.empty_display_size = .10
	obj.empty_display_type = 'PLAIN_AXES'
	obj.parent = parent
	for property in propertyList:
 
		obj[property[0]] = property[1]
	if collection == None:
		collection = bpy.context.scene.collection
		
	collection.objects.link(obj)
		
		
	return obj

def find_asset_browser():
    for each_window in bpy.context.window_manager.windows:
        each_screen = each_window.screen
        #if each_screen.name.lower() == "layout":
        for each_area in each_screen.areas:
            if each_area.type == "FILE_BROWSER":
                for each_space in each_area.spaces:
                    if each_space.type == "FILE_BROWSER":
                        if each_space.browse_mode == "ASSETS":
                            return each_window, each_screen, each_area, each_space
    return None, None, None, None

def getGameNameFromAssetBrowser():
	gameName = None
	_, _, _, asset_browser_space = find_asset_browser()
	if asset_browser_space != None and "RE Assets - " in asset_browser_space.params.asset_library_reference:
		gameName = asset_browser_space.params.asset_library_reference.split("RE Assets - ")[1]
	return gameName

def getAssetBlendPathFromAssetBrowser():
	gameName = getGameNameFromAssetBrowser()
	libName = f"RE Assets - {gameName}" 
	blendPath = None
	if gameName != None:
		for lib in bpy.context.preferences.filepaths.asset_libraries:
			if lib.name == libName:
				#Verify that the required re asset files exist before returning anything
				if os.path.isfile(os.path.join(bpy.path.abspath(lib.path),f"GameInfo_{gameName}.json")) and os.path.isfile(os.path.join(bpy.path.abspath(lib.path),f"REAssetLibrary_{gameName}.blend")):
					blendPath = os.path.join(bpy.path.abspath(lib.path),f"REAssetLibrary_{gameName}.blend")
				break
	return blendPath
def getAssetLibrary(name):
	libraryExists = False
	
	for lib in bpy.context.preferences.filepaths.asset_libraries:
		if lib.name == name:
			libraryExists = True
			newLib = lib
			break
		
	if not libraryExists:
		bpy.ops.preferences.asset_library_add()
		newLib = bpy.context.preferences.filepaths.asset_libraries[-1]
	return newLib

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
class WM_OT_InitializeREAssetLibrary(Operator):
	bl_label = "Initialize RE Asset Library"
	bl_idname = "re_asset.initialize_library"
	bl_description = "Loads all loadable assets from the REAssetCatalog_XXXX.tsv file in the same directory as the blend file.\nTHIS WILL CLEAR ALL ASSETS FROM THE CURRENT LIBRARY"
	bl_options = {'INTERNAL'}
	def execute(self, context):
		print("Initializing RE Engine Asset Library...")
		blendDir = os.path.split(bpy.path.abspath(bpy.context.blend_data.filepath))[0]
		gameName = None
		gameInfoPath = wildCardFileSearch(glob.escape(os.path.join(blendDir,"GameInfo_"))+"*")
		if gameInfoPath == None:
			raise Exception("GameInfo json file missing.")
		else:
			if os.path.isfile(gameInfoPath):
				try:
					with open(gameInfoPath,"r", encoding ="utf-8") as file:
						gameInfo = loadGameInfo(gameInfoPath)
						gameName = gameInfo["GameName"]
				except:
					raise Exception(f"Failed to load {gameInfoPath}")
					
			else:
				print(f"RE Asset Library - Missing GameInfo:{gameInfoPath}")
			if gameName != None:
				catalogPath = os.path.join(blendDir,f"REAssetCatalog_{gameName}.tsv")
			else:
				self.report({"ERROR"},"Game name not set.")
				return {'CANCELLED'}
			if not os.path.isfile(catalogPath):
				self.report({"ERROR"},"REAssetCatalog_{gameName} catalog file missing. Cannot load.")
				return {'CANCELLED'}
			bpy.context.scene["isREAssetLibrary"] = True
			bpy.context.scene["REAssetLibrary_Game"] = gameName
			
			libraryName = f"RE Assets - {gameName}"
			library = getAssetLibrary(libraryName)
			library.name = libraryName
			library.path = blendDir
			bpy.ops.re_asset.import_catalog()
			bpy.ops.re_asset.fetch_re_asset_thumbnails()
			# retrieve the context of the asset browser
			asset_browser_window, asset_browser_screen, asset_browser_area, asset_browser_space = find_asset_browser()
			if asset_browser_space != None:
				asset_browser_space.params.asset_library_reference = f"RE Assets - {gameName}"
			
			bpy.ops.wm.save_userpref()
			bpy.ops.wm.save_mainfile()
			self.report({"INFO"},"Loaded RE Assets.")
		print("Finished initializing.")
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None
	
class WM_OT_ImportREAssetLibraryFromCatalog(Operator):
	bl_label = "Reload RE Asset Catalog File"
	bl_idname = "re_asset.import_catalog"
	bl_description = "Loads all loadable assets from the REAssetCatalog_XXXX.tsv file in the same directory as the blend file"
	bl_options = {'INTERNAL'}
	
	def execute(self, context):
		
		
			
			
		blendDir = os.path.split(bpy.path.abspath(bpy.context.blend_data.filepath))[0]
		try:
			gameName = os.path.split(bpy.context.blend_data.filepath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
		except:
			gameName = "UNKN"
		#print(f"Game Name:{gameName}")
		
		if gameName != None:
			catalogPath = os.path.join(blendDir,f"REAssetCatalog_{gameName}.tsv")
			gameInfoPath = os.path.join(blendDir,f"GameInfo_{gameName}.json")
		else:
			self.report({"ERROR"},"Game name not set in blend file.")
			return {'CANCELLED'}
		if not os.path.isfile(catalogPath):
			self.report({"ERROR"},f"REAssetCatalog_{gameName}.tsv catalog file missing. Cannot load.")
			return {'CANCELLED'}
		
		if os.path.isfile(gameInfoPath):
			gameInfo = loadGameInfo(gameInfoPath)
				
		else:
			self.report({"ERROR"},f"GameInfo_{gameName}.json file missing. Cannot load.")
			return {'CANCELLED'}
		
		assetCollection = getCollection("RE Assets")
		
		existingAssetObjDict = dict()
		for obj in assetCollection.all_objects:
			if obj.get("~TYPE") == "RE_ASSET_LIBRARY_ASSET":
				fullAssetPath = obj.get("assetPath","UNKNPATH")
				if obj.get("platExt","") != "":
					fullAssetPath += "." + obj["platExt"]
				if obj.get("langExt","") != "":
					fullAssetPath += "."+obj["langExt"]
				#print(fullAssetPath.lower())
				existingAssetObjDict[fullAssetPath.lower()] = obj
					
				
					
		

		assetEntryList = loadREAssetCatalogFile(catalogPath,set(gameInfo["fileTypeWhiteList"]))
		categorySet = set([entry[2].strip() for entry in assetEntryList])
		catalogIDDict = createBlenderCatalog(list(categorySet), os.path.split(bpy.data.filepath)[0])
		#print(categorySet)
		
		for assetEntry in assetEntryList:
			filePath,displayName,category,tagString,platExt,langExt = assetEntry[0],assetEntry[1],assetEntry[2].strip(),assetEntry[3],assetEntry[4],assetEntry[5]
			
			fullAssetPath = filePath
			if platExt != "":
				fullAssetPath += "." + platExt
			if langExt != "":
				fullAssetPath += "." + langExt
			
			#print(fullAssetPath.lower())
			
			assetType = os.path.splitext(filePath)[1][1:].upper()
			
			if fullAssetPath.lower() not in existingAssetObjDict:
				assetObj = createEmpty(displayName,[("~TYPE","RE_ASSET_LIBRARY_ASSET"),("~GAME",gameName),("assetType",assetType),("assetPath",filePath)],parent=None,collection = assetCollection)
				if platExt != "":
					assetObj["platExt"] = platExt
				if langExt != "":
					assetObj["langExt"] = langExt
				existingAssetObjDict[fullAssetPath.lower()] = assetObj
				#print(f"Created new asset obj {assetObj.name}")
			else:
				assetObj = existingAssetObjDict[fullAssetPath.lower()]
				assetObj.name = displayName
				#print(f"Found existing asset obj {assetObj.name}")
			assetObj.asset_mark()
			assetObj.asset_data.description = filePath
			tagList = tagString.split(",")
			for existingTag in assetObj.asset_data.tags:
				assetObj.asset_data.tags.remove(existingTag)
				
			for tag in tagList:
				if tag.strip() != "":
					assetObj.asset_data.tags.new(tag)
			#assetObj.asset_data.author
			if category in catalogIDDict:
				assetObj.asset_data.catalog_id = catalogIDDict[category]
		
		asset_browser_window, asset_browser_screen, asset_browser_area, asset_browser_space = find_asset_browser()
		if asset_browser_space != None:
			with bpy.context.temp_override(area=asset_browser_area):
				bpy.ops.asset.library_refresh()
			#print(assetObj.asset_data.catalog_id)
		#bpy.ops.re_asset.fetch_re_asset_thumbnails()
		self.report({"INFO"},"Loaded RE Assets.")
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None
	def draw(self,context):
		layout = self.layout
		layout.label(text="Are you sure you want to reimport the catalog?")
		layout.label(text="This will reset any unsaved names.")
	def invoke(self,context,event):
		return context.window_manager.invoke_props_dialog(self)

class WM_OT_SaveREAssetLibraryToCatalog(Operator):
	bl_label = "Save Changes To Catalog"
	bl_idname = "re_asset.save_to_catalog"
	bl_description = "Saves all changes to RE Asset names, categories and tags made in Blender to REAssetCatalog_XXXX.tsv"
	bl_options = {'INTERNAL'}
	
	def execute(self, context):
		
		
			
			
		blendDir = os.path.split(bpy.path.abspath(bpy.context.blend_data.filepath))[0]
		blender_assets_cats_path = os.path.join(blendDir, "blender_assets.cats.txt")
		try:
			gameName = os.path.split(bpy.context.blend_data.filepath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
		except:
			gameName = None
		print(f"Game Name:{gameName}")
		
		
		if gameName != None:
			catalogPath = os.path.join(blendDir,f"REAssetCatalog_{gameName}.tsv")
		else:
			self.report({"ERROR"},"Game name not set in blend file.")
			return {'CANCELLED'}
		if not os.path.isfile(catalogPath):
			self.report({"ERROR"},f"REAssetCatalog_{gameName}.tsv catalog file missing. Cannot load.")
			return {'CANCELLED'}
		
		
		bpy.ops.wm.save_mainfile()
		
		if not os.path.isfile(blender_assets_cats_path):
			self.report({"ERROR"},f"blender_assets.cats.txt file missing. Cannot load.")
			return {'CANCELLED'}
			
		
		assetCollection = getCollection("RE Assets")
		
		
		
		existingAssetObjDict = dict()
		for obj in assetCollection.all_objects:
			if obj.get("~TYPE") == "RE_ASSET_LIBRARY_ASSET":
				fullAssetPath = obj.get("assetPath","UNKNPATH")
				if obj.get("platExt","") != "":
					fullAssetPath += "." + obj["platExt"]
				if obj.get("langExt","") != "":
					fullAssetPath += "."+obj["langExt"]
				#print(fullAssetPath.lower())
				existingAssetObjDict[fullAssetPath.lower()] = obj
					
				
					
		assetEntryList = loadREAssetCatalogFile(catalogPath,set())
		catalogUUIDDict = getCatalogUUIDDict(blender_assets_cats_path)
		#print(categorySet)
		with open(catalogPath,"w",encoding = "utf-8") as outputFile:
			outputFile.write("File Path\tDisplay Name\tCategory (Forward Slash Separated)\tTags (Comma Separated)\tPlatform Extension\tLanguage Extension\n")#Write header line
			for assetEntry in assetEntryList:
				filePath,displayName,category,tagString,platExt,langExt = assetEntry[0],assetEntry[1],assetEntry[2].strip(),assetEntry[3],assetEntry[4],assetEntry[5]
				
				fullAssetPath = filePath
				if platExt != "":
					fullAssetPath += "." + platExt
				if langExt != "":
					fullAssetPath += "." + langExt
				
				#print(fullAssetPath.lower())
				
				if fullAssetPath.lower() in existingAssetObjDict:
					assetObj = existingAssetObjDict[fullAssetPath.lower()]
					
					#print(f"Found existing asset obj {assetObj.name}")
					if "." in assetObj.name and assetObj.name.rsplit(".",1)[1].isdigit():
						newDisplayName = assetObj.name.rsplit(".",1)[0]
					else:
						newDisplayName = assetObj.name
					newTagString = ""
					if len(assetObj.asset_data.tags) > 0:
						newTagString += assetObj.asset_data.tags[0].name
					if len(assetObj.asset_data.tags) > 1:
						for tag in assetObj.asset_data.tags[1:]:
							newTagString += f",{tag.name}"
					#assetObj.asset_data.author
					if assetObj.asset_data.catalog_id in catalogUUIDDict:
						newCategory = catalogUUIDDict[assetObj.asset_data.catalog_id]
					else:
						newCategory = category
					"""
					if newDisplayName != displayName or newCategory != category or newTagString != tagString:			
						print(f"{displayName} changed")
						if newDisplayName != displayName:
							print(f"\tnew:{newDisplayName}")
							
						if newCategory != category:
							print(f"\tnew:{newCategory}")
							
						if newTagString != tagString:
							print(f"\tnew:{newTagString}")
					"""
					outputFile.write(f"{filePath}\t{newDisplayName}\t{newCategory}\t{newTagString}\t{platExt}\t{langExt}\n")
				else:
					outputFile.write(f"{filePath}\t{displayName}\t{category}\t{tagString}\t{platExt}\t{langExt}\n")
						
						
		self.report({"INFO"},"Saved changes to RE Asset Catalog.")
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None
	def draw(self,context):
		layout = self.layout
		layout.label(text="Save changes made to RE Assets to catalog?")
		layout.label(text="This will also save the current blend file.")
	def invoke(self,context,event):
		return context.window_manager.invoke_props_dialog(self)

def generateGitHubIssueURL(user,repo,gameName,desc):
    gameName = gameName.replace(" ","+")
    desc = desc.replace(" ","+").replace("\n","%0D%0A")
    url = f"https://github.com/{user}/{repo}/issues/new?labels=catalog+update&title=[{gameName}]+Catalog+Update+{str(datetime.today().strftime('%Y-%m-%d'))}&body={desc}"
    return url


#-- Google Drive Download
# Had to add this because github doesn't allow files above 100 MB
def download_file_from_google_drive(file_id, destination, chunk_size=32768):
    url = "https://drive.usercontent.google.com/download?export=download"

    session = requests.Session()
    params = {'id': file_id, 'confirm': 't'}
    response = session.get(url, params=params, stream=True)

    for i, chunk_size_ in save_response_content(response, destination, chunk_size):
        yield i, chunk_size_


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None


def save_response_content(response, destination, chunk_size):
    with open(destination, "wb") as f:
        for i, chunk in enumerate(response.iter_content(chunk_size)):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                yield i, chunk_size
#--

class WM_OT_ExportCatalogDiff(Operator):
	bl_label = "Generate Library Diff"
	bl_idname = "re_asset.export_catalog_diff"
	bl_description = "Exports changes made to library compared to it's original state to a CSV file."
	bl_options = {'INTERNAL'}
	def execute(self, context):
		blendDir = os.path.split(bpy.path.abspath(bpy.context.blend_data.filepath))[0]
		blender_assets_cats_path = os.path.join(blendDir, "blender_assets.cats.txt")
		try:
			gameName = os.path.split(bpy.context.blend_data.filepath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
		except:
			gameName = None
		print(f"Game Name:{gameName}")
		timestamp = str(datetime.now(UTC)).split(".")[0].replace(" ","_").replace(":","").replace("-","")
		
		if gameName != None:
			catalogPath = os.path.join(blendDir,f"REAssetCatalog_{gameName}.tsv")
			packedAssetCatalogPath = os.path.join(blendDir,f"packedAssetCat_{gameName}.zst")
			diffZipPath = os.path.join(blendDir,"Diff",f"Diff_REAssetCatalog_{gameName}_{timestamp}.zip")
		else:
			self.report({"ERROR"},"Game name not set in blend file.")
			return {'CANCELLED'}
		if not os.path.isfile(catalogPath):
			self.report({"ERROR"},f"REAssetCatalog_{gameName}.tsv catalog file missing. Cannot load.")
			return {'CANCELLED'}
		
		if not os.path.isfile(packedAssetCatalogPath):
			self.report({"ERROR"},f"packedAssetCat_{gameName}.zst catalog file missing. Cannot load.")
			return {'CANCELLED'}
		
		print("Saving catalog changes...")
		bpy.ops.re_asset.save_to_catalog()
		
		os.makedirs(os.path.split(diffZipPath)[0],exist_ok = True)
		#Build dict of old asset paths
		oldAssetDict = dict()
		
		assetEntryList = loadREAssetCatalogData(decompressFileZSTD_Bytes(packedAssetCatalogPath),set())
		for assetEntry in assetEntryList:
			filePath,displayName,category,tagString,platExt,langExt = assetEntry[0],assetEntry[1],assetEntry[2].strip(),assetEntry[3],assetEntry[4],assetEntry[5]
			
			fullAssetPath = filePath
			if platExt != "":
				fullAssetPath += "." + platExt
			if langExt != "":
				fullAssetPath += "." + langExt
			entry = dict()
			entry["displayName"] = displayName
			entry["category"] = category
			entry["tagString"] = tagString
			oldAssetDict[fullAssetPath.lower()] = entry
		print(f"Old Asset Count:{len(oldAssetDict)}")
		assetEntryList = loadREAssetCatalogFile(catalogPath,set())
		print(f"New Asset Count:{len(assetEntryList)}")
		changeCount = 0
		addCount = 0
		with StringIO() as stream:
			stream.write("File Path\tDisplay Name\tCategory (Forward Slash Separated)\tTags (Comma Separated)\tPlatform Extension\tLanguage Extension\n")#Write header line
			#Check new asset list for differences, write asset ent
			for assetEntry in assetEntryList:
				filePath,displayName,category,tagString,platExt,langExt = assetEntry[0],assetEntry[1],assetEntry[2].strip(),assetEntry[3],assetEntry[4],assetEntry[5]
				
				fullAssetPath = filePath
				if platExt != "":
					fullAssetPath += "." + platExt
				if langExt != "":
					fullAssetPath += "." + langExt
				
				#print(fullAssetPath.lower())
				
				if fullAssetPath.lower() in oldAssetDict:
					#print("found entry")
					oldAssetEntry = oldAssetDict[fullAssetPath.lower()]
					if oldAssetEntry["displayName"] != displayName or oldAssetEntry["category"] != category or oldAssetEntry["tagString"] != tagString:
						stream.write(f"{filePath}\t{displayName}\t{category}\t{tagString}\t{platExt}\t{langExt}\n")
						changeCount += 1
				else:
					stream.write(f"{filePath}\t{displayName}\t{category}\t{tagString}\t{platExt}\t{langExt}\n")
					addCount += 1
			print(f"Change Count:{changeCount}")
			print(f"Add Count:{addCount}")
			if changeCount != 0 or addCount != 0:
				with zipfile.ZipFile(diffZipPath, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
				    zf.writestr(f"Diff_REAssetCatalog_{gameName}_{timestamp}.tsv", stream.getvalue())
				openFolder(os.path.split(diffZipPath)[0])
				
				#githubURL = generateGitHubIssueURL(
				#user = "NSACloud",
				#repo = "RE-Asset-Library-Collection",
				#gameName = gameName,
				#desc = f"{changeCount} asset entries changed.\n\n(Don't forget to attach the generated diff zip file by dragging it into this box)",
				#)
				#bpy.ops.wm.url_open(url = githubURL)
				self.report({"INFO"},"Generated Diff file.")
			else:
				self.report({"INFO"},"No changes have been made to the asset library so a Diff file can't be generated.")
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None
	def draw(self,context):
		layout = self.layout
		layout.label(text="This will generate a zip file containing all changes made.")
	def invoke(self,context,event):
		return context.window_manager.invoke_props_dialog(self)
class WM_OT_ImportCatalogDiff(Operator):
	bl_label = "Import Library Changes"
	bl_idname = "re_asset.import_catalog_diff"
	bl_description = "Imports \"_diff\" catalog files. If a directory is chosen, all _diff files will be imported.\nThis will modify the REAssetCatalog file."
	bl_options = {'INTERNAL'}
	def execute(self, context):
		if True:#TODO
			self.report({"INFO"},"Imported RE Asset library changes.")
		else:
			self.report({"ERROR"},"Failed to import RE Asset library changes.")
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None

class WM_OT_PackageREAssetLibrary(Operator):
	bl_label = "Package RE Asset Library"
	bl_idname = "re_asset.package_re_asset_library"
	bl_description = "Packages asset library into .reassetlib file. Can be imported from addon preferences.\nAlso generates packedAssetCat_XXXX.zst for comparing library changes."
	bl_options = {'INTERNAL'}
	def execute(self, context):
		if bpy.context.scene.get("isREAssetLibrary"):
			blendDir = os.path.split(bpy.path.abspath(bpy.context.blend_data.filepath))[0]
			try:
				gameName = os.path.split(bpy.context.blend_data.filepath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
			except:
				gameName = None
			print(f"Game Name:{gameName}")
			if zipLibrary(blendDir, gameName):
				openFolder(blendDir)
				self.report({"INFO"},"Packaged RE Asset library.")
			else:
				self.report({"ERROR"},"Failed to package RE Asset library. See console for details.")
		else:
			self.report({"ERROR"},"This blend file is not an RE Asset Library. Cannot package.")
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None
	def draw(self,context):
		layout = self.layout
		layout.label(text="Package the library into an .reassetlib file?")
		layout.label(text="This will overwrite packedAssetCat_XXXX.zst.")
		layout.label(text="Any changes in the library are compared to this file.")
		layout.label(text="Submit Changes To GitHub won't work as intended.")
	def invoke(self,context,event):
		return context.window_manager.invoke_props_dialog(self)
	
	
class WM_OT_CheckForREAssetLibraryUpdate(Operator):
	bl_label = "Check For Library Update"
	bl_idname = "re_asset.check_for_library_update"
	bl_description = "Check if a newer version of the library is available on the asset library repository"
	bl_options = {'INTERNAL'}
	
	URL: bpy.props.StringProperty(default="", options = {"HIDDEN"})
	CRC: bpy.props.StringProperty(default="0", options = {"HIDDEN"})
	releaseDescription: bpy.props.StringProperty(default="", options = {"HIDDEN"})
	timestamp: bpy.props.StringProperty(default="0", options = {"HIDDEN"})
	downloadSize: bpy.props.StringProperty(default="0", options = {"HIDDEN"})
	updateIsAvailable: bpy.props.BoolProperty(default = False, options = {"HIDDEN"})
	
	def execute(self, context):
		if os.path.split(bpy.context.blend_data.filepath)[1].startswith("REAssetLibrary_"):#Operator run in asset blend file
			blendDir = os.path.split(bpy.path.abspath(bpy.context.blend_data.filepath))[0]
			try:
				gameName = os.path.split(bpy.context.blend_data.filepath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
			except:
				gameName = "UNKN"
		else:#Operator run elsewhere from asset browser
			gameName = "UNKN"
			blendPath = getAssetBlendPathFromAssetBrowser()
			if blendPath != None:
				gameName = os.path.split(blendPath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
				blendDir = os.path.split(blendPath)[0]
		
		assetLibDir = os.path.dirname(os.path.dirname(blendDir))
		
		print(f"Game Name:{gameName}")
		outFilePath = os.path.join(assetLibDir,f"{gameName}.reassetlib")
		
		print(assetLibDir)
		if self.URL != "":
			print("Updating RE Engine Asset Library...")
			libCRC = int(self.CRC)
			
			"""
			content = downloadFileContent(self.URL)
			if content != None:
				with open(outFilePath,"wb") as outFile:
					outFile.write(content)
			"""
			for _,_ in download_file_from_google_drive(file_id=self.URL,destination=outFilePath):
				pass
			if os.path.isfile(outFilePath):
				if libCRC == getFileCRC(outFilePath):
					print("CRC Check Passed")
					bpy.ops.re_asset.importlibrary(filepath = outFilePath,currentBlendPath = bpy.path.abspath(bpy.context.blend_data.filepath))
					#bpy.ops.re_asset.import_catalog()
					#bpy.ops.re_asset.fetch_re_asset_thumbnails()
					
					#bpy.ops.wm.save_mainfile()
					self.report({"INFO"},"Updated RE Asset Library.")
					try:
						os.remove(outFilePath)
					except:
						pass
				else:
					print("CRC Check failed, aborting install.")
					self.report({"INFO"},"Failed to update RE Asset Library, CRC check failed. Try downloading the asset library again.")
					return {'CANCELLED'}
		else:
			self.report({"ERROR"},"Game is not on repository or repository is unreachable.")
			return {'CANCELLED'}
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None
	
	def invoke(self, context, event):
		if os.path.split(bpy.context.blend_data.filepath)[1].startswith("REAssetLibrary_"):#Operator run in asset blend file
			blendDir = os.path.split(bpy.path.abspath(bpy.context.blend_data.filepath))[0]
			try:
				gameName = os.path.split(bpy.context.blend_data.filepath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
			except:
				gameName = "UNKN"
		else:#Operator run elsewhere from asset browser
			gameName = "UNKN"
			blendPath = getAssetBlendPathFromAssetBrowser()
			if blendPath != None:
				gameName = os.path.split(blendPath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
				blendDir = os.path.split(blendPath)[0]
		print(f"Checking for {gameName} update...")
		packageInfoPath = os.path.join(blendDir,f"packageInfo_{gameName}.json")
		
		
		
		directoryDict = downloadREAssetLibDirectory()
		
		libDirectoryEntry = None
		if directoryDict != None:
			#print(directoryDict)
			if directoryDict.get("libraryList"):
				libraryList = directoryDict.get("libraryList")
				for entry in libraryList:
					if entry["gameName"] == gameName:
						libDirectoryEntry = entry
						break
		if libDirectoryEntry != None:
			self.CRC = str(entry["CRC"])
			self.URL = entry["URL"]
			self.releaseDescription = entry.get("releaseDescription","")
			self.timestamp = entry["timestamp"]
			print("Repository Timestamp: "+str(entry["timestamp"]))
			self.downloadSize = str(entry["compressedSize"])
		timestamp = "0"
		if os.path.isfile(packageInfoPath):
			try:
				with open(packageInfoPath,"r", encoding ="utf-8") as file:
					packageInfoDict = json.load(file)
					timestamp = packageInfoDict["timestamp"]
					print("Local Timestamp: "+str(timestamp))
			except:
				print(f"Failed to load {packageInfoPath}")
		
		if timestamp < self.timestamp:
			self.updateIsAvailable = True
			return context.window_manager.invoke_props_dialog(self,width = 400,confirm_text = "Update Asset Library")
		else:
			print("No update available.")
			return context.window_manager.invoke_popup(self)
	
	def draw(self,context):
		layout = self.layout
		if self.updateIsAvailable:
			layout.label(text="An update is available.")
			layout.label(text=self.releaseDescription)
			layout.label(text=f"Update Date: {self.timestamp}")
			layout.label(text = f"Download Size: {formatByteSize(int(self.downloadSize))}")
		else:
			layout.label(text="Asset library is up to date.")

class WM_OT_OpenLibraryFolder(Operator):
	bl_label = "Open Library Folder"
	bl_description = "Opens the folder containing this blend file."
	bl_idname = "re_asset.open_library_folder"

	def execute(self, context):
		try:
			openFolder(os.path.split(bpy.context.blend_data.filepath)[0])
		except:
			pass
		return {'FINISHED'}
	
class WM_OT_GenerateMaterialCompendium(Operator):
	bl_label = "Generate Material Compendium"
	bl_description = "Generates file containing paths to all material shaders. This is used for the MDF Updater"
	bl_idname = "re_asset.generate_material_compendium"
	libraryPath : bpy.props.StringProperty(
	   name = "Library Path",
	   description = "",
	   default = "",
	   options = {"HIDDEN","SKIP_SAVE"})
	gameName : bpy.props.StringProperty(
	   name = "Game Name",
	   description = "",
	   default = "",
	   options = {"HIDDEN","SKIP_SAVE"})
	def execute(self, context):
		try:
			if self.gameName != "":
				gameName = self.gameName
			else:
				gameName = os.path.split(bpy.context.blend_data.filepath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
			
			if self.libraryPath != "":
				libPath = self.libraryPath
			else:
				libPath = os.path.split(bpy.context.blend_data.filepath)[0]
			generateMaterialCompendium(libPath,gameName)
			self.report({"INFO"},"Generated Material Compendium.")
		except Exception as err:
			print(err)
			self.report({"ERROR"},"Could not generate compendium. See console. (Window > Toggle System Console)")
		return {'FINISHED'}
	
class WM_OT_GenerateRSZCRCCompendium(Operator):
	bl_label = "Generate RSZ CRC Compendium"
	bl_description = "Generates file containing paths to all rsz instance types. This is used for the RSZ CRC Updater"
	bl_idname = "re_asset.generate_rszcrc_compendium"
	libraryPath : bpy.props.StringProperty(
	   name = "Library Path",
	   description = "",
	   default = "",
	   options = {"HIDDEN","SKIP_SAVE"})
	gameName : bpy.props.StringProperty(
	   name = "Game Name",
	   description = "",
	   default = "",
	   options = {"HIDDEN","SKIP_SAVE"})
	def execute(self, context):
		try:
			if self.gameName != "":
				gameName = self.gameName
			else:
				gameName = os.path.split(bpy.context.blend_data.filepath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
			
			if self.libraryPath != "":
				libPath = self.libraryPath
			else:
				libPath = os.path.split(bpy.context.blend_data.filepath)[0]
			generateRSZCRCCompendium(libPath,gameName)
			self.report({"INFO"},"Generated CRC Compendium.")
		except Exception as err:
			print(err)
			self.report({"ERROR"},"Could not generate compendium. See console. (Window > Toggle System Console)")
		
		return {'FINISHED'}