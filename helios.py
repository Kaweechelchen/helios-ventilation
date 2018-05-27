"""
Helios vent module
"""

import yaml
import requests
import xmltodict
import re
import sys

from pprint import pprint

with open("config.yml", 'r') as configfile:
    try:
        config = yaml.load(configfile)
    except yaml.YAMLError as exc:
        print(exc)

def call(url, data):
    try:
        request = requests.post(url, data=data)
        request.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        print (err)
    return request

def callWithPass(url, data):
    call(
        url = url,
        data = 'v00402={}&'.format(config["password"]) + data
    )

# Check if authentication works and log in current session
login = callWithPass(
    url = 'http://{}/info.htm'.format(config["host"]),
    data = 'v00402={}'.format(config["password"])
)

def setSpeed(speed):
    if speed == 'auto':
        # auto: v00101 = 0
        # manu: v00101 = 1
        callWithPass(
            url = 'http://{}/info.htm'.format(config["host"]),
            data = 'v00101=0'
        )
    else:
        callWithPass(
            url = 'http://{}/info.htm'.format(config["host"]),
            data = 'v00102={}&v00101=1'.format(int(speed))
        )

def getKeyNames():
    originalKeyNames = requests.get('http://{}/data/lab8_en.xml'.format(config["host"])).text

    originalKeyNames = xmltodict.parse(originalKeyNames)

    originalIds = originalKeyNames["PARAMETER"]["ID"]
    originalKeys = originalKeyNames["PARAMETER"]["VL"]

    keyNames = {}

    for idx, id in enumerate(originalIds):
        originalKey = re.search('(?:\d\s)?([^:\d\n]+)(?::)?', originalKeys[idx]).group(1)
        keyNames[id] = originalKey

    return keyNames

# Read data from vent system:
def getRawValues():
    originalValues = call(
        url = 'http://{}/data/werte8.xml'.format(config["host"]),
        data = 'xml=/data/werte8.xml'
    ).text

    originalValues = xmltodict.parse(originalValues)

    originalIds = originalValues["PARAMETER"]["ID"]
    originalValues = originalValues["PARAMETER"]["VA"]

    rawValues = {}

    for idx, id in enumerate(originalIds):
        rawValues[id] = originalValues[idx]

    return rawValues

def status():
    keys = getKeyNames()
    rawValues = getRawValues()

    values = {}

    for key in keys:
        if key in rawValues:
            try:
                values[keys[key]] = int(rawValues[key])
            except ValueError:
                try:
                    values[keys[key]] = float(rawValues[key])
                except ValueError:
                    values[keys[key]] = rawValues[key]
        else:
            values[keys[key]] = None

    return values

def temperatures():
    rawValues = getRawValues()

    temperatures = {}

    temperatures["internal"] = {}
    temperatures["external"] = {}

    temperatures["internal"]["in"] = rawValues["v00105"]
    temperatures["internal"]["out"] = rawValues["v00107"]
    temperatures["external"]["in"] = rawValues["v00104"]
    temperatures["external"]["out"] = rawValues["v00106"]

    return temperatures

def speed(value = -1):
    if value == 'auto':
        setSpeed('auto')
    elif int(value) >= 0:
        setSpeed(int(value))
    rawValues = getRawValues()

    modeMap = {
        0: 'auto',
        1: 'manual'
    }

    return {
        'mode': modeMap[int(rawValues["v00101"])],
        'speed': int(rawValues["v00102"])
    }

if len(sys.argv) > 1:
    FUNCTION_MAP = {
        'speed' : speed,
        'temperatures': temperatures,
        'status': status
    }

    if len(sys.argv) > 2:
        func = FUNCTION_MAP[sys.argv[1]]
        pprint(func(sys.argv[2]))
    else:
        func = FUNCTION_MAP[sys.argv[1]]
        pprint(func())
