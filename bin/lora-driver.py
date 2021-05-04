#!/usr/bin/env python3

import json
import random
from datetime import datetime

import paho.mqtt.subscribe as subscribe
import redis
import requests

contract = {
    "name": "",
    "description": "",
    "branch": "",
    "model": "",
    "local": "",
    "mac": "",
    "sensors": [{
        "type": "",
        "description": "",
        "name": ""
    }]
}

data = {
    "mac": "",
    "token": "",
    "measures": [{
        "name": "",
        "value": "",
        "date": ""
    }]
}

bbApps = [
    'type-accelerometer', 'type-air-temperature', 'type-animal-speed',
    'type-animal-weight', 'type-black-globe-temperature',
    'type-body-temperature', 'type-ch4', 'type-co2', 'type-dew-point-temperature',
    'type-dry-bulb-temperature', 'type-gate-opened', 'type-gdop',
    'type-geographic-coordinate', 'type-geographic-coordinate',
    'type-gyroscope', 'type-heart-rate', 'type-magnetometer', 'type-ph',
    'type-precipitation', 'type-relative-humidity', 'type-respiratory-frequency',
    'type-retal-temperature', 'type-soil-moisture', 'type-soil-nitrogen',
    'type-soil-temperature', 'type-soil-water-potencial', 'type-solar-radiation',
    'type-water-temperature', 'type-wet-bulb-temperature', 'type-wind-speed'
]

bigboxx = "127.0.0.1"
#bigboxx = "192.168.0.22"
bb_api_port = 3000
api = f"http://{bigboxx}:{bb_api_port}/"

cs_api_port = 8080
cs_api = f'http://{bigboxx}:{cs_api_port}/api'

rdb = redis.Redis(host="192.168.0.100")

subscribe_topic = "application/#"

session = requests.Session()
headers = {"Content-Type": "application/json"}


def getdevEUI():
    devEUI = ''
    for i in range(16):
        devEUI += (hex(random.getrandbits(4))[2:])
    return devEUI


def getappKey():
    appKey = ''
    for i in range(32):
        appKey = appKey + hex(random.getrandbits(4))[2:]
    return appKey


def getCreatedApplications():
    apps = []
    response = session.get(cs_api + '/applications?limit=50&organizationID=1', headers=headers)
    resp = response.json()
    for i in resp['result']:
        apps.append(i['name'])
    return apps


def getSessionJWT():
    body = {
        "email": "admin",
        "password": "admin"
    }

    response = session.post(cs_api + '/internal/login', headers=headers, data=json.dumps(body))
    tk = response.json()
    return tk['jwt']


def getDeviceProfileID():
    response = session.get(cs_api + '/device-profiles?limit=1&organizationID=1', headers=headers)
    device = response.json()
    return device['result'][0]['id']


def getServiceProfileID():
    response = session.get(cs_api + '/service-profiles?limit=1&organizationID=1', headers=headers)
    device = response.json()
    return device['result'][0]['id']


def getAppID(appName):
    response = session.get(cs_api + '/applications?limit=50&organizationID=1&search=' + appName, headers=headers)
    id = response.json()

    return (id['result'][0]['id'])


def createAppKey(devEUI):
    body = {
        'deviceKeys': {
            'appKey': 'string',
            'devEUI': 'string',
            'genAppKey': 'string',
            'nwkKey': 'string'
        }
    }

    body['deviceKeys']['appKey'] = getappKey()
    body['deviceKeys']['devEUI'] = devEUI
    body['deviceKeys']['nwkKey'] = getappKey()

    response = session.post(cs_api + f'/devices/{devEUI}/keys', headers=headers, data=json.dumps(body))


def createDev(appName):
    body = {
        "device": {
            "applicationID": '',
            "description": '',
            "devEUI": '',
            "deviceProfileID": '',
            "isDisabled": False,
            "name": '',
            "referenceAltitude": 0,
            "skipFCntCheck": True,
            "tags": {},
            "variables": {}
        }
    }

    name = appName.split('-')[1:]
    for devType in ('MSB', 'LSB'):
        body['device']['applicationID'] = getAppID(appName)
        body['device']['name'] = 'DEV'
        body['device']['description'] = 'Devices '
        body['device']['devEUI'] = getdevEUI()
        body['device']['deviceProfileID'] = getDeviceProfileID()

        for n in name:
            body['device']['name'] += f'-{n.capitalize()}'
            body['device']['description'] += f' {n.capitalize()}'

        body['device']['name'] += f'-{devType}'
        body['device']['description'] += f' - {devType}'

        response = session.post(cs_api + '/devices', headers=headers, data=json.dumps(body))
        # print(json.dumps(body))
        body['device']['name'] = 'DEV'
        body['device']['description'] = 'Devices '

        createAppKey(body['device']['devEUI'])


def createApp(appName):
    body = {
        "application": {
            "description": "Measurements of: ",
            "id": 1,
            "name": appName,
            "organizationID": "1",
            "payloadCodec": "",
            "payloadDecoderScript": "",
            "payloadEncoderScript": "",
            "serviceProfileID": getServiceProfileID()
        }
    }

    name = appName.split('-')[1:]
    for n in name:
        body['application']['description'] += f' {n.capitalize()}'

    response = session.post(cs_api + '/applications', headers=headers, data=json.dumps(body))

    createDev(appName)


def get_date():
    now = datetime.now()
    return str(now.strftime("%d%m%y%H%M%S"))


def get_macddr(deveui):
    mac_addr = deveui[0:2] + ":" + deveui[2:4] + ":" + \
               deveui[4:6] + ":" + deveui[6:8] + ":" + \
               deveui[8:10] + ":" + deveui[10:12]
    return mac_addr


def get_token(dev_mac):
    token = rdb.get(dev_mac)

    if token.__str__() == "None":
        valid_token = False
    else:
        valid_token = True

    return valid_token, token


def get_message(message):
    msg = json.loads(str(message.payload.decode("utf-8")))
    dev_mac = get_macddr(msg["devEUI"])

    valid_token, token = get_token(dev_mac)

    # Se possui contrato valido
    if valid_token:
        dt = data.copy()
        dt["mac"] = dev_mac
        dt["token"] = bytes.decode(token)
        dt["measures"][0]["name"] = msg["applicationName"]
        dt["measures"][0]["value"] = msg["object"]
        dt["measures"][0]["date"] = get_date()

        response = session.post(api + "measure", headers=headers, data=json.dumps(dt))

    # Se nao tem contrato valido
    else:
        ct = contract.copy()
        ct["mac"] = dev_mac
        ct["name"] = msg["deviceName"]
        ct["model"] = "LoRaDEVICE"
        ct["local"] = "Farm e-Cattle"
        ct["branch"] = "LoRaDEVICE"
        ct["description"] = "Medidor LoRa " + msg["deviceName"]
        ct["sensors"][0]["name"] = msg["applicationName"]
        ct["sensors"][0]["type"] = msg["applicationName"]
        ct["sensors"][0]["description"] = "Medidor LoRa " + msg["deviceName"]

        # POST de requisição do contrato
        response = session.post(api + "device", headers=headers, data=json.dumps(ct))

        response = json.loads(response.text)
        rdb.mset({ct["mac"]: response["token"]})


def on_message(client, userdata, message):
    get_message(message)


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    headers['Authorization'] = getSessionJWT()

    createdApps = getCreatedApplications()
    for item in bbApps:
        if not set([item]) <= set(createdApps):
            createApp(item)

    while True:
        subscribe.callback(on_message, subscribe_topic, hostname=bigboxx)
