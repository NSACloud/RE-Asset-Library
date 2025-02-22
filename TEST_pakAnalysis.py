#Author: NSA Cloud
import os
from math import log,pow,ceil

from modules.pak.file_re_pak import ReadPakTOC
from modules.pak.re_pak_utils import extractFileList
from modules.hashing.pymmh3.pymmh3 import hash_wide


#TEST_PATH = r"natives\STM\player\mod\f\pl200\f_body200.mesh.2109148288"

TEST_PATH = r"natives\STM\Quest\QuestData\NormalQuestData.user.2"

#Legacy Pak Test
#PAK_PATH = r"J:\SteamLibrary\steamapps\common\Devil May Cry 5\re_chunk_000.pak"
#Legacy Patch Pak Test
#PAK_PATH = r"J:\SteamLibrary\steamapps\common\Devil May Cry 5\re_chunk_000.pak.patch_001.pak"

#MHR Pak
PAK_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\MonsterHunterRise\re_chunk_000.pak"
EXTRACT_OUT_DIR = r"D:\EXTRACT\TEST_EXTRACT"

#tocList = ReadPakTOC(PAK_PATH)

def concatInt(a, b):
	
		try:
			return int(pow(10, (round(log(b, 10)) + 1)) * a + b)
		except:#Only when hash is 0 (invalidated) or negative(which shouldn't happen)
			return int(f"{a}{b}")

def pathToPakHash(path):
	path = path.replace(os.sep,"/").replace("\\","/")
	return concatInt(hash_wide(path.lower()),hash_wide(path.upper()))


"""

for entry in tocList:
	pass
	#print(entry.hashNameLower)
	#print(concatInt(entry.hashNameLower,entry.hashNameUpper))

#lookupDict = {f"{entry.hashNameLower}{entry.hashNameUpper}" : entry for entry in tocList}
lookupDict = {concatInt(entry.hashNameLower,entry.hashNameUpper) : entry for entry in tocList}

#for entry in tocList:
	#print(f"{entry.compressedSize}")
	
	

lookUpHash = pathToPakHash(TEST_PATH)

if lookUpHash in lookupDict:
	entry = lookupDict[lookUpHash]
	print(entry.compressionType)
	with open(PAK_PATH,"rb") as file:
		file.seek(entry.offset)
		outPath = os.path.join(EXTRACT_OUT_DIR,TEST_PATH)
		os.makedirs(os.path.split(outPath)[0],exist_ok=True)
		with open(os.path.join(EXTRACT_OUT_DIR,TEST_PATH),"wb") as outFile:
			outFile.write(file.read(entry.compressedSize))

"""

extractFileList([TEST_PATH], PAK_PATH, EXTRACT_OUT_DIR)