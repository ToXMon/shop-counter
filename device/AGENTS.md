# device/AGENTS.md

Owner: see STATE.md (default Codex, or Tolu by hand). Read root AGENTS.md first.

## What this module is

Firmware for the M5Stack CoreS3. A thin client. Spec: docs/INTERFACES.md section 4.

Language: ______ (PENDING P2; fill in on first commit: MicroPython / Arduino + M5Unified / UIFlow 2).

## Build order

1. `device/smoke_http.sh`: from the laptop, `curl` both routes against the stub. Proves the contract before any firmware.
2. Wi-Fi join + `POST /intent {type:"buy", source:"button"}` on button press. Show "Sent" on screen.
3. `POST /utterance` with a hard-coded text string on a second button. Speak `reply.speech` via TTS (on-device TTS is weak; acceptable fallback: the laptop speaks via the companion screen's `speechSynthesis`, and the device shows the text).
4. Push-to-talk: record 16 kHz mono WAV while held, POST as multipart `audio` (PENDING P3a).
5. RFID badge read (built-in RFID2 unit on CoreS3) -> `POST /intent source:"badge"`.
6. Long-press -> `POST /session/clear`, screen "Ready".

## Hard rules (module-specific)

- The device stores only `session_id`, the backend base URL, and Wi-Fi credentials. Nothing from checkout. It never calls `/state`.
- Wi-Fi SSID/password in `device/secrets.h` or `device/secrets.py`, gitignored. `device/secrets.example.*` committed.
- Every HTTP call has a 10 s timeout and shows an error state on screen. Never hang the UI.
- Button fallback for the badge is first-class, not an afterthought. Label it "TAP TO BUY".

## Cut points for this module (in order)

Barcode scan -> on-device STT -> RFID (keep button) -> on-device TTS (keep screen text + laptop speech).

## Smoke

`device/smoke_http.sh` passes against the stub and against the real backend.
