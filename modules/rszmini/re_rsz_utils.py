#Author: NSA Cloud
import os

from ..gen_functions import read_uint

from .file_re_scn import SCNFile
from .file_re_pfb import PFBFile
from .file_re_user import UserFile
from .file_re_rsz import RSZFile


def ReadRSZAutoDetectType(stream,game="MHRise",shortRead = False):#Game doesn't matter since this a stripped down version that doesn't parse the instances
	startPos = stream.tell()
	try:
		magic = read_uint(stream)
	except:
		magic = 0
	stream.seek(startPos)
	rszFile = None
	match magic:
		case 5129043:#SCN
			rszFile = SCNFile()
			
			pass
		case 5395285:#USER
			rszFile = UserFile()
			pass
		case 4343376:#PFB
			rszFile = PFBFile()
			pass
		case 5919570:#RSZ
			rszFile = RSZFile()
		case _:
			print(f"Unsupported RSZ Magic: {magic}")
			
			
	if rszFile != None:
		if shortRead:
			rszFile.short_read(file = stream, game = game)
		else:
			rszFile.read(file = stream, game = game)
	return rszFile

def WriteRSZFile(rszFile,filePath,game = "MHRise"):#Game doesn't matter, it's kept for compatibility with the full rsz parser
	with open(filePath,"wb") as file:
		rszFile.write(file,game)
def getRSZResourcePaths(stream):
	rszFile = ReadRSZAutoDetectType(stream,shortRead = True)
	if rszFile != None:
		if rszFile.Header.magic == 5919570:# Is Embedded RSZ
			results = {entry.string for entry in rszFile.RSZUserDataInfoList}
		else:
			results = {entry.string for entry in rszFile.ResourceInfoList} | {entry.string for entry in rszFile.UserDataInfoList} | {entry.string for entry in rszFile.rsz.RSZUserDataInfoList}
	return results

def getRSZInstanceTypeIDs(stream):#Gets all Type ID hashes used for instances
	rszFile = ReadRSZAutoDetectType(stream,shortRead = True)
	results = set()
	if rszFile != None:
		if rszFile.Header.magic == 5919570:# Is Embedded RSZ
			results = {entry.typeIDHash for entry in rszFile.InstanceInfoList}
		else:
			results = {entry.typeIDHash for entry in rszFile.rsz.InstanceInfoList}
	return results

def getRSZCRCs(stream):#Returns dict of TypeID > CRC
	rszFile = ReadRSZAutoDetectType(stream,shortRead = True)
	results = dict()
	if rszFile != None:
		if rszFile.Header.magic == 5919570:# Is Embedded RSZ
			results = {entry.typeIDHash : entry.CRC for entry in rszFile.InstanceInfoList}
		else:
			results = {entry.typeIDHash : entry.CRC for entry in rszFile.rsz.InstanceInfoList}
	return results

