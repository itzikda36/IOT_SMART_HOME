"""Reliable MQTT Tests 1-5 for Assignment 1.
Student: Itzhak Davidov | ID suffix: 6233
Broker: broker.hivemq.com:1883 | MQTT 3.1.1 | Keep Alive: 90 s
"""

import socket
import threading
import time
import uuid
import warnings
from pathlib import Path

import paho.mqtt.client as mqtt

warnings.filterwarnings("ignore", category=DeprecationWarning)

BROKER = "broker.hivemq.com"
PORT = 1883
KEEPALIVE = 90
TOPIC_PREFIX = "iot/home_ID6233/tests"
RESULTS_FILE = Path(__file__).with_name("live_test_results_6233.txt")

# test_no: (clean_session, subscribe_qos, publish_qos, expect_offline_delivery)
TESTS = {
    1: (True,  0, 0, False),
    2: (False, 0, 0, False),
    3: (True,  1, 1, False),
    4: (False, 1, 1, True),
    5: (False, 1, 0, False),
}

_LOG_LINES = []


def log(text=""):
    print(text, flush=True)
    _LOG_LINES.append(str(text))
    RESULTS_FILE.write_text("\n".join(_LOG_LINES) + "\n", encoding="utf-8")


def make_client(client_id, clean_session):
    """Create an MQTT 3.1.1 client using the compatibility callback API."""
    try:
        return mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION1,
            client_id=client_id,
            clean_session=clean_session,
            protocol=mqtt.MQTTv311,
        )
    except (AttributeError, TypeError):
        return mqtt.Client(
            client_id=client_id,
            clean_session=clean_session,
            protocol=mqtt.MQTTv311,
        )


def resolve_ipv4():
    """Resolve the public broker to IPv4 for a predictable Windows connection path."""
    return socket.gethostbyname(BROKER)


def connect_wait(client, host, timeout=20, attempts=3):
    """Connect and wait for MQTT CONNACK, retrying transient public-broker failures."""
    last_error = None
    for attempt in range(1, attempts + 1):
        connected = threading.Event()
        result = {"rc": None}

        def on_connect(c, u, flags, rc):
            result["rc"] = rc
            connected.set()

        client.on_connect = on_connect
        loop_started = False
        try:
            rc = client.connect(host, PORT, keepalive=KEEPALIVE)
            if rc != mqtt.MQTT_ERR_SUCCESS:
                raise RuntimeError(f"connect() returned {rc}")
            client.loop_start()
            loop_started = True
            if not connected.wait(timeout):
                raise TimeoutError(f"no MQTT CONNACK within {timeout}s")
            if result["rc"] != 0:
                raise ConnectionError(f"broker rejected CONNECT, rc={result['rc']}")
            return
        except Exception as exc:
            last_error = exc
            try:
                client.disconnect()
            except Exception:
                pass
            if loop_started:
                try:
                    client.loop_stop()
                except Exception:
                    pass
            if attempt < attempts:
                time.sleep(2 * attempt)

    raise TimeoutError(f"MQTT connection failed after {attempts} attempts: {last_error}")


def subscribe_wait(client, topic, qos, timeout=8):
    """Subscribe and wait for SUBACK so the broker has definitely stored the subscription."""
    ack = threading.Event()

    def on_subscribe(c, u, mid, granted_qos):
        ack.set()

    client.on_subscribe = on_subscribe
    rc, _mid = client.subscribe(topic, qos=qos)
    if rc != mqtt.MQTT_ERR_SUCCESS:
        raise RuntimeError(f"subscribe() returned {rc}")
    if not ack.wait(timeout):
        raise TimeoutError("SUBACK timeout")


def disconnect_cleanly(client, wait=0.8):
    """Give the network loop time to transmit DISCONNECT before stopping it."""
    try:
        client.disconnect()
        time.sleep(wait)
    finally:
        try:
            client.loop_stop()
        except Exception:
            pass


def run_test(test_no, broker_ip, run_token):
    clean, sub_qos, pub_qos, expected = TESTS[test_no]

    # Unique per program run, but every ID/topic still ends in 6233 as requested.
    sub_id = f"IoT_ItzhakD_T{test_no}_{run_token}_6233"
    pub_id = f"IoT_ItzhakD_PUB{test_no}_{run_token}_6233"
    topic = f"{TOPIC_PREFIX}/test{test_no}_{run_token}_6233"
    payload = f"offline-message-test-{test_no}-6233"

    log(f"Test {test_no}: clean_session={clean}, SUB QoS={sub_qos}, PUB QoS={pub_qos}")

    # Phase A: establish subscription and then go offline.
    sub = make_client(sub_id, clean)
    connect_wait(sub, broker_ip)
    subscribe_wait(sub, topic, sub_qos)
    log("  A) subscriber connected + SUBACK received")
    disconnect_cleanly(sub)
    time.sleep(1.2)

    # Phase B: publish while subscriber is offline.
    pub = make_client(pub_id, True)
    connect_wait(pub, broker_ip)
    info = pub.publish(topic, payload=payload, qos=pub_qos, retain=False)
    if pub_qos > 0:
        info.wait_for_publish(timeout=10)
    else:
        time.sleep(0.8)
    log("  B) publisher sent the offline message")
    disconnect_cleanly(pub)
    time.sleep(1.5)

    # Phase C: reconnect SAME subscriber ID. Do not subscribe again.
    got = []
    received = threading.Event()
    sub2 = make_client(sub_id, clean)

    def on_message(c, u, m):
        got.append(m.payload.decode(errors="replace"))
        received.set()

    sub2.on_message = on_message
    connect_wait(sub2, broker_ip)
    received.wait(5.0)
    disconnect_cleanly(sub2)

    actual = bool(got)
    ok = actual == expected
    log(f"  C) reconnect without re-subscribing -> message_received={actual}")
    log(f"  Expected offline delivery={expected} -> {'PASS' if ok else 'FAIL'}")
    if got:
        log(f"  Received: {got}")
    log()
    return ok


def main():
    run_token = uuid.uuid4().hex[:6]
    _LOG_LINES.clear()
    if RESULTS_FILE.exists():
        RESULTS_FILE.unlink()

    log("Assignment 1 MQTT automated test runner - FIXED")
    log("Student: Itzhak Davidov | suffix: 6233")
    log(f"Broker: {BROKER}:{PORT} | Keep Alive: {KEEPALIVE}s")
    log(f"Run token: {run_token}")
    log("-" * 72)

    broker_ip = resolve_ipv4()
    log(f"Resolved broker IPv4: {broker_ip}")
    try:
        with socket.create_connection((broker_ip, PORT), timeout=7):
            log("TCP connectivity check: PASS")
    except Exception as exc:
        log(f"TCP connectivity check: FAIL ({exc})")
        log("The MQTT tests were not started.")
        return 2

    log("-" * 72)
    passed = 0
    errors = 0
    for n in range(1, 6):
        try:
            ok = run_test(n, broker_ip, run_token)
            passed += int(ok)
        except Exception as exc:
            errors += 1
            log(f"Test {n}: ERROR -> {type(exc).__name__}: {exc}")
            log("Continuing to the next test...")
            log()
            time.sleep(2)

    log("-" * 72)
    log(f"FINAL RESULT: {passed}/5 tests passed | connection/runtime errors: {errors}")
    log(f"Results saved to: {RESULTS_FILE.name}")
    if passed == 5 and errors == 0:
        log("STATUS: READY FOR SCREENSHOT")
        return 0
    log("STATUS: Send this screen/result file to ChatGPT for the next fix.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
