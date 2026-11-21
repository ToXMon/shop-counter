# CoreS3 button checkpoint

The button and audio client is for the stub checkpoint. Pairing is manual and temporary.
Do not use it with live checkout until the team agrees on pairing and offer revision.
The device never requests state or receives a handoff URL.

1. Connect the laptop and CoreS3 to a private hotspot.
2. Copy `secrets.example.h` to `secrets.h` and set Wi-Fi and laptop IP.
3. Run `python3 scripts/stub_backend.py` from the repository root.
4. Verify the USB device is the CoreS3 before flashing.
5. Run `~/.local/bin/pio run -d device -t upload --upload-port /dev/cu.usbmodem101`.
6. Create a stub pick with `POST /utterance` from the laptop.
7. Open the serial monitor at 115200 baud and send `session <session_id>`.
8. Press the bottom-centre touch button marked TAP TO BUY.
9. Check the device says Sent and the stub receives `POST /intent`.
10. Hold the bottom-left touch area to record up to five seconds.
11. Release to send a 16 kHz mono WAV to `/utterance`.
12. Clear the stub session between shoppers and restart the device.

The existing stub does not parse audio. Use an audio-capable test receiver or backend.

The stub must be reachable at the laptop IP on the private hotspot. Its state route
is unauthenticated, so use fake data only. Do not expose it on venue Wi-Fi.
The serial session command must identify the same active session as the displayed
pick. No protocol for automatic pairing or offer revisions exists here yet.
