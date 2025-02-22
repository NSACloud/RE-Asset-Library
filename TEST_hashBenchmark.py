#Author: NSA Cloud
from modules.hashing.mmh3.pymmh3 import hashUTF16Old, hashUTF16
from modules.pak.re_pak_utils import readListFileSet
import time
timeFormat = "%d"
LIST_PATH = r"D:\EXTRACT\RE3NONRT_EXTRACT\re3_pak_names_release_2.list"
#LIST_PATH = r"D:\EXTRACT\RE4_EXTRACT\RE4_Release_Pak.list"

print("Starting hash benchmark")
filePathSet = readListFileSet(LIST_PATH)
print(f"{len(filePathSet)} entries")
hashWideSet = set()
hashStartTime = time.time()
for filePath in filePathSet:
	hashWideSet.add(hashUTF16Old(filePath))
hashEndTime = time.time()
hashTime =  hashEndTime - hashStartTime
hashTimeInt = int(hashTime*1000)
print(f"Hash took {hashTimeInt} ms.")
hashWide2Set = set()
hash2StartTime = time.time()
for filePath in filePathSet:
	hashWide2Set.add(hashUTF16(filePath))
hash2EndTime = time.time()
hash2Time =  hash2EndTime - hash2StartTime


hash2TimeInt = int(hash2Time*1000)
percent = "{:.2f} %".format((round(hashTimeInt / hash2TimeInt,3)-1.0)*100)
print(f"Hash2 took {hash2TimeInt} ms.")
print(f"{percent} difference")

if hashWideSet == hashWide2Set:
	print("\nSets match")
else:
	print("\nFailed, results do not match")



