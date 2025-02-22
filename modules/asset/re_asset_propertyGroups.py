#Author: NSA Cloud
import bpy
from bpy.props import (StringProperty,
					   BoolProperty,
					   IntProperty,
					   FloatProperty,
					   FloatVectorProperty,
					   EnumProperty,
					   PointerProperty,
					   CollectionProperty,
					   )



class REAssetWhiteListEntryPropertyGroup(bpy.types.PropertyGroup):
	
	fileType: bpy.props.StringProperty(
        name="File Type",
		default = "mesh",
    )
	
	
class ASSET_UL_FileTypeWhiteList(bpy.types.UIList):
	
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		layout.prop(item,"fileType")
	# Disable double-click to rename
	def invoke(self, context, event):
		return {'PASS_THROUGH'}
	
class REAssetLibEntryPropertyGroup(bpy.types.PropertyGroup):
	
	displayName: bpy.props.StringProperty(
        name="Library Name",
		default = "GAME",
    )
	gameName: bpy.props.StringProperty(
        name="Game Name",
		default = "GAME",
    )
	releaseDescription: bpy.props.StringProperty(
        name="Release Description",
		default = "",
    )
	timestamp: bpy.props.StringProperty(
        name="Package Date",
		default = "TIME",
    )
	CRC: bpy.props.StringProperty(
        name="CRC",
		default = "0",
    )
	compressedSize: bpy.props.StringProperty(
        name="Download Size",
		default = "0",
    )
	uncompressedSize: bpy.props.StringProperty(
        name="Installed Size",
		default = "0",
    )
	URL: bpy.props.StringProperty(
        name="URL",
		default = "https://github.com/",
    )
	
class ASSET_UL_REAssetLibList(bpy.types.UIList):
	
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		layout.label(text=f"{item.gameName}")
	# Disable double-click to rename
	def invoke(self, context, event):
		return {'PASS_THROUGH'}