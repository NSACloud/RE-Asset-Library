#Author: NSA Cloud
import os
import json

from ..hashing.mmh3.pymmh3 import hashUTF8
from ..pak.re_pak_utils import loadGameInfo,extractFilesFromPakCache

from shutil import copyfile
from .file_re_mdf import readMDF,writeMDF,Property,TextureBinding
def makeMDFBackup(mdfPath):
	bakIndex = 0
	bakPath = f"{mdfPath}.bak{bakIndex}"
	if os.path.isfile(mdfPath):
		while(os.path.isfile(bakPath)):
			bakIndex += 1
			bakPath = f"{mdfPath}.bak{bakIndex}"
		try:
			copyfile(mdfPath,bakPath)
		except Exception as err:
			print(f"Failed to create backup of {mdfPath} - {str(err)}")
def getMaterialByHash(mdfPath,matNameHash):
	material = None
	try:
		mdfFile = readMDF(mdfPath)
		for mat in mdfFile.materialList:
			if mat.matNameHash == matNameHash:
				material = mat
				#print("Found sample mat")
				break
	except Exception as err:
		print(f"Failed to retrieve material from sample MDF {mdfPath} {str(err)}")
	if material == None:
		print(f"Failed to retrieve sample material {matNameHash} at {mdfPath}")
	return material
	
def batchUpdateMDFFiles(modDirectory,compendiumPath,searchSubdirectories,createBackups):
	print(f"Checking for outdated MDF files in: {modDirectory}")
	mdfList = []
	for root, dirs, files in os.walk(modDirectory):
		for fileName in files:
			if ".mdf2." in fileName and ".bak" not in fileName:#not fileName.endswith(".bak"):
				mdfList.append(os.path.join(root,fileName))
		
		if not searchSubdirectories:
			break
	
	if not os.path.isfile(compendiumPath):
		raise Exception("Compendium path is invalid")
	try:
		with open(compendiumPath,"r", encoding ="utf-8") as file:
			materialCompendium = json.load(file)
			
	except:
		raise Exception(f"Failed to load {compendiumPath}")
	assetLibDir = os.path.split(compendiumPath)[0]
	gameName = os.path.split(compendiumPath)[1].split("MaterialCompendium_")[1].split(".json")[0]
	gameInfoPath = os.path.join(assetLibDir,f"GameInfo_{gameName}.json")	
	gameInfo = loadGameInfo(gameInfoPath)
	mdfVersion = gameInfo["fileVersionDict"]["MDF2_VERSION"]
	
	extractInfoPath = os.path.join(assetLibDir,f"ExtractInfo_{gameName}.json")	
	
	if not os.path.isfile(extractInfoPath):
		raise Exception("Extract info path is invalid")
	try:
		with open(extractInfoPath,"r", encoding ="utf-8") as file:
			extractInfo = json.load(file)
			chunkPath = os.path.join(extractInfo["extractPath"],"natives",extractInfo["platform"])
			print(f"Extract Path: {chunkPath}")
	except:
		raise Exception(f"Failed to load {extractInfoPath}")
	
	pakCachePath = os.path.join(assetLibDir,f"PakCache_{gameName}.pakcache")	
	
	if not os.path.isfile(pakCachePath):
		raise Exception("Pak cache path is invalid")
	print("Extracting newest shader files...")
	mdfExtractList = [entry["mdfPath"] for entry in materialCompendium.values()]
	#print(mdfExtractList)
	extractFilesFromPakCache(gameInfoPath, mdfExtractList, extractInfoPath, pakCachePath,extractDependencies=False)
	print(f"Extracted {len(mdfExtractList)} files.")
	
	
	mmtrMaterialCache = dict()
	
	updatedFileCount = 0
	
	for mdfPath in mdfList:
		print(f"Checking {mdfPath}")
		requiresUpdate = False
		try:
			mdfFile = readMDF(mdfPath)
			for material in mdfFile.materialList:
				mmtrHash = str(hashUTF8(material.mmtrPath.lower()))
				#print(material.materialName)
				#print(mmtrHash)
				if mmtrHash not in mmtrMaterialCache:
					
					if mmtrHash in materialCompendium:
						compendiumEntry = materialCompendium[mmtrHash]
						#print(materialCompendium[mmtrHash])
						samplePath = os.path.join(chunkPath,compendiumEntry["mdfPath"].replace("/",os.sep)+f".{mdfVersion}")
						sampleMaterial = getMaterialByHash(samplePath, compendiumEntry["matNameHash"])
						mmtrMaterialCache[mmtrHash] = sampleMaterial
					else:
						print(f"MMTR path {material.mmtrPath} not in compendium, can't update {material.materialName} material.")
						sampleMaterial = None
				else:
					sampleMaterial = mmtrMaterialCache[mmtrHash]
					if sampleMaterial != None:
						
						#Properties
						
						newPropNameSet = set([item.propName for item in sampleMaterial.propertyList])
						#print(newPropNameSet)
				        
				        
						oldPropNameSet = set([item.propName for item in material.propertyList])
						#print(oldPropNameSet)
				        
						addedPropDifference = newPropNameSet.difference(oldPropNameSet)
						if len(addedPropDifference) != 0:
							requiresUpdate = True
							print(f"Added properties in {material.materialName} material:")
							for propName in addedPropDifference:
								for prop in sampleMaterial.propertyList:
									if prop.propName == propName:
										newProp = Property()
										newProp.propName = propName
										newProp.value = prop.value[:]
										material.propertyList.append(newProp)
							print(addedPropDifference)
						removedPropDifference = oldPropNameSet.difference(newPropNameSet)
						if len(removedPropDifference) != 0:
							requiresUpdate = True
							print(f"Removed properties in {material.materialName} material:")
							material.propertyList = [mat for mat in material.propertyList if mat.propName not in removedPropDifference]
							print(removedPropDifference)
							
						#Texture Bindings
						
						newBindingNameSet = set([item.textureType for item in sampleMaterial.textureList])
						#print(newPropNameSet)
				        
				        
						oldBindingNameSet = set([item.textureType for item in material.textureList])
						#print(oldPropNameSet)
				        
						addedBindingDifference = newBindingNameSet.difference(oldBindingNameSet)
						if len(addedBindingDifference) != 0:
							requiresUpdate = True
							print(f"Added texture bindings in {material.materialName} material:")
							for textureType in addedBindingDifference:
								for binding in sampleMaterial.textureList:
									if binding.textureType == textureType:
										newBinding = TextureBinding()
										newBinding.textureType = textureType
										newBinding.texturePath = binding.texturePath
										material.textureList.append(newBinding)
							print(addedBindingDifference)
						removedBindingDifference = oldBindingNameSet.difference(newBindingNameSet)
						if len(removedBindingDifference) != 0:
							requiresUpdate = True
							print(f"Removed texture bindings in {material.materialName} material:")
							material.textureList = [mat for mat in material.textureList if mat.textureType not in removedBindingDifference]
							print(removedBindingDifference)
						
					else:
						print(f"Sample material for {material.mmtrPath} missing.")
						print(mmtrHash)
			if requiresUpdate:
				if createBackups:
					makeMDFBackup(mdfPath)
				writeMDF(mdfFile, mdfPath)
				updatedFileCount += 1
				print("Update completed.")
			else:
				print("No update required.")
				
						#print(samplePath)
			#print(mdfPath)
		except Exception as err:
			print(f"Failed to read {mdfPath}: {str(err)}")
	return updatedFileCount

#Runs on Blender collections
def batchUpdateMDFCollections(compendiumPath,bpy):
	print(f"Checking for outdated MDF collections...")
	
	if not os.path.isfile(compendiumPath):
		raise Exception("Compendium path is invalid")
	try:
		with open(compendiumPath,"r", encoding ="utf-8") as file:
			materialCompendium = json.load(file)
			
	except:
		raise Exception(f"Failed to load {compendiumPath}")
	mdfList = [col for col in bpy.data.collections if col.get("~TYPE") == "RE_MDF_COLLECTION"]

	assetLibDir = os.path.split(compendiumPath)[0]
	gameName = os.path.split(compendiumPath)[1].split("MaterialCompendium_")[1].split(".json")[0]
	gameInfoPath = os.path.join(assetLibDir,f"GameInfo_{gameName}.json")	
	gameInfo = loadGameInfo(gameInfoPath)
	mdfVersion = gameInfo["fileVersionDict"]["MDF2_VERSION"]
	
	extractInfoPath = os.path.join(assetLibDir,f"ExtractInfo_{gameName}.json")	
	
	if not os.path.isfile(extractInfoPath):
		raise Exception("Extract info path is invalid")
	try:
		with open(extractInfoPath,"r", encoding ="utf-8") as file:
			extractInfo = json.load(file)
			chunkPath = os.path.join(extractInfo["extractPath"],"natives",extractInfo["platform"])
			print(f"Extract Path: {chunkPath}")
	except:
		raise Exception(f"Failed to load {extractInfoPath}")
	
	pakCachePath = os.path.join(assetLibDir,f"PakCache_{gameName}.pakcache")	
	
	if not os.path.isfile(pakCachePath):
		raise Exception("Pak cache path is invalid")
	print("Extracting newest shader files...")
	mdfExtractList = [entry["mdfPath"] for entry in materialCompendium.values()]
	#print(mdfExtractList)
	extractFilesFromPakCache(gameInfoPath, mdfExtractList, extractInfoPath, pakCachePath,extractDependencies=False)
	print(f"Extracted {len(mdfExtractList)} files.")
	
	
	mmtrMaterialCache = dict()
	
	updatedFileCount = 0
	
	for mdfCollection in mdfList:
		print(f"Checking {mdfCollection.name}")
		requiresUpdate = False
		materialList = [obj for obj in mdfCollection.all_objects if obj.get("~TYPE") == "RE_MDF_MATERIAL"]
		for materialObj in materialList:
			matData = materialObj.re_mdf_material
			mmtrHash = str(hashUTF8(matData.mmtrPath.lower()))
			
			if mmtrHash not in mmtrMaterialCache:
				
				if mmtrHash in materialCompendium:
					compendiumEntry = materialCompendium[mmtrHash]
					#print(materialCompendium[mmtrHash])
					samplePath = os.path.join(chunkPath,compendiumEntry["mdfPath"].replace("/",os.sep)+f".{mdfVersion}")
					sampleMaterial = getMaterialByHash(samplePath, compendiumEntry["matNameHash"])
					mmtrMaterialCache[mmtrHash] = sampleMaterial
				else:
					print(f"MMTR path {matData.mmtrPath} not in compendium, can't update {materialObj.name}")
					sampleMaterial = None
			else:
				sampleMaterial = mmtrMaterialCache[mmtrHash]
				if sampleMaterial != None:
					
					#Properties
					
					newPropNameSet = set([item.propName for item in sampleMaterial.propertyList])
					#print(newPropNameSet)
			        
			        
					oldPropNameSet = set([item.prop_name for item in matData.propertyList_items])
					#print(oldPropNameSet)
			        
					addedPropDifference = newPropNameSet.difference(oldPropNameSet)
					if len(addedPropDifference) != 0:
						requiresUpdate = True
						print(f"Added properties in {materialObj.name}:")
						for propName in addedPropDifference:
							for prop in sampleMaterial.propertyList:
								if prop.propName == propName:
									newProp = matData.propertyList_items.add()
									newProp.prop_name = propName
									newProp.padding = prop.padding
									lowerPropName = prop.propName.lower()
									if  (prop.paramCount == 4 and ("color" in lowerPropName or "_col_" in lowerPropName) and "rate" not in lowerPropName):
										newProp.data_type = "COLOR"
										newProp.color_value = prop.propValue
									elif prop.paramCount == 1 and ("Use" in prop.propName or "_or_" in prop.propName or prop.propName.startswith("is")):
										newProp.data_type = "BOOL"
										newProp.bool_value = bool(prop.propValue[0])
									elif prop.paramCount > 1:
										newProp.data_type = "VEC4"
										newProp.float_vector_value = tuple(prop.propValue)
									else:
										newProp.data_type = "FLOAT"
										newProp.float_value = float(prop.propValue[0])

						print(addedPropDifference)
					removedPropDifference = oldPropNameSet.difference(newPropNameSet)
					if len(removedPropDifference) != 0:
						requiresUpdate = True
						indicesRemovalList = []
						
						for index, prop in enumerate(matData.propertyList_items):
							if prop.prop_name in removedPropDifference:
								indicesRemovalList.append(index)
						
						for index in reversed(sorted(indicesRemovalList)):
							matData.propertyList_items.remove(index)
						print(f"Removed properties in {materialObj.name}")
						print(removedPropDifference)
						
					#Texture Bindings
					
					newBindingNameSet = set([item.textureType for item in sampleMaterial.textureList])
					#print(newPropNameSet)
			        
			        
					oldBindingNameSet = set([item.textureType for item in matData.textureBindingList_items])
					#print(oldPropNameSet)
			        
					addedBindingDifference = newBindingNameSet.difference(oldBindingNameSet)
					if len(addedBindingDifference) != 0:
						requiresUpdate = True
						print(f"Added texture bindings in {materialObj.name} material:")
						for textureType in addedBindingDifference:
							for binding in sampleMaterial.textureList:
								if binding.textureType == textureType:
									newBinding = matData.textureBindingList_items.add()
									newBinding.textureType = textureType
									newBinding.path = binding.texturePath
						print(addedBindingDifference)
					removedBindingDifference = oldBindingNameSet.difference(newBindingNameSet)
					if len(removedBindingDifference) != 0:
						requiresUpdate = True
						indicesRemovalList = []
						
						for index, binding in enumerate(matData.textureBindingList_items):
							if binding.textureType in removedBindingDifference:
								indicesRemovalList.append(index)
						
						for index in reversed(sorted(indicesRemovalList)):
							matData.textureBindingList_items.remove(index)
						print(f"Removed texture bindings in {materialObj.name}")
						print(removedBindingDifference)
					
				else:
					print(f"Sample material for {matData.mmtrPath} missing.")
					print(mmtrHash)
		if requiresUpdate:
			updatedFileCount += 1
			print("Update completed.")
		else:
			print("No update required.")
			
					#print(samplePath)
		#print(mdfPath)
	return updatedFileCount