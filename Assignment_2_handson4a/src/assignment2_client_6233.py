# Assignment 2 - IoT / MQTT
# Student: Itzhak Davidov | last 4 digits: 6233

import argparse
import csv
import json
import time
from datetime import datetime
import paho.mqtt.client as mqtt

from mqtt_init_6233 import (
    BROKER, PORT, KEEPALIVE,
    DHT_TOPIC, BUTTON_TOPIC, RELAY_CMD_TOPIC, RELAY_STATUS_TOPIC
)

def make_client(client_id):
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id, clean_session=True)
    except Exception:
        return mqtt.Client(client_id=client_id, clean_session=True)

class Assignment2Client:
    def __init__(self):
        self.client = make_client("IOT_ASSIGNMENT2_6233")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.samples = []
        self.relay_on = False
        self.button_events = 0
        self.collect_dht = False
        self.react_to_button = False

    def connect(self):
        print(f"Connecting to {BROKER}:{PORT} ...")
        self.client.connect(BROKER, PORT, KEEPALIVE)
        self.client.loop_start()

    def close(self):
        self.client.loop_stop()
        self.client.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("connected OK")
            client.subscribe([
                (DHT_TOPIC, 0),
                (BUTTON_TOPIC, 0),
                (RELAY_STATUS_TOPIC, 0),
            ])
            print("Subscribed to cube group 6233")
        else:
            print("Bad connection. rc =", rc)

    def on_message(self, client, userdata, msg):
        raw = msg.payload.decode("utf-8", "ignore")
        print(f"RX {msg.topic}: {raw}")

        if msg.topic == DHT_TOPIC and self.collect_dht:
            self.handle_dht(raw)
        elif msg.topic == BUTTON_TOPIC:
            self.handle_button(raw)
        elif msg.topic == RELAY_STATUS_TOPIC:
            self.handle_relay_status(raw)

    def handle_dht(self, raw):
        try:
            data = json.loads(raw)
            t = float(data["temperature"])
            h = float(data["humidity"])
        except Exception:
            # Backwards-compatible parser for old emulator:
            # "Temperature: 22.5 Humidity: 75.1"
            parts = raw.replace(":", "").split()
            t = float(parts[1])
            h = float(parts[3])

        row = (datetime.now().isoformat(timespec="seconds"), t, h)
        self.samples.append(row)
        print(f"DHT sample {len(self.samples):02d}/20 -> T={t:.1f} C, H={h:.1f}%")

    def handle_button(self, raw):
        pressed = False
        try:
            data = json.loads(raw)
            pressed = int(data.get("value", 0)) == 1
        except Exception:
            pressed = "1" in raw

        if pressed:
            self.button_events += 1
            print(f"BUTTON event #{self.button_events}")
            if self.react_to_button:
                self.set_relay(not self.relay_on)

    def handle_relay_status(self, raw):
        try:
            data = json.loads(raw)
            self.relay_on = str(data.get("relay", "")).upper() == "ON"
        except Exception:
            self.relay_on = raw.strip().upper() in {"1", "ON", "TRUE"}
        print("RELAY confirmed:", "ON" if self.relay_on else "OFF")

    def set_relay(self, on):
        self.relay_on = bool(on)
        payload = json.dumps({"value": 1 if on else 0})
        self.client.publish(RELAY_CMD_TOPIC, payload, qos=0)
        print("TX relay command:", "ON" if on else "OFF")

    def test1(self):
        print("\n=== TEST 1: DHT - 20 samples / 10 minutes ===")
        self.collect_dht = True
        deadline = time.time() + 610
        while len(self.samples) < 20 and time.time() < deadline:
            time.sleep(1)
        self.collect_dht = False

        with open("dht_samples_6233.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "temperature_c", "humidity_pct"])
            w.writerows(self.samples)
        print(f"Saved {len(self.samples)} samples to dht_samples_6233.csv")

    def test2(self):
        print("\n=== TEST 2: RELAY ON / OFF ===")
        self.set_relay(True)
        time.sleep(3)
        self.set_relay(False)
        time.sleep(3)
        print("TEST 2 complete")

    def test3(self):
        print("\n=== TEST 3: BUTTON -> RELAY toggle ===")
        self.react_to_button = True
        print("Press the BUTTON emulator. Each press toggles the RELAY.")
        time.sleep(120)
        self.react_to_button = False
        print(f"TEST 3 complete. Button events detected: {self.button_events}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", choices=["1", "2", "3"], required=True)
    args = parser.parse_args()

    app = Assignment2Client()
    app.connect()
    time.sleep(2)
    try:
        {"1": app.test1, "2": app.test2, "3": app.test3}[args.test]()
    finally:
        app.close()

if __name__ == "__main__":
    main()
