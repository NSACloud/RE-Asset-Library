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


from ..gen_functions import formatByteSize


class ToggleStringPropertyGroup(bpy.types.PropertyGroup):
	enabled: BoolProperty(
		name="",
		description = "Check to enable extracting of this",
		default = True,
	)
	path: StringProperty(
        name="",
		description = "",
	)
	fileSize: StringProperty(#Stored as string because blender uses int32s
        name="",
		description = "",
		default = "0",
	)
	
	
class ASSET_UL_StringCheckList(bpy.types.UIList):
	
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		layout.prop(item,"enabled")
		layout.label(text = f"{item.path} ({formatByteSize(int(item.fileSize))})")
		
	def invoke(self, context, event):
		return {'PASS_THROUGH'}
	