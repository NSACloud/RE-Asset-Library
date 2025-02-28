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
		
		
	def write(self,file):
		pass#TODO

class PakTOC():
	def __init__(self):
		self.entryList = []
		
	def read(self,file,header):
		
		if header.majorVersion == 2:
			entrySize = PAK_VER_2_ENTRY_SIZE
			entryStruct = ver2EntryStruct
		else:
			entrySize = PAK_VER_4_ENTRY_SIZE
			entryStruct = ver4EntryStruct
		
		
		tocData = file.read(entrySize*header.entryCount)
		
		if header.feature == 8:
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
				
				self.entryList.append(entry)
				#print(entry.offset)
				if entry.hashNameLower == 0:
					raise Exception("Invalidated pak entries found.\nPak files cannot be extracted when mods are installed using Fluffy Manager.\nUninstall any mods and verify integrity of game files on Steam.")
		
	def write(self,file):
		pass#TODO

class PakHeader():
	def __init__(self):
		self.magic = 1095454795
		self.majorVersion = 0
		self.minorVersion = 0
		self.feature = 0
		self.entryCount = 0
		self.fingerprint = 0
		
	def read(self,file):
		self.magic = read_uint(file)
		if self.magic != 1095454795:
			raise Exception("File is not an RE Engine pak file. Cannot import.")
		self.majorVersion = read_ubyte(file)
		self.minorVersion = read_ubyte(file)
		self.feature = read_ushort(file)
		self.entryCount = read_uint(file)
		self.fingerprint = read_uint(file)
		
		
		if self.majorVersion != 2 and self.majorVersion != 4 or self.minorVersion != 0 and self.minorVersion != 1:
			raise Exception(f"Invalid Pak Version ({self.majorVersion}.{self.minorVersion}), expected 2.0, 4.0 & 4.1")
					
		if self.feature != 0 and self.feature != 8:
			raise Exception(f"Unsupported Encryption Type ({self.feature})")
			
	def write(self,file):
		write_uint(file,self.magic)
		write_ubyte(file,self.majorVersion)
		write_ubyte(file,self.minorVersion)
		write_ushort(file,self.feature)
		write_uint(file,self.fingerprint)
		

class PakFile():
	def __init__(self):
		self.header = PakHeader()
		self.toc = PakTOC()
		self.data = bytes()#Unused
	def read(self,file):#For testing, not supposed to be used
		self.header.read(file)
		self.toc.read(file,self.header)
		self.data = file.read()
	def readTOC(self,file):
		self.header.read(file)
		self.toc.read(file,self.header)
		

def ReadPakTOC(pakPath):
	if os.path.getsize(pakPath) != 0:#Check for empty paks Capcom puts in when updating to rt versions
		with open(pakPath,"rb") as file:
			pakFile = PakFile()
			pakFile.readTOC(file)
			return pakFile.toc.entryList
	else:
		return []