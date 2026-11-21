#include <Arduino.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <M5Unified.h>
#include <WiFi.h>
#include <M5UnitUnifiedRFID.h>
#include <M5UnitUnifiedNFC.h>
#include <wiring/m5_unit_unified_wiring.hpp>
#if __has_include("../secrets.h")
#include "../secrets.h"
#else
#include "../secrets.example.h"
#endif

String session;
m5::unit::UnitUnified units;
m5::unit::UnitRFID2 reader;
m5::nfc::NFCLayerA nfc(reader);
bool readerReady = false;
bool badgeSent = false;
unsigned long lastBadgePoll = 0;

void show(const char* status, const String& detail = "") {
  M5.Display.fillScreen(TFT_BLACK);
  M5.Display.setTextColor(TFT_WHITE, TFT_BLACK);
  M5.Display.setTextDatum(middle_center);
  M5.Display.setTextSize(3);
  M5.Display.drawString(status, M5.Display.width() / 2, 80);
  M5.Display.setTextSize(1);
  if (!detail.isEmpty()) M5.Display.drawString(detail, M5.Display.width() / 2, 135);
  M5.Display.drawFastHLine(0, 180, M5.Display.width(), TFT_DARKGREY);
  M5.Display.drawString("Hold to talk", M5.Display.width() / 6, 210);
  M5.Display.drawString("Tap to review", M5.Display.width() / 2, 210);
}

void sendIntent(const char* source = "button") {
  if (session.isEmpty()) { show("Ready", "Waiting for session"); return; }
  if (WiFi.status() != WL_CONNECTED) { show("Ready", "Wi-Fi disconnected; retry"); WiFi.reconnect(); return; }
  JsonDocument request;
  request["session_id"] = session;
  request["type"] = "buy";
  request["source"] = source;
  String body;
  serializeJson(request, body);
  HTTPClient http;
  http.setConnectTimeout(10000);
  http.setTimeout(10000);
  if (!http.begin(String(BACKEND_URL) + "/intent")) { show("Ready", "Connection error"); return; }
  http.addHeader("Content-Type", "application/json");
  show("Looking it up");
  const int status = http.POST(body);
  if (status != 200) { http.end(); show("Ready", "Review request failed"); return; }
  JsonDocument response;
  const DeserializationError error = deserializeJson(response, http.getStream());
  http.end();
  if (error || response["session_id"] != session || !response["handoff"]["status"].is<const char*>()) { show("Ready", "Invalid response"); return; }
  const char* result = response["handoff"]["status"];
  show(String(result) == "ready" ? "Scan on the Mac" : "Ready",
       String(result) == "ready" ? "" : "Check the Mac before trying again");
}

constexpr size_t sampleRate = 16000;
constexpr size_t chunkSamples = 320;
constexpr size_t maxSamples = sampleRate * 5;
int16_t* audioSamples = nullptr;
size_t sampleCount = 0;
bool recording = false;
bool chunkPending = false;

void put16(uint8_t* p, uint16_t n) { p[0] = n; p[1] = n >> 8; }
void put32(uint8_t* p, uint32_t n) { put16(p, n); put16(p + 2, n >> 16); }

class AudioBody : public Stream {
 public:
  AudioBody(const String& sessionId, const int16_t* data, size_t samples)
      : pcm(reinterpret_cast<const uint8_t*>(data)), pcmBytes(samples * 2) {
    prefix = "--counter-boundary\r\nContent-Disposition: form-data; name=\"session_id\"\r\n\r\n" + sessionId +
             "\r\n--counter-boundary\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"utterance.wav\"\r\nContent-Type: audio/wav\r\n\r\n";
    suffix = "\r\n--counter-boundary--\r\n";
    memcpy(wav, "RIFF", 4); put32(wav + 4, 36 + pcmBytes); memcpy(wav + 8, "WAVEfmt ", 8);
    put32(wav + 16, 16); put16(wav + 20, 1); put16(wav + 22, 1); put32(wav + 24, sampleRate);
    put32(wav + 28, sampleRate * 2); put16(wav + 32, 2); put16(wav + 34, 16);
    memcpy(wav + 36, "data", 4); put32(wav + 40, pcmBytes);
  }
  size_t length() const { return prefix.length() + sizeof(wav) + pcmBytes + suffix.length(); }
  int available() override { return length() - position; }
  int peek() override { return byteAt(position); }
  int read() override { int value = byteAt(position); if (value >= 0) ++position; return value; }
  size_t write(uint8_t) override { return 0; }
 private:
  int byteAt(size_t index) const {
    if (index < prefix.length()) return static_cast<uint8_t>(prefix[index]);
    index -= prefix.length(); if (index < sizeof(wav)) return wav[index];
    index -= sizeof(wav); if (index < pcmBytes) return pcm[index];
    index -= pcmBytes; if (index < suffix.length()) return static_cast<uint8_t>(suffix[index]);
    return -1;
  }
  String prefix, suffix;
  const uint8_t* pcm;
  size_t pcmBytes, position = 0;
  uint8_t wav[44];
};

void sendAudio() {
  if (WiFi.status() != WL_CONNECTED) { show("Ready", "Wi-Fi disconnected"); return; }
  AudioBody body(session, audioSamples, sampleCount);
  HTTPClient http;
  http.setConnectTimeout(10000); http.setTimeout(10000);
  if (!http.begin(String(BACKEND_URL) + "/utterance")) { show("Ready", "Connection error"); return; }
  http.addHeader("Content-Type", "multipart/form-data; boundary=counter-boundary");
  show("Looking it up");
  const int status = http.sendRequest("POST", &body, body.length());
  if (status != 200) { http.end(); show("Ready", "Audio request failed"); return; }
  JsonDocument response;
  const DeserializationError error = deserializeJson(response, http.getStream());
  http.end();
  if (error || response["session_id"] != session || !response["reply"]["speech"].is<const char*>()) { show("Ready", "Invalid response"); return; }
  show("Ready");
}

void beginRecording() {
  if (session.isEmpty()) { show("Ready", "Waiting for session"); return; }
  if (!audioSamples) audioSamples = static_cast<int16_t*>(ps_malloc(maxSamples * sizeof(int16_t)));
  if (!audioSamples) { show("Ready", "Audio memory error"); return; }
  M5.Speaker.end();
  if (!M5.Mic.begin()) { show("Ready", "Microphone error"); return; }
  sampleCount = 0; chunkPending = false; recording = true;
  show("Listening");
}

void updateRecording() {
  if (!recording) return;
  if (chunkPending && !M5.Mic.isRecording()) { sampleCount += chunkSamples; chunkPending = false; }
  const bool stop = !M5.BtnA.isPressed() || sampleCount >= maxSamples;
  if (stop && !chunkPending) {
    recording = false; M5.Mic.end();
    if (sampleCount) { show("Looking it up"); sendAudio(); } else { show("Ready", "No audio captured"); }
    return;
  }
  if (!stop && !chunkPending) {
    if (!M5.Mic.record(audioSamples + sampleCount, chunkSamples, sampleRate)) {
      recording = false; M5.Mic.end(); show("Ready", "Microphone error"); return;
    }
    chunkPending = true;
  }
}

void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);
  M5.setTouchButtonHeight(60);
  Serial.begin(115200);
  readerReady = m5::unit::wiring::addI2C(units, reader, 0, m5::unit::wiring::NessoPort::PortA) && units.begin();
  show("Ready", "Connecting Wi-Fi");
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  const unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) { M5.update(); delay(20); }
  show("Ready", WiFi.status() == WL_CONNECTED ? "Waiting for session" : "Wi-Fi connection failed");
}

void loop() {
  M5.update();
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("session ")) {
      session = line.substring(8);
      badgeSent = false;
      show("Ready", session.isEmpty() ? "Waiting for session" : (WiFi.status() == WL_CONNECTED ? "" : "Wi-Fi disconnected"));
    }
  }
  if (readerReady && !recording && !badgeSent && !session.isEmpty() && millis() - lastBadgePoll >= 300) {
    lastBadgePoll = millis();
    m5::nfc::a::PICC tag;
    if (nfc.detect(tag, 50)) {
      nfc.deactivate();
      badgeSent = true;
      sendIntent("badge");
    }
  }
  if (!recording && M5.BtnA.wasPressed()) beginRecording();
  if (recording) updateRecording();
  else if (M5.BtnB.wasPressed()) sendIntent();
  delay(10);
}
