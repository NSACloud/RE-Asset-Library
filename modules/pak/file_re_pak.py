#Author: NSA Cloud

#Credit to Ekey, I used REE Pak Tool as a reference for this

import os

from struct import Struct
import time

timeFormat = "%d"

from ..gen_functions import read_ubyte,read_ushort,read_uint,read_uint64,write_ubyte,write_ushort,write_uint,write_uint64

from ..encryption.re_pak_encryption import decryptData

PAK_VER_2_ENTRY_SIZE = 24
PAK_VER_4_ENTRY_SIZE = 48

ver2EntryStruct = Struct("<QQII")
ver4EntryStruct = Struct("<IIQQQQQ")

class PakTOCEntry():
	def __init__(self):
		self.hashNameLower = 0
		self.hashNameUpper = 0
		self.offset = 0
		self.compressedSize = 0
		self.decompressedSize = 0
		self.attributes = 0
		self.checksum = 0
		self.compressionType = 0
		self.encryptionType = 0
		
	def read(self,file,entryStruct):
		
		if entryStruct == ver2EntryStruct:
			(
			self.offset,
			self.decompressedSize,
			self.hashNameLower,
			self.hashNameUpper,
			) = entryStruct.unpack(file.read(PAK_VER_2_ENTRY_SIZE))
		elif entryStruct == ver4EntryStruct:
			(self.hashNameLower,
			self.hashNameUpper,
			self.offset,
			self.compressedSize,
			self.decompressedSize,
			self.attributes,
			self.checksum,
			)= entryStruct.unpack(file.read(PAK_VER_4_ENTRY_SIZE))
		self.compressionType = 0
		self.encryptionType = 0
		
		
	def write(self,file):#Only writes pak version 4 for pak patches
		file.write(ver4EntryStruct.pack(
		self.hashNameLower,
		self.hashNameUpper,
		self.offset,
		self.compressedSize,
		self.decompressedSize,
		self.attributes,
		self.checksum,
		)
		)

class PakTOC():
	def __init__(self):
		self.entryList = []
		
	def read(self,file,header,remapTable):
		
		isRemapTableUsed = remapTable != None
		
		if header.majorVersion == 2:
			entrySize = PAK_VER_2_ENTRY_SIZE
			entryStruct = ver2EntryStruct
		else:
			entrySize = PAK_VER_4_ENTRY_SIZE
			entryStruct = ver4EntryStruct
		
		
		tocData = file.read(entrySize*header.entryCount)
		
		if header.featureIsTOCEncrypted:
			if header.featureUseUnknTable:
				file.seek(4,1)#Skip empty table, used in wilds HD texture pak
			decryptStartTime = time.time()
			
			encryptedKey = bytearray(file.read(128))
			#raise Exception("Decryption not implemented yet")
			tocData = decryptData(bytearray(tocData),encryptedKey)
			decryptEndTime = time.time()
			decryptionTime =  decryptEndTime - decryptStartTime
			print(f"TOC Decryption took {timeFormat%(decryptionTime * 1000)} ms.")
		if entryStruct == ver2EntryStruct:
			for unpackData in ver2EntryStruct.iter_unpack(tocData):
				entry = PakTOCEntry()
				(
				entry.offset,
				entry.decompressedSize,
				entry.hashNameLower,
				entry.hashNameUpper,
				) = unpackData
				
				self.entryList.append(entry)
				
				if entry.hashNameLower == 0:
					raise Exception("Invalidated pak entries found.\nPak files cannot be extracted when mods are installed using Fluffy Manager.\nUninstall any mods and verify integrity of game files on Steam.")
		else:
			for unpackData in ver4EntryStruct.iter_unpack(tocData):
				entry = PakTOCEntry()
				(entry.hashNameLower,
				entry.hashNameUpper,
				entry.offset,
				entry.compressedSize,
				entry.decompressedSize,
				entry.attributes,
				entry.checksum,
				) = unpackData
				entry.compressionType = entry.attributes & 0xF
				entry.encryptionType = (entry.attributes & 0x00FF0000) >> 16
				entry.useRemapTable = (entry.attributes >> 24) & 0xFF
				
				if entry.useRemapTable and isRemapTableUsed:
					entry.offset = remapTable.entryList[entry.offset].fileOffset
					#print(f"Remapped {entry.hashNameLower}-{entry.hashNameUpper} to {entry.offset}")
				
				self.entryList.append(entry)
				#print(entry.offset)
				#print(entry.__dict__)
				if entry.hashNameLower == 0:
					raise Exception("Invalidated pak entries found.\nPak files cannot be extracted when mods are installed using Fluffy Manager.\nUninstall any mods and verify integrity of game files on Steam.")
		
	def write(self,file):
		for entry in self.entryList:
			entry.write(file)

class PakHeader():
	def __init__(self):
		self.magic = 1095454795
		self.majorVersion = 0
		self.minorVersion = 0
		self.feature = 0
		self.entryCount = 0
		self.fingerprint = 0
		
		#Has no function in reading or writing, purely to make code easier to read
		self.featureIsTOCEncrypted = False
		self.featureUseUnknTable = False
		self.featureUseRemapTable = False
	def read(self,file):
		self.magic = read_uint(file)
		if self.magic != 1095454795:
			raise Exception("File is not an RE Engine pak file. Cannot import.")
		self.majorVersion = read_ubyte(file)
		self.minorVersion = read_ubyte(file)
		self.feature = read_ushort(file)
		self.entryCount = read_uint(file)
		self.fingerprint = read_uint(file)
		
		self.featureIsTOCEncrypted = bool((self.feature >> 3) & 1)
		self.featureUseUnknTable = bool((self.feature >> 4) & 1)
		self.featureUseRemapTable = bool((self.feature >> 5) & 1)
		
		
		if self.majorVersion != 2 and self.majorVersion != 4 or self.minorVersion != 0 and self.minorVersion != 1 and self.minorVersion != 2:
			raise Exception(f"Invalid Pak Version ({self.majorVersion}.{self.minorVersion}), expected 2.0, 4.0 & 4.1")
			
		#if self.feature != 0 and self.feature != 8 and self.feature != 24 and self.feature != 40:
		#	raise Exception(f"Unsupported Encryption Type ({self.feature})")
			
	def write(self,file):
		write_uint(file,self.magic)
		write_ubyte(file,self.majorVersion)
		write_ubyte(file,self.minorVersion)
		write_ushort(file,self.feature)
		write_uint(file,self.entryCount)
		write_uint(file,self.fingerprint)
		

class PakRemapTableEntry():
	def __init__(self):
		self.fileOffset = 0
		self.unkn = 0
		
	def read(self,file):	
		self.fileOffset = read_uint(file)
		self.unkn = read_uint(file)

class PakRemapTable():
	def __init__(self):
		
		#TODO Fix this to read chunks properly
		#There's a lot of things I'll have to change to make this work properly and I don't want to get into it right now
		#This will cause .mov and possibly some sound files to not extract correctly in pragmata and newer.
		 
		self.unkn0 = 0#TODO change to uint block size
		self.unkn1 = 0#
		self.entryCount = 0
		self.entryList = []
		
	def read(self,file):
		
		self.unkn0 = read_ushort(file)
		self.unkn1 = read_ushort(file)#
		self.entryCount = read_uint(file)
		if self.unkn1 == 8:
			for _ in range(0,self.entryCount):
				entry = PakRemapTableEntry()
				entry.read(file)
				self.entryList.append(entry)
		

class PakFile():
	def __init__(self):
		self.header = PakHeader()
		self.toc = PakTOC()
		self.remapTable = None
		self.data = bytes()#Unused
	def read(self,file):#For testing, not supposed to be used
		self.header.read(file)
		#Does not remap offsets, keeps them as the original ones
		self.toc.read(file,self.header,self.remapTable)
		self.data = file.read()
	def readTOC(self,file):
		self.header.read(file)
		if self.header.majorVersion >= 5 or (self.header.majorVersion == 4 and self.header.minorVersion >= 2) and self.header.featureUseRemapTable:
			tocStartPos = file.tell()
			remapTableOffset = 16 + self.header.entryCount * 48
			if self.header.featureUseUnknTable:
				remapTableOffset += 4#Skip unkn table
			if self.header.featureIsTOCEncrypted:
				remapTableOffset += 128#Encryption key size
			#print(f"Remap table offset: {remapTableOffset}")
			file.seek(remapTableOffset)
			self.remapTable = PakRemapTable()
			print("Loading pak remap table.")
			self.remapTable.read(file)
			
			if self.remapTable.unkn1 != 8:
				print("Warning: Remap table value is not 8, skipping.")
				self.remapTable = None
			file.seek(tocStartPos)
		self.toc.read(file,self.header,self.remapTable)
		
	def write(self,file):#Only for creating patch paks when called by pak utils atm
		self.header.write(file)
		self.toc.write(file)
		for entry in self.toc.entryList:
			file.seek(entry.offset)
			file.write(entry.fileData)
	
	def writeDebug(self,file):#For dumping decrypted pak
		self.header.write(file)
		self.toc.write(file)
		if self.header.feature == 8 or self.header.feature == 24 or self.header.feature == 40:
			if self.header.feature == 24:
				file.seek(4,1)#Skip empty table, used in wilds HD texture pak
			for _ in range(128):#Write dummy encryption key
				write_ubyte(file,255)
		file.write(self.data)
	
def ReadPakTOC(pakPath):
	try:
		if os.path.getsize(pakPath) != 0:#Check for empty paks Capcom puts in when updating to rt versions
			with open(pakPath,"rb") as file:
				pakFile = PakFile()
				pakFile.readTOC(file)
				return pakFile.toc.entryList
		else:
			return []
	except Exception as err:
		print(f"Could not read {pakPath}, skipping. {str(err)}")
		return []

#Not for use with large paks
def readPak(filepath):
	pakFile = None
	try:
		file = open(filepath,"rb")
		pakFile = PakFile()
		pakFile.read(file)
	except:
		raise Exception("Failed to open " + filepath)
	file.close()
	return pakFile

def writePak(pakFile,filepath):
	try:
		file = open(filepath,"wb")
	except:
		raise Exception("Failed to open " + filepath)

	pakFile.write(file)
	file.close()
	
def writePakDecrypted(pakFile,filepath):
	try:
		file = open(filepath,"wb")
	except:
		raise Exception("Failed to open " + filepath)

	pakFile.writeDebug(file)
	file.close()