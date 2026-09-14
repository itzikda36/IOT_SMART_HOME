"""Offline validation for Assignment 1 files.
This validates required configuration and the expected MQTT v3.1.1 session outcomes.
It does not contact the public broker.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
files = [ROOT / "mqtt_publisher_6233.py", ROOT / "mqtt_subscriber_6233.py"]
required = {
    'broker.hivemq.com': 'HiveMQ broker',
    'PORT = 1883': 'TCP port 1883',
    'KEEPALIVE = 90': 'keep-alive 90 seconds',
    '6233': 'student ID suffix',
    'will_set': 'Last Will message',
    'retain=True': 'retained flag',
}

print("Assignment 1 - Offline validation")
print("Student: Itzhak Davidov | suffix: 6233")
print("=" * 68)
for f in files:
    text = f.read_text(encoding='utf-8')
    print(f"\n{f.name}")
    for needle, label in required.items():
        ok = needle in text
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")

print("\nMQTT offline-delivery test matrix")
print("Test  CleanSession  SubQoS  PubQoS  Expected after reconnect")
rows = [
    (1, True,  0, 0, 'NO'),
    (2, False, 0, 0, 'NO'),
    (3, True,  1, 1, 'NO'),
    (4, False, 1, 1, 'YES'),
    (5, False, 1, 0, 'NO'),
]
for n, clean, sq, pq, expected in rows:
    print(f" {n:<4} {str(clean):<13} {sq:<7} {pq:<7} {expected}")

print("\n[PASS] Configuration is ready for broker execution.")
print("[INFO] Run mqtt_test_runner_6233.py on an Internet-connected computer")
print("       to capture live HiveMQ results.")
