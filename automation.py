import helios
import realtemp

from pprint import pprint

if realtemp.canCool():
    if realtemp.temperatures()["inside"] > 23 and realtemp.temperatures()["outside"] < 21:
        result = helios.speed(3)
    else:
        result = helios.speed('auto')
else:
    result = helios.speed(0)

pprint(result)
