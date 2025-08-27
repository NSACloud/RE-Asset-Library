#Author: NSA Cloud

import bpy
import os


from ..gen_functions import splitNativesPath,raiseWarning
from ..blender_utils import showErrorMessageBox



RE_MESH_EDITOR_PREFERENCES_NAME = None

def findREMeshEditorAddon():
	global RE_MESH_EDITOR_PREFERENCES_NAME
	if RE_MESH_EDITOR_PREFERENCES_NAME == None:
		if hasattr(bpy.types, "OBJECT_PT_mdf_tools_panel"):
			#print("RE Mesh Editor is installed")
			for addon in bpy.context.preferences.addons:
				#print(addon)
				if "RE-Mesh-Editor" in addon.module:
					RE_MESH_EDITOR_PREFERENCES_NAME = addon.module
					break
	return RE_MESH_EDITOR_PREFERENCES_NAME
def getChunkPathList(gameName):
	chunkPathList = []
	meshEditorPreferencesName = findREMeshEditorAddon()
	if meshEditorPreferencesName:
		ADDON_PREFERENCES = bpy.context.preferences.addons[meshEditorPreferencesName].preferences
		#print(gameName)
		chunkPathList = [bpy.path.abspath(item.path) for item in ADDON_PREFERENCES.chunkPathList_items if item.gameName == gameName ]
		#print(chunkPathList)
	return chunkPathList

def addChunkPath(chunkPath,gameName):
	meshEditorPreferencesName = findREMeshEditorAddon()
	
	if meshEditorPreferencesName == None:
		raise Exception("RE Mesh Editor is not installed. It is required for RE Asset Library to function. Install it.")
		
	ADDON_PREFERENCES = bpy.context.preferences.addons[meshEditorPreferencesName].preferences
	foundExisting = False
	for item in ADDON_PREFERENCES.chunkPathList_items:
		if item.gameName == gameName and item.path == chunkPath:
			foundExisting = True
			break
		
	if not foundExisting:
		item = ADDON_PREFERENCES.chunkPathList_items.add()
		item.gameName = gameName
		item.path = chunkPath
		print(f"Saved chunk path for {gameName}: {chunkPath}")
		bpy.ops.wm.save_userpref()
	
def importREMeshAsset(obj,meshPath,assetPreferences):
	print(f"RE Asset Library - Attemping import of {obj.name}")
	print("Game Name: "+str(obj.get("~GAME")))
	
	if meshPath != None:
		#objMatrix = obj.matrix_world
		
		split = os.path.split(meshPath)
		lastImportedCollection = bpy.context.scene.get("REMeshLastImportedCollection")
		if assetPreferences.showMeshImportOptions:
			meshEditorPreferencesName = findREMeshEditorAddon()
			if meshEditorPreferencesName:
				meshEditorPreferences = bpy.context.preferences.addons[meshEditorPreferencesName].preferences
				
				originalSetting = meshEditorPreferences.dragDropImportOptions
				meshEditorPreferences.dragDropImportOptions = True
				bpy.ops.re_mesh.importfile("INVOKE_DEFAULT",directory=split[0], files=[{"name":split[1]}])
				meshEditorPreferences.dragDropImportOptions = originalSetting
				
			else:
				print("Mesh editor preferences not found. Can't import.")
		else:
			bpy.ops.re_mesh.importfile(directory=split[0], files=[{"name":split[1]}])
		
		
		#I didn't intend for this to move the objects but this actually ends up working out	
		#Blender moves all selected objects to the placed location on an asset import, meaning I can just use that to put meshes at it's placed position
		if assetPreferences.placeAtCursor:
			if bpy.context.scene.get("REMeshLastImportedCollection") != None and bpy.context.scene["REMeshLastImportedCollection"] != lastImportedCollection:
				if bpy.context.scene["REMeshLastImportedCollection"] in bpy.data.collections:
					meshCollection = bpy.data.collections[bpy.context.scene["REMeshLastImportedCollection"]]
					if len(meshCollection.all_objects) != 0:
						for meshObj in meshCollection.all_objects: 
							#activeObj = meshCollection.all_objects[0]
							meshObj.select_set(True)
							#bpy.context.view_layer.objects.active = activeObj
	else:
		showErrorMessageBox(obj.get("assetPath",obj.name)+" - File not found at any chunk paths")


def importREChainAsset(obj,chainPath,assetPreferences):
	print(f"RE Asset Library - Attemping import of {obj.name}")
	if chainPath != None:
		if hasattr(bpy.types, "OBJECT_PT_chain_object_mode_panel"):
			armatureDataName = ""
			split = os.path.split(chainPath)
			meshCollectionName = split[1].split(".chain")[0]+".mesh"
			#print(meshCollectionName)
			if meshCollectionName in bpy.data.collections:
				for obj in bpy.data.collections[meshCollectionName].all_objects:
					if obj.type == "ARMATURE":
						armatureDataName = obj.data.name
						break
			bpy.ops.re_chain.importfile("INVOKE_DEFAULT",filepath = chainPath,directory=split[0], files=[{"name":split[1]}],targetArmature = armatureDataName)
		else:
			showErrorMessageBox("RE Chain Editor is not installed. Chain files can't be imported.")	
	else:
		showErrorMessageBox(obj.get("assetPath",obj.name)+" - File not found at any chunk paths")
def importREChain2Asset(obj,chainPath,assetPreferences):
	print(f"RE Asset Library - Attemping import of {obj.name}")
	
	if chainPath != None:
		if hasattr(bpy.types, "OBJECT_PT_chain_object_mode_panel"):
			armatureDataName = ""
			split = os.path.split(chainPath)
			meshCollectionName = split[1].split(".chain")[0]+".mesh"
			#print(meshCollectionName)
			if meshCollectionName in bpy.data.collections:
				for obj in bpy.data.collections[meshCollectionName].all_objects:
					if obj.type == "ARMATURE":
						armatureDataName = obj.data.name
						break
			bpy.ops.re_chain2.importfile("INVOKE_DEFAULT",filepath = chainPath,directory=split[0], files=[{"name":split[1]}],targetArmature = armatureDataName)
		else:
			showErrorMessageBox("RE Chain Editor is not installed. Chain files can't be imported.")
			
	else:
		showErrorMessageBox(obj.get("assetPath",obj.name)+" - File not found at any chunk paths")
		
def importREFBXSkelAsset(obj,fbxSkelPath,assetPreferences):
	print(f"RE Asset Library - Attemping import of {obj.name}")
	print("Game Name: "+str(obj.get("~GAME")))
	
	if fbxSkelPath != None:
		#objMatrix = obj.matrix_world
		
		split = os.path.split(fbxSkelPath)
		bpy.ops.re_fbxskel.importfile(filepath = fbxSkelPath,directory=split[0], files=[{"name":split[1]}])
	else:
		showErrorMessageBox(obj.get("assetPath",obj.name)+" - File not found at any chunk paths")					
				