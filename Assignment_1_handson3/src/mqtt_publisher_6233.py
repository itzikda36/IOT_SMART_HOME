"""Assignment 1 - MQTT Publisher
Student: Itzhak Davidov | ID last 4 digits: 6233
"""

import argparse
import threading
import time

import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
KEEPALIVE = 90
TOPIC = "iot/home_ID6233/sensor_6233"
RETAINED_TOPIC = "iot/home_ID6233/retained_6233"
WILL_TOPIC = "iot/home_ID6233/status_6233"

TESTS = {
    1: {"clean_session": True,  "pub_qos": 0, "sub_qos": 0},
    2: {"clean_session": False, "pub_qos": 0, "sub_qos": 0},
    3: {"clean_session": True,  "pub_qos": 1, "sub_qos": 1},
    4: {"clean_session": False, "pub_qos": 1, "sub_qos": 1},
    5: {"clean_session": False, "pub_qos": 0, "sub_qos": 1},
}


def create_client(client_id: str, clean_session: bool):
    """Create a Paho MQTT v3.1.1 client, compatible with Paho 1.x/2.x."""
    try:
        return mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION1,
            client_id=client_id,
            clean_session=clean_session,
            protocol=mqtt.MQTTv311,
        )
    except AttributeError:
        return mqtt.Client(
            client_id=client_id,
            clean_session=clean_session,
            protocol=mqtt.MQTTv311,
        )


def main():
    parser = argparse.ArgumentParser(description="MQTT publisher for Assignment 1")
    parser.add_argument("--test", type=int, choices=range(1, 6), default=4)
    parser.add_argument("--message", default="Hello from Itzhak Davidov - 6233")
    parser.add_argument("--retained-demo", action="store_true",
                        help="Publish a retained message to the retained topic")
    args = parser.parse_args()

    cfg = TESTS[args.test]
    connected = threading.Event()
    client_id = f"IoT_ID_6233_PUB_T{args.test}"
    client = create_client(client_id, cfg["clean_session"])

    def on_connect(client, userdata, flags, rc):
        print(f"CONNECTED rc={rc} broker={BROKER}:{PORT}")
        connected.set()

    def on_disconnect(client, userdata, rc):
        print(f"DISCONNECTED rc={rc}")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    # Last Will message: broker publishes it if this client disconnects unexpectedly.
    client.will_set(
        WILL_TOPIC,
        payload="Publisher 6233 disconnected unexpectedly",
        qos=1,
        retain=True,
    )

    print(f"Student: Itzhak Davidov | suffix: 6233")
    print(f"Test {args.test}: clean_session={cfg['clean_session']} pub_qos={cfg['pub_qos']}")
    print(f"Client ID: {client_id}")
    print(f"Keep Alive: {KEEPALIVE} seconds")
    print(f"Connecting to {BROKER}:{PORT} ...")

    client.connect(BROKER, PORT, keepalive=KEEPALIVE)
    client.loop_start()
    if not connected.wait(10):
        client.loop_stop()
        raise TimeoutError("Connection to broker timed out")

    topic = RETAINED_TOPIC if args.retained_demo else TOPIC
    retain = bool(args.retained_demo)
    payload = "Retained message - Itzhak Davidov 6233" if retain else args.message

    info = client.publish(topic, payload=payload, qos=cfg["pub_qos"], retain=retain)
    info.wait_for_publish(timeout=10)
    print(f"PUBLISHED topic={topic}")
    print(f"payload={payload!r} qos={cfg['pub_qos']} retain={retain}")

    time.sleep(1)
    client.disconnect()
    client.loop_stop()
    print("Publisher finished successfully")


if __name__ == "__main__":
    main()
