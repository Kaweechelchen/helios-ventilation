import helios
import realtemp
import yaml

from pprint import pprint

with open("config.yml", 'r') as configfile:
    try:
        config = yaml.load(configfile)
    except yaml.YAMLError as exc:
        print(exc)

if realtemp.canCool():
    if realtemp.temperatures()["inside"] > config["override"]["aboveTemp"] and realtemp.diff() > config["override"]["difference"]:
        result = helios.speed(3)
    else:
        result = helios.speed('auto')
else:
    result = helios.speed(0)

pprint(result)
