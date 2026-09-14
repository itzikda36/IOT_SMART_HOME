# Assignment 2 - IoT / MQTT
# Student: Itzhak Davidov | last 4 digits: 6233

import json
import sys
from PyQt5 import QtWidgets
import paho.mqtt.client as mqtt
from mqtt_init_6233 import BROKER, PORT, KEEPALIVE, RELAY_CMD_TOPIC, RELAY_STATUS_TOPIC

def make_client(client_id):
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id, clean_session=True)
    except Exception:
        return mqtt.Client(client_id=client_id, clean_session=True)

class RelayWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RELAY Emulator - 6233")
        self.state = False

        self.client = make_client("IOT_RELAY_6233")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.status = QtWidgets.QLabel("Disconnected")
        self.state_label = QtWidgets.QLabel("OFF")
        self.btn = QtWidgets.QPushButton("Connect")
        self.btn.clicked.connect(self.connect_mqtt)

        form = QtWidgets.QFormLayout(self)
        form.addRow("Broker", QtWidgets.QLabel(f"{BROKER}:{PORT}"))
        form.addRow("Command topic", QtWidgets.QLabel(RELAY_CMD_TOPIC))
        form.addRow("Status topic", QtWidgets.QLabel(RELAY_STATUS_TOPIC))
        form.addRow("MQTT", self.status)
        form.addRow("Relay", self.state_label)
        form.addRow(self.btn)
        self.update_style()

    def connect_mqtt(self):
        self.status.setText("Connecting...")
        self.client.connect(BROKER, PORT, KEEPALIVE)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.status.setText("Connected")
            self.btn.setEnabled(False)
            self.client.subscribe(RELAY_CMD_TOPIC, qos=0)
            self.publish_status()
        else:
            self.status.setText(f"Connection error: {rc}")

    def on_message(self, client, userdata, msg):
        raw = msg.payload.decode("utf-8", "ignore").strip()
        value = raw.upper()
        try:
            data = json.loads(raw)
            value = str(data.get("value", data.get("relay", raw))).upper()
        except Exception:
            pass

        if value in {"1", "ON", "TRUE"}:
            self.set_state(True)
        elif value in {"0", "OFF", "FALSE"}:
            self.set_state(False)
        elif value == "TOGGLE":
            self.set_state(not self.state)
        else:
            print("Unknown relay command:", raw)

    def set_state(self, on):
        self.state = bool(on)
        self.state_label.setText("ON" if self.state else "OFF")
        self.update_style()
        self.publish_status()
        print("RELAY state ->", "ON" if self.state else "OFF")

    def update_style(self):
        self.state_label.setStyleSheet(
            "font-size: 26px; font-weight: bold; "
            + ("background:#b7f7bd;" if self.state else "background:#e5e5e5;")
        )

    def publish_status(self):
        if self.client.is_connected():
            self.client.publish(
                RELAY_STATUS_TOPIC,
                json.dumps({"relay": "ON" if self.state else "OFF"}),
                qos=0,
                retain=True,
            )

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = RelayWindow()
    w.resize(600, 230)
    w.show()
    sys.exit(app.exec_())
