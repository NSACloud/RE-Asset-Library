#Author: NSA Cloud
from ..gen_functions import textColors,raiseWarning,raiseError,getPaddingAmount,read_uint,read_int,read_uint64,read_float,read_short,read_ushort,read_ubyte,read_unicode_string,read_byte,write_uint,write_int,write_uint64,write_float,write_short,write_ushort,write_ubyte,write_unicode_string,write_byte
from .file_re_rsz import RSZFile
DEBUG_MODE = False
class SIZEDATA():
	def __init__(self):
		self.HEADER_SIZE = 64
		self.GAMEOBJECTINFO_SIZE = 32
		self.FOLDERINFO_SIZE = 8
		self.RESOURCEINFO_SIZE = 8
		self.USERDATAINFO_SIZE = 16
		self.PREFABINFO_SIZE = 8


def debugprint(string):
	if DEBUG_MODE:
		print(string)
class SCNHeader():
	def __init__(self):
		self.magic = 5129043
		self.infoCount = 0
		self.resourceCount = 0
		self.folderCount = 0
		self.prefabCount = 0
		self.userdataCount = 0
		self.folderInfoOffset = 0
		self.resourceInfoOffset = 0
		self.prefabInfoOffset = 0
		self.userdataInfoOffset = 0
		self.stringListOffset = 0#Internal, For writing
		self.dataOffset = 0
		
		
	def read(self,file):
		self.magic = read_uint(file)
		if self.magic != 5129043:
			raiseError("File is not a SCN file.")
		self.infoCount = read_uint(file)
		self.resourceCount = read_uint(file)
		self.folderCount = read_uint(file)
		self.prefabCount = read_uint(file)
		self.userdataCount = read_uint(file)
		self.folderInfoOffset = read_uint64(file)
		self.resourceInfoOffset = read_uint64(file)
		self.prefabInfoOffset = read_uint64(file)
		self.userdataInfoOffset = read_uint64(file)
		self.dataOffset = read_uint64(file)
		
	def write(self,file):
		write_uint(file, self.magic)
		write_uint(file, self.infoCount)
		write_uint(file, self.resourceCount)
		write_uint(file, self.folderCount)
		write_uint(file, self.prefabCount)
		write_uint(file, self.userdataCount)
		write_uint64(file, self.folderInfoOffset)
		write_uint64(file, self.resourceInfoOffset)
		write_uint64(file, self.prefabInfoOffset)
		write_uint64(file, self.userdataInfoOffset)
		write_uint64(file, self.dataOffset)

	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class GameObjectInfo():
	def __init__(self):
		self.uuid = b'\x00'*16
		self.objectTableIndex = 0
		self.objectTableParentIndex = -1
		self.componentCount = 0
		self.unkn = 0
		self.prefabID = -1
		
	def read(self,file):
		self.uuid = str(int.from_bytes(file.read(16),byteorder = "little", signed = False))
		self.objectTableIndex = read_int(file)
		self.objectTableParentIndex = read_int(file)
		self.componentCount = read_ushort(file)
		self.unkn = read_short(file)
		self.prefabID = read_int(file)
		
	def write(self,file):
		file.write(self.uuid)
		write_int(file, self.objectTableIndex)
		write_int(file, self.objectTableParentIndex)
		write_ushort(file, self.componentCount)
		write_short(file, self.unkn)
		write_int(file, self.prefabID)
	
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)
	
class FolderInfo():
	def __init__(self):
		self.objectTableIndex = 0
		self.objectTableParentIndex = -1
		
	def read(self,file):
		self.objectTableIndex = read_int(file)
		self.objectTableParentIndex = read_int(file)
	def write(self,file):
		write_int(file, self.objectTableIndex)
		write_int(file, self.objectTableParentIndex)
	
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class UserDataInfo():
	def __init__(self):
		self.hash = 0
		self.CRC = 0
		self.stringOffset = 0
		self.string = ""
		
	def read(self,file):
		self.hash = read_uint(file)
		self.CRC = read_uint(file)
		self.stringOffset = read_uint64(file)
		currentPos = file.tell()
		file.seek(self.stringOffset)
		self.string = read_unicode_string(file)
		file.seek(currentPos)
	def write(self,file):
		write_uint(file, self.hash)
		write_uint(file, self.CRC)
		write_uint64(file, self.stringOffset)
	
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class ResourceInfo():
	def __init__(self):
		self.stringOffset = 0
		self.string = ""
		
	def read(self,file):
		self.stringOffset = read_uint64(file)
		currentPos = file.tell()
		file.seek(self.stringOffset)
		self.string = read_unicode_string(file)
		file.seek(currentPos)
	def write(self,file):
		write_uint64(file, self.stringOffset)
	
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class PrefabInfo():
	def __init__(self):
		self.stringOffset = 0
		self.string = ""
		self.objectTableParentIndex = -1
		
	def read(self,file):
		self.stringOffset = read_uint(file)
		currentPos = file.tell()
		file.seek(self.stringOffset)
		self.string = read_unicode_string(file)
		file.seek(currentPos)
		self.objectTableParentIndex = read_int(file)
	def write(self,file):
		write_uint(file, self.stringOffset)
		write_int(file, self.objectTableParentIndex)
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)
	
class SCNFile():
	def __init__(self):
		self.sizeData = SIZEDATA()
		self.Header = SCNHeader()
		self.GameObjectInfoList = []
		self.FolderInfoList = []
		self.UserDataInfoList = []
		self.ResourceInfoList = []
		self.PrefabInfoList = []
		self.rsz = RSZFile()
	def read(self,file,game):
		debugprint("Reading SCN Header")
		#print(game)
		self.Header.read(file)
			
		for i in range(0,self.Header.infoCount):
			entry = GameObjectInfo()
			entry.read(file)
			self.GameObjectInfoList.append(entry)
			
		file.seek(self.Header.folderInfoOffset)	
		debugprint("Reading Folder Info")
		for i in range(0,self.Header.folderCount):
			entry = FolderInfo()
			entry.read(file)
			self.FolderInfoList.append(entry)
			
		file.seek(self.Header.resourceInfoOffset)
		debugprint("Reading Resource Info")
		for i in range(0,self.Header.resourceCount):
			entry = ResourceInfo()
			entry.read(file)
			self.ResourceInfoList.append(entry)
			
		file.seek(self.Header.prefabInfoOffset)
		debugprint("Reading Prefab Info")
		for i in range(0,self.Header.prefabCount):
			entry = PrefabInfo()
			entry.read(file)
			self.PrefabInfoList.append(entry)
			
		file.seek(self.Header.userdataInfoOffset)
		debugprint("Reading UserData Info")
		for i in range(0,self.Header.userdataCount):
			entry = UserDataInfo()
			entry.read(file)
			self.UserDataInfoList.append(entry)
		file.seek(self.Header.dataOffset)
		self.rsz.read(file,self.Header.dataOffset,game)
	def gatherStrings(self):
		stringOffsetDict = {}
		currentOffset = 0
		for resourceInfo in self.ResourceInfoList:
			stringOffsetDict[resourceInfo.string] = currentOffset
			currentOffset += len(resourceInfo.string) * 2 + 2
		for prefabInfo in self.PrefabInfoList:
			stringOffsetDict[prefabInfo.string] = currentOffset
			currentOffset += len(prefabInfo.string) * 2 + 2
		for userDataInfo in self.UserDataInfoList:
			stringOffsetDict[userDataInfo.string] = currentOffset
			currentOffset += len(userDataInfo.string) * 2 + 2
		return stringOffsetDict
	
	def recalculateOffsets(self,stringOffsetDict):
		self.Header.infoCount = len(self.GameObjectInfoList)
		self.Header.resourceCount = len(self.ResourceInfoList)
		self.Header.folderCount = len(self.FolderInfoList)
		self.Header.prefabCount = len(self.PrefabInfoList)
		self.Header.userdataCount = len(self.UserDataInfoList)
		
		self.Header.folderInfoOffset = self.sizeData.HEADER_SIZE + self.sizeData.GAMEOBJECTINFO_SIZE * self.Header.infoCount
		self.Header.resourceInfoOffset = self.Header.folderInfoOffset + self.sizeData.FOLDERINFO_SIZE * self.Header.folderCount
		self.Header.prefabInfoOffset = self.Header.resourceInfoOffset + self.sizeData.RESOURCEINFO_SIZE * self.Header.resourceCount + getPaddingAmount(self.Header.resourceInfoOffset + self.sizeData.RESOURCEINFO_SIZE * self.Header.resourceCount, 16)
		self.Header.userdataInfoOffset = self.Header.prefabInfoOffset + self.sizeData.PREFABINFO_SIZE * self.Header.prefabCount + getPaddingAmount(self.Header.prefabInfoOffset + self.sizeData.PREFABINFO_SIZE * self.Header.prefabCount, 16)
		if stringOffsetDict != {}:
			lastStringEntry = list(stringOffsetDict.items())[-1]
		else:
			lastStringEntry = ("",0)
		stringStartOffset = self.Header.userdataInfoOffset + self.sizeData.USERDATAINFO_SIZE * self.Header.userdataCount
		self.Header.dataOffset = stringStartOffset + lastStringEntry[1] + (len(lastStringEntry[0])*2+2)
		for resourceInfo in self.ResourceInfoList:
			resourceInfo.stringOffset = stringOffsetDict[resourceInfo.string]+stringStartOffset
		
		for prefabInfo in self.PrefabInfoList:
			prefabInfo.stringOffset = stringOffsetDict[prefabInfo.string]+stringStartOffset
		
		for userDataInfo in self.UserDataInfoList:
			userDataInfo.stringOffset = stringOffsetDict[userDataInfo.string]+stringStartOffset
	
	def write(self,file,game):
		stringOffsetDict = self.gatherStrings()
		self.recalculateOffsets(stringOffsetDict)
		
		self.Header.write(file)

		for entry in self.GameObjectInfoList:
			entry.write(file)
		
		file.seek(self.Header.folderInfoOffset)
		for entry in self.FolderInfoList:
			entry.write(file)
		
		file.seek(self.Header.resourceInfoOffset)
		for entry in self.ResourceInfoList:
			entry.write(file)
			
			
		file.seek(self.Header.prefabInfoOffset)
		for entry in self.PrefabInfoList:
			entry.write(file)
		
		file.seek(self.Header.userdataInfoOffset)
		for entry in self.UserDataInfoList:
			entry.write(file)
		
		for string in stringOffsetDict.keys():
			write_unicode_string(file, string)
		
		file.seek(self.Header.dataOffset)
		self.rsz.write(file,self.Header.dataOffset,game)
	
	
	def short_read(self,file,game):#For getting hashes used without reading full rsz
		debugprint("Reading SCN Header")
		self.Header.read(file)
			
		for i in range(0,self.Header.infoCount):
			entry = GameObjectInfo()
			entry.read(file)
			self.GameObjectInfoList.append(entry)
			
		file.seek(self.Header.folderInfoOffset)	
		debugprint("Reading Folder Info")
		for i in range(0,self.Header.folderCount):
			entry = FolderInfo()
			entry.read(file)
			self.FolderInfoList.append(entry)
			
		file.seek(self.Header.resourceInfoOffset)
		debugprint("Reading Resource Info")
		for i in range(0,self.Header.resourceCount):
			entry = ResourceInfo()
			entry.read(file)
			self.ResourceInfoList.append(entry)
			
		file.seek(self.Header.prefabInfoOffset)
		debugprint("Reading Prefab Info")
		for i in range(0,self.Header.prefabCount):
			entry = PrefabInfo()
			entry.read(file)
			self.PrefabInfoList.append(entry)
			
		file.seek(self.Header.userdataInfoOffset)
		debugprint("Reading UserData Info")
		for i in range(0,self.Header.userdataCount):
			entry = UserDataInfo()
			entry.read(file)
			self.UserDataInfoList.append(entry)
		file.seek(self.Header.dataOffset)
		self.rsz.short_read(file,self.Header.dataOffset)
	
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

def readRE_SCN(filepath,game = "MHRise"):
	
	
	
	#print(textColors.OKCYAN + "__________________________________\nSCN read started." + textColors.ENDC)
	print("Opening " + filepath)
	try:  
		file = open(filepath,"rb")
	except:
		raiseError("Failed to open " + filepath)
	
	scnFile = SCNFile()
	scnFile.read(file,game)
	file.close()
	#print(textColors.OKGREEN + "__________________________________\nSCN read finished." + textColors.ENDC)
	return scnFile

def readRE_SCN_Instances(filepath,game = "MHRise"):
	#print(textColors.OKCYAN + "__________________________________\nSCN read started." + textColors.ENDC)
	print("Opening " + filepath)
	try:  
		file = open(filepath,"rb")
	except:
		raiseError("Failed to open " + filepath)
	
	scnFile = SCNFile()
	scnFile.short_read(file,game)
	file.close()
	#print(textColors.OKGREEN + "__________________________________\nSCN read finished." + textColors.ENDC)
	return scnFile
def writeRE_SCN(scnFile,filepath,game = "MHRise"):
	#print(textColors.OKCYAN + "__________________________________\nSCN write started." + textColors.ENDC)
	print("Opening " + filepath)
	try:
		file = open(filepath,"wb")
	except:
		raiseError("Failed to open " + filepath)
	
	scnFile.write(file,game)
	file.close()
	#print(textColors.OKGREEN + "__________________________________\nSCN write finished." + textColors.ENDC)
