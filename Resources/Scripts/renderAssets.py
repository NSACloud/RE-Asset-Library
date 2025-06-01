#Author: NSA Cloud

import bpy
import os
import math
import json
from zlib import crc32
import time
from mathutils import Vector

#------Render Settings
IMAGE_RES = 256

HDRI_ROT = (0.0,0.0,155.0)#Euler in degrees
HDRI_STRENGTH = 2.0
EXPOSURE = 0.5

CAMERA_DISTANCE = 1.7#Relative to object bbox size
CAMERA_ROT = (55.0,0.0,45.0)


IMAGE_FORMAT = "JPEG2000"
#IMAGE_FORMAT = "PNG"
RENDER_BOTH_FORMATS = False
IMAGE_QUALITY_COMPRESSION = 93#This is about the limit to where hair starts looking crunchy
#-------

#Convert to radians
CAMERA_ROT = (math.radians(CAMERA_ROT[0]),math.radians(CAMERA_ROT[1]),math.radians(CAMERA_ROT[2]))
HDRI_ROT = (math.radians(HDRI_ROT[0]),math.radians(HDRI_ROT[1]),math.radians(HDRI_ROT[2]))

# Python module to redirect the sys.stdout
from contextlib import redirect_stdout
import sys
argv = sys.argv
try:
	argv = argv[argv.index("--") + 1:]
except:
	raise Exception("RenderJob_XXXX.json path argument missing")
#print(argv)
RENDER_JOB_PATH = argv[0]

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

def getCamera(name):
    if name in bpy.data.objects and bpy.data.objects[name].type == "CAMERA":
        cameraObj = bpy.data.objects[name]
    else:
        cameraData = bpy.data.cameras.new(name)
        cameraObj = bpy.data.objects.new(name,cameraData)
        bpy.context.scene.collection.objects.link(cameraObj)
    return cameraObj

def setupScene(hdriPath):
    #Render
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.eevee.use_raytracing = True
    bpy.context.scene.view_settings.view_transform = "AgX"
    bpy.context.scene.view_settings.look = "AgX - Medium High Contrast"
    bpy.context.scene.view_settings.exposure = EXPOSURE
    #Output
    bpy.context.scene.render.resolution_x = IMAGE_RES
    bpy.context.scene.render.resolution_y = IMAGE_RES
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.image_settings.file_format = IMAGE_FORMAT
    bpy.context.scene.render.image_settings.quality = IMAGE_QUALITY_COMPRESSION
    #World
    if bpy.context.scene.world != None:
        world = bpy.context.scene.world
        world.use_nodes = True
        nodeTree = world.node_tree
        nodeTree.nodes.clear()
        nodes = nodeTree.nodes
        links = nodeTree.links
        
        currentPos = [-600,0]
        
        texCoordNode = nodes.new('ShaderNodeTexCoord')
        texCoordNode.location = currentPos
        currentPos[0] += 300
        
        mappingNode = nodes.new('ShaderNodeMapping')
        mappingNode.location = currentPos
        
        mappingNode.inputs["Rotation"].default_value = HDRI_ROT
        
        links.new(texCoordNode.outputs["Generated"],mappingNode.inputs["Vector"])
        
        currentPos[0] += 300
        
        imageNode = nodes.new('ShaderNodeTexEnvironment')
        imageNode.name = "HDRI"
        imageNode.label = "HDRI"
        imageNode.location = currentPos
        
        links.new(mappingNode.outputs["Vector"],imageNode.inputs["Vector"])
		
        imageData = None
        if os.path.isfile(hdriPath):
            imageData = bpy.data.images.load(hdriPath,check_existing = True)
        else:
            print(f"RE Asset Library - ERROR: Attempted to load missing resource: {hdriPath}")
        if imageData != None:
            imageNode.image = imageData
        
        currentPos[0] += 300
        
        bgNode = nodes.new("ShaderNodeBackground")
        bgNode.name = "Background"
        bgNode.label = "Background"
        bgNode.location = currentPos
        
        bgNode.inputs["Strength"].default_value = HDRI_STRENGTH
        links.new(imageNode.outputs["Color"],bgNode.inputs["Color"])
        
        currentPos[0] += 300
        
        outNode = nodes.new("ShaderNodeOutputWorld")
        outNode.name = "World Output"
        outNode.label = "World Output"
        outNode.location = currentPos
        
        links.new(bgNode.outputs["Background"],outNode.inputs["Surface"])
        
def alignCameraToObject(target):
    cameraObj = getCamera("AssetThumbnailCamera")
    cameraObj.data.clip_end = 100000
    cameraObj.data.clip_start = 0.01
    cameraObj.location = (0.0,0.0,0.0)
    cameraObj.rotation_euler = (0.0,0.0,0.0)
    
    if "CameraHelper" in bpy.data.objects:
        emptyObj = bpy.data.objects["CameraHelper"]
    else:
        emptyObj = bpy.data.objects.new("CameraHelper",None)
        bpy.context.scene.collection.objects.link(emptyObj)
    emptyObj.rotation_euler = CAMERA_ROT
    bpy.context.scene.camera = cameraObj

    o = bpy.data.objects["Mesh Bounding Box"]
    local_bbox_center = 0.125 * sum((Vector(b) for b in o.bound_box), Vector())
    global_bbox_center = o.matrix_world @ local_bbox_center

    emptyObj.location = global_bbox_center
    
    cameraObj.location[2] = max(o.dimensions) * CAMERA_DISTANCE
    cameraObj.parent = emptyObj 
   

def importREMesh(filePath,options,showImportOptions = False):
    split = os.path.split(filePath)
    bpy.ops.re_mesh.importfile(directory=split[0],
    files=[{"name":split[1]}],
    clearScene = options["clearScene"],
    createCollections = options["createCollections"],
    loadMaterials = options["loadMaterials"],
    loadMDFData = options["loadMDFData"],
    loadUnusedTextures = options["loadUnusedTextures"],
    loadUnusedProps = options["loadUnusedProps"],
    useBackfaceCulling = options["useBackfaceCulling"],
    reloadCachedTextures = options["reloadCachedTextures"],
    mdfPath = options["mdfPath"],
    importAllLODs = options["importAllLODs"],
    importBlendShapes = options["importBlendShapes"],
    rotate90 = options["rotate90"],
    mergeArmature = options["mergeArmature"],
    importArmatureOnly = options["importArmatureOnly"],
    mergeGroups = options["mergeGroups"],
    importShadowMeshes = options["importShadowMeshes"],
    importOcclusionMeshes = options["importOcclusionMeshes"],
    importBoundingBoxes = options["importBoundingBoxes"],
    )
    
    meshCollection = bpy.data.collections[bpy.context.scene["REMeshLastImportedCollection"]]
    
    armatureObj = None
    subMeshList = []
    
    for obj in meshCollection.all_objects:
        if obj.type == "MESH":
            subMeshList.append(obj)
        elif obj.type == "ARMATURE":
            armatureObj = obj
    
    del bpy.context.scene["REMeshLastImportedCollection"]#Clear last imported collection after import is done so it can be determined if the next import failed
    
    return armatureObj, subMeshList
def renderMeshThumbnail(meshPath,outPath,hdriPath):#Use category to determine if object should be rendered a special way (EX: Fixing the camera so that weapons face a way looks right)

    meshImportOptions = {"clearScene":True,
    "createCollections":True,
    "loadMaterials":True,
    "loadMDFData":False,
    "loadUnusedTextures":False,
    "loadUnusedProps":False,
    "useBackfaceCulling":True,
    "reloadCachedTextures":False,
    "mdfPath":"",
    "importAllLODs":False,
    "importBlendShapes":False,
    "rotate90":True,
    "mergeArmature":"",
    "importArmatureOnly":False,
    "mergeGroups":False,
    "importShadowMeshes":False,
    "importOcclusionMeshes":False,
    "importBoundingBoxes":True
    }
    setupScene(hdriPath)
    #bpy.ops.outliner.orphans_purge()
    importError = False
    try:
        armatureObj, subMeshList = importREMesh(meshPath,meshImportOptions)
        for subMesh in subMeshList:#Hair rendering fix
            if "fakeao" in subMesh.name.lower() or "fake_ao" in subMesh.name.lower():
                bpy.data.objects.remove(bpy.data.objects[subMesh.name],do_unlink = True)
    
    except Exception as err:
        print(f"Import error: {meshPath} - {str(err)}")
        importError = True
    meshCollection = bpy.data.collections.get(os.path.split(meshPath)[1].split(".")[0]+".mesh",None)
    if not importError:
        if "Mesh Bounding Sphere" in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects["Mesh Bounding Sphere"],do_unlink = True)
        
        if "Mesh Bounding Box" in bpy.data.objects:
            targetObj = bpy.data.objects["Mesh Bounding Box"]
            
        else:
            targetObj = subMeshList[0]#TODO get submesh
        alignCameraToObject(targetObj)
        
       
        bpy.context.scene.render.filepath = outPath
        bpy.ops.render.render(write_still = True)
		
        if RENDER_BOTH_FORMATS:
            bpy.context.scene.render.image_settings.file_format = "PNG"
            bpy.context.scene.render.filepath = outPath.replace(".jp2",".png")
            bpy.ops.render.render(write_still = True)

#--------------
print("\nRender Asset Script Started")
RE_MESH_EDITOR_PREFERENCES_NAME = None
try:
	bpy.ops.wm.console_toggle()
except:
	pass

if os.path.isfile(RENDER_JOB_PATH):

    file = open(RENDER_JOB_PATH,"r", encoding ="utf-8")
    renderJobDict = json.load(file)
    file.close()
    
    #gameName = renderJobDict["GAME"]
    outPath = renderJobDict["Output Path"]
    hdriPath = renderJobDict["HDRI Path"]
    
    jobCount = len(renderJobDict["entryList"])
    
    meshEditorPreferencesName = findREMeshEditorAddon()
    if meshEditorPreferencesName:
        #Disable show console setting temporarily while renders are being done so it doesn't constantly open and close
        ADDON_PREFERENCES = bpy.context.preferences.addons[meshEditorPreferencesName].preferences
        consoleSetting = ADDON_PREFERENCES.showConsole
        ADDON_PREFERENCES.showConsole = False
        print("Disabled RE Mesh Editor console show setting")
    else:
        ADDON_PREFERENCES = None
        
    print("Render Job Started")
	
    for index, entry in enumerate(renderJobDict["entryList"]):
        #print(entry)
        with redirect_stdout(None):#Remove blender console spam
            thumbnailPath = os.path.join(outPath,entry["outputName"])
            meshPath = entry["path"]
        if not os.path.exists(thumbnailPath):
            print(f"Current Render Job {index} / {jobCount}: "+entry["outputName"]+f"\n{meshPath}")
            with redirect_stdout(None):
                renderMeshThumbnail(meshPath,thumbnailPath,hdriPath)
    if ADDON_PREFERENCES:#Reset show console setting to original value
        ADDON_PREFERENCES.showConsole = consoleSetting
        print("Reset RE Mesh Editor console show setting")
    print()
    print("Render Job Finished")
    try:
        bpy.ops.wm.console_toggle()
    except:
        pass
    bpy.ops.wm.quit_blender()
	
    
else:
    print("RenderJob.json is missing, cannot render.")
time.sleep(5)
try:
	bpy.ops.wm.console_toggle()
except:
	pass