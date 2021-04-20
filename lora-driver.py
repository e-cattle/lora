import json
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

# bigboxx = "127.0.0.1"
bigboxx = "192.168.0.22"
api_port = 3000
api = f"http://{bigboxx}:{api_port}/"
rdb = redis.Redis(host="192.168.0.100")

subscribe_topic = "application/#"

session = requests.Session()
headers = {"Content-Type": "application/json"}


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
    while True:
        subscribe.callback(on_message, subscribe_topic, hostname=bigboxx)
