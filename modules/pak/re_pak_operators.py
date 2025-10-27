#Author: NSA Cloud
import bpy
import os
import json
from pathlib import Path

from bpy.types import Operator,OperatorFileListElement
from bpy_extras.io_utils import ImportHelper
from ..blender_utils import showMessageBox
from ..asset.re_asset_utils import getFileCRC,loadREAssetCatalogFile,buildNativesPathFromCatalogEntry
from ..asset.blender_re_asset import addChunkPath
from ..asset.re_asset_operators import getAssetBlendPathFromAssetBrowser
from .re_pak_utils import loadGameInfo,scanForPakFiles,createPakCacheFile,extractPakMP,STREAMING_FILE_TYPE_SET,createPakPatch,extractModPak
from .re_pak_propertyGroups import ToggleStringPropertyGroup
from ..gen_functions import openFolder


class WM_OT_PromptSetExtractInfo(Operator):
	bl_label = "Set Up Automatic Game File Extraction"
	bl_idname = "re_asset.prompt_extract_info"
	bl_description = ""
	bl_options = {'INTERNAL'}
	
	libraryPath : bpy.props.StringProperty(
	   name = "Library Path",
	   description = "",
	   default = "",
	   options = {"HIDDEN"})
	
	def execute(self, context):
		bpy.ops.re_asset.set_game_extract_paths("INVOKE_DEFAULT",libraryPath = bpy.path.abspath(self.libraryPath))
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None
	
	def invoke(self, context, event):
		
		if self.libraryPath != "":
			return context.window_manager.invoke_props_dialog(self,width = 600,confirm_text = "Set Game Extract Paths")

	
	def draw(self,context):
		layout = self.layout
		if self.libraryPath != "":
			layout.label(text="The file was not found on your system.")
			layout.label(text=f"Would you like to set up automatic game file extraction?")


def update_exePath(self, context):
	if "DevilMayCry5.exe" in self.exePath:
		self.platform = "x64"
	
	if self.exePath.endswith(".exe"):
		try:
			self.extractPath = os.path.split(bpy.path.abspath(self.exePath))[0]
		except:
			pass
class WM_OT_SetExtractInfo(Operator):
	bl_label = "Set Game Extract Paths"
	bl_idname = "re_asset.set_game_extract_paths"
	bl_description = "Set the path of the main .exe for the game and the location you want to extract files to.\nThis is required for extracting game files"
	bl_options = {'INTERNAL'}
	
	
	libraryPath : bpy.props.StringProperty(
	   name = "Library Path",
	   description = "",
	   default = "",
	   options = {"HIDDEN"})
	exePath : bpy.props.StringProperty(
	   name = "Game EXE Path",
	   description = "Set the path to the main executable file for the game. Example: MonsterHunterWilds.exe.\nYou can find where this file is located by right clicking the game in Steam > Browse Local Files.\nThis is used to determine where pak files are and when the game is updated.\nDo not set it to anything other than the game .exe or extracted files may be corrupted when you try to extract them after a game update",
	   default = "",
	   subtype = "FILE_PATH",
	   update = update_exePath,)
	extractPath : bpy.props.StringProperty(
	   name = "Extract Path",
	   description = "Set where you want to put extracted chunk files. By default it will be extracted to the game install folder",
	   subtype = "DIR_PATH")
	
	platform: bpy.props.EnumProperty(
		name="Platform",
		description="Set where you downloaded the game from. This is used to determine the path needed to extract files",
		items=[("x64", "Steam (Older Titles)", "(x64) Choose this option for DMC5 and the non ray tracing versions of RE2 and RE3. (Before 2021)"),
			   ("STM", "Steam", "(STM) Choose this option for all newer titles. (2021 or newer)"),
			   ("MSG", "Game Pass", "(MSG) Choose this option if you own the Microsoft Game Pass version of the game."),
			   ]
		,default = "STM"
		)
	def execute(self, context):
		#Make absolutely sure it can't be set wrong
		wrongEXESet = set(["CrashReport.exe","InstallerMessage.exe","pathdumper.exe"])
		
		libPath = bpy.path.abspath(self.libraryPath)
		
		exePath = None
		dirPath = None
		if os.path.isfile(libPath) and "REAssetLibrary_" in libPath and libPath.endswith(".blend"):
			gameName = os.path.split(libPath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
			libDir = os.path.split(libPath)[0]
			if os.path.isfile(bpy.path.abspath(self.exePath)):
				if os.path.split(self.exePath)[1] not in wrongEXESet:
					
					exePath = os.path.realpath(bpy.path.abspath(self.exePath))
					print(f"EXE Path:{exePath}")
					
				
			try:
				newDirPath = os.path.realpath(os.path.join(bpy.path.abspath(self.extractPath),f"{gameName}_EXTRACT","re_chunk_000"))
				print(f"Extract Path:{newDirPath}")
				os.makedirs(newDirPath,exist_ok = True)
				if os.path.isdir(newDirPath):
					dirPath = newDirPath
			except Exception as err:
				print(str(err))
			
			if exePath != None and dirPath != None:
				extractInfoDict = dict()
				extractInfoDict["exePath"] = exePath
				extractInfoDict["exeDate"] = os.path.getmtime(exePath)
				extractInfoDict["exeCRC"] = getFileCRC(exePath)
				extractInfoDict["extractPath"] = newDirPath
				extractInfoDict["platform"] = self.platform
				
				try: 
					bpy.ops.wm.console_toggle()
				except:
					 pass
				
				print(f"Setting up {gameName} extraction. This may take a second.")
				
				
				try: 
					bpy.ops.wm.console_toggle()
				except:
					pass
				print("Scanning for pak files...")
				pakPriorityList = scanForPakFiles(os.path.split(exePath)[0])
				if len(pakPriorityList) != 0:
					pakPriorityList.reverse()#Reverse the list so that the newest paths are cached first
					pakCachePath = os.path.join(libDir,f"PakCache_{gameName}.pakcache")
					createPakCacheFile(pakPriorityList,pakCachePath)
					extractInfoPath = os.path.join(libDir,f"ExtractInfo_{gameName}.json")
					with open(extractInfoPath,"w", encoding ="utf-8") as outFile:
						json.dump(extractInfoDict,outFile)
						print(f"Wrote {os.path.split(extractInfoPath)[1]}")
					
					
					addChunkPath(chunkPath=os.path.join(newDirPath,"natives",self.platform),gameName = gameName)
					
					showMessageBox("Game extraction set up completed.")
					
				else:
					print("No pak files were found in game directory. Cannot continue.")
				self.report({"INFO"},"Set game extract paths.")
			else:
				self.report({"ERROR"},"EXE or extract path is invalid.")
			
		else:
			self.report({"ERROR"},"Invalid library path. Could not set extract paths.")
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None
	def invoke(self,context,event):
		if self.libraryPath == "":
			if "REAssetLibrary_" in os.path.split(bpy.context.blend_data.filepath)[1]:#Set extract path from asset library blend file
				self.libraryPath = bpy.context.blend_data.filepath
			else:#Set extract path from asset browser dropdown menu
				blendPath = getAssetBlendPathFromAssetBrowser()
				if blendPath != None:
					self.libraryPath = blendPath
					
		#Pre fill fields if extract paths have been set before
		if self.libraryPath != "":
			libPath = bpy.path.abspath(self.libraryPath)
			libDir = os.path.split(libPath)[0]
			gameName = os.path.split(libPath)[1].split("REAssetLibrary_")[1].split(".blend")[0]
			extractInfoPath = os.path.join(libDir,f"ExtractInfo_{gameName}.json")
			if os.path.isfile(extractInfoPath):
				try:
					with open(extractInfoPath,"r", encoding ="utf-8") as file:
						extractInfo = json.load(file)
						try:
							self.exePath = extractInfo["exePath"]		
							path = Path(extractInfo["extractPath"])	
							parts = path.parts
							gameExtractIndex = parts.index(f"{gameName}_EXTRACT")
							self.extractPath = str(Path(*parts[:gameExtractIndex]))
						except:
							pass
						self.platform = extractInfo["platform"]
				except:
					raise Exception(f"Failed to load {extractInfoPath}")
		region = bpy.context.region
		centerX = region.width // 2
		centerY = region.height
		context.window.cursor_warp(centerX,centerY)
		return context.window_manager.invoke_props_dialog(self,width = 650)
	def draw(self,context):
		layout = self.layout
		layout.prop(self,"exePath")
		row = layout.row()
		
		if len(self.extractPath) > 70:
			row.alert = True
			row.prop(self,"extractPath")
			layout.label(text="Extract path is very long.",icon = "ERROR")
			layout.label(text="File paths may exceed the max length of 255 characters and fail to extract.")
			layout.label(text="Consider changing this to a shorter path such as C:\EXTRACT.")
		else:
			row.prop(self,"extractPath")
		layout.prop(self,"platform")
EXTRACT_WINDOW_SIZE = 750
SPLIT_FACTOR = .45


def update_checkAllCategories(self, context):
	if self.checkAllCategories == True:
		for item in self.categoryList_items:
			item.enabled = True
		self.checkAllCategories = False
def update_uncheckAllCategories(self, context):
	if self.uncheckAllCategories == True:
		for item in self.categoryList_items:
			item.enabled = False
		self.uncheckAllCategories = False

def update_checkAllPaks(self, context):
	if self.checkAllPaks == True:
		for item in self.pakList_items:
			item.enabled = True
		self.checkAllPaks = False
def update_uncheckAllPaks(self, context):
	if self.uncheckAllPaks == True:
		for item in self.pakList_items:
			item.enabled = False
		self.uncheckAllPaks = False


class WM_OT_ExtractGameFiles(Operator):
	bl_label = "Extract Game Files"
	bl_idname = "re_asset.extract_game_files"
	bl_description = "Choose which files to extract from the game's files. You must use the Set Game Extract Paths button first.\n\nNOTE: If you have mods installed using Fluffy Manager and archive invalidation is disabled in the options, uninstall any mods and verify game files on Steam.\n\nOtherwise any files that have been modified will not be extracted.\n\nUse the Reload Pak Cache button afterwards."
	bl_options = {'INTERNAL'}
	
	gameName : bpy.props.StringProperty(
	   name = "gameName",
	   description = "",
	   default = "",
	   options = {"HIDDEN"})
	
	outDir : bpy.props.StringProperty(
	   name = "outDir",
	   description = "",
	   default = "",
	   options = {"HIDDEN"})
	
	platform : bpy.props.StringProperty(
	   name = "platform",
	   description = "",
	   default = "",
	   options = {"HIDDEN"})
	gameDir : bpy.props.StringProperty(
	   name = "gameDir",
	   description = "",
	   default = "",
	   options = {"HIDDEN"})
	catalogPath : bpy.props.StringProperty(
	   name = "catalogPath",
	   description = "",
	   default = "",
	   options = {"HIDDEN"})
	gameInfoPath : bpy.props.StringProperty(
	   name = "catalogPath",
	   description = "",
	   default = "",
	   options = {"HIDDEN"})
	
	categoryList_items: bpy.props.CollectionProperty(type = ToggleStringPropertyGroup)
	categoryList_index: bpy.props.IntProperty(name="")
	
	pakList_items: bpy.props.CollectionProperty(type = ToggleStringPropertyGroup)
	pakList_index: bpy.props.IntProperty(name="")
	skipUnknowns : bpy.props.BoolProperty(
	   name = "Skip Unknowns",
	   description = "Skips files where the name is unknown.\nIf disabled, these files will be extracted to the re_chunk_000\\UNKNOWN folder as .bin files",
	   default = True)
	
	#Can't call operators to modify an operator's parameters, so had to get uh.. creative with it
	checkAllCategories : bpy.props.BoolProperty(
	   name = "Check All Categories",
	   description = "Select all categories to be extracted",
	   default = False,
	   update = update_checkAllCategories
	   )
	uncheckAllCategories : bpy.props.BoolProperty(
	   name = "Uncheck All Categories",
	   description = "Deselect all categories to be extracted",
	   default = False,
	   update = update_uncheckAllCategories
	   )
	
	checkAllPaks : bpy.props.BoolProperty(
	   name = "Check All Paks",
	   description = "Select all pak files to be extracted",
	   default = False,
	   update = update_checkAllPaks
	   )
	uncheckAllPaks : bpy.props.BoolProperty(
	   name = "Uncheck All Paks",
	   description = "Deselect all pak files to be extracted",
	   default = False,
	   update = update_uncheckAllPaks
	   )
	def execute(self, context):
		print("Processing selected paks and categories...")
		pakPathList = []
		checkedCategorySet = set()
		for item in self.pakList_items:
			if item.enabled:
				pakPathList.append(os.path.join(self.gameDir,item.path))
		
		for item in self.categoryList_items:
			if item.enabled:
				if item.path != "Uncategorized Files":
					checkedCategorySet.add(item.path)
				else:
					checkedCategorySet.add("")
				
		
		gameInfo = loadGameInfo(self.gameInfoPath)
		filePathList = []
		for row in [entry for entry in loadREAssetCatalogFile(self.catalogPath) if entry[2] in checkedCategorySet]:
			nativesPath = buildNativesPathFromCatalogEntry(row, gameInfo["fileVersionDict"].get(f"{os.path.splitext(row[0])[1][1::].upper()}_VERSION",999), self.platform)
			filePathList.append(nativesPath)
			#print(os.path.splitext(row[0])[1] in STREAMING_FILE_TYPE_SET)
			if os.path.splitext(row[0])[1] in STREAMING_FILE_TYPE_SET:
				#No need to verify if the path exists, that will be done when they're hashed
				streamingPath = nativesPath.replace(f"natives/{self.platform}/",f"natives/{self.platform}/streaming/")
				#print(streamingPath)
				filePathList.append(streamingPath)
		try: 
			bpy.ops.wm.console_toggle()
		except:
			 pass
		extractPakMP(filePathList, pakPathList, self.outDir)
		try: 
			bpy.ops.wm.console_toggle()
		except:
			 pass
		showMessageBox("Extracted game files.")
		self.report({"INFO"},"Extracted game files.")
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None
	
	def invoke(self, context, event):
		region = bpy.context.region
		centerX = region.width // 2
		centerY = region.height
		
		#currentX = event.mouse_region_X
		#currentY = event.mouse_region_Y
		
		
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
			
		print(f"Game Name:{gameName}")
		self.gameName = gameName
		extractInfoPath = os.path.join(blendDir,f"ExtractInfo_{gameName}.json")
		if os.path.isfile(extractInfoPath):
			try:
				with open(extractInfoPath,"r", encoding ="utf-8") as file:
					extractInfo = json.load(file)
					self.gameDir = os.path.split(extractInfo["exePath"])[0]
					self.outDir = extractInfo["extractPath"]
					self.platform = extractInfo["platform"]
					if os.path.isdir(self.gameDir):
						pakPriorityList = scanForPakFiles(self.gameDir)
					else:
						raise Exception(f"Game directory not found {self.gameDir}")
			except:
				raise Exception(f"Failed to load {extractInfoPath}")
			#TODO
			
		else:
			self.report({"ERROR"},"Extract paths are not set.")
			return {'CANCELLED'}
		
		self.gameInfoPath = os.path.join(blendDir,f"GameInfo_{gameName}.json")
		if not os.path.isfile(self.gameInfoPath):
			raise Exception(f"GameInfo_{self.gameName}.json is missing.")
		self.catalogPath = os.path.join(blendDir,f"REAssetCatalog_{gameName}.tsv")
		print(f"Catalog Path: {self.catalogPath}")
		if os.path.isfile(self.catalogPath):
			categoryList = {row[2] for row in loadREAssetCatalogFile(self.catalogPath)}#Get set of categories to remove duplicates
			#Sort list to put file type categories at the bottom
			fileTypeList = []
			for entry in categoryList:
				if " Files" in entry:
					fileTypeList.append(entry)
					
			for entry in fileTypeList:
				categoryList.remove(entry)
			
			categoryList = sorted(list(categoryList))
			categoryList.extend(sorted(fileTypeList))
			self.categoryList_items.clear()
			for entry in categoryList:
				item = self.categoryList_items.add()
				if entry == "":
					item.path = "Uncategorized Files"
				else:
					item.path = entry
			
			self.pakList_items.clear()
			for entry in pakPriorityList:
				newPath = os.path.relpath(entry,self.gameDir)#Start paths from game dir
				item = self.pakList_items.add()
				item.path = newPath
				
		else:
			self.report({"ERROR"},"Asset catalog missing.")
			return {'CANCELLED'}
		
		
		#Move cursor to center so extract window is at the center of the window
		context.window.cursor_warp(centerX,centerY)
	
		return context.window_manager.invoke_props_dialog(self,width = EXTRACT_WINDOW_SIZE,confirm_text = "Extract Game Files")

	
	def draw(self,context):
		layout = self.layout
		layout = self.layout
		rowCount = 8
		uifontscale = 9 * context.preferences.view.ui_scale
		max_label_width = int((EXTRACT_WINDOW_SIZE*(1-SPLIT_FACTOR)*(2-SPLIT_FACTOR)) // uifontscale)
		layout.label(text=f"Game: {self.gameName}")
		split = layout.split(factor = SPLIT_FACTOR)#Indent list slightly to make it more clear it's a part of a sub panel
		col1 = split.column()
		col2 = split.column()
		row = col1.row()
		col1_1 = row.column()
		col1_2 = row.row()
		col1_2.alignment = "RIGHT"
		col1_1.label(text = f"Category Count: {str(len(self.categoryList_items))}")
		col1_2.prop(self,"checkAllCategories",icon="CHECKMARK", icon_only=True)
		col1_2.prop(self,"uncheckAllCategories",icon="X", icon_only=True)
		col1.template_list(
			listtype_name = "ASSET_UL_StringCheckList", 
			list_id = "categoryList",
			dataptr = self,
			propname = "categoryList_items",
			active_dataptr = self, 
			active_propname = "categoryList_index",
			rows = rowCount,
			type='DEFAULT'
			)
		row = col2.row()
		col2_1 = row.column()
		col2_2 = row.row()
		col2_2.alignment = "RIGHT"
		col2_1.label(text = f"Pak Count: {str(len(self.pakList_items))}")
		col2_2.prop(self,"checkAllPaks",icon="CHECKMARK", icon_only=True)
		col2_2.prop(self,"uncheckAllPaks",icon="X", icon_only=True)
		col2.template_list(
			listtype_name = "ASSET_UL_StringCheckList", 
			list_id = "pakList",
			dataptr = self,
			propname = "pakList_items",
			active_dataptr = self, 
			active_propname = "pakList_index",
			rows = rowCount,
			type='DEFAULT'
			)
		
		layout.separator()
		layout.prop(self,"skipUnknowns")
class WM_OT_OpenExtractFolder(Operator):
	bl_label = "Open Extract Folder"
	bl_description = "Opens the folder extracted game files are saved to."
	bl_idname = "re_asset.open_chunk_extract_folder"

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
		print(f"Game Name:{gameName}")
		extractInfoPath = os.path.join(blendDir,f"ExtractInfo_{gameName}.json")
		if os.path.isfile(extractInfoPath):
			try:
				with open(extractInfoPath,"r", encoding ="utf-8") as file:
					extractInfo = json.load(file)
					extractDir = extractInfo["extractPath"]
					if os.path.isdir(extractDir):
						try:
							os.startfile(extractDir)
						except:
							pass
						
			except:
				raise Exception(f"Failed to load {extractInfoPath}")
			#TODO
			
		else:
			self.report({"ERROR"},"Game files are not extracted.")
		return {'FINISHED'}
	
class WM_OT_ReloadPakCache(Operator):
	bl_label = "Reload Pak Cache"
	bl_description = "Manually rescan all pak files.\nThis is usually done automatically after a change to the game .exe file is detected.\nNOTE: Using Fluffy Manager with archive invalidation enabled in the options will prevent any modified files from being extracted.\nUse this option after uninstalling all Fluffy Manager mods and verifying game files on Steam."
	bl_idname = "re_asset.reload_pak_cache"

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
		print(f"Game Name:{gameName}")
		extractInfoPath = os.path.join(blendDir,f"ExtractInfo_{gameName}.json")
		if os.path.isfile(extractInfoPath):
			try:
				with open(extractInfoPath,"r", encoding ="utf-8") as file:
					extractInfo = json.load(file)
					exePath = extractInfo["exePath"]
					if os.path.isfile(exePath):
						gameDir = os.path.split(exePath)[0]
						pakPriorityList = scanForPakFiles(gameDir)
						if len(pakPriorityList) != 0:
							pakPriorityList.reverse()#Reverse the list so that the newest paths are cached first
							pakCachePath = os.path.join(blendDir,f"PakCache_{gameName}.pakcache")
							createPakCacheFile(pakPriorityList,pakCachePath)
							self.report({"INFO"},"Reloaded cached pak info.")
						else:
							self.report({"ERROR"},"No pak files found in game directory.")
						
						
			except:
				raise Exception(f"Failed to load {extractInfoPath}")
			
		else:
			self.report({"ERROR"},"Game file extraction is not set up.")
		return {'FINISHED'}
def update_pakDir(self, context):
	if os.path.isdir(bpy.path.abspath(self.pakDir)):
		try:
			absPakDir = bpy.path.abspath(self.pakDir)
			outDir = os.path.dirname(os.path.normpath(absPakDir))
			#print(absPakDir)
			#print(outDir)
			if outDir == absPakDir:
				outDir = os.path.dirname(outDir)
			#print(f"pakDirName:{os.path.basename(os.path.normpath(absPakDir))}")
			self.outPath = os.path.join(outDir,os.path.basename(os.path.normpath(absPakDir))+".pak")
		except:
			pass
class WM_OT_CreatePakPatch(Operator):
	bl_label = "Create Pak Patch"
	bl_idname = "re_asset.create_pak_patch"
	bl_description = "Create a pak patch from a selected directory. The natives folder must be inside the selected directory.\nRequired for textures to work in MH Wilds. (May change in the future)\nInstall using Fluffy Manager."
	bl_options = {'REGISTER'}
	
	
	pakDir : bpy.props.StringProperty(
	   name = "Mod Directory",
	   description = "Set the folder containing the natives folder for your mod",
	   subtype = "DIR_PATH",
	   update = update_pakDir)
	
	outPath : bpy.props.StringProperty(
	   name = "Pak Output Path",
	   description = "Set the path where you want the patch pak to saved",
	   subtype = "FILE_PATH",
   )
	def execute(self, context):
		
		pakDir = bpy.path.abspath(self.pakDir)
		
		outPath = bpy.path.abspath(self.outPath)
		
		if os.path.isdir(pakDir) and outPath.endswith(".pak"):
			try:
				try: 
					bpy.ops.wm.console_toggle()
				except:
					 pass
				createPakPatch(pakDir,outPath)
			except:
				self.report({"ERROR"},"Failed to create patch pak. See Window > Toggle System Console")
			try: 
				bpy.ops.wm.console_toggle()
			except:
				 pass
			if os.path.isfile(outPath):
				try:
					os.startfile(os.path.split(outPath)[0])
				except:
					pass
				bpy.context.scene["lastExportedPatchPak"] = outPath
				self.report({"INFO"},"Created pak patch.")
			else:
				self.report({"ERROR"},"Failed to create patch pak. See Window > Toggle System Console")
		else:
			self.report({"ERROR"},"Mod directory or output pak path is invalid.")
			
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None
	def invoke(self,context,event):
		if self.outPath == "":
			if "lastExportedPatchPak" in bpy.context.scene:
				self.outPath = bpy.context.scene["lastExportedPatchPak"]
				if self.pakDir == "" and "natives" in bpy.context.scene.re_mdf_toolpanel.modDirectory:
					self.pakDir = os.path.dirname(os.path.dirname(os.path.dirname(bpy.path.abspath(bpy.context.scene.re_mdf_toolpanel.modDirectory))))
			else:
				if hasattr(bpy.types, "OBJECT_PT_mdf_tools_panel"):
					print(f"Found mod directory:{bpy.context.scene.re_mdf_toolpanel.modDirectory}")
					try:
						if "natives" in bpy.context.scene.re_mdf_toolpanel.modDirectory:
							self.pakDir = os.path.dirname(os.path.dirname(os.path.dirname(bpy.path.abspath(bpy.context.scene.re_mdf_toolpanel.modDirectory))))
							print(f"Set pak dir:{self.pakDir}")
					except:
						pass
		region = bpy.context.region
		centerX = region.width // 2
		centerY = region.height
		context.window.cursor_warp(centerX,centerY)
		return context.window_manager.invoke_props_dialog(self,width = 650)
	def draw(self,context):
		layout = self.layout
		layout.prop(self,"pakDir")
		layout.prop(self,"outPath")
def getAssetLibraryItems():
	libEntryList = []
	for lib in bpy.context.preferences.filepaths.asset_libraries:
		if lib.name.startswith("RE Assets - "):
			gameName = lib.name.split("RE Assets - ")[1]
			gameInfoPath = os.path.join(bpy.path.abspath(lib.path),f"GameInfo_{gameName}.json")
			if os.path.isfile(gameInfoPath):
				libEntryList.append((bpy.path.abspath(lib.path),gameName,""))
	return libEntryList
class WM_OT_UnpackModPak(bpy.types.Operator, ImportHelper):
	'''Unpack Mod Pak File'''
	bl_idname = "re_asset.unpack_mod_pak"
	bl_label = "Extract Mod Pak"
	bl_options = {'PRESET', "REGISTER", "UNDO"}
	files : bpy.props.CollectionProperty(
			name="File Path",
			type=OperatorFileListElement,
			)
	directory : bpy.props.StringProperty(
			subtype='DIR_PATH',
			options={'SKIP_SAVE'}
			)
	assetLib: bpy.props.EnumProperty(
		name="Game",
		description="Choose which game to extract the pak file for. The corresponding asset library for the game must be installed and set up for extracting files.",
		items=getAssetLibraryItems()
		)
	looseFilesPath : bpy.props.StringProperty(
			name = "",
			description = "(Optional) Pick a directory containing loose files to scan for additional file paths. All subdirectories will be searched.\nThis is intended to be used when a mod includes files outside of the pak file.\nTip: hold shift and right click a folder, then click \"Copy as path\" and paste it here.",
			#subtype='DIR_PATH',
			default = ""
			)
	outputPath : bpy.props.StringProperty(
			name = "",
			description = "(Optional) Pick directory to place extracted files.\nTip: hold shift and right click a folder, then click \"Copy as path\" and paste it here.\nIf unchanged, the pak will be extracted to whatever folder it's located in",
			#subtype='DIR_PATH',
			default = ""
			)
	filename_ext = ".pak"
	filter_glob: bpy.props.StringProperty(default="*.pak", options={'HIDDEN'})
	def draw(self, context):
		layout = self.layout
		layout.prop(self,"assetLib")
		layout.label(text = "Loose Files Directory (Optional)")
		layout.prop(self,"looseFilesPath")
		layout.label(text = "Output Directory (Optional)")
		layout.prop(self,"outputPath")
		layout.label(icon="ERROR",text = "Large pak files may be slow")
	def invoke(self, context, event):
		
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	def execute(self, context):
		libDir = bpy.path.abspath(self.assetLib)
		
		if self.looseFilesPath != "":
			looseFileDir = bpy.path.abspath(self.looseFilesPath.replace("\"",""))
		else:
			looseFileDir = ""
		if os.path.isdir(libDir) and libDir != "":
			gameName = os.path.split(libDir)[1]
			print(f"Game Name:{gameName}")
			try: 
				bpy.ops.wm.console_toggle()
			except:
				 pass
			for file in self.files:
				pakPath = os.path.join(self.directory,file.name)
				if self.outputPath != "":
					outPath = bpy.path.abspath(self.outputPath.replace("\"",""))
				else:
					outPath = os.path.splitext(pakPath)[0].replace("re_chunk_000","re_chunk_mod")+"_extract"#Rename to re_chunk_mod so the mesh editor doesn't pick it up as a chunk directory
				
				
				extractModPak(libDir,gameName,pakPath,outPath,looseFileDir)
				try:
					openFolder(outPath)
				except:
					pass
			try: 
				bpy.ops.wm.console_toggle()
			except:
				 pass
			
			self.report({"INFO"},"Finished pak extraction. Do not reupload any mod without the original author's permission!")
		else:
			showMessageBox(f"The asset library must be set to the game you're extracting from.",title="Unpack Mod Pak")
			return {'CANCELLED'}
		return {'FINISHED'}
	
class PAK_FH_drag_import(bpy.types.FileHandler):
	bl_idname = "PAK_FH_drag_import"
	bl_label = "File handler for RE Pak extraction"
	bl_import_operator = "re_asset.unpack_mod_pak"
	bl_file_extensions = ".pak;"
	
	@classmethod
	def poll_drop(cls, context):
		return (context.area and context.area.type == 'VIEW_3D')