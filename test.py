import requests
import certifi
from bs4 import BeautifulSoup
import lxml
from datetime import datetime

def TWSE():
    YMD = datetime.now().strftime('%Y%m%d')
    YMD = str(20171110)
    res = requests.get('http://www.twse.com.tw/exchangeReport/MI_INDEX?response=html&date='+YMD+'&type=MS')

    soup = BeautifulSoup(res.text, 'html.parser')
    TWSE = soup.table.find_all('td')[11].text.replace(',',"")
    return TWSE


print TWSE()
