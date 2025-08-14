#Author: NSA Cloud
import bpy
import os

from bpy.types import Operator

from ..blender_utils import showMessageBox
from .re_mdf_updater_utils import batchUpdateMDFFiles,batchUpdateMDFCollections


def getCompendiumAssetLibraryItems():
	libEntryList = []
	for lib in bpy.context.preferences.filepaths.asset_libraries:
		if lib.name.startswith("RE Assets - "):
			gameName = lib.name.split("RE Assets - ")[1]
			compendiumPath = os.path.join(bpy.path.abspath(lib.path),f"MaterialCompendium_{gameName}.json")
			if os.path.isfile(compendiumPath):
				libEntryList.append((compendiumPath,gameName,""))
	return libEntryList

class WM_OT_BatchMDFUpdater(Operator):
	bl_label = "Batch MDF Updater"
	bl_idname = "re_asset.batch_mdf_updater"
	bl_description = "Updates all .mdf2 (material) files in the chosen directory using the newest MDF files from the pak files"
	bl_options = {'INTERNAL'}
	
	assetLib: bpy.props.EnumProperty(
		name="Game",
		description="Choose which game to update MDF files for. This is only supported for asset libraries that have support for this feature",
		items=getCompendiumAssetLibraryItems()
		)
	
	dirPath : bpy.props.StringProperty(
	   name = "Mod Directory",
	   description = "Choose the folder containing your mod's MDF files.",
	   default = "",
	   subtype = "DIR_PATH",)

	searchSubdirectories : bpy.props.BoolProperty(
	   name = "Search Subdirectories",
	   description = "Search all directories inside the chosen directory for MDF files to update.",
	   default = True,
	   )
	createBackups : bpy.props.BoolProperty(
	   name = "Create MDF Backups",
	   description = "If an MDF file is updated, create a copy of the original file with .bak on the end of it.",
	   default = True,
	   )
	
	def execute(self, context):
		
		
		modDirectory = bpy.path.abspath(self.dirPath)
		if os.path.isdir(modDirectory) and self.assetLib != "":
			try: 
				bpy.ops.wm.console_toggle()
			except:
				 pass
			updateCount = batchUpdateMDFFiles(modDirectory=modDirectory,compendiumPath=self.assetLib,searchSubdirectories = self.searchSubdirectories,createBackups = self.createBackups)
			try: 
				bpy.ops.wm.console_toggle()
			except:
				 pass
			showMessageBox(f"Updated {updateCount} MDF files.",title="MDF Updater")
			self.report({"INFO"},"Finished updating MDF files.")
		else:
			showMessageBox(f"An asset library with MDF updater support must be chosen and a mod directory must be set.",title="MDF Updater")
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
		return context.window_manager.invoke_props_dialog(self,width = 500,confirm_text = "Update MDF Files")

	
	def draw(self,context):
		layout = self.layout
		if self.assetLib != "":
			layout.label(text="Update MDF files for the latest game version.")
			layout.prop(self,"assetLib")
			layout.prop(self,"dirPath")
			layout.prop(self,"searchSubdirectories")
			layout.prop(self,"createBackups")
		else:
			layout.label(text=f"No asset libraries that support this feature are installed.",icon = "ERROR")

class WM_OT_BlenderMDFUpdater(Operator):
	bl_label = "Blender MDF Updater"
	bl_idname = "re_asset.blender_mdf_updater"
	bl_description = "Updates all MDF collections loaded in the current blend file"
	bl_options = {'INTERNAL'}
	
	assetLib: bpy.props.EnumProperty(
		name="Game",
		description="Choose which game to update MDF files for. This is only supported for asset libraries that have support for this feature",
		items=getCompendiumAssetLibraryItems()
		)
	
	
	def execute(self, context):
		
		if self.assetLib != "":
			try: 
				bpy.ops.wm.console_toggle()
			except:
				 pass
			updateCount = batchUpdateMDFCollections(self.assetLib,bpy)
			try: 
				bpy.ops.wm.console_toggle()
			except:
				 pass
			showMessageBox(f"Updated {updateCount} MDF collections.",title="MDF Updater")
			self.report({"INFO"},"Finished updating MDF collections.")
		else:
			showMessageBox(f"An asset library with MDF updater support must be chosen.",title="MDF Updater")
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
		return context.window_manager.invoke_props_dialog(self,width = 500,confirm_text = "Update MDF Collections")

	
	def draw(self,context):
		layout = self.layout
		if self.assetLib != "":
			layout.label(text="Update MDF collections in Blender for the latest game version.")
			layout.prop(self,"assetLib")
		else:
			layout.label(f"No asset libraries that support this feature are installed.",icon = "ERROR")
			