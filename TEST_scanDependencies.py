#Author: NSA Cloud

from modules.pak.re_pak_utils import getMDFReferences
from modules.mdf.file_re_mdf import readMDF
MDF_PATH = r"D:\EXTRACT\RE4_EXTRACT\re_chunk_000\natives\STM\_Chainsaw\Character\ch\cha0\cha000\00\cha000_00.mdf2.32"

mdfFile = readMDF(MDF_PATH)
resultSet = getMDFReferences(mdfFile)

print(resultSet)