#Author: NSA Cloud
import zstandard as zstd
import zlib
import os
import sys
from multiprocessing import Pool
from time import sleep
import json
from io import BytesIO
import struct
def read_int64(file_object, endian = '<'):
     data = struct.unpack(endian+'q', file_object.read(8))[0]
     return data
#from ..encryption.re_pak_encryption import decryptResource
resourceModulus = 1568686865054570187863272147082498742496103300192247296268169267816005687059

resourceExponent = 509867534609654097950522059535285117929468839027994234503264598402576925376

def decryptResource(buffer):
	with BytesIO(buffer) as stream:
		offset = 0
		blockCount = (len(buffer) - 8) // 128
		decryptedSize = read_int64(stream)
		
		resultData = bytearray(decryptedSize+1)
		for _ in range(0,blockCount):
			key = int.from_bytes(stream.read(64),byteorder="little")
			data = int.from_bytes(stream.read(64),byteorder="little")
			
			
			mod = pow(key,resourceExponent,resourceModulus)
			result = data // mod
			
			decryptedBlock = result.to_bytes((result.bit_length() + 7) // 8,byteorder="little")
			resultData[offset:offset+len(decryptedBlock)] = decryptedBlock
			offset+=8
		return resultData

class CompressionTypes:
	COMPRESSION_TYPE_NONE = 0
	COMPRESSION_TYPE_DEFLATE = 1
	COMPRESSION_TYPE_ZSTD = 2

def pakExtractor(jobDict):
	jobIndex = jobDict["jobIndex"]
	#print(f"Extraction Job {str(jobIndex).zfill(2)} Started")
	#sys.stdout.flush()
	outDir = jobDict["outDir"]
	pakPath = jobDict["pakPath"]
	decompressorZSTD = zstd.ZstdDecompressor()
	
	#decompressorDeflate = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
	with open(pakPath,"rb") as pakStream:
		
		
		for entry in jobDict["fileEntries"]:
			try:
				pakStream.seek(entry["offset"])
				fileData = pakStream.read(entry["compressedSize"])
				if entry["encryptionType"] > 0:
					#print(f"Encrypted file ({entry.encryptionType}):{filePath}]")
					fileData = decryptResource(fileData)
				
				match entry["compressionType"]:
					case CompressionTypes.COMPRESSION_TYPE_DEFLATE:
						#print("Deflate Compression")
						fileData = zlib.decompress(fileData,wbits=-zlib.MAX_WBITS)
						pass#TODO
					case CompressionTypes.COMPRESSION_TYPE_ZSTD:
						#print("ZSTD Compression")
						fileData = decompressorZSTD.decompress(fileData)
				
				outPath = os.path.join(outDir,entry["filePath"])
				os.makedirs(os.path.split(outPath)[0],exist_ok=True)
				with open(outPath,"wb") as outFile:
					outFile.write(fileData)
			except Exception as err:
				print("Failed to extract " + entry["filePath"] + f" {str(err)}")
				
				#print(f"Extracted {outPath}")
			
	#print(f" Extraction Job {str(jobIndex+1).zfill(2)} Finished")
	sys.stdout.write(f"Extraction Job {str(jobIndex+1).zfill(2)} Finished")
	sys.stdout.flush()
	return True

def runPakExtractJob(jobJSONPath):
	try:
		with open(jobJSONPath,"r", encoding ="utf-8") as file:
			jobJSONDict = json.load(file)
		print("Loaded job JSON.")
	except Exception as e:
		print(f"Error reading the extraction job JSON: {e}")
    # Create a pool of workers to extract the files in parallel
	print("Starting " + str(jobJSONDict["maxThreads"])+ " pak extraction jobs.")
	jobCount = len(jobJSONDict["jobList"])
	print(f"{jobCount} jobs to process.")
	
	print("\nThis may take a long time depending on the speed of your CPU and hard drive.")
	print("Don't worry if it looks stuck, it will finish eventually.\n")
	with Pool(processes=jobJSONDict["maxThreads"]) as pool:
		#print(jobJSONDict["jobList"])
		results = pool.imap_unordered(func=pakExtractor, iterable = jobJSONDict["jobList"],chunksize = 1)
		for i, results in enumerate(results):
			sys.stdout.write(f" ({i+1} of {jobCount})\n")
			sys.stdout.flush()
		
TEMPDIR = os.path.join(os.path.abspath(os.path.split(__file__)[0]),"TEMP")
JOB_JSON_NAME = os.path.join(TEMPDIR,"TEMP_PAK_EXTRACT_JOB.json")
if __name__ == '__main__':
	print("Subprocess started.")

	# Check if the file exists
	if os.path.isfile(JOB_JSON_NAME):
		runPakExtractJob(JOB_JSON_NAME)
	else:
		print(f"The file {os.path.split(JOB_JSON_NAME)[1]} does not exist.")