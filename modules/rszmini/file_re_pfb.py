#Author: NSA Cloud
from ..gen_functions import textColors,raiseWarning,raiseError,getPaddingAmount,read_uint,read_int,read_uint64,read_float,read_short,read_ushort,read_ubyte,read_unicode_string,read_byte,write_uint,write_int,write_uint64,write_float,write_short,write_ushort,write_ubyte,write_unicode_string,write_byte
from .file_re_rsz import RSZFile
DEBUG_MODE = False
class SIZEDATA():
	def __init__(self):
		self.HEADER_SIZE = 56
		self.GAMEOBJECTINFO_SIZE = 12
		self.RESOURCEINFO_SIZE = 8
		self.USERDATAINFO_SIZE = 16
		self.PREFABINFO_SIZE = 8
		self.UNKN_PFB_INFO_SIZE = 16


def debugprint(string):
	if DEBUG_MODE:
		print(string)
class PFBHeader():
	def __init__(self):
		self.magic = 4343376
		self.infoCount = 0
		self.resourceCount = 0
		self.unknPFBInfoCount = 0
		self.userdataCount = 0
		self.reserved = 0
		self.unknPFBInfoOffset = 0
		self.resourceInfoOffset = 0
		self.userdataInfoOffset = 0
		self.stringListOffset = 0#Internal, For writing
		self.dataOffset = 0
		
		
	def read(self,file):
		self.magic = read_uint(file)
		if self.magic != 4343376:
			raiseError("File is not a PFB file.")
		self.infoCount = read_uint(file)
		self.resourceCount = read_uint(file)
		self.unknPFBInfoCount = read_uint(file)
		self.userdataCount = read_uint(file)
		self.reserved = read_uint(file)
		self.unknPFBInfoOffset = read_uint64(file)
		self.resourceInfoOffset = read_uint64(file)
		self.userdataInfoOffset = read_uint64(file)
		self.dataOffset = read_uint64(file)
		
	def write(self,file):
		write_uint(file, self.magic)
		write_uint(file, self.infoCount)
		write_uint(file, self.resourceCount)
		write_uint(file, self.unknPFBInfoCount)
		write_uint(file, self.userdataCount)
		write_uint(file, self.reserved)
		write_uint64(file, self.unknPFBInfoOffset)
		write_uint64(file, self.resourceInfoOffset)
		write_uint64(file, self.userdataInfoOffset)
		write_uint64(file, self.dataOffset)

	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class GameObjectInfoPFB():
	def __init__(self):
		self.uuid = "0"
		self.objectTableIndex = 0
		self.objectTableParentIndex = -1
		self.componentCount = 0
	def read(self,file):
		
		self.objectTableIndex = read_int(file)
		self.objectTableParentIndex = read_int(file)
		self.componentCount = read_uint(file)
		
	def write(self,file):
		write_int(file, self.objectTableIndex)
		write_int(file, self.objectTableParentIndex)
		write_uint(file, self.componentCount)
	
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)
	
class UnknPFBInfo():
	def __init__(self):
		self.objectTableIndex = 0
		self.shortA = 0
		self.shortB = 0
		self.intA = 0
		self.gameObjectID = 0
		
	def read(self,file):
		self.objectTableIndex = read_int(file)
		self.shortA = read_short(file)
		self.shortB = read_short(file)
		self.intA = read_int(file)
		self.gameObjectID = read_int(file)
	def write(self,file):
		write_int(file, self.objectTableIndex)
		write_short(file, self.shortA)
		write_short(file, self.shortB)
		write_int(file, self.intA)
		write_int(file, self.gameObjectID)
	
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
	
class PFBFile():
	def __init__(self):
		self.sizeData = SIZEDATA()
		self.Header = PFBHeader()
		self.GameObjectInfoList = []
		self.UnknPFBInfoList = []
		self.UserDataInfoList = []
		self.ResourceInfoList = []
		self.rsz = RSZFile()
	def read(self,file,game):
		debugprint("Reading PFB Header")
		self.Header.read(file)
		for i in range(0,self.Header.infoCount):
			entry = GameObjectInfoPFB()
			entry.read(file)
			self.GameObjectInfoList.append(entry)
			
		file.seek(self.Header.unknPFBInfoOffset)	
		debugprint("Reading Unknown PFB Info")
		for i in range(0,self.Header.unknPFBInfoCount):
			unknPFBInfoEntry = UnknPFBInfo()
			unknPFBInfoEntry.read(file)
			self.UnknPFBInfoList.append(unknPFBInfoEntry)
			
		file.seek(self.Header.resourceInfoOffset)
		debugprint("Reading Resource Info")
		for i in range(0,self.Header.resourceCount):
			entry = ResourceInfo()
			entry.read(file)
			self.ResourceInfoList.append(entry)
			
			
		file.seek(self.Header.userdataInfoOffset)
		debugprint("Reading UserData Info")
		for i in range(0,self.Header.userdataCount):
			entry = UserDataInfo()
			entry.read(file)
			self.UserDataInfoList.append(entry)
		
		debugprint(self.Header)
		for entry in self.UnknPFBInfoList:
			debugprint(entry)
		file.seek(self.Header.dataOffset)
		
		#self.rsz.short_read(file,self.Header.dataOffset)#For gathering hashes
		self.rsz.read(file,self.Header.dataOffset,game)
	
	def short_read(self,file,game):
		debugprint("Reading PFB Header")
		self.Header.read(file)
			
		for i in range(0,self.Header.infoCount):
			entry = GameObjectInfoPFB()
			entry.read(file)
			self.GameObjectInfoList.append(entry)
			
		file.seek(self.Header.unknPFBInfoOffset)	
		debugprint("Reading Unknown PFB Info")
		for i in range(0,self.Header.unknPFBInfoCount):
			unknPFBInfoEntry = UnknPFBInfo()
			unknPFBInfoEntry.read(file)
			self.UnknPFBInfoList.append(unknPFBInfoEntry)
			
		file.seek(self.Header.resourceInfoOffset)
		debugprint("Reading Resource Info")
		for i in range(0,self.Header.resourceCount):
			entry = ResourceInfo()
			entry.read(file)
			self.ResourceInfoList.append(entry)
			
			
		file.seek(self.Header.userdataInfoOffset)
		debugprint("Reading UserData Info")
		for i in range(0,self.Header.userdataCount):
			entry = UserDataInfo()
			entry.read(file)
			self.UserDataInfoList.append(entry)
		
		debugprint(self.Header)
		for entry in self.UnknPFBInfoList:
			debugprint(entry)
		file.seek(self.Header.dataOffset)
		
		self.rsz.short_read(file,self.Header.dataOffset)#For gathering hashes
		#self.rsz.read(file,self.Header.dataOffset,game)
	def gatherStrings(self):
		stringOffsetDict = {}
		currentOffset = 0
		for resourceInfo in self.ResourceInfoList:
			stringOffsetDict[resourceInfo.string] = currentOffset
			currentOffset += len(resourceInfo.string) * 2 + 2
		for userDataInfo in self.UserDataInfoList:
			stringOffsetDict[userDataInfo.string] = currentOffset
			currentOffset += len(userDataInfo.string) * 2 + 2
		return stringOffsetDict
	
	def recalculateOffsets(self,stringOffsetDict):
		self.Header.infoCount = len(self.GameObjectInfoList)
		self.Header.unknPFBInfoCount = len(self.UnknPFBInfoList)
		self.Header.resourceCount = len(self.ResourceInfoList)
		self.Header.userdataCount = len(self.UserDataInfoList)
		
		self.Header.unknPFBInfoOffset = self.sizeData.HEADER_SIZE + self.sizeData.GAMEOBJECTINFO_SIZE * self.Header.infoCount
		self.Header.resourceInfoOffset = self.Header.unknPFBInfoOffset + self.sizeData.UNKN_PFB_INFO_SIZE * self.Header.unknPFBInfoCount
		self.Header.userdataInfoOffset = self.Header.resourceInfoOffset + self.sizeData.RESOURCEINFO_SIZE * self.Header.resourceCount + getPaddingAmount(self.Header.resourceInfoOffset + self.sizeData.RESOURCEINFO_SIZE * self.Header.resourceCount, 16)
		lastStringEntry = list(stringOffsetDict.items())[-1]
		stringStartOffset = self.Header.userdataInfoOffset + self.sizeData.USERDATAINFO_SIZE * self.Header.userdataCount
		self.Header.dataOffset = stringStartOffset + lastStringEntry[1] + (len(lastStringEntry[0])*2+2)
		for resourceInfo in self.ResourceInfoList:
			resourceInfo.stringOffset = stringOffsetDict[resourceInfo.string]+stringStartOffset
		
		for userDataInfo in self.UserDataInfoList:
			userDataInfo.stringOffset = stringOffsetDict[userDataInfo.string]+stringStartOffset
	
	def write(self,file,game):
		stringOffsetDict = self.gatherStrings()
		self.recalculateOffsets(stringOffsetDict)
		
		self.Header.write(file)
		for entry in self.GameObjectInfoList:
			entry.write(file)
		file.seek(self.Header.unknPFBInfoOffset)
		for entry in self.UnknPFBInfoList:
			entry.write(file)
		file.seek(self.Header.resourceInfoOffset)
		for entry in self.ResourceInfoList:
			entry.write(file)
			
		
		file.seek(self.Header.userdataInfoOffset)
		for entry in self.UserDataInfoList:
			entry.write(file)
		
		for string in stringOffsetDict.keys():
			write_unicode_string(file, string)
		
		file.seek(self.Header.dataOffset)
		self.rsz.write(file,self.Header.dataOffset,game)

	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

def readRE_PFB(filepath, game = "MHRise"):
	#print(textColors.OKCYAN + "__________________________________\nPFB read started." + textColors.ENDC)
	#print("Opening " + filepath)
	try:  
		file = open(filepath,"rb")
	except:
		raiseError("Failed to open " + filepath)
	
	pfbFile = PFBFile()
	pfbFile.read(file,game)
	file.close()
	#print(textColors.OKGREEN + "__________________________________\nPFB read finished." + textColors.ENDC)
	return pfbFile

def readRE_PFB_Instances(filepath, game = "MHRise"):
	#print(textColors.OKCYAN + "__________________________________\nPFB read started." + textColors.ENDC)
	#print("Opening " + filepath)
	try:  
		file = open(filepath,"rb")
	except:
		raiseError("Failed to open " + filepath)
	
	pfbFile = PFBFile()
	pfbFile.short_read(file,game)
	file.close()
	#print(textColors.OKGREEN + "__________________________________\nPFB read finished." + textColors.ENDC)
	return pfbFile
def writeRE_PFB(PFBFile,filepath,game):
	#print(textColors.OKCYAN + "__________________________________\nPFB write started." + textColors.ENDC)
	print("Opening " + filepath)
	try:
		file = open(filepath,"wb")
	except:
		raiseError("Failed to open " + filepath)
	
	PFBFile.write(file,game)
	file.close()
	#print(textColors.OKGREEN + "__________________________________\nPFB write finished." + textColors.ENDC)
