# from ..crelds import ADO_TOKEN
import os

try:
   ADO_TOKEN = os.environ["ADO_TOKEN"]
   # print(ADO_TOKEN)
except KeyError:
   print("Please set the environment variable ADO_TOKEN")

QUERY_ID = "abb94139-79de-4924-b2f1-73468d05fc20"
QUERY_LINK = "https://dev.azure.com/HAL-LMKRD/RESDEV/_apis/wit/queries/"
WIQL_LINK = "https://dev.azure.com/HAL-LMKRD/RESDEV/_apis/wit/wiql/"
HEADERS = {'Content-type': 'application/json'}
DB_NAME = "ado.db"