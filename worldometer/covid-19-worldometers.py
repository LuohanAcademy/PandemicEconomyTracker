# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 10:04:56 2021

@author: wb-zkw663436
"""
from covid_daily.constants import AVAILABLE_COUNTRIES
import requests
from lxml.html import fromstring
import re
import json
from datetime import datetime
import pandas as pd
import time
import socket


socket.setdefaulttimeout(20)
lines = re.compile(r'[\n\t]')
comments = re.compile(r'\/\*(.*?)\*\/')
spaces = re.compile(r'[ ]{2,}')
chart = re.compile(r'(Highcharts\.chart\(\"[a-zA-z\-]*\"\, )(.*?)(\}\)\;)')
chart_title = re.compile(r'(Highcharts\.chart\(\"[a-zA-z\-]*\"\, )')
chart_end = re.compile(r'\)\;')
options = re.compile(r' [\w]+\: ')
xaxis = re.compile(r'(\"xAxis\"\: \{)(.*?)(\}\,)')
yaxis = re.compile(r'(\"yAxis\"\: \{ \"title\"\: \{ \"text\"\: \")(.*?)(\")')
series = re.compile(r'(\"series\"\: \[\{)(.*?)(\}( ){0,}\]\,)')


tags = AVAILABLE_COUNTRIES
result = pd.DataFrame(columns=('date','index_value','country','index_name'))

for tag in tags:
    url = f"https://www.worldometers.info/coronavirus/country/{tag}/"
    
    print(f"Retrieving Coronavirus data from Country with Tag: {tag}")
    
    req = requests.get(url)
    
    if req.status_code != 200:
        continue
        
    root = fromstring(req.text)
    scripts = root.xpath(".//script")
    
    for script in scripts:
        if not script.text_content().strip().__contains__("Highcharts.chart"):
            continue
            
        value = script.text_content().strip()
        real_value = script.text_content().strip()
        
        value = lines.sub('', value)
        value = comments.sub('', value)
        value = spaces.sub(' ', value)
        value = value.replace('\'', '\"')
        value = chart.search(value).group(0)
        
        title = chart_title.search(value).group(0).replace('Highcharts.chart(\"', '').replace('\", ', '')
        
        value = chart_title.sub('', value)
        value = chart_end.sub('', value)

        words = options.findall(value)
        for word in words:
            value = value.replace(word, ' \"' + word.replace(' ', '').replace(':', '') + '\": ')
            
        column = yaxis.search(value).group(0).replace('"yAxis": { "title": { "text": "', '').replace('"', '')
        
        value = '{' + ', '.join([
            xaxis.search(value).group(0).replace('},', '}'),
            series.search(value).group(0)[::-1].replace(',]', ']', 1)[::-1].replace(', }', ' }')
        ]) + '}'
        
        value = json.loads(value)

        x = value['series'][0]['data']
        #y = [datetime.strptime(val, '%b %d, %Y') for val in value['xAxis']['categories']]
        data = pd.DataFrame({'date': value['xAxis']['categories'], 'index_value': x})
        data['country'] = tag
        data['index_name'] = title
        result = pd.concat([result,data],axis=0)
    time.sleep(2)


result.to_excel('covid-data.xlsx','Sheet1')



