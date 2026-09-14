"""Assignment 1 - MQTT Subscriber
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
    parser = argparse.ArgumentParser(description="MQTT subscriber for Assignment 1")
    parser.add_argument("--test", type=int, choices=range(1, 6), default=4)
    parser.add_argument("--duration", type=int, default=15)
    parser.add_argument("--retained-demo", action="store_true")
    parser.add_argument("--skip-subscribe", action="store_true",
                        help="Reconnect without SUBSCRIBE to verify a persistent session")
    args = parser.parse_args()

    cfg = TESTS[args.test]
    connected = threading.Event()
    received = []
    client_id = f"IoT_ID_6233_SUB_T{args.test}"
    client = create_client(client_id, cfg["clean_session"])

    def on_connect(client, userdata, flags, rc):
        print(f"CONNECTED rc={rc} broker={BROKER}:{PORT}")
        connected.set()
        if not args.skip_subscribe:
            topic = RETAINED_TOPIC if args.retained_demo else TOPIC
            client.subscribe(topic, qos=cfg["sub_qos"])
            print(f"SUBSCRIBED topic={topic} qos={cfg['sub_qos']}")
        else:
            print("SUBSCRIBE skipped - checking stored persistent session")

    def on_message(client, userdata, msg):
        payload = msg.payload.decode("utf-8", errors="replace")
        received.append((msg.topic, payload, msg.qos, msg.retain))
        print(f"MESSAGE topic={msg.topic} payload={payload!r} qos={msg.qos} retain={msg.retain}")

    def on_disconnect(client, userdata, rc):
        print(f"DISCONNECTED rc={rc}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.will_set(
        WILL_TOPIC,
        payload="Subscriber 6233 disconnected unexpectedly",
        qos=1,
        retain=True,
    )

    print(f"Student: Itzhak Davidov | suffix: 6233")
    print(f"Test {args.test}: clean_session={cfg['clean_session']} sub_qos={cfg['sub_qos']}")
    print(f"Client ID: {client_id}")
    print(f"Keep Alive: {KEEPALIVE} seconds")
    print(f"Connecting to {BROKER}:{PORT} ...")

    client.connect(BROKER, PORT, keepalive=KEEPALIVE)
    client.loop_start()
    if not connected.wait(10):
        client.loop_stop()
        raise TimeoutError("Connection to broker timed out")

    time.sleep(args.duration)
    print(f"Messages received: {len(received)}")
    client.disconnect()
    client.loop_stop()
    print("Subscriber finished successfully")


if __name__ == "__main__":
    main()
