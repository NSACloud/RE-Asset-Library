#Author: NSA Cloud

#Requires binary2strings > pip install binary2strings

from modules.pak.re_pak_utils import debugDataIterator,scanForPakFiles
import binary2strings as b2s

MIN_LENGTH = 8
MAX_LENGTH = 250

GAME_DIR = r"J:\SteamLibrary\steamapps\common\Street Fighter 6"

stringOutPath = r"D:\EXTRACT\SF6_EXTRACT\DUMP\pathStringDump_SF6.txt"

pakList = scanForPakFiles(GAME_DIR)

#Uncomment to specify only specific paks

#pakList = [
#	r"J:\SteamLibrary\steamapps\common\Street Fighter 6\re_chunk_000.pak.patch_016.pak",
#	r"J:\SteamLibrary\steamapps\common\Street Fighter 6\re_chunk_000.pak.patch_008.pak",
#	]
uniqueStringSet = set()


knownExtensions = tuple(['.abcmesh', '.aeeq', '.aesr', '.aimap', '.aimapattr', '.ainvm', '.ainvmmgr', '.aivspc', '.aiwayp', '.aiwaypmgr', '.amix', '.areamap', '.areaquery', '.asrc', '.auto', '.bhvt', '.bnk', '.ccbk', '.cdef', '.cfil', '.chain', '.chain2', '.chainwnd', '.chf', '.clip', '.clo', '.clrp', '.clsm', '.clsp', '.cmat', '.coco', '.csdf', '.cset', '.dblc', '.def', '.dlg', '.dlgcf', '.dlglist', '.dlgtml', '.eem', '.efcsv', '.efx', '.fbik', '.fbxskel', '.fchar', '.fcmndatals', '.fextdata', '.filter', '.finf', '.fol', '.fpolygon', '.fslt', '.fsm', '.fsmv2', '.fsubchar', '.fxct', '.gcf', '.gclo', '.gcp', '.gml', '.gpbf', '.gpuc', '.gpumotlist', '.grnd', '.gsty', '.gtl', '.gui', '.guisd', '.hapvib', '.havokcloth', '.hf', '.htex', '.ies', '.ift', '.ikbodyrig', '.ikdamage', '.ikfs', '.ikhd', '.ikleg2', '.iklizard', '.iklookat2', '.ikls', '.ikmulti', '.ikspinecg', '.iktrain', '.iktrain2', '.ikwagon', '.jcns', '.jmap', '.jntexprgraph', '.jointlodgroup', '.lfa', '.lmap', '.lod', '.lprb', '.mame', '.mameac', '.mcambank', '.mcamlist', '.mcol', '.mdf2', '.mesh', '.mlgd', '.mmtr', '.mmtrs', '.mot', '.motbank', '.motcam', '.motfsm', '.motfsm2', '.motlist', '.mottree', '.mov', '.mpci', '.msg', '.nar', '.ncf', '.nmr', '.nnfp', '.ocioc', '.oft', '.ord', '.pci', '.pck', '.pfb', '.pog', '.poglst', '.prb', '.psop', '.rbd', '.rbs', '.rcf', '.rcfg', '.rcol', '.rdc', '.rdd', '.rdl', '.retargetrig', '.rmesh', '.road', '.rtbs', '.rtex', '.rtmr', '.sbd', '.sbnk', '.scn', '.sdf', '.sdftex', '.sfur', '.skeleton', '.spck', '.spmdl', '.spmt', '.sss', '.sst', '.star', '.stmesh', '.strands', '.sts', '.swms', '.tean', '.terr', '.tex', '.tml', '.tmlbld', '.tmlfsm2', '.trtd', '.ucurve', '.ucurvelist', '.user', '.uvar', '.uvs', '.vmap', '.vsdf', '.vsdflist', '.vsrc', '.wcbk', '.wcc', '.wcggp', '.wcgp', '.wcja', '.wcjm', '.wcjmv', '.wcjr', '.wcmo', '.wcms', '.wcmsw', '.wcmts', '.wcp', '.wcr', '.wcrb', '.wcrd', '.wcsa', '.wcsf', '.wcss', '.wcst', '.wcsw', '.wcswn', '.wcta', '.wcv', '.wel', '.wfa', '.wgs', '.wid', '.wlqg', '.wms', '.wpi', '.wrap', '.wss', '.wtos', '.wtot', '.ziva', '.zivacomb'])

#--------------------

#TODO Make this multiprocessed and parse files with known formats rather than scanning their binary to ensure as many paths as possible are found

print("Extracting paths from pak files...")
with open(stringOutPath,"w",encoding = "utf-8") as outFile: 
	for data in debugDataIterator(pakList):
		#print(len(data))
		for (string, type, span, is_interesting) in b2s.extract_all_strings(data, only_interesting=True):
			splitString = string.split("\n")
			for newString in splitString:
				newString = newString.strip().replace("@","")
				if newString.count("/") >= 2 and len(newString) >= MIN_LENGTH and len(newString) <= MAX_LENGTH and newString.count(".") == 1 and newString.endswith(knownExtensions):
					#print(len(newString))
					if newString not in uniqueStringSet:
						uniqueStringSet.add(newString)
						outFile.write(f"{newString}\n")
						#print(f"{type}:{is_interesting}:{string}")
			
	print("Done")