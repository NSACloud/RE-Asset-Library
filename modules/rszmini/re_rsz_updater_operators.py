#Author: NSA Cloud
import bpy
import os

from bpy.types import Operator

from ..blender_utils import showMessageBox
from .re_rsz_updater_utils import batchUpdateRSZFiles


def getCRCCompendiumAssetLibraryItems():
	libEntryList = []
	for lib in bpy.context.preferences.filepaths.asset_libraries:
		if lib.name.startswith("RE Assets - "):
			gameName = lib.name.split("RE Assets - ")[1]
			compendiumPath = os.path.join(bpy.path.abspath(lib.path),f"CRCCompendium_{gameName}.json")
			if os.path.isfile(compendiumPath):
				libEntryList.append((compendiumPath,gameName,""))
	return libEntryList

class WM_OT_BatchRSZUpdater(Operator):
	bl_label = "Batch RSZ CRC Updater"
	bl_idname = "re_asset.batch_rsz_updater"
	bl_description = "Updates outdated CRC values for .scn, .pfb and .user files.\nThis can allow for outdated RSZ files to work after an update, but certain files may not work if there have been structural changes"
	bl_options = {'INTERNAL'}
	
	assetLib: bpy.props.EnumProperty(
		name="Game",
		description="Choose which game to update MDF files for. This is only supported for asset libraries that have support for this feature",
		items=getCRCCompendiumAssetLibraryItems()
		)
	
	dirPath : bpy.props.StringProperty(
	   name = "Mod Directory",
	   description = "Choose the folder containing your mod's RSZ (scn/pfb/user) files.",
	   default = "",
	   subtype = "DIR_PATH",)

	searchSubdirectories : bpy.props.BoolProperty(
	   name = "Search Subdirectories",
	   description = "Search all directories inside the chosen directory for RSZ files to update.",
	   default = True,
	   )
	createBackups : bpy.props.BoolProperty(
	   name = "Create RSZ Backups",
	   description = "If an RSZ file is updated, create a copy of the original file with .bak on the end of it.",
	   default = True,
	   )
	
	def execute(self, context):
		
		
		modDirectory = bpy.path.abspath(self.dirPath)
		if os.path.isdir(modDirectory) and self.assetLib != "":
			gameName = os.path.split(self.assetLib)[1].split("CRCCompendium_")[1].split(".json")[0]
			libraryDir = os.path.dirname(self.assetLib)
			try: 
				bpy.ops.wm.console_toggle()
			except:
				 pass
			updateCount = batchUpdateRSZFiles(modDirectory=modDirectory,libraryDir = libraryDir,gameName = gameName,searchSubdirectories = self.searchSubdirectories,createBackups = self.createBackups)
			try: 
				bpy.ops.wm.console_toggle()
			except:
				 pass
			showMessageBox(f"Updated {updateCount} RSZ files.",title="RSZ Updater")
			self.report({"INFO"},"Finished updating RSZ files.")
		else:
			showMessageBox(f"An asset library with RSZ updater support must be chosen and a mod directory must be set.",title="RSZ Updater")
			return {'CANCELLED'}
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None
	
	def invoke(self, context, event):
		region = bpy.context.region
		centerX = region.width // 2
		centerY = region.height
		context.window.cursor_warp(centerX,centerY)
		if "modWorkspace_directory" in bpy.context.scene:
			self.dirPath = bpy.context.scene["modWorkspace_directory"]
		return context.window_manager.invoke_props_dialog(self,width = 500,confirm_text = "Update RSZ Files")

	
	def draw(self,context):
		layout = self.layout
		if self.assetLib != "":
			layout.label(icon = "ERROR",text="EXPERIMENTAL")
			layout.label(text="Update RSZ (scn,pfb,user) files for the latest game version.")
			layout.label(text="Note that this may not work if the file has had structural changes.")
			layout.label(text="Be sure to check that it's working properly in game.")
			layout.prop(self,"assetLib")
			layout.prop(self,"dirPath")
			layout.prop(self,"searchSubdirectories")
			layout.prop(self,"createBackups")
		else:
			layout.label(text=f"No asset libraries that support this feature are installed.",icon = "ERROR")