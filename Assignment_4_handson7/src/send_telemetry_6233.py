"""ThingsBoard telemetry helper for Assignment 4 (6233).

The device token is intentionally NOT stored in this repository.
Set the THINGSBOARD_TOKEN environment variable before running.
"""
import json
import os
import urllib.request

HOST = "https://thingsboard.cloud"
TOKEN = os.environ.get("THINGSBOARD_TOKEN")


def send_temperature(value: float) -> None:
    if not TOKEN:
        raise SystemExit(
            "THINGSBOARD_TOKEN is not set. Set it in your terminal and run again."
        )
    url = f"{HOST}/api/v1/{TOKEN}/telemetry"
    payload = json.dumps({"temperature": value}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        print(f"Sent temperature={value}; HTTP {response.status}")


if __name__ == "__main__":
    send_temperature(25)   # normal telemetry example
    send_temperature(35)   # triggers High_Temperature_6233 (> 30 C)
