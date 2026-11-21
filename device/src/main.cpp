#include <Arduino.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <M5Unified.h>
#include <WiFi.h>
#if __has_include("../secrets.h")
#include "../secrets.h"
#else
#include "../secrets.example.h"
#endif

String session;

void show(const String& message) {
  M5.Display.clear();
  M5.Display.setCursor(0, 0);
  M5.Display.setTextSize(2);
  M5.Display.println(message);
  M5.Display.println("\nHOLD bottom left to talk\nTAP bottom centre to buy");
}

void sendIntent() {
  if (session.isEmpty()) { show("Pair session first"); return; }
  if (WiFi.status() != WL_CONNECTED) { show(String("Wi-Fi status ") + static_cast<int>(WiFi.status()) + "\nRetrying connection"); WiFi.reconnect(); return; }
  JsonDocument request;
  request["session_id"] = session;
  request["type"] = "buy";
  request["source"] = "button";
  String body;
  serializeJson(request, body);
  HTTPClient http;
  http.setConnectTimeout(10000);
  http.setTimeout(10000);
  if (!http.begin(String(BACKEND_URL) + "/intent")) { show("HTTP error"); return; }
  http.addHeader("Content-Type", "application/json");
  const int status = http.POST(body);
  if (status != 200) { http.end(); show("Intent error"); return; }
  JsonDocument response;
  const DeserializationError error = deserializeJson(response, http.getStream());
  http.end();
  if (error || response["session_id"] != session || !response["handoff"]["status"].is<const char*>()) { show("Invalid response"); return; }
  const char* result = response["handoff"]["status"];
  const char* speech = response["reply"]["speech"] | "";
  show(String(result) == "ready" ? String("Sent\n") + speech : String("Intent: ") + result + "\n" + speech);
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
  if (WiFi.status() != WL_CONNECTED) { show("Wi-Fi disconnected"); return; }
  AudioBody body(session, audioSamples, sampleCount);
  HTTPClient http;
  http.setConnectTimeout(10000); http.setTimeout(10000);
  if (!http.begin(String(BACKEND_URL) + "/utterance")) { show("HTTP error"); return; }
  http.addHeader("Content-Type", "multipart/form-data; boundary=counter-boundary");
  const int status = http.sendRequest("POST", &body, body.length());
  if (status != 200) { http.end(); show("Audio request error"); return; }
  JsonDocument response;
  const DeserializationError error = deserializeJson(response, http.getStream());
  http.end();
  if (error || response["session_id"] != session || !response["reply"]["speech"].is<const char*>()) { show("Invalid response"); return; }
  show(String(response["reply"]["speech"].as<const char*>()));
}

void beginRecording() {
  if (session.isEmpty()) { show("Pair session first"); return; }
  if (!audioSamples) audioSamples = static_cast<int16_t*>(ps_malloc(maxSamples * sizeof(int16_t)));
  if (!audioSamples) { show("Audio memory error"); return; }
  M5.Speaker.end();
  if (!M5.Mic.begin()) { show("Microphone error"); return; }
  sampleCount = 0; chunkPending = false; recording = true;
  show("Listening (5 sec max)");
}

void updateRecording() {
  if (!recording) return;
  if (chunkPending && !M5.Mic.isRecording()) { sampleCount += chunkSamples; chunkPending = false; }
  const bool stop = !M5.BtnA.isPressed() || sampleCount >= maxSamples;
  if (stop && !chunkPending) {
    recording = false; M5.Mic.end();
    if (sampleCount) { show("Sending audio"); sendAudio(); } else { show("No audio captured"); }
    return;
  }
  if (!stop && !chunkPending) {
    if (!M5.Mic.record(audioSamples + sampleCount, chunkSamples, sampleRate)) {
      recording = false; M5.Mic.end(); show("Microphone error"); return;
    }
    chunkPending = true;
  }
}

void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);
  M5.setTouchButtonHeight(60);
  Serial.begin(115200);
  show("Connecting Wi-Fi");
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  const unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) { M5.update(); delay(20); }
  show(WiFi.status() == WL_CONNECTED ? "Send session via USB" : "Wi-Fi error");
}

void loop() {
  M5.update();
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("session ")) {
      session = line.substring(8);
      show(session.isEmpty() ? "Pair session first" : (WiFi.status() == WL_CONNECTED ? "Session paired" : String("Paired; Wi-Fi status ") + static_cast<int>(WiFi.status())));
    }
  }
  if (!recording && M5.BtnA.wasPressed()) beginRecording();
  if (recording) updateRecording();
  else if (M5.BtnB.wasPressed()) sendIntent();
  delay(10);
}
