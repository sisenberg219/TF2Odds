from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import psycopg2
import xlsxwriter
import re


#Crates 6,22,35,36,46,48,51,52,53,74,78,79,86,88,89 can no longer be opened
#Crates 1-18 Have No Stranges
#Crates 19-81 Will drop Strange Weapons
#Crate 81+ that are not cases will drop weapons of a strange quality and sometimes cosmetics of a strange quality

#SteamAPI Key
sKey = ""

#Backpack.tf API key constructor
key = "" 
url = "https://backpack.tf/api/IGetCurrencies/v1?key={0}".format(key)
response = requests.get(url).json()

#WebAPI GetSchemaItems Constructor
ID = "https://api.steampowered.com/IEconItems_440/GetSchemaItems/v0001/?key={0}".format(sKey)
sID = requests.get(ID).json()


dict = [
    {'name': "Test" ,'id': "AmongUs", 'type': ""}
       ]


start = [0, 1150,8198,9230,10233,11252,12257,30032,31228]

for i in range(len(start)):
    sValue = start[i]
    ID = "https://api.steampowered.com/IEconItems_440/GetSchemaItems/v0001/?key={0}&start={1}".format(sKey,sValue)
    sID = requests.get(ID).json()
    count = 0
    for i in sID["result"]['items']:
        dict.append({'name': i['name'], 'id': i['defindex'], 'type': i['item_class']})

#Edge Cases for items who's API Get names do not match the Dataframe Names in a way that can be solved by slicing the String. Manually reviewed by seeing which Rows do not have any entry in their Can_Be_Strange Column
for j in range(len(dict)):
    if dict[j]['name'] == "Elf Defence":
        dict[j]['name'] = "Elf Defense"

    if dict[j]['name'] == "Panic Attack Shotgun":
        dict[j]['name'] = "Panic Attack"
        
    if dict[j]['name'] == "The Claidheamohmor":
        dict[j]['name'] = "Claidheamh Mòr"
        
    if dict[j]['name'] == "Strange Part: Ally Healing Done":
        dict[j]['name'] = "Strange Part: Allied Healing Done" 
                 
for i in range(len(dict)):
    #if "The" in dict[i]['name'] and 'weapon' in dict[i]['type']:
    if "The" in dict[i]['name']: 
        dict[i]['name'] = dict[i]['name'][4:]
       

#Item Quality Values = Strange(11), Unique(6)
#appid, tradable and craftable are always constant values. Tf2 has an appid of 440 and uncrated items are always Tradable and Craftable. 
qValue = 0
phURL = "https://backpack.tf/api/IGetPriceHistory/v1?key=629a61f673e8b141fa664108&appid=440&item={0}&quality={1}&tradable=Tradable&craftable=Craftable".format("itemName",qValue)


#constructor for the website that will be scraped
base_url = "https://wiki.teamfortress.com/wiki/Mann_Co._Supply_Crate"
active = base_url + "/Active_series"
retired = base_url + "/Retired_series" 

#Array of crate# that cannot be currently opened. These will be excluded from the final csv file
noOpen = [6,22,35,36,46,48,51,52,53,74,78,79,86,88,89]
crateNames = []
itemIDs = {}

#Scrapes all of the tables in the URl and stores them as seperate dataFrames
dfs = pd.read_html(active)

#constructor allowing user to store multiple sheets inside of an excel file
writer = pd.ExcelWriter('crates.xlsx', engine='xlsxwriter')


for i in range(len(dfs)):
    df = dfs[i]
    cNum = len(df.columns)
    df.columns = df.columns.map(str) #Sets the values of each column header to a string to later be iterable
    sheetName = df.columns[0] 
    
    #Loop to store cases/non traditional crates. Proof of concept. Will be finished when odds can be properly calculated
    #if sheetName != "0" and cNum != 3: #Cases will have 12 elements
        #df.columns= ['Item_Name','Item_Drop_Odds','Test','2','3','4','5','6','7','S8','9','10']
        #df = pd.DataFrame(df.values.ravel(),columns=['Item_Name'])
        #df.dropna(how='all', inplace=True)
        #df.drop_duplicates(subset=['Item_Name'],inplace=True)
        #df = df[df['Item_Name'].str.contains('Drop rate is an estimate only.|Items obtained from this crate might have the Strange quality.|(Items in this crate cannot be Strange or Unusual.)|(Contents may be Strange or Unusual with an Unusual Weapon effect.)') == False]
        #itemDrop = []
        #df['Item_Drop_Odds'] = pd.NaT
        #df.reset_index(drop=True, inplace=True)
        #df.to_excel(writer, sheet_name=sheetName)
        
    if sheetName != "0" and cNum == 3: #All Crates will have 3 elements
        df.columns= ['Item_Name','Test','Item_Drop_Odds']
        df2 = df[['Item_Name', 'Item_Drop_Odds']]
        df2 = df2.replace('Item_Drop_Odds', str('NaN'))
        df2['Can_Be_Strange'] = ""
        df2['itemID'] = ""
        df2.dropna(inplace = True)
        df2.drop([0,1], inplace=True)
        df2 = df2[df2['Item_Drop_Odds'].str.contains('Drop rate is an estimate only.|Items obtained from this crate might have the Strange quality.|Weapons obtained from this crate will have the Strange quality.') == False]   
        df2.reset_index(drop=True, inplace=True)
        temp = re.search('\d+', sheetName ).group()
        crateName = int(temp)
 
        if crateName >= 82:
            for row in df2.itertuples():
                for i in range(len(dict)):
                    if row[1] == dict[i]['name']:
                        if 'weapon' in dict[i]['type']:
                            df2.at[row.Index,"Can_Be_Strange"] = "Always"
                            df2.at[row.Index,"itemID"] = dict[i]['id']
                        elif 'wearable' in dict[i]['type']:
                            df2.at[row.Index,"Can_Be_Strange"] = "Yes"
                            df2.at[row.Index,"itemID"] = dict[i]['id']
                        else:
                            df2.at[row.Index,"Can_Be_Strange"] = "No"
                            df2.at[row.Index,"itemID"] = dict[i]['id']
                    if row[1] == 'or an Exceedingly Rare Special Item!':
                            df2.at[row.Index,"Can_Be_Strange"] = "Yes"
                            df2.at[row.Index,"itemID"] = '999999'
            
                            
        if crateName <= 81 and crateName >= 18:
            for row in df2.itertuples():
                for i in range(len(dict)):
                    if row[1] in dict[i]['name']:
                        if 'weapon' in dict[i]['type']: 
                            df2.at[row.Index,"Can_Be_Strange"] = "Always"
                            df2.at[row.Index,"itemID"] = dict[i]['id']
                        else:
                            df2.at[row.Index,"Can_Be_Strange"] = "No"
                            df2.at[row.Index,"itemID"] = dict[i]['id']
                    if row[1] == 'or an Exceedingly Rare Special Item!':
                            df2.at[row.Index,"Can_Be_Strange"] = "No"
                            df2.at[row.Index,"itemID"] = '999999'
        
        if crateName < 18:
            for row in df2.itertuples():
                for i in range(len(dict)):
                    df2.at[row.Index,"Can_Be_Strange"] = "No"
                    df2.at[row.Index,"itemID"] = dict[i]['id']
                if row[1] == 'or an Exceedingly Rare Special Item!':
                            df2.at[row.Index,"Can_Be_Strange"] = "No"
                            df2.at[row.Index,"itemID"] = 999999    
    
        df2.set_index('itemID', inplace=True)  
        df2.to_excel(writer, sheet_name=sheetName)
        df2.to_csv(sheetName +".csv")

writer.save()
print("Jobs Done :D")
