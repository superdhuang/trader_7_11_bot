#coding:utf-8
# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import webapp2
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from requests_toolbelt.adapters import appengine

from urllib3 import PoolManager
from urllib3.contrib.appengine import AppEngineManager, is_appengine_sandbox

if is_appengine_sandbox():
    # AppEngineManager uses AppEngine's URLFetch API behind the scenes
    http = AppEngineManager()
else:
    # PoolManager uses a socket-level API behind the scenes
    http = PoolManager()

appengine.monkeypatch()

# 取得加權指數
def GetTWSE():
    YMD = datetime.now().strftime('%Y%m%d')
    res = requests.get('http://www.twse.com.tw/exchangeReport/MI_INDEX?response=html&date='+YMD+'&type=MS')
    if len(res.text) > 1000: # check if data exists
        soup = BeautifulSoup(res.text, 'html.parser')
        TWSE = soup.table.find_all('td')[11].text.replace(',',"")
    else:
        TWSE = str("no data")
    return TWSE 

#取得期貨收盤價
def GetTXF1():
    Y = datetime.now().strftime('%Y')
    M = datetime.now().strftime('%m')
    D = datetime.now().strftime('%d')
    keys = {'syear': Y, 'smonth': M, 'sday': D}
    res = requests.get('http://www.taifex.com.tw/chinese/3/3_1_1.asp')

    soup = BeautifulSoup(res.text, 'lxml')
    contract = soup.select('table')[2].select('table')[1].select('td')[1].text
    close = soup.select('table')[2].select('table')[1].select('td')[5].text
    return contract, close

#取得三大法人買賣超
def GetLpDiffVol():
    Y = datetime.now().strftime('%Y')
    M = datetime.now().strftime('%m')
    D = datetime.now().strftime('%d')
    keys = {'syear': Y, 'smonth': M, 'sday': D}
    res = requests.get('http://www.twse.com.tw/fund/BFI82U?response=html&dayDate=&weekDate=&monthDate=&type=day')

    soup = BeautifulSoup(res.text, 'lxml')
    lpvoldiff = soup.select('table')[0].select('td')[19].text
    return lpvoldiff

#取得成交量
def GetTotVol():
    res = requests.get('http://www.twse.com.tw/exchangeReport/FMTQIK?response=html&date=')

    soup = BeautifulSoup(res.text, 'lxml')
    totvol = soup.select('table')[0].select('td')[-4].text 
    return totvol

#送訊息至Line,ifttt
def sendLineEvent(twse,txf1,voldiff,totvol):
    Y = datetime.now().strftime('%Y')
    M = datetime.now().strftime('%m')
    D = datetime.now().strftime('%d')

    diff = float(txf1) - float(twse)
    evt = ''
    if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
      # Production
        evt = 'get_tw_info'
    else:
      # Local development server
        evt = 'get_tw_info_dev'
    diff_per = round(((100*float(diff))/float(twse)), 3)
    msg = Y+'/'+M+'/'+D+'台灣盤後資料<br>'
    msg += '大盤指數:'+str(twse)+'<br>期貨近月:'+str(txf1)+'<br>正逆價差:'+str(diff)+'('+str(diff_per)+'%)'+'<br>總成交量:'+str(totvol)+'億<br>外資買賣:'+str(voldiff)+'億'
    payload = {"value1":msg}
    print(payload)
    r = requests.post('https://maker.ifttt.com/trigger/'+evt+'/with/key/drajffDtgBqECN8jfUSQJF',json=payload)
    print r.text
    r = requests.post('https://maker.ifttt.com/trigger/get_tw_info_dev/with/key/drajffDtgBqECN8jfUSQJF',json=payload)

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        # get all information
        t = GetTWSE()
        contract, c = GetTXF1()
        diff = float(c) - float(t)
        voldiff = GetLpDiffVol().replace(',','')
        totvol  = GetTotVol().replace(',','')
        voldiff_shift = int(voldiff) // 100000000 # convert to 0.1B
        totvol_shift  = int(totvol) // 100000000 # convert to 0.1B

        sendLineEvent(t, c, voldiff_shift, totvol_shift)
        self.response.write(t+'--'+c+'--'+str(diff)+'--'+contract+'--'+str(voldiff_shift)+'--'+str(totvol_shift))

app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
