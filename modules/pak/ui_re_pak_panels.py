#Author: NSA Cloud
import bpy

from bpy.types import (Panel,
					   Menu,
					   Operator,
					   PropertyGroup,
					   )

class OBJECT_PT_ExtractGameFilesPanel(Panel):
	bl_label = "Extract Game Files"
	bl_idname = "OBJECT_PT_re_pak_panel"
	bl_space_type = "VIEW_3D"   
	bl_region_type = "UI"
	bl_category = "RE Assets"
	bl_context = "objectmode"

	@classmethod
	def poll(self,context):
		return context is not None and context.scene.get("isREAssetLibrary")

	def draw(self, context):
		scene = context.scene
		#re_chain_toolpanel = scene.re_chain_toolpanel
		layout = self.layout
		layout.operator("re_asset.set_game_extract_paths",icon = "CURRENT_FILE")
		layout.operator("re_asset.extract_game_files",icon = "DOCUMENTS")
		layout.operator("re_asset.open_chunk_extract_folder",icon = "FOLDER_REDIRECT")
		layout.operator("re_asset.reload_pak_cache",icon = "FILE_REFRESH")
		
		
		
		
		