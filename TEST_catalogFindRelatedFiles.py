#Author: NSA Cloud

from modules.asset.re_asset_utils import loadGameInfo,catalogGetAllFilesInDir

CATALOG_PATH = r"J:\REAssetLibrary\RE4\REAssetCatalog_RE4.tsv"

TEST_DIR = r"_Chainsaw\Character\ch\cha0\cha000\00"

GAME_INFO_PATH =  r"J:\REAssetLibrary\RE4\GameInfo_RE4.json"
gameInfo = loadGameInfo(GAME_INFO_PATH)

resultSet = catalogGetAllFilesInDir(CATALOG_PATH, TEST_DIR, gameInfo)

print(resultSet)