import yaml
import sys

from influxdb import InfluxDBClient

from pprint import pprint

with open("config.yml", 'r') as configfile:
    try:
        config = yaml.load(configfile)
    except yaml.YAMLError as exc:
        print(exc)

influx = InfluxDBClient(config["influx"]["host"], 8086, config["influx"]["user"], config["influx"]["pass"], config["influx"]["db"])

def getTemperature(node):
    result = influx.query(
        "SELECT temperature FROM {} WHERE (\"node\" = '{}') ORDER BY time DESC LIMIT 1;".format(config["influx"]["table"], node)
    )
    return result.raw["series"][0]["values"][0][1]

def temperatures():
    return {
        'inside': float(getTemperature(config["node"]["inside"])),
        'outside': float(getTemperature(config["node"]["outside"]))
    }

def diff():
    realTemperatures = temperatures()
    return realTemperatures["inside"] - realTemperatures["outside"]

def canCool():
    return diff() >= 0

if len(sys.argv) > 1:
    FUNCTION_MAP = {
        'canCool' : canCool,
        'diff': diff,
        'temperatures': temperatures
    }

    func = FUNCTION_MAP[sys.argv[1]]
    pprint(func())
