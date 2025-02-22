#Author: NSA Cloud

from modules.pak.re_pak_utils import scanForPakFiles,extractPakMP,extractAll

#Multiprocessed, has somewhat slow startup time but can extract paks very quickly.

GAME_DIR = r"J:\SteamLibrary\steamapps\common\Street Fighter 6"
#GAME_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\MonsterHunterRise"
#GAME_DIR = r"H:\Steam Games\steamapps\common\MonsterHunterRiseDemo"
EXTRACT_PATH = r"J:\TEST_EXTRACT"
#EXTRACT_PATH = r"D:\EXTRACT\SF6_EXTRACT\re_chunk_000"

LIST_PATH = r"D:\EXTRACT\SF6_EXTRACT\SF6_Pak_Release.list"

pakList = scanForPakFiles(GAME_DIR)

outPathSet = set()
with open(LIST_PATH,"r",encoding = "utf-8") as file:
	for line in file.readlines():
		if "natives" in line:
			outPath = "natives" + line.strip().split("natives")[1]
			outPathSet.add(outPath)

filePathList = sorted(list(outPathSet))

extractPakMP(filePathList, pakList, EXTRACT_PATH,skipUnknowns=True)
	