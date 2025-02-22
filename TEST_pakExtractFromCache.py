#Author: NSA Cloud

from modules.pak.re_pak_utils import extractFilesFromPakCache

#Single threaded, intended for extracting small amounts of files very quickly


GAME_INFO_PATH = r"J:\REAssetLibrary\RE4\GameInfo_RE4.json"
EXTRACT_INFO_PATH = r"J:\REAssetLibrary\RE4\ExtractInfo_RE4.json"
PAK_CACHE_PATH = r"J:\REAssetLibrary\RE4\PakCache_RE4.pakcache"

filePathList = [
	r"natives/STM/_Chainsaw/Character/ch/cha0/cha000/00/cha000_00.mesh.221108797",
	
	]


extractFilesFromPakCache(GAME_INFO_PATH,filePathList,EXTRACT_INFO_PATH,PAK_CACHE_PATH,extractDependencies = True,blenderAssetObj = None)