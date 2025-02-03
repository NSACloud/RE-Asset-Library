import bpy

from bpy.types import (Panel,
					   Menu,
					   Operator,
					   PropertyGroup,
					   )

class OBJECT_PT_REAssetLibraryPanel(Panel):
	bl_label = "RE Asset Library Tools"
	bl_idname = "OBJECT_PT_re_asset_library_panel"
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
		layout.label(text = "Thumnbnail Tools")
		layout.operator("re_asset.render_re_asset_thumbnails", icon = "SCENE")
		layout.operator("re_asset.fetch_re_asset_thumbnails", icon = "RENDERLAYERS")
		layout.label(text = "Catalog Tools")
		layout.operator("re_asset.import_catalog",icon = "FILE_REFRESH")
		layout.operator("re_asset.save_to_catalog", icon = "FILE_TICK")
		layout.operator("re_asset.export_catalog_diff", icon = "INTERNET")
		#layout.operator("re_asset.import_catalog_diff", icon = "IMPORT")#TODO
		layout.operator("re_asset.check_for_library_update",icon="IMPORT")#Temp Testing
		layout.label(text = "Export Tools")
		layout.operator("re_asset.package_re_asset_library")
		