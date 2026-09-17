#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include <HT_SSD1306Wire.h>

// Configurações do dispositivo
const char* deviceName = "ESP-0001";      

// Configurações do Wi-Fi
const char* ssid = "LabNano 3D";        
const char* password = "12345678";      

// Configurações do Broker MQTT
const char* mqtt_server = "129.148.60.17";  
const int mqtt_port = 1883;                
const char* mqtt_user = "labnano3d";       
const char* mqtt_pass = "testes";          

// Instâncias
WiFiClient espClient;
PubSubClient client(espClient);
Adafruit_ADS1115 ads;
static SSD1306Wire display(0x3c, 500000, SDA_OLED, SCL_OLED,
                           GEOMETRY_128_64, RST_OLED);

// Status
String wifiStatus = "Desconectado";
String mqttStatus = "Desconectado";
String adcValue = "Aguardando";

// Display
void updateDisplay() {
  display.clear();
  display.setFont(ArialMT_Plain_10);
  int16_t xPos = (128 - display.getStringWidth(deviceName)) / 2;
  display.drawString(xPos, 0, deviceName);
  display.drawString(0, 12, "Wi-Fi: " + wifiStatus);
  display.drawString(0, 22, "MQTT: " + mqttStatus);
  display.drawString(0, 34, "Diff0_1: " + adcValue);
  display.display();
}

// WiFi
void connectWiFi() {
  Serial.println("=== Iniciando conexão Wi-Fi ===");
  wifiStatus = "Conectando...";
  mqttStatus = "Desconectado";
  updateDisplay();

  WiFi.begin(ssid, password);
  WiFi.setHostname(deviceName);

  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    tentativas++;
    if (tentativas > 40) {
      Serial.println("\n[ERRO] Não conseguiu conectar ao Wi-Fi!");
      return;
    }
  }
  wifiStatus = "Conectado";
  updateDisplay();
  Serial.println("\n[OK] Conectado ao Wi-Fi");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
}

// MQTT
void connectMQTT() {
  Serial.println("=== Iniciando conexão MQTT ===");
  mqttStatus = "Conectando...";
  updateDisplay();

  while (!client.connected()) {
    Serial.print("Conectando ao broker MQTT...");
    if (client.connect(deviceName, mqtt_user, mqtt_pass)) {
      Serial.println(" [OK]");
      mqttStatus = "Conectado";
      updateDisplay();
    } else {
      Serial.print(" [FALHA] Código: ");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Iniciando Setup ===");

  Serial.println("Inicializando display...");
  display.init();
  display.clear();
  updateDisplay();
  Serial.println("[OK] Display pronto.");

  Serial.println("Inicializando ADS1115...");
  if (!ads.begin()) {
    Serial.println("[ERRO] Falha ao inicializar ADS1115.");
    while (1);
  }
  ads.setGain(GAIN_FOUR);
  ads.setDataRate(RATE_ADS1115_16SPS);
  Serial.println("[OK] ADS1115 pronto.");

  connectWiFi();
  client.setServer(mqtt_server, mqtt_port);
  connectMQTT();

  Serial.println("=== Setup concluído ===\n");
}

void loop() {
  // Conexão Wi-Fi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[AVISO] Wi-Fi desconectado. Tentando reconectar...");
    wifiStatus = "Desconectado";
    updateDisplay();
    connectWiFi();
  }

  // Conexão MQTT
  if (!client.connected()) {
    Serial.println("[AVISO] MQTT desconectado. Tentando reconectar...");
    mqttStatus = "Desconectado";
    updateDisplay();
    connectMQTT();
  }
  client.loop();

  // ---- Leitura diferencial entre A0 e A1 ----
  Serial.println("\n--- Leitura diferencial A0-A1 ---");
  int16_t diff_0_1 = ads.readADC_Differential_0_1();
  adcValue = String(diff_0_1);
  Serial.print("ADC Diff0_1: ");
  Serial.println(diff_0_1);

  // Publica valor bruto no tópico solicitado
  client.publish("espeleorobo/roda1/sensor1", String(diff_0_1).c_str());

  updateDisplay();
  delay(100);
}