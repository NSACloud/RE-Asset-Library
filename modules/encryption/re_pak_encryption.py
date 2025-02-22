#Author: NSA Cloud

#Credit to Ekey, I used REE Pak Tool as a reference for this

from io import BytesIO
from ..gen_functions import read_int64

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
	
pakModulus = 159698812988050218931858239943049262341923379380497049607963099060350749796841519254496552755248247329341478707377115125501762531718759783782383570809803402506531457975457952012594520782163709189669755418441371452643663587642874518466328131049057000622627886084167490189664122550047644173530214666260708854653

pakExponent = 65537

def decryptKey(encryptedKey):

	key = int.from_bytes(encryptedKey,byteorder="little")
	
	result = pow(key,pakExponent,pakModulus)

	return bytearray(result.to_bytes((result.bit_length() + 7) // 8,byteorder="little"))

def decryptData(buffer,encryptedKey):
	key = decryptKey(encryptedKey)
	key.extend(b'\x00')

	if len(key) > 0:
		for i in range(0,len(buffer)):
			val = (i+key[i % 32] * key[i % 29])
			buffer[i] ^= ((i+key[i % 32] * key[i % 29]) % 256)
	return buffer