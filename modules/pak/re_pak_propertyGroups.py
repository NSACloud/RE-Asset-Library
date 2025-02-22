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



class ToggleStringPropertyGroup(bpy.types.PropertyGroup):
	enabled: BoolProperty(
		name="",
		description = "Check to enable extracting of this",
		default = True
	)
	path: StringProperty(
        name="",
		description = "",
	)
	
	
class ASSET_UL_StringCheckList(bpy.types.UIList):
	
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		layout.prop(item,"enabled")
		layout.label(text = item.path)
		
	def invoke(self, context, event):
		return {'PASS_THROUGH'}
	