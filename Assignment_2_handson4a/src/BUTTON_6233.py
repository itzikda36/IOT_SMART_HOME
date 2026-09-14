# Assignment 2 - IoT / MQTT
# Student: Itzhak Davidov | last 4 digits: 6233

import json
import sys
from PyQt5 import QtWidgets
import paho.mqtt.client as mqtt
from mqtt_init_6233 import BROKER, PORT, KEEPALIVE, BUTTON_TOPIC

def make_client(client_id):
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id, clean_session=True)
    except Exception:
        return mqtt.Client(client_id=client_id, clean_session=True)

class ButtonWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BUTTON Emulator - 6233")
        self.client = make_client("IOT_BUTTON_6233")
        self.client.on_connect = self.on_connect

        self.status = QtWidgets.QLabel("Disconnected")
        self.connect_btn = QtWidgets.QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_mqtt)
        self.push_btn = QtWidgets.QPushButton("PUSH BUTTON")
        self.push_btn.setEnabled(False)
        self.push_btn.clicked.connect(self.push_button)

        form = QtWidgets.QFormLayout(self)
        form.addRow("Broker", QtWidgets.QLabel(f"{BROKER}:{PORT}"))
        form.addRow("Topic", QtWidgets.QLabel(BUTTON_TOPIC))
        form.addRow("MQTT", self.status)
        form.addRow(self.connect_btn)
        form.addRow(self.push_btn)

    def connect_mqtt(self):
        self.status.setText("Connecting...")
        self.client.connect(BROKER, PORT, KEEPALIVE)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.status.setText("Connected")
            self.connect_btn.setEnabled(False)
            self.push_btn.setEnabled(True)
        else:
            self.status.setText(f"Connection error: {rc}")

    def push_button(self):
        payload = json.dumps({"value": 1})
        self.client.publish(BUTTON_TOPIC, payload, qos=0)
        print(f"BUTTON -> {BUTTON_TOPIC}: {payload}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = ButtonWindow()
    w.resize(520, 210)
    w.show()
    sys.exit(app.exec_())
