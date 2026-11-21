# device/AGENTS.md

Owner: see STATE.md (default Codex, or Tolu by hand). Read root AGENTS.md first.

## What this module is

Firmware for the M5Stack CoreS3. A thin client. Spec: docs/INTERFACES.md section 4.

Language: **PlatformIO + Arduino framework + M5Unified** (decided 12:38, PENDING P2 resolved). `pio` is installed at `~/.local/bin/pio`. `platformio.ini` board: `m5stack-cores3`. Libraries: `m5stack/M5Unified`, `m5stack/M5Unit-RFID` (or the MFRC522 path M5Unified exposes), `bblanchon/ArduinoJson`. Fallback if the audio path is not working by 14:30: UIFlow 2 / MicroPython on the same board.

Hardware on the table (photo, 12:40): M5Stack CoreS3 (main device), M5StickS3 (spare; could be the "badge" or a second button), RFID 2 unit (MFRC522, I2C, Port A), Hat ENV-III, Hat ToF, Unit Gesture, Unit GPS v1.1, a proto/breakout board. Only CoreS3 + RFID 2 are in scope. Everything else is cut from the start.

Reference builds: OpenAI's "Reflect" (CoreS3 + phone session for audio) at https://youcanjustbuildthings.openai.chatgpt.site/projects/official-reflect, and Espressif's realtime ESP32 demo. Both confirm: keep audio capture simple (push-to-talk WAV), let the backend do the intelligence.

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

## Current checkpoint

The button sent intent to the stub on CoreS3 hardware.
A test receiver accepted 16 kHz mono WAV from the microphone.
The current stub does not parse audio.
It uses manual USB session pairing for stub testing only.
See `device/README.md` for setup and its live-pairing limitation.
