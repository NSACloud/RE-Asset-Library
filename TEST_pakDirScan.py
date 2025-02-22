#Author: NSA Cloud

from modules.pak.re_pak_utils import scanForPakFiles,createPakCacheFile

GAME_DIR = r"J:\SteamLibrary\steamapps\common\RESIDENT EVIL 4  BIOHAZARD RE4"
#GAME_DIR = r"J:\SteamLibrary\steamapps\common\Street Fighter 6"

CACHE_OUT_PATH = r"J:\REAssetLibrary\RE4\PakCache_RE4.zst"

pakList = scanForPakFiles(GAME_DIR)

#print(pakList)


for index, entry in enumerate(pakList):
	print(f"{index} - {entry}")
	
createPakCacheFile(pakList, CACHE_OUT_PATH)
