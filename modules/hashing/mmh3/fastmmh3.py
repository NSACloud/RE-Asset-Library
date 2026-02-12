import ctypes
from ctypes import c_bool, c_uint8, c_uint32, c_uint64, POINTER, byref, c_void_p,c_int
from pathlib import Path
from typing import Union

import platform

def is_windows():
    return platform.system() == 'Windows'


def is_linux():
    return platform.system() == 'Linux'


def is_mac():
    return platform.system() == 'Darwin'

class FastMMH3:
    def __init__(self, dll_path: Union[str, Path] = None):
        if dll_path is None:
            # Try to find the DLL next to the .py file first
            module_dir = Path(__file__).parent.absolute()
			
            if is_windows():
                dll_name = "fastMMH3Wrapper.dll"
            elif is_linux():
                dll_name = "fastMMH3Wrapper.so"
			#elif is_mac():
				#Maybe TODO
            else:
                raise RuntimeError(f'This OS ({platform.system()}) is unsupported.')
            possible_paths = [
                module_dir / dll_name,           # Next to .py file
                Path.cwd() / dll_name,           # Current working directory
                dll_name,                        # System PATH
            ]
            
            for path in possible_paths:
                try:
                    self._dll = ctypes.CDLL(str(path))
                    break
                except OSError:
                    continue
            else:
                raise Exception(
                    f"Could not find {dll_name} in any of these locations:\n" + 
                    "\n".join(f"- {p}" for p in possible_paths)
                )
        else:
            try:
                self._dll = ctypes.CDLL(str(dll_path))
            except OSError as e:
                raise Exception(f"Failed to load FastMMH3 DLL from {dll_path}: {e}")
        
        self._dll.murmurhash3_32.argtypes = [c_void_p, c_int, c_uint32]
        self._dll.murmurhash3_32.restype = c_uint32
    
        self._dll.pakHash.argtypes = [c_void_p, c_int,c_void_p, c_int, c_uint32]
        self._dll.pakHash.restype = c_uint64
    def hashUTF16(self,string,seed = -1):
        data = bytes(string,"utf-16le")
        return self._dll.murmurhash3_32(data, len(data), seed)
    
    def hashUTF8(self,string,seed = -1):
        data = bytes(string,"utf-8")
        return self._dll.murmurhash3_32(data, len(data), seed)
	
    def pakHash(self,string):
        dataA = bytes(string.lower(),"utf-16le")
        dataB = bytes(string.upper(),"utf-16le")
        return self._dll.pakHash(dataA, len(dataA),dataB, len(dataB), -1)