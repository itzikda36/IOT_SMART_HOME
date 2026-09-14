Assignment 1 - IoT / MQTT
Student: Itzhak Davidov
ID last 4 digits: 6233

Files:
- mqtt_publisher_6233.py   : Publisher with QoS, clean session, retained message, Last Will, keep-alive 90 s.
- mqtt_subscriber_6233.py  : Subscriber for Tests 1-5 and retained-message demo.
- mqtt_test_runner_6233.py : Automated Tests 1-5 against broker.hivemq.com:1883 (robust reconnect/retry version).
- offline_validation_6233.py : Offline configuration/logic validation.
- Assignment_1_IoT_Itzhak_Davidov_6233.docx : Submission report.

Install dependency:
  py -m pip install -r requirements.txt

Run live tests:
  py mqtt_test_runner_6233.py

Example manual Test 4:
  Terminal 1: py mqtt_subscriber_6233.py --test 4
  After subscription is established, stop it.
  Terminal 2: py mqtt_publisher_6233.py --test 4 --message "offline test 4"
  Terminal 1: py mqtt_subscriber_6233.py --test 4 --skip-subscribe

Retained message demo:
  py mqtt_publisher_6233.py --test 4 --retained-demo
  py mqtt_subscriber_6233.py --test 4 --retained-demo

Live-run note:
- RUN_LIVE_TESTS.bat saves the console output automatically to live_test_results_6233.txt.
- Client IDs are unique per run and still end in 6233 to avoid stale public-broker sessions.
