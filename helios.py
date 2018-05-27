"""
Helios vent module
"""

import yaml
import requests
import xmltodict
import re

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
    callWithPass(
        url = 'http://{}/info.htm'.format(config["host"]),
        data = 'v00102={}'.format(speed)
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

def speed(value = None):
    if value:
        setSpeed(int(value))
    else:
        rawValues = getRawValues()
        return int(rawValues["v00102"])
