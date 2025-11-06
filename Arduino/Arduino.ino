#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <RTClib.h>

// ==== Pinos RC522 ====
#define SS_PIN   10
#define RST_PIN  9
MFRC522 mfrc522(SS_PIN, RST_PIN);

// ==== RTC ====
RTC_DS3231 rtc;

// ==== LEDs ====
#define LED_YELLOW 3
#define LED_GREEN  4
#define LED_RED    5

// ==== Debounce ====
const unsigned long DEBOUNCE_MS = 1500;
String ultimoUID = "";
unsigned long ultimoMillis = 0;

// ==== Timeout para resposta do Python ====
const unsigned long ACK_TIMEOUT_MS = 2000; // 2s

void setAllOff() {
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, LOW);
}

void showYellow() {
  digitalWrite(LED_YELLOW, HIGH);
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, LOW);
}

void showGreen(unsigned long ms = 800) {
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_GREEN, HIGH);
  digitalWrite(LED_RED, LOW);
  delay(ms);
  setAllOff();
}

void showRed(unsigned long ms = 1200) {
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, HIGH);
  delay(ms);
  setAllOff();
}

void setup() {
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  setAllOff();

  Serial.begin(9600);
  while (!Serial) { ; }

  // RTC (opcional)
  Wire.begin();
  rtc.begin();
  // rtc.adjust(DateTime(F(__DATE__), F(__TIME__))); // <-- use 1x se precisar acertar

  SPI.begin();
  mfrc522.PCD_Init();
  delay(50);

  //Serial.println("READY"); // simples “ping” pro PC saber que subiu
}

bool waitAckFromPython() {
  unsigned long start = millis();
  String line = "";
  while (millis() - start < ACK_TIMEOUT_MS) {
    while (Serial.available() > 0) {
      char c = (char)Serial.read();
      if (c == '\r') continue;
      if (c == '\n') {
        line.trim();
        if (line == "OK")  return true;
        if (line == "ERR") return false;
        line = ""; // ignora linhas desconhecidas
      } else {
        line += c;
      }
    }
  }
  // se não veio nada no tempo, considerar erro
  return false;
}

void loop() {
  // Sem novo cartão?
  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial())   return;

  // Status “lendo”
  showYellow();

  // Monta UID
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();

  // Debounce (mesmo cartão em < DEBOUNCE_MS)
  unsigned long agora = millis();
  if (uid == ultimoUID && (agora - ultimoMillis) < DEBOUNCE_MS) {
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
    setAllOff();
    return;
  }
  ultimoUID = uid;
  ultimoMillis = agora;

  // Envia UID para o Python
  Serial.println(uid);

  // Aguarda resposta do Python (OK / ERR)
  bool ok = waitAckFromPython();

  if (ok) showGreen();
  else    showRed();

  // Finaliza comunicação com este cartão
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
}
