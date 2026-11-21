# CoreS3 live device

The CoreS3 uses a private hotspot and an explicitly paired session. The backend
stays on loopback. The device proxy exposes only the paired session's device
routes. It filters checkout-bearing fields and plays replies on the Mac.

1. Connect the Mac and CoreS3 to the private hotspot.
2. Copy `secrets.example.h` to `secrets.h`. Set Wi-Fi and the Mac proxy URL.
3. Run the live backend on `127.0.0.1:8788`.
4. Run `python3 device/device_proxy.py --host <mac-hotspot-ip> --session <session_id>`.
5. Confirm the USB target is the CoreS3. Flash with `pio run -d device -t upload --upload-port <port>`.
6. Open serial at 115200 baud. Send `session <session_id>` to pair the displayed offer.
7. Hold the bottom-left area to talk. Release to send up to five seconds of audio.
8. Wait for the Mac reply. Tap the bottom centre to review the paired offer.
9. Scan the Mac QR on the shopper's phone. Stop before payment during tests.

The proxy accepts only button intent. RFID remains disabled for live testing.
The proxy logs route names and outcomes only. It never logs audio or checkout data.
It rejects `/state` and filters device responses. Each device HTTP call has a
10-second timeout. Voice processing continues in the proxy and is polled.
If pairing or voice fails, the device refuses intent until a fresh pairing.
Re-pair after a session clear. The old session must not be reused.
