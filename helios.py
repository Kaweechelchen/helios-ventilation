"""
Helios vent module
"""

import yaml
import requests
import xmltodict
import re
import sys
import json

from influxdb import InfluxDBClient

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
        try:
            rawValues[id] = int(originalValues[idx])
        except ValueError:
            try:
                rawValues[id] = float(originalValues[idx])
            except ValueError:
                rawValues[id] = originalValues[idx]

    return rawValues

def status():
    keys = getKeyNames()
    rawValues = getRawValues()

    values = {}

    for key in keys:
        if key in rawValues:
            values[keys[key]] = rawValues[key]
        else:
            values[keys[key]] = None

    return values

def sensors():
    rawValues = getRawValues()

    sensors = {}

    sensors["internal"] = {}
    sensors["external"] = {}
    sensors["internal"]['temperature'] = {}
    sensors["internal"]['humidity'] = {}
    sensors["external"]['temperature'] = {}

    sensors["internal"]['temperature']["in"] = rawValues["v00105"]
    sensors["internal"]['temperature']["out"] = rawValues["v00107"]
    sensors["internal"]['humidity']["out"] = rawValues["v02136"]
    sensors["external"]['temperature']["in"] = rawValues["v00104"]
    sensors["external"]['temperature']["out"] = rawValues["v00106"]

    return sensors

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

def logStatus():
    influx = InfluxDBClient(config["influx"]["host"], 8086, config["influx"]["user"], config["influx"]["pass"], config["influx"]["db"])

    sensorData = sensors()

    json_body = [
        {
            "measurement": "ventilation",
            "fields": {
                "temperature_external_in":  sensorData['external']['temperature']['in'],
                "temperature_external_out": sensorData['external']['temperature']['out'],
                "temperature_internal_in":  sensorData['internal']['temperature']['in'],
                "temperature_internal_out": sensorData['internal']['temperature']['out'],
                "humidity_internal_out":    sensorData['internal']['humidity']['out']
            }
        }
    ]

    influx.write_points(json_body)

    return json.dumps(json_body)

    #result = influx.write_points(json.dumps(sensors()))

    #return result

if len(sys.argv) > 1:
    FUNCTION_MAP = {
        'speed' : speed,
        'sensors': sensors,
        'status': status,
        'logStatus': logStatus
    }

    if len(sys.argv) > 2:
        func = FUNCTION_MAP[sys.argv[1]]
        print(json.dumps(func(sys.argv[2])))
    else:
        func = FUNCTION_MAP[sys.argv[1]]
        #print(json.dumps(func()))
        print(func())
