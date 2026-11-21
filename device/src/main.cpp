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
  M5.Display.println("\nTAP TO BUY: touch bottom centre");
}

void sendIntent() {
  if (session.isEmpty()) { show("Pair session first"); return; }
  if (WiFi.status() != WL_CONNECTED) { show("Wi-Fi disconnected"); return; }
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

void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);
  Serial.begin(115200);
  show("Connecting Wi-Fi");
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
      show(session.isEmpty() ? "Pair session first" : "Session paired");
    }
  }
  if (M5.BtnB.wasPressed()) sendIntent();
  delay(10);
}
