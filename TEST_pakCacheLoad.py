#Author: NSA Cloud

from modules.pak.re_pak_utils import readPakCache


CACHE_PATH = r"J:\REAssetLibrary\RE4\PakCache_RE4.zst"


pakList, lookupDict = readPakCache(CACHE_PATH)
#for entry in lookupDict:
	#print(entry)