# Assignment 2 - IoT / MQTT
# Student: Itzhak Davidov | last 4 digits: 6233

import json
import random
import sys
from PyQt5 import QtCore, QtWidgets
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
KEEPALIVE = 90
DHT_TOPIC = "iot/6233/cubes/dht/sts"


def make_client(client_id):
    # Use callback API v1 to stay compatible with the assignment callbacks.
    return mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION1,
        client_id=client_id,
        clean_session=True,
    )


class DHTWindow(QtWidgets.QWidget):
    mqtt_connected = QtCore.pyqtSignal(int)
    mqtt_disconnected = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DHT Emulator - 6233")

        self.client = make_client("IOT_DHT_6233")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

        self.status = QtWidgets.QLabel("Disconnected")
        self.temp = QtWidgets.QLabel("--")
        self.hum = QtWidgets.QLabel("--")
        self.btn = QtWidgets.QPushButton("Connect")
        self.btn.clicked.connect(self.connect_mqtt)

        form = QtWidgets.QFormLayout(self)
        form.addRow("Broker", QtWidgets.QLabel(f"{BROKER}:{PORT}"))
        form.addRow("Topic", QtWidgets.QLabel(DHT_TOPIC))
        form.addRow("Status", self.status)
        form.addRow("Temperature °C", self.temp)
        form.addRow("Humidity %", self.hum)
        form.addRow(self.btn)

        # QTimer must be started from the Qt GUI thread.
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(30_000)  # 20 samples in 10 minutes
        self.timer.timeout.connect(self.publish_sample)

        # MQTT callbacks run on Paho's network thread, so marshal GUI work
        # back to the Qt thread through signals.
        self.mqtt_connected.connect(self.handle_connected)
        self.mqtt_disconnected.connect(self.handle_disconnected)

    def connect_mqtt(self):
        self.status.setText("Connecting...")
        self.btn.setEnabled(False)
        try:
            self.client.connect(BROKER, PORT, KEEPALIVE)
            self.client.loop_start()
        except Exception as exc:
            self.status.setText(f"Connection failed: {exc}")
            self.btn.setEnabled(True)

    # Paho thread callback: do not touch Qt widgets/timers directly here.
    def on_connect(self, client, userdata, flags, rc):
        self.mqtt_connected.emit(int(rc))

    # Paho thread callback: do not touch Qt widgets/timers directly here.
    def on_disconnect(self, client, userdata, rc):
        self.mqtt_disconnected.emit(int(rc))

    @QtCore.pyqtSlot(int)
    def handle_connected(self, rc):
        if rc == 0:
            self.status.setText("Connected")
            self.btn.setEnabled(False)
            self.publish_sample()   # first sample immediately
            self.timer.start()     # then every 30 seconds
        else:
            self.status.setText(f"Connection error: {rc}")
            self.btn.setEnabled(True)

    @QtCore.pyqtSlot(int)
    def handle_disconnected(self, rc):
        self.timer.stop()
        self.status.setText("Disconnected")
        self.btn.setEnabled(True)

    @QtCore.pyqtSlot()
    def publish_sample(self):
        temperature = round(22.0 + random.uniform(0.1, 1.0), 1)
        humidity = round(74.0 + random.uniform(0.1, 2.4), 1)
        payload = json.dumps({"temperature": temperature, "humidity": humidity})
        self.client.publish(DHT_TOPIC, payload, qos=0)
        self.temp.setText(str(temperature))
        self.hum.setText(str(humidity))
        print(f"DHT -> {DHT_TOPIC}: {payload}", flush=True)

    def closeEvent(self, event):
        self.timer.stop()
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = DHTWindow()
    w.resize(520, 220)
    w.show()
    sys.exit(app.exec_())
