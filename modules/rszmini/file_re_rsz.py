#Author: NSA Cloud

#Stripped down RSZ reader purely for reading rsz headers

from ..gen_functions import textColors,raiseWarning,raiseError,getPaddingAmount,read_uint,read_int,read_uint64,read_float,read_ushort,read_ubyte,read_unicode_string,read_byte,write_uint,write_int,write_uint64,write_float,write_ushort,write_ubyte,write_unicode_string,write_byte
#from .re_rsz_lookup_main import getRSZInstance
DEBUG_MODE = False

def debugprint(string):
	if DEBUG_MODE:
		print(string)

class SIZEDATA():
	def __init__(self):
		self.HEADER_SIZE = 48
		self.INSTANCEINFO_SIZE = 8
		self.OBJECTTABLEENTRY_SIZE = 4
		self.RSZUSERDATAINFO_SIZE = 16
class RSZHeader():
	def __init__(self):
		
		self.magic = 5919570
		self.version = 16
		self.objectCount = 0
		self.instanceCount = 1
		self.userdataCount = 0
		self.reserved = 0
		self.instanceOffset = 0
		self.dataOffset = 0
		self.userdataOffset = 0
		
		
	def read(self,file,RSZOffset = 0):
		self.magic = read_uint(file)
		if self.magic != 5919570:
			raiseError("File is not a RSZ file.")
		self.version = read_uint(file)
		self.objectCount = read_uint(file)
		self.instanceCount = read_uint(file)
		self.userdataCount = read_uint(file)
		self.reserved = read_uint(file)
		self.instanceOffset = read_uint64(file)
		self.dataOffset = read_uint64(file)
		self.userdataOffset = read_uint64(file)
		
	def write(self,file):
		write_uint(file, self.magic)
		write_uint(file, self.version)
		write_uint(file, self.objectCount)
		write_uint(file, self.instanceCount)
		write_uint(file, self.userdataCount)
		write_uint(file, self.reserved)
		write_uint64(file, self.instanceOffset)
		write_uint64(file, self.dataOffset)
		write_uint64(file, self.userdataOffset)

	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class InstanceInfo():
	def __init__(self):
		self.typeIDHash = 0
		self.CRC = 0
		
	def read(self,file):
		self.typeIDHash = read_uint(file)
		self.CRC = read_uint(file)
		
	def write(self,file):
		write_uint(file, self.typeIDHash)
		write_uint(file, self.CRC)
	
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)
	
class RSZUserDataInfo():
	def __init__(self):
		self.instanceIndex = 0
		self.hash = 0
		self.stringOffset = 0
		self.string = ""
		
	def read(self,file,RSZOffset):
		self.instanceIndex = read_int(file)
		self.hash = read_uint(file)
		self.stringOffset = read_uint64(file)
		currentPos = file.tell()
		file.seek(RSZOffset+self.stringOffset)
		self.string = read_unicode_string(file)
		file.seek(currentPos)
	def write(self,file):
		write_int(file, self.instanceIndex)
		write_uint(file, self.hash)
		write_uint64(file, self.stringOffset)
	
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

	
class RSZFile():
	def __init__(self):
		self.RSZOffset = 0
		self.sizeData = SIZEDATA()
		self.Header = RSZHeader()
		self.ObjectTable = []
		self.InstanceInfoList = []
		self.RSZUserDataInfoList = []
		self.stringList = []#For writing user data
		self.InstanceList = [None]
	def short_read(self,file,RSZOffset = 0,game = "MHRise"):#Read everything but the instances themselves
		self.RSZOffset = RSZOffset
		debugprint("Reading RSZ Header")
		self.Header.read(file)
		debugprint(self.Header)
		debugprint(file.tell())
		debugprint("Reading Object Table")
		for i in range(0,self.Header.objectCount):
			self.ObjectTable.append(read_int(file))
		debugprint(self.ObjectTable)
		file.seek(self.RSZOffset+self.Header.instanceOffset)
		debugprint("Reading Instance Info")
		for i in range(0,self.Header.instanceCount):
			instanceInfoEntry = InstanceInfo()
			instanceInfoEntry.read(file)
			self.InstanceInfoList.append(instanceInfoEntry)
			debugprint(instanceInfoEntry)
		
		
		file.seek(self.RSZOffset+self.Header.userdataOffset)
		debugprint("Reading RSZ UserData")
		externalUserDataIndexSet = set()#For checking if an instance should be skipped when reading and writing
		externalUserDataIndexDict = {}
		for i in range(0,self.Header.userdataCount):
			userDataEntry = RSZUserDataInfo()
			userDataEntry.read(file,RSZOffset)
			self.RSZUserDataInfoList.append(userDataEntry)
			externalUserDataIndexSet.add(userDataEntry.instanceIndex)
	def read(self,file,RSZOffset = 0,game = "MHRise"):
		self.RSZOffset = RSZOffset
		debugprint("Reading RSZ Header")
		self.Header.read(file)
		debugprint(self.Header)
		debugprint(file.tell())
		debugprint("Reading Object Table")
		for i in range(0,self.Header.objectCount):
			self.ObjectTable.append(read_int(file))
		debugprint(self.ObjectTable)
		file.seek(self.RSZOffset+self.Header.instanceOffset)
		debugprint("Reading Instance Info")
		for i in range(0,self.Header.instanceCount):
			instanceInfoEntry = InstanceInfo()
			instanceInfoEntry.read(file)
			self.InstanceInfoList.append(instanceInfoEntry)
			debugprint(instanceInfoEntry)
		
		
		file.seek(self.RSZOffset+self.Header.userdataOffset)
		debugprint("Reading RSZ UserData")
		externalUserDataIndexSet = set()#For checking if an instance should be skipped when reading and writing
		externalUserDataIndexDict = {}
		for i in range(0,self.Header.userdataCount):
			userDataEntry = RSZUserDataInfo()
			userDataEntry.read(file,RSZOffset)
			self.RSZUserDataInfoList.append(userDataEntry)
			externalUserDataIndexSet.add(userDataEntry.instanceIndex)
		
		
		
		file.seek(self.RSZOffset+self.Header.dataOffset)
		self.rszData = file.read()
		
		"""
		for currentIndex,instanceInfo in enumerate(self.InstanceInfoList[1::]):#Skip first null instance
			try:
				instance = getRSZInstance(instanceInfo.typeIDHash,game)()
			except:
				print("No RSZ Instance found for hash " + str(hex(instanceInfo.typeIDHash)))
				print("Failed to parse instance " + str(currentIndex + 1))
				raise
			#print(instance.instanceInfo)
			if currentIndex + 1 not in externalUserDataIndexSet:
				try:
					instance.read(file)
				except:
					print("Failed to parse instance " + str(currentIndex + 1))
					print(instance.instanceInfo.name+"\n")
					raise
			else:
				instance.instanceInfo.tagList.add("EXTERNAL_USERDATA")
				for rszUserData in self.RSZUserDataInfoList:
					if rszUserData.instanceIndex == currentIndex + 1:
						instance.externalUserDataPath = rszUserData.string
			debugprint(instance)
			if currentIndex + 1 not in self.ObjectTable:
				instance.instanceInfo.isObject = False
			self.InstanceList.append(instance)
			#if instance.instanceInfo.name == "via.Prefab":
				#print(instance.v1)
			"""
	def gatherStrings(self):
		stringOffsetDict = {}
		currentOffset = 0
		for userDataInfo in self.RSZUserDataInfoList:
			stringOffsetDict[userDataInfo.string] = currentOffset
			currentOffset += len(userDataInfo.string) * 2 + 2
		return stringOffsetDict
	
	def recalculateOffsets(self,stringOffsetDict):
		self.Header.objectCount = len(self.ObjectTable)
		self.Header.instanceCount = len(self.InstanceInfoList)
		self.Header.userdataCount = len(self.RSZUserDataInfoList)
		
		self.Header.instanceOffset = self.sizeData.HEADER_SIZE + self.sizeData.OBJECTTABLEENTRY_SIZE * self.Header.objectCount
		self.Header.userdataOffset = self.Header.instanceOffset + self.sizeData.INSTANCEINFO_SIZE * self.Header.instanceCount + getPaddingAmount(self.RSZOffset + self.Header.instanceOffset + self.sizeData.INSTANCEINFO_SIZE * self.Header.instanceCount, 16)
		if stringOffsetDict != {}:
			lastStringEntry = list(stringOffsetDict.items())[-1]
		else:
			lastStringEntry = ("",0)
			
		stringStartOffset = self.Header.userdataOffset + self.sizeData.RSZUSERDATAINFO_SIZE * self.Header.userdataCount
		self.Header.dataOffset = stringStartOffset + lastStringEntry[1] + (len(lastStringEntry[0])*2+2) + getPaddingAmount(self.RSZOffset + stringStartOffset + lastStringEntry[1] + (len(lastStringEntry[0])*2+2), 16)
		
		for userDataInfo in self.RSZUserDataInfoList:
			userDataInfo.stringOffset = stringOffsetDict[userDataInfo.string]+stringStartOffset

	def write(self,file,RSZOffset,game):
		self.RSZOffset = RSZOffset
		stringOffsetDict = self.gatherStrings()
		self.recalculateOffsets(stringOffsetDict)
		
		
		self.Header.write(file)
		
		for objectTableEntry in self.ObjectTable:
			write_int(file,objectTableEntry)
		
		file.seek(self.RSZOffset + self.Header.instanceOffset)
		for instanceInfoEntry in self.InstanceInfoList:
			instanceInfoEntry.write(file)
		print(file.tell())
		file.seek(self.RSZOffset + self.Header.userdataOffset)
		for rszUserDataEntry in self.RSZUserDataInfoList:
			rszUserDataEntry.write(file)
					
		for string in stringOffsetDict.keys():
			write_unicode_string(file, string)
		
		file.seek(self.RSZOffset + self.Header.dataOffset)#+16 to create null instance
		file.write(self.rszData)
		"""
		for instance in self.InstanceList[1::]:
			instance.write(file)
		"""
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)