# Demo support for Assignment 3 - IoT / Hands-On 6
# Student: Itzhak Davidov | Last 4 digits: 6233

import json
import random
import sys
from PyQt5 import QtCore, QtWidgets
import paho.mqtt.client as mqtt

LAST4 = "6233"
BROKER = "broker.hivemq.com"
PORT = 1883
BASE = f"iot/{LAST4}/cubes"
DHT_TOPIC = f"{BASE}/dht/sts"
BUTTON_TOPIC = f"{BASE}/button/sts"
RELAY_CMD_TOPIC = f"{BASE}/relay/cmd"
RELAY_STATUS_TOPIC = f"{BASE}/relay/sts"


def make_client(client_id):
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id, clean_session=True)
    except Exception:
        return mqtt.Client(client_id=client_id, clean_session=True)


class Signals(QtCore.QObject):
    connected = QtCore.pyqtSignal(int)
    relay_command = QtCore.pyqtSignal(str)


class Simulator(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("White Cube Demo Simulator - 6233")
        self.resize(600, 360)
        self.client = make_client(f"IOT_CUBE_SIM_{LAST4}_{random.randint(1000,9999)}")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.signals = Signals()
        self.signals.connected.connect(self.on_connected)
        self.signals.relay_command.connect(self.on_relay_command)
        self.relay_on = False
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel("MQTT Cube Simulator - DHT + Button + Relay")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size:20px;font-weight:700;")
        layout.addWidget(title)

        self.status = QtWidgets.QLabel(f"Broker: {BROKER}:{PORT} | Disconnected")
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        self.connect_btn = QtWidgets.QPushButton("CONNECT")
        self.connect_btn.clicked.connect(self.connect_mqtt)
        layout.addWidget(self.status)
        layout.addWidget(self.connect_btn)

        dht = QtWidgets.QGroupBox("DHT sensor events")
        dht_layout = QtWidgets.QHBoxLayout(dht)
        hot = QtWidgets.QPushButton("Send 23.5 C (Relay should turn ON)")
        cold = QtWidgets.QPushButton("Send 21.5 C (Relay should turn OFF)")
        hot.clicked.connect(lambda: self.send_dht(23.5, 74.0))
        cold.clicked.connect(lambda: self.send_dht(21.5, 76.0))
        dht_layout.addWidget(hot)
        dht_layout.addWidget(cold)
        layout.addWidget(dht)

        btn_group = QtWidgets.QGroupBox("Button sensor event")
        btn_layout = QtWidgets.QHBoxLayout(btn_group)
        button = QtWidgets.QPushButton("PUSH BUTTON")
        button.clicked.connect(self.send_button)
        btn_layout.addWidget(button)
        layout.addWidget(btn_group)

        relay_group = QtWidgets.QGroupBox("Relay cube")
        relay_layout = QtWidgets.QVBoxLayout(relay_group)
        self.relay_label = QtWidgets.QLabel("OFF")
        self.relay_label.setAlignment(QtCore.Qt.AlignCenter)
        self.relay_label.setStyleSheet("font-size:30px;font-weight:800;background:#e6e6e6;padding:12px;")
        relay_layout.addWidget(self.relay_label)
        layout.addWidget(relay_group)

        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

    def connect_mqtt(self):
        self.status.setText(f"Broker: {BROKER}:{PORT} | Connecting...")
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        self.signals.connected.emit(int(rc))

    def _on_message(self, client, userdata, msg):
        self.signals.relay_command.emit(msg.payload.decode("utf-8", "ignore"))

    def on_connected(self, rc):
        if rc == 0:
            self.status.setText(f"Broker: {BROKER}:{PORT} | CONNECTED")
            self.connect_btn.setEnabled(False)
            self.client.subscribe(RELAY_CMD_TOPIC, qos=0)
            self.publish_relay_status()
            self.log.appendPlainText(f"Subscribed: {RELAY_CMD_TOPIC}")
        else:
            self.status.setText(f"Connection failed rc={rc}")

    def send_dht(self, temp, humidity):
        payload = json.dumps({"temperature": temp, "humidity": humidity})
        self.client.publish(DHT_TOPIC, payload, qos=0)
        self.log.appendPlainText(f"DHT -> {DHT_TOPIC}: {payload}")

    def send_button(self):
        payload = json.dumps({"value": 1})
        self.client.publish(BUTTON_TOPIC, payload, qos=0)
        self.log.appendPlainText(f"BUTTON -> {BUTTON_TOPIC}: {payload}")

    def on_relay_command(self, raw):
        try:
            data = json.loads(raw)
            value = str(data.get("value", data.get("relay", ""))).upper()
        except Exception:
            value = raw.strip().upper()
        if value in {"1", "ON", "TRUE"}:
            self.relay_on = True
        elif value in {"0", "OFF", "FALSE"}:
            self.relay_on = False
        elif value == "TOGGLE":
            self.relay_on = not self.relay_on
        else:
            return
        self.relay_label.setText("ON" if self.relay_on else "OFF")
        self.relay_label.setStyleSheet(
            "font-size:30px;font-weight:800;padding:12px;" +
            ("background:#b8f5bf;" if self.relay_on else "background:#e6e6e6;")
        )
        self.log.appendPlainText(f"RELAY command received: {raw} -> {'ON' if self.relay_on else 'OFF'}")
        self.publish_relay_status()

    def publish_relay_status(self):
        if self.client.is_connected():
            payload = json.dumps({"relay": "ON" if self.relay_on else "OFF"})
            self.client.publish(RELAY_STATUS_TOPIC, payload, qos=0, retain=True)

    def closeEvent(self, event):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    w = Simulator()
    w.show()
    sys.exit(app.exec_())
