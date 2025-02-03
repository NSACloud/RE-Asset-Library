bl_info = {
	"name": "RE Asset Library",
	"author": "NSA Cloud",
	"version": (0, 1),
	"blender": (4, 3, 0),
	"location": "Asset Browser > RE Assets",
	"description": "Quickly search through and import RE Engine meshes.",
	"warning": "Requires RE Mesh Editor",
	"wiki_url": "https://github.com/NSACloud/RE-Asset-Library",
	"tracker_url": "",
	"category": "Import-Export"}

import bpy
from . import addon_updater_ops

from bpy.app.handlers import persistent

import os
import json
import queue
import shutil
import subprocess

from .modules.gen_functions import formatByteSize
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty,PointerProperty
from bpy.types import Operator,AddonPreferences

from .modules.blender_re_asset import (
	importREMeshAsset,
	importREChainAsset,
	importREChain2Asset,
	)
from .modules.re_asset_operators import (
	getAssetLibrary,
	unzipLibrary,
	loadGameInfo,
	downloadREAssetLibDirectory,
	downloadFileContent,
	getFileCRC,
	download_file_from_google_drive,
	
	WM_OT_RenderREAssets,
	WM_OT_FetchREAssetThumbnails,
	WM_OT_ImportREAssetLibraryFromCatalog,
	WM_OT_SaveREAssetLibraryToCatalog,
	WM_OT_ExportCatalogDiff,
	WM_OT_ImportCatalogDiff,
	WM_OT_PackageREAssetLibrary,
	WM_OT_InitializeREAssetLibrary,
	WM_OT_CheckForREAssetLibraryUpdate,
	
	REToolListFileToREAssetCatalogAndGameInfo,

)
from .modules.re_asset_propertyGroups import (
	REAssetWhiteListEntryPropertyGroup,
	ASSET_UL_FileTypeWhiteList,
	REAssetLibEntryPropertyGroup,
	ASSET_UL_REAssetLibList,

)
from .modules.ui_re_asset_panels import (
	OBJECT_PT_REAssetLibraryPanel,
	)

class LIST_OT_NewWhiteListItem(Operator):
	bl_idname = "re_asset.new_whitelist_item"
	bl_label = "Add File Type"
	bl_description = "Add file type to whitelist.\nWhen creating a new asset library, choose which file types will be imported into the library.\nNOTE: Allowing too many file types may cause the asset browser to slow down."
	bl_options ={"INTERNAL"}
	def execute(self, context): 
		bpy.context.preferences.addons[__name__].preferences.fileTypeWhiteList_items.add() 
		return{'FINISHED'}

class LIST_OT_DeleteWhiteListItem(Operator):
	bl_idname = "re_asset.delete_whitelist_item"
	bl_label = "Remove File Type"
	bl_options ={"INTERNAL"}
	bl_description = "Remove file type from the whitelist"
	def execute(self, context): 
		whiteList = bpy.context.preferences.addons[__name__].preferences.fileTypeWhiteList_items
		index = bpy.context.preferences.addons[__name__].preferences.fileTypeWhiteList_index
		whiteList.remove(index)
		bpy.context.preferences.addons[__name__].preferences.fileTypeWhiteList_index = min(max(0, index - 1), len(whiteList) - 1)
		
		return{'FINISHED'}
	
class LIST_OT_ResetWhiteListItems(Operator):
	bl_idname = "re_asset.reset_whitelist_items"
	bl_label = "Reset to Default"
	bl_options ={"INTERNAL"}
	bl_description = "Resets the filetype whitelist to it's default values."
	def execute(self, context): 
		whiteList = bpy.context.preferences.addons[__name__].preferences.fileTypeWhiteList_items
		whiteList.clear()
		item = whiteList.add()
		item.fileType = "mesh"
		
		item = whiteList.add()
		item.fileType = "chain"
		
		item = whiteList.add()
		item.fileType = "chain2"
		return{'FINISHED'}
class REAssetPreferences(AddonPreferences):
	bl_idname = __name__
	# addon updater preferences
	assetLibraryPath: StringProperty(
		name="Asset Library Path",
		subtype='DIR_PATH',
		description = "Location to store downloaded/created RE Asset libraries",
		default = os.path.join(os.path.dirname(os.path.realpath(__file__)),"REAssetLibrary")
	)
	
	showMeshImportOptions : BoolProperty(
	   name = "Show Mesh Import Options",
	   description = "When dragging an RE Asset onto the 3D View, prompt with import options",
	   default = True)
	placeAtCursor : BoolProperty(
	   name = "Place At Cursor",
	   description = "When dragging an RE Asset, it will be imported at the location that it was dragged to.\nIf this is disabled, it will be imported at the world origin.\nNote that if you are creating mesh mods, do not check this option. Having objects not imported at the world origin may cause issues when exporting",
	   default = False)
	
	instanceDuplicates : BoolProperty(
	   name = "Instance Duplicates",
	   description = "If a mesh is imported more than once, create an instance of previously imported mesh.\nNOTE: The Create Collections import option must be enabled",
	   default = True)
	
	
	fileTypeWhiteList_items: bpy.props.CollectionProperty(type=REAssetWhiteListEntryPropertyGroup)
	fileTypeWhiteList_index: bpy.props.IntProperty(name="")
	
	auto_check_update: bpy.props.BoolProperty(
	    name = "Auto-check for Update",
	    description = "If enabled, auto-check for updates using an interval",
	    default = False,
	)
	
	updater_interval_months: bpy.props.IntProperty(
	    name='Months',
	    description = "Number of months between checking for updates",
	    default=0,
	    min=0
	)
	updater_interval_days: bpy.props.IntProperty(
	    name='Days',
	    description = "Number of days between checking for updates",
	    default=7,
	    min=0,
	)
	updater_interval_hours: bpy.props.IntProperty(
	    name='Hours',
	    description = "Number of hours between checking for updates",
	    default=0,
	    min=0,
	    max=23
	)
	updater_interval_minutes: bpy.props.IntProperty(
	    name='Minutes',
	    description = "Number of minutes between checking for updates",
	    default=0,
	    min=0,
	    max=59
	)
	def draw(self, context):
		layout = self.layout
		op = self.layout.operator(
        'wm.url_open',
        text='Donate on Ko-fi',
        icon='FUND'
        )
		op.url = 'https://ko-fi.com/nsacloud'
		
		layout.label(text="RE Asset Libraries")
		layout.prop(self,"assetLibraryPath")
		layout.operator("re_asset.open_re_asset_library_folder",icon = "FILE_FOLDER")
		layout.row()
		layout.operator("re_asset.download_re_asset_library",icon = "INTERNET")
		layout.operator("re_asset.detect_re_asset_library",icon = "FILE_REFRESH")
		layout.operator("re_asset.create_re_asset_library",icon = "NEWFOLDER")
		
		layout.row()
		layout.label(text="New Asset Library File Type Whitelist")
		layout.template_list("ASSET_UL_FileTypeWhiteList", "", self, "fileTypeWhiteList_items", self, "fileTypeWhiteList_index",rows = 4)
		row = layout.row()
		col = row.column()
		col.operator("re_asset.new_whitelist_item")
		col = row.column()
		col.operator("re_asset.delete_whitelist_item")
		layout.operator("re_asset.reset_whitelist_items")
		layout.label(text="Import Options")
		layout.prop(self,"showMeshImportOptions")
		layout.prop(self,"placeAtCursor")
		#layout.prop(self,"instanceDuplicates")
		addon_updater_ops.update_settings_ui(self,context)


class ImportREAssetLib(bpy.types.Operator, ImportHelper):
	'''Import RE Engine Asset Library (.reassetlib) File'''
	bl_idname = "re_asset.importlibrary"
	bl_label = "Import RE Asset Library (.reassetlib)"
	bl_options = {'PRESET', "REGISTER", "UNDO"}
	
	filename_ext = ".reassetlib"
	filter_glob: StringProperty(default="*.reassetlib", options = {"HIDDEN"})
	
	def execute(self, context):
		if os.path.isfile(self.filepath):
			assetLibraryDir = bpy.path.abspath(bpy.context.preferences.addons[__name__].preferences.assetLibraryPath)
			gameName = unzipLibrary(assetLibraryDir, self.filepath)
			if gameName != None:
				print(f"Attemping to install {gameName} library...")
				newLibraryDir = os.path.join(assetLibraryDir,gameName)
				os.makedirs(newLibraryDir,exist_ok=True)
				outputCatalogPath = os.path.join(newLibraryDir,f"REAssetCatalog_{gameName}.tsv")
				outputGameInfoPath = os.path.join(newLibraryDir,f"GameInfo_{gameName}.json")
				addonDir = os.path.split(__file__)[0]
				sourceBlendPath = os.path.join(addonDir,"Resources","Blend","libraryBase.blend")
				outputBlendPath = os.path.join(newLibraryDir,f"REAssetLibrary_{gameName}.blend")
				scriptPath = os.path.join(addonDir,"Resources","Scripts","initializeLibrary.py")
				
				if not os.path.isfile(outputBlendPath):
					shutil.copy(sourceBlendPath,outputBlendPath)
					
				if os.path.isfile(outputCatalogPath) and os.path.isfile(outputGameInfoPath) and os.path.isfile(outputBlendPath) and os.path.isfile(scriptPath):
					subprocess.Popen([bpy.app.binary_path, outputBlendPath, "--python", scriptPath])
				else:
					self.report({"ERROR"},"Missing files, cannot create library.")
					return {'CANCELLED'}
				return {"FINISHED"}
		self.report({"INFO"},"Failed to import RE Asset Library. See Window > Toggle System Console for details")
		return {"CANCELLED"}
	
def getAssetDirectoryItems(self,context):
	entryList = []
	for index,entry in enumerate(self.assetLibList_items):
		entryList.append((str(index),entry.displayName,""))
	return entryList
class WM_OT_DownloadREAssetLibrary(Operator):
	bl_label = "Download RE Asset Libraries"
	bl_description = "Download RE Asset Libaries"
	bl_idname = "re_asset.download_re_asset_library"
	bl_options = {'INTERNAL'}
	
		
	libraryListEntry: EnumProperty(
		name="RE Asset Library",
		description="Choose which asset library to download from the repository",
		items= getAssetDirectoryItems
		)
	assetLibList_items: bpy.props.CollectionProperty(type = REAssetLibEntryPropertyGroup)
	assetLibList_index: bpy.props.IntProperty(name="")
	def execute(self, context):
		if len(self.assetLibList_items) != 0:
			bpy.ops.wm.save_userpref()#Save preferences to prevent asset library path from being lost
			entry = self.assetLibList_items[int(self.libraryListEntry)]
			libraryDir = bpy.path.abspath(bpy.context.preferences.addons[__name__].preferences.assetLibraryPath)
			os.makedirs(libraryDir,exist_ok = True)
			outFilePath = os.path.join(libraryDir,f"{entry.gameName}.reassetlib")
			libCRC = int(entry.CRC)
			"""
			content = downloadFileContent(entry.URL)
			if content != None:
				with open(outFilePath,"wb") as outFile:
					outFile.write(content)
			"""
			for _,_ in download_file_from_google_drive(file_id=entry.URL,destination=outFilePath):
				pass
			if os.path.isfile(outFilePath):
				if libCRC == getFileCRC(outFilePath):
					print("CRC Check Passed")
					bpy.ops.re_asset.importlibrary(filepath = outFilePath)
					try:
						os.remove(outFilePath)
					except:
						pass
				else:
					print("CRC Check failed, aborting install.")
					self.report({"ERROR"},"CRC Check on the downloaded file failed. Try downloading the library again.")
				
		return {'FINISHED'}
		
	def invoke(self, context, event):
		self.assetLibList_items.clear()
		directoryDict = downloadREAssetLibDirectory()
		
		"""
		TESTPATH = r"D:\Modding\Monster Hunter Wilds\AssetLibrary\REAssetLib_directory.json"
		with open(TESTPATH,"r", encoding ="utf-8") as file:
			directoryDict = json.load(file)
		"""
		#directoryDict = None
		if directoryDict != None:
			#print(directoryDict)
			if directoryDict.get("libraryList"):
				libraryList = directoryDict.get("libraryList")
				for entry in libraryList:
					item = self.assetLibList_items.add()
					item.gameName = entry["gameName"]
					item.displayName = entry["displayName"]
					item.timestamp = entry["timestamp"]
					item.CRC = str(entry["CRC"])
					item.compressedSize = str(entry["compressedSize"])
					item.uncompressedSize = str(entry["uncompressedSize"])
					item.URL = entry["URL"]
			return context.window_manager.invoke_props_dialog(self,width = 400,confirm_text = "Download Asset Library")
		else:
			return context.window_manager.invoke_popup(self)

	def draw(self, context):
		layout = self.layout
		if len(self.assetLibList_items) != 0:
			layout.prop(self,"libraryListEntry")
		layout.separator()
		layout.label(text="Info")
		box = layout.box()
		if len(self.assetLibList_items) != 0:
			entry = self.assetLibList_items[int(self.libraryListEntry)]
			box.label(text = f"Library Name: {entry.gameName}")
			
			box.separator()
			box.label(text = f"Last Update: {entry.timestamp}")
			
			box.label(text = f"Download Size: {formatByteSize(int(entry.compressedSize))}")
			box.label(text = f"Installed Size: {formatByteSize(int(entry.uncompressedSize))}")
			
			layout.label(text="Blender will become unresponsive while downloading the library.",icon = "ERROR")
		else:
			box.label(text = "Failed to retrieve available asset libraries.")
			box.label(text = "Check your internet connection.")
class WM_OT_CreateNewREAssetLibrary(Operator):
	bl_label = "Create New RE Asset Library"
	bl_description = "Create a new asset library using an RETool .list file"
	bl_idname = "re_asset.create_re_asset_library"
	bl_options = {'INTERNAL'}
	gameName: EnumProperty(
		name="",
		description="Set which game to create the library for",
		items= [ 
		("DMC5", "Devil May Cry 5", ""),
		("RE2", "Resident Evil 2", ""),
		("RE3", "Resident Evil 3", ""),
		("RE8", "Resident Evil 8", ""),	
		("RE2RT", "Resident Evil 2 Ray Tracing", ""),
		("RE3RT", "Resident Evil 3 Ray Tracing", ""),
		("RE7RT", "Resident Evil 7 Ray Tracing", ""),
		("MHRSB", "Monster Hunter Rise", ""),
		("SF6", "Street Fighter 6", ""),
		("RE4", "Resident Evil 4", ""),
		("DD2", "Dragon's Dogma 2", ""),
		("KG", "Kunitsu-Gami", ""),
		("DR", "Dead Rising", ""),
		("MHWILDS", "Monster Hunter Wilds", ""),
		]
    )
	listPath: StringProperty(
		name="List Path",
		subtype='FILE_PATH',
		description = "Location of RE Tool .list file. Make sure to use the correct one for the game you set.\nIf you don't have a .list file, download one from the GitHub repo by pressing the Download List Files button below\nTip: You can shift right click the list file and click Copy as path, then paste it into this field",
		
	)
	def draw(self,context):
		layout = self.layout
		layout.prop(self,"gameName")
		layout.prop(self,"listPath")
		op = self.layout.operator(
        'wm.url_open',
        text='Download List Files',
        icon='TEXT'
        )
		
		op.url = 'https://github.com/Ekey/REE.PAK.Tool/tree/main/Projects'
		
	@classmethod
	def poll(self,context):
		return context is not None
	def execute(self, context):
		
		newListPath = self.listPath.replace("\"","")
		if os.path.isfile(newListPath):
			#if os.path.isdir(bpy.context.preferences.addons[__name__].preferences.assetLibraryPath):
				newLibraryDir = os.path.join(bpy.path.abspath(bpy.context.preferences.addons[__name__].preferences.assetLibraryPath),self.gameName)
				bpy.ops.wm.save_userpref()#Save preferences to prevent asset library path from being lost
				os.makedirs(newLibraryDir,exist_ok=True)
				outputCatalogPath = os.path.join(newLibraryDir,f"REAssetCatalog_{self.gameName}.tsv")
				outputGameInfoPath = os.path.join(newLibraryDir,f"GameInfo_{self.gameName}.json")
				addonDir = os.path.split(__file__)[0]
				sourceBlendPath = os.path.join(addonDir,"Resources","Blend","libraryBase.blend")
				outputBlendPath = os.path.join(newLibraryDir,f"REAssetLibrary_{self.gameName}.blend")
				scriptPath = os.path.join(addonDir,"Resources","Scripts","initializeLibrary.py")
				
				whiteListSet = set()
				for item in bpy.context.preferences.addons[__name__].preferences.fileTypeWhiteList_items:
					whiteListSet.add(item.fileType.lower())
				
				REToolListFileToREAssetCatalogAndGameInfo(newListPath, outputCatalogPath, outputGameInfoPath,list(whiteListSet))
				shutil.copy(sourceBlendPath,outputBlendPath)
				if os.path.isfile(outputCatalogPath) and os.path.isfile(outputGameInfoPath) and os.path.isfile(outputBlendPath) and os.path.isfile(scriptPath):
					subprocess.Popen([bpy.app.binary_path, outputBlendPath, "--python", scriptPath])
				else:
					self.report({"ERROR"},"Missing files, cannot create library.")
					return {'CANCELLED'}
					self.report({"INFO"},"Created new RE Asset Library.")
				return {'FINISHED'}
				self.report({"INFO"},"Created new RE Asset Library.")
			#else:
				#self.report({"ERROR"},"Invalid asset library path.")
		else:
			self.report({"ERROR"},"Invalid list path.")
		
		return {'FINISHED'}
	
	def invoke(self,context,event):
		return context.window_manager.invoke_props_dialog(self)
class WM_OT_DetectREAssetLibrary(Operator):
	bl_label = "Refresh RE Asset Libraries"
	bl_description = "Check for any libraries that are not listed and add them to the list."
	bl_idname = "re_asset.detect_re_asset_library"
	bl_options = {'INTERNAL'}
	
		
	@classmethod
	def poll(self,context):
		return context is not None
	def execute(self, context):
		assetLibraryPath = bpy.path.abspath(bpy.context.preferences.addons[__name__].preferences.assetLibraryPath)
		
		if not os.path.isdir(assetLibraryPath):
			self.report({"ERROR"},"Invalid RE asset library path.")
			return {'CANCELLED'}
		subDirectoryList = [ f.name for f in os.scandir(assetLibraryPath) if f.is_dir() ]
		for directory in subDirectoryList:
			if os.path.isfile(os.path.join(assetLibraryPath,directory,f"REAssetLibrary_{directory.upper()}.blend")):
				#Get existing library entry or make a new one
				libName = f"RE Assets - {directory.upper()}"
				library = getAssetLibrary(libName)
				library.name = libName
				library.path = os.path.join(assetLibraryPath,directory)
		for lib in bpy.context.preferences.filepaths.asset_libraries:#Remove any paths that don't exist
			if "RE Assets - " in lib.name and not os.path.isdir(lib.path):
				bpy.context.preferences.filepaths.asset_libraries.remove(lib)
		
		self.report({"INFO"},"Refreshed RE Asset Library list.")
		return {'FINISHED'}
	
class WM_OT_OpenREAssetLibraryFolder(Operator):
	bl_label = "Open RE Asset Library Folder"
	bl_description = "Opens the folder containing RE Asset Libraries in File Explorer"
	bl_idname = "re_asset.open_re_asset_library_folder"

	def execute(self, context):
		try:
			os.startfile(bpy.path.abspath(bpy.context.preferences.addons[__name__].preferences.assetLibraryPath))
		except:
			pass
		return {'FINISHED'}

class WM_OT_SetREAssetSettings(Operator):
	bl_label = "Configure RE Asset Settings"
	bl_description = "Configure settings for imported RE Asset Library assets"
	bl_idname = "re_asset_library.set_re_asset_settings"
	bl_context = "objectmode"
	bl_options = {'INTERNAL'}
	
	showMeshImportOptions : BoolProperty(
	   name = "Show Mesh Import Options",
	   description = "When dragging an RE Asset onto the 3D View, prompt with import options",
	   default = True)
	placeAtCursor : BoolProperty(
	   name = "Place At Cursor",
	   description = "When dragging an RE Asset, it will be imported at the location that it was dragged to.\nIf this is disabled, it will be imported at the world origin.\nNote that if you are creating mesh mods, do not check this option. Having objects not imported at the world origin may cause issues when exporting",
	   default = False)
	
	instanceDuplicates : BoolProperty(
	   name = "Instance Duplicates",
	   description = "If a mesh is imported more than once, create an instance of previously imported mesh.\nNOTE: The Create Collections import option must be enabled",
	   default = True)
	
	
	
	def draw(self,context):
		layout = self.layout
		layout.prop(self,"showMeshImportOptions")
		layout.prop(self,"placeAtCursor")
		#layout.prop(self,"instanceDuplicates")#TODO
		
	@classmethod
	def poll(self,context):
		return context is not None and context.scene is not None
	
	def invoke(self,context,event):
		preferences = bpy.context.preferences.addons[__name__].preferences
		self.showMeshImportOptions = preferences.showMeshImportOptions
		self.placeAtCursor = preferences.placeAtCursor
		self.instanceDuplicates = preferences.instanceDuplicates
		
		return context.window_manager.invoke_props_dialog(self)
	def execute(self, context):
		
		preferences = bpy.context.preferences.addons[__name__].preferences
		preferences.showMeshImportOptions = self.showMeshImportOptions
		preferences.placeAtCursor = self.placeAtCursor
		preferences.instanceDuplicates = self.instanceDuplicates
		
		self.report({"INFO"},"Set RE Asset settings.")
		return {'FINISHED'}
	
	def invoke(self,context,event):
		
		#self.OverrideDamping = 
		
		return context.window_manager.invoke_props_dialog(self)

def re_asset_settings_button(self, context):
    self.layout.operator(WM_OT_SetREAssetSettings.bl_idname,icon = "SETTINGS")


execution_queue = queue.Queue()

def run_in_main_thread(function):
    execution_queue.put(function)

def execute_queued_functions():
	#print("Queue Check Ran")
	while not execution_queue.empty():
		function = execution_queue.get()
		function()
	else:
		#print("Timer Stop")
		return None
	return 0.5

def deleteLastREAsset():
	#print("Delete function run")
	if bpy.context.scene.get("lastREAsset") and bpy.context.scene.get("lastREAsset") in bpy.data.objects:
		bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.get("lastREAsset")], do_unlink=True)#Remove asset placement object
		#print(bpy.context.scene.get("lastREAsset") +" Deleted")
		del bpy.context.scene["lastREAsset"]
@persistent
def REAssetPostHandler(lapp_context):
	gameInfoPath = None
	gameInfo = None
	
	if len(lapp_context.import_items) == 1:#Make sure it's an asset drag and drop
		item = lapp_context.import_items[0]
		if item.id.get("~TYPE") == "RE_ASSET_LIBRARY_ASSET":
			addonPreferences = bpy.context.preferences.addons[__name__].preferences
			gameInfoPath = os.path.join(os.path.split(item.source_library.filepath)[0],"GameInfo_"+item.id.get("~GAME","UNKN")+".json")
			#print(gameInfoPath)
			if os.path.isfile(gameInfoPath):
				gameInfo = loadGameInfo(gameInfoPath)
			else:
				print(f"RE Asset Library - Missing GameInfo:{gameInfoPath}")
			assetType = item.id.get("assetType","UNKN")
			bpy.context.scene["lastREAsset"] = item.id.name
			if gameInfo != None:
				match assetType:
					case "MESH":
						importREMeshAsset(item.id,gameInfo,addonPreferences)
					case "CHAIN":
						importREChainAsset(item.id,gameInfo,addonPreferences)
					case "CHAIN2":
						importREChain2Asset(item.id,gameInfo,addonPreferences)
					case _:
						print(f"RE Asset Library - Unsupported Asset Type, cannot import. {item.id.name} - {assetType} ")
						print("Make sure all RE addons are up to date.")
			
			if not bpy.app.timers.is_registered(execute_queued_functions()):
				bpy.app.timers.register(execute_queued_functions)
			
			#Run every .5 seconds until object is deleted after linking, can't do this in the post handler or blender will complain
			run_in_main_thread(deleteLastREAsset)
		
# Registration
classes = [
	REAssetWhiteListEntryPropertyGroup,
	ASSET_UL_FileTypeWhiteList,
	REAssetLibEntryPropertyGroup,
	ASSET_UL_REAssetLibList,
	LIST_OT_NewWhiteListItem,
	LIST_OT_DeleteWhiteListItem,
	LIST_OT_ResetWhiteListItems,
	REAssetPreferences,
	
	
	
	WM_OT_InitializeREAssetLibrary,
	WM_OT_DownloadREAssetLibrary,
	WM_OT_CreateNewREAssetLibrary,
	WM_OT_DetectREAssetLibrary,
	WM_OT_OpenREAssetLibraryFolder,
	WM_OT_CheckForREAssetLibraryUpdate,
	
	ImportREAssetLib,
	
	
	WM_OT_SetREAssetSettings,
	WM_OT_RenderREAssets,
	WM_OT_FetchREAssetThumbnails,
	WM_OT_ImportREAssetLibraryFromCatalog,
	WM_OT_SaveREAssetLibraryToCatalog,
	WM_OT_ExportCatalogDiff,
	WM_OT_ImportCatalogDiff,
	WM_OT_PackageREAssetLibrary,
	OBJECT_PT_REAssetLibraryPanel,
	]

def on_register():
	if len(bpy.context.preferences.addons[__name__].preferences.fileTypeWhiteList_items) == 0:
		bpy.ops.re_asset.reset_whitelist_items()
	bpy.ops.wm.save_userpref()#Save preferences on register, otherwise when a new blend file is opened, the addon might not be registered on the new instance.
def register():
	addon_updater_ops.register(bl_info)
	for classEntry in classes:
		bpy.utils.register_class(classEntry)
		
	bpy.types.ASSETBROWSER_MT_editor_menus.append(re_asset_settings_button)
	bpy.app.handlers.blend_import_post.append(REAssetPostHandler)
	bpy.app.timers.register(on_register, first_interval=.01)
	
	
def unregister():
	addon_updater_ops.unregister()
	for classEntry in classes:
		bpy.utils.unregister_class(classEntry)
	bpy.types.ASSETBROWSER_MT_editor_menus.remove(re_asset_settings_button)
	if REAssetPostHandler in bpy.app.handlers.blend_import_post:
		bpy.app.handlers.blend_import_post.remove(REAssetPostHandler)
if __name__ == '__main__':
	register()