# Assignment 2 - IoT / MQTT configuration
# Student: Itzhak Davidov | last 4 digits: 6233

BROKER = "broker.hivemq.com"
PORT = 1883
KEEPALIVE = 60

BASE_TOPIC = "iot/6233/cubes"
DHT_TOPIC = f"{BASE_TOPIC}/dht/sts"
BUTTON_TOPIC = f"{BASE_TOPIC}/button/sts"
RELAY_CMD_TOPIC = f"{BASE_TOPIC}/relay/cmd"
RELAY_STATUS_TOPIC = f"{BASE_TOPIC}/relay/sts"
