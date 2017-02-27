import requests
import json

def callbacks(arg):
    print arg

def get_symbol(symbol):
    url = "http://d.yimg.com/aq/autoc?query="+symbol+"&region=US&lang=en-US&callback="
    result = requests.get(url)
    data = result.json()
    print data
    for x in data['ResultSet']['Result']:
       print x['name'], x['symbol']


company = get_symbol("MSFT")

print(company)