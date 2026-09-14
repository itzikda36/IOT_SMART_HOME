# Assignment 3 - IoT / Hands-On 6
# Student: Itzhak Davidov | Last 4 digits: 6233

import json
import random
import sys
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets
import paho.mqtt.client as mqtt

STUDENT = "Itzhak Davidov"
LAST4 = "6233"

DEFAULT_BROKER = "broker.hivemq.com"
DEFAULT_PORT = 1883
COURSE_BROKER = "139.162.222.115"
COURSE_PORT = 80
COURSE_USERNAME = "MATZI"
COURSE_PASSWORD = "MATZI"

BASE_TOPIC = f"iot/{LAST4}/cubes"
DHT_TOPIC = f"{BASE_TOPIC}/dht/sts"
BUTTON_TOPIC = f"{BASE_TOPIC}/button/sts"
RELAY_CMD_TOPIC = f"{BASE_TOPIC}/relay/cmd"
RELAY_STATUS_TOPIC = f"{BASE_TOPIC}/relay/sts"
DEFAULT_SUB_TOPIC = f"{BASE_TOPIC}/#"


def make_client(client_id, clean_session=True):
    """Create a paho client compatible with paho-mqtt 1.x and 2.x."""
    try:
        return mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION1,
            client_id=client_id,
            clean_session=clean_session,
        )
    except Exception:
        return mqtt.Client(client_id=client_id, clean_session=clean_session)


class MqttSignals(QtCore.QObject):
    connected = QtCore.pyqtSignal(int)
    disconnected = QtCore.pyqtSignal(int)
    message = QtCore.pyqtSignal(str, str)
    log = QtCore.pyqtSignal(str)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"IoT Hands-On 6 - {STUDENT} ({LAST4})")
        self.resize(1150, 760)

        self.client = None
        self.signals = MqttSignals()
        self.signals.connected.connect(self.on_mqtt_connected)
        self.signals.disconnected.connect(self.on_mqtt_disconnected)
        self.signals.message.connect(self.on_mqtt_message)
        self.signals.log.connect(self.append_log)

        self.relay_state = False
        self.last_event_command = None
        self.running_timer = QtCore.QTimer(self)
        self.running_timer.setSingleShot(True)
        self.running_timer.timeout.connect(self.disconnect_mqtt)

        self.build_ui()
        self.apply_profile(0)

    # ---------- UI ----------
    def build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)

        title = QtWidgets.QLabel("Assignment 3 - MQTT GUI + Event Handler")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 700; padding: 8px;")
        root.addWidget(title)

        subtitle = QtWidgets.QLabel(
            f"Student: {STUDENT} | Last 4 digits: {LAST4} | Topics: {BASE_TOPIC}/..."
        )
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        subtitle.setStyleSheet("color: #555; padding-bottom: 8px;")
        root.addWidget(subtitle)

        # Connection group
        connection = QtWidgets.QGroupBox("Connection / Session Settings")
        grid = QtWidgets.QGridLayout(connection)

        self.profile = QtWidgets.QComboBox()
        self.profile.addItems(["HiveMQ Demo", "White Cube (course preset)"])
        self.profile.currentIndexChanged.connect(self.apply_profile)

        self.host = QtWidgets.QLineEdit()
        self.port = QtWidgets.QSpinBox()
        self.port.setRange(1, 65535)
        self.runtime = QtWidgets.QSpinBox()
        self.runtime.setRange(0, 86400)
        self.runtime.setSuffix(" sec (0 = unlimited)")
        self.runtime.setValue(0)
        self.client_id = QtWidgets.QLineEdit(f"IOT_GUI_{LAST4}_{random.randint(1000, 9999)}")
        self.username = QtWidgets.QLineEdit()
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.keepalive = QtWidgets.QSpinBox()
        self.keepalive.setRange(10, 600)
        self.keepalive.setValue(60)

        self.connect_btn = QtWidgets.QPushButton("CONNECT")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.status = QtWidgets.QLabel("DISCONNECTED")
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        self.set_status(False)

        labels_widgets = [
            ("Broker profile", self.profile),
            ("Broker / Host", self.host),
            ("Port", self.port),
            ("Running time", self.runtime),
            ("Client ID", self.client_id),
            ("Username", self.username),
            ("Password", self.password),
            ("Keep Alive", self.keepalive),
        ]
        for i, (label, widget) in enumerate(labels_widgets):
            row, col = divmod(i, 4)
            base = col * 2
            grid.addWidget(QtWidgets.QLabel(label), row, base)
            grid.addWidget(widget, row, base + 1)

        grid.addWidget(self.connect_btn, 2, 0, 1, 2)
        grid.addWidget(QtWidgets.QLabel("Connection status"), 2, 2)
        grid.addWidget(self.status, 2, 3, 1, 2)
        root.addWidget(connection)

        middle = QtWidgets.QHBoxLayout()
        root.addLayout(middle, 1)

        # Left: subscribe/publish
        left = QtWidgets.QVBoxLayout()
        middle.addLayout(left, 1)

        sub_group = QtWidgets.QGroupBox("Continuous Subscriber")
        sub_form = QtWidgets.QFormLayout(sub_group)
        self.sub_topic = QtWidgets.QLineEdit(DEFAULT_SUB_TOPIC)
        self.subscribe_btn = QtWidgets.QPushButton("SUBSCRIBE")
        self.subscribe_btn.clicked.connect(self.subscribe_topic)
        sub_form.addRow("Topic", self.sub_topic)
        sub_form.addRow(self.subscribe_btn)
        left.addWidget(sub_group)

        pub_group = QtWidgets.QGroupBox("Publisher / Device Control")
        pub_form = QtWidgets.QFormLayout(pub_group)
        self.pub_topic = QtWidgets.QLineEdit(RELAY_CMD_TOPIC)
        self.pub_message = QtWidgets.QLineEdit('{"value": 1}')
        self.publish_btn = QtWidgets.QPushButton("PUBLISH")
        self.publish_btn.clicked.connect(self.publish_manual)

        relay_buttons = QtWidgets.QHBoxLayout()
        self.relay_on_btn = QtWidgets.QPushButton("RELAY ON")
        self.relay_off_btn = QtWidgets.QPushButton("RELAY OFF")
        self.relay_on_btn.clicked.connect(lambda: self.set_relay(True, "manual control"))
        self.relay_off_btn.clicked.connect(lambda: self.set_relay(False, "manual control"))
        relay_buttons.addWidget(self.relay_on_btn)
        relay_buttons.addWidget(self.relay_off_btn)
        relay_widget = QtWidgets.QWidget()
        relay_widget.setLayout(relay_buttons)

        self.relay_indicator = QtWidgets.QLabel("UNKNOWN")
        self.relay_indicator.setAlignment(QtCore.Qt.AlignCenter)
        self.relay_indicator.setStyleSheet("font-size:18px;font-weight:700;background:#ddd;padding:6px;")

        pub_form.addRow("Topic", self.pub_topic)
        pub_form.addRow("Message", self.pub_message)
        pub_form.addRow(self.publish_btn)
        pub_form.addRow("Relay control", relay_widget)
        pub_form.addRow("Relay status", self.relay_indicator)
        left.addWidget(pub_group)

        # Right: event handler
        event_group = QtWidgets.QGroupBox("Event Handler / Automatic Reaction")
        event_form = QtWidgets.QFormLayout(event_group)
        self.event_enabled = QtWidgets.QCheckBox("Enable event handler")
        self.event_enabled.setChecked(True)
        self.event_mode = QtWidgets.QComboBox()
        self.event_mode.addItems([
            "DHT temperature -> Relay",
            "Button press -> Relay toggle",
        ])
        self.threshold = QtWidgets.QDoubleSpinBox()
        self.threshold.setRange(-20.0, 80.0)
        self.threshold.setDecimals(1)
        self.threshold.setValue(22.5)
        self.threshold.setSuffix(" C")
        self.event_status = QtWidgets.QLabel("Waiting for sensor event...")
        self.event_status.setWordWrap(True)
        self.event_status.setStyleSheet("font-weight:600;padding:8px;background:#f3f3f3;")

        explanation = QtWidgets.QLabel(
            "Reaction: in DHT mode, T >= threshold turns the relay ON; "
            "T < threshold turns it OFF. In Button mode, each press toggles the relay."
        )
        explanation.setWordWrap(True)

        event_form.addRow(self.event_enabled)
        event_form.addRow("Event source", self.event_mode)
        event_form.addRow("Temperature threshold", self.threshold)
        event_form.addRow("Current reaction", self.event_status)
        event_form.addRow(explanation)
        middle.addWidget(event_group, 1)

        # Log
        log_group = QtWidgets.QGroupBox("MQTT Messages / Application Log")
        log_layout = QtWidgets.QVBoxLayout(log_group)
        self.log_box = QtWidgets.QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QtGui.QFont("Consolas", 10))
        clear_btn = QtWidgets.QPushButton("Clear log")
        clear_btn.clicked.connect(self.log_box.clear)
        log_layout.addWidget(self.log_box)
        log_layout.addWidget(clear_btn)
        root.addWidget(log_group, 2)

    def apply_profile(self, index):
        if index == 1:
            self.host.setText(COURSE_BROKER)
            self.port.setValue(COURSE_PORT)
            self.username.setText(COURSE_USERNAME)
            self.password.setText(COURSE_PASSWORD)
        else:
            self.host.setText(DEFAULT_BROKER)
            self.port.setValue(DEFAULT_PORT)
            self.username.clear()
            self.password.clear()

    def set_status(self, connected):
        if connected:
            self.status.setText("CONNECTED")
            self.status.setStyleSheet(
                "background:#b8f5bf;color:#14551d;font-weight:800;padding:7px;border-radius:4px;"
            )
            self.connect_btn.setText("DISCONNECT")
        else:
            self.status.setText("DISCONNECTED")
            self.status.setStyleSheet(
                "background:#ffd1d1;color:#7d1111;font-weight:800;padding:7px;border-radius:4px;"
            )
            self.connect_btn.setText("CONNECT")

    # ---------- MQTT ----------
    def toggle_connection(self):
        if self.client is not None and self.client.is_connected():
            self.disconnect_mqtt()
        else:
            self.connect_mqtt()

    def connect_mqtt(self):
        try:
            cid = self.client_id.text().strip() or f"IOT_GUI_{LAST4}_{random.randint(1000,9999)}"
            self.client = make_client(cid, clean_session=True)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            user = self.username.text().strip()
            if user:
                self.client.username_pw_set(user, self.password.text())

            host = self.host.text().strip()
            port = int(self.port.value())
            keepalive = int(self.keepalive.value())
            self.append_log(f"Connecting to {host}:{port} as {cid} ...")
            self.client.connect(host, port, keepalive)
            self.client.loop_start()
        except Exception as exc:
            self.append_log(f"CONNECT ERROR: {exc}")
            QtWidgets.QMessageBox.critical(self, "MQTT connection error", str(exc))

    def disconnect_mqtt(self):
        self.running_timer.stop()
        if self.client is not None:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
        self.set_status(False)
        self.append_log("Disconnected")

    def _on_connect(self, client, userdata, flags, rc):
        self.signals.connected.emit(int(rc))

    def _on_disconnect(self, client, userdata, rc, *args):
        try:
            code = int(rc)
        except Exception:
            code = 0
        self.signals.disconnected.emit(code)

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8", "ignore")
        self.signals.message.emit(msg.topic, payload)

    @QtCore.pyqtSlot(int)
    def on_mqtt_connected(self, rc):
        if rc == 0:
            self.set_status(True)
            self.append_log("Connected OK")
            self.subscribe_topic()
            secs = int(self.runtime.value())
            if secs > 0:
                self.running_timer.start(secs * 1000)
                self.append_log(f"Auto-disconnect scheduled after {secs} seconds")
        else:
            self.append_log(f"Connection failed, rc={rc}")
            self.set_status(False)

    @QtCore.pyqtSlot(int)
    def on_mqtt_disconnected(self, rc):
        self.set_status(False)
        self.append_log(f"Disconnected (rc={rc})")

    def subscribe_topic(self):
        topic = self.sub_topic.text().strip()
        if not topic:
            return
        if self.client is None or not self.client.is_connected():
            self.append_log("Subscribe requested, but MQTT is not connected")
            return
        result, mid = self.client.subscribe(topic, qos=0)
        self.append_log(f"SUBSCRIBE {topic} (result={result}, mid={mid})")

    def publish_manual(self):
        self.publish(self.pub_topic.text().strip(), self.pub_message.text())

    def publish(self, topic, payload, qos=0, retain=False):
        if self.client is None or not self.client.is_connected():
            self.append_log("Publish requested, but MQTT is not connected")
            return False
        info = self.client.publish(topic, payload, qos=qos, retain=retain)
        self.append_log(f"TX {topic}: {payload}")
        return info.rc == mqtt.MQTT_ERR_SUCCESS

    # ---------- Message handling / event handler ----------
    @QtCore.pyqtSlot(str, str)
    def on_mqtt_message(self, topic, payload):
        self.append_log(f"RX {topic}: {payload}")

        if topic == RELAY_STATUS_TOPIC:
            self.handle_relay_status(payload)

        if not self.event_enabled.isChecked():
            return

        mode = self.event_mode.currentText()
        if mode.startswith("DHT") and topic == DHT_TOPIC:
            self.handle_dht_event(payload)
        elif mode.startswith("Button") and topic == BUTTON_TOPIC:
            self.handle_button_event(payload)

    def handle_relay_status(self, payload):
        state = None
        try:
            data = json.loads(payload)
            raw = str(data.get("relay", data.get("value", ""))).upper()
        except Exception:
            raw = payload.strip().upper()

        if raw in {"1", "ON", "TRUE"}:
            state = True
        elif raw in {"0", "OFF", "FALSE"}:
            state = False

        if state is not None:
            self.relay_state = state
            text = "ON" if state else "OFF"
            self.relay_indicator.setText(text)
            bg = "#b8f5bf" if state else "#e6e6e6"
            self.relay_indicator.setStyleSheet(
                f"font-size:18px;font-weight:700;background:{bg};padding:6px;"
            )

    def handle_dht_event(self, payload):
        try:
            data = json.loads(payload)
            temp = float(data["temperature"])
            humidity = float(data.get("humidity", 0.0))
        except Exception as exc:
            self.append_log(f"DHT parse error: {exc}")
            return

        threshold = float(self.threshold.value())
        desired = temp >= threshold
        action = "ON" if desired else "OFF"
        self.event_status.setText(
            f"DHT event: T={temp:.1f} C, H={humidity:.1f}% -> Relay {action} "
            f"(threshold {threshold:.1f} C)"
        )
        self.append_log(
            f"EVENT DHT: {temp:.1f} C {'>=' if desired else '<'} {threshold:.1f} C -> RELAY {action}"
        )
        # Avoid unnecessary repeated commands while readings stay on same side of threshold.
        if self.last_event_command != desired:
            self.set_relay(desired, "DHT event handler")
            self.last_event_command = desired

    def handle_button_event(self, payload):
        pressed = False
        try:
            data = json.loads(payload)
            pressed = int(data.get("value", 0)) == 1
        except Exception:
            pressed = payload.strip() in {"1", "ON", "TRUE", "PRESS"}

        if pressed:
            desired = not self.relay_state
            self.event_status.setText(
                f"BUTTON event -> Relay {'ON' if desired else 'OFF'}"
            )
            self.append_log(
                f"EVENT BUTTON: press detected -> RELAY {'ON' if desired else 'OFF'}"
            )
            self.set_relay(desired, "button event handler")

    def set_relay(self, on, reason="event handler"):
        payload = json.dumps({"value": 1 if on else 0})
        if self.publish(RELAY_CMD_TOPIC, payload):
            self.append_log(f"REACTION ({reason}): relay command -> {'ON' if on else 'OFF'}")

    def append_log(self, text):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.appendPlainText(f"[{stamp}] {text}")
        bar = self.log_box.verticalScrollBar()
        bar.setValue(bar.maximum())

    def closeEvent(self, event):
        self.disconnect_mqtt()
        event.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
