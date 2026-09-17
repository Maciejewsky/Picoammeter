/*
 * ESP32 Firmware for Keithley LabNano3D
 * Provides ADS1115 ADC readings via serial communication
 * 
 * Required Libraries:
 * - Adafruit ADS1X15 (install via Arduino Library Manager)
 * - HT_SSD1306Wire (optional, for ESP32 boards with OLED display)
 * 
 * Hardware Connections:
 * - ESP32 SDA -> ADS1115 SDA
 * - ESP32 SCL -> ADS1115 SCL
 * - ESP32 3V3 -> ADS1115 VDD
 * - ESP32 GND -> ADS1115 GND
 * 
 * Serial Protocol:
 * Commands from PC:
 *   - "INFO" -> Returns device info as JSON
 *   - "READ_ADS <channel> <gain>" -> Returns ADC reading
 * 
 * Responses to PC:
 *   - "OK:<value>" for successful readings
 *   - "ERROR:<message>" for errors
 */

#include <Wire.h>
#include <Adafruit_ADS1X15.h>

// Optional display support for ESP32 boards with built-in OLED
// Uncomment the following lines if your ESP32 board has an OLED display
// #define HAS_DISPLAY
// #include <HT_SSD1306Wire.h>

// Create ADS1115 object
Adafruit_ADS1115 ads;

#ifdef HAS_DISPLAY
// Create display object (for ESP32 boards with OLED)
static SSD1306Wire display(0x3c, 500000, SDA_OLED, SCL_OLED,
                           GEOMETRY_128_64, RST_OLED);

// Display update function
void updateDisplay(String line1, String line2 = "", String line3 = "") {
  display.clear();
  display.setFont(ArialMT_Plain_10);
  display.drawString(0, 0, line1);
  if (line2.length() > 0) display.drawString(0, 12, line2);
  if (line3.length() > 0) display.drawString(0, 24, line3);
  display.display();
}
#endif

// Device info
const char* DEVICE_ID = "ESP32_ADS1115";
const char* FIRMWARE_VERSION = "1.0.0";

// Communication settings
const long BAUD_RATE = 115200;

void setup() {
  // Initialize serial communication
  Serial.begin(BAUD_RATE);
  Serial.println("\n=== ESP32 LabNano3D Starting ===");
  
  // Wait up to 5 seconds for serial port to connect (prevents hanging)
  unsigned long startTime = millis();
  while (!Serial && (millis() - startTime < 5000)) {
    ; // Wait for serial port to connect or timeout
  }
  
#ifdef HAS_DISPLAY
  // Initialize display FIRST (important for some ESP32 boards)
  // This properly configures the I2C bus
  Serial.println("Initializing display...");
  display.init();
  display.clear();
  updateDisplay("LabNano3D", "Initializing...");
  Serial.println("[OK] Display ready");
#endif
  
  // Initialize I2C (if display wasn't initialized)
#ifndef HAS_DISPLAY
  Wire.begin();
#endif
  
  // Small delay to allow I2C bus to stabilize
  delay(100);
  
  // Initialize ADS1115
  Serial.println("Initializing ADS1115...");
  
#ifdef HAS_DISPLAY
  updateDisplay("LabNano3D", "ADS1115...");
#endif
  
  // Try default address (0x48) first
  if (!ads.begin(0x48)) {
    Serial.println("ERROR:Failed to initialize ADS1115 at address 0x48");
    Serial.println("Trying alternate address 0x49...");
    
#ifdef HAS_DISPLAY
    updateDisplay("LabNano3D", "ADS1115 0x48 fail", "Trying 0x49...");
#endif
    
    // Try alternate address (0x49)
    if (!ads.begin(0x49)) {
      Serial.println("ERROR:Failed to initialize ADS1115 at address 0x49");
      Serial.println("Please check I2C connections and ADS1115 address");
      
#ifdef HAS_DISPLAY
      updateDisplay("ERROR", "ADS1115", "Not found!");
#endif
      
      while (1); // Stop if ADS1115 not found
    }
  }
  
  // Set default gain and data rate for better compatibility
  ads.setGain(GAIN_ONE);  // +/- 4.096V range (default)
  
  Serial.println("[OK] ADS1115 initialized successfully");
  
#ifdef HAS_DISPLAY
  updateDisplay("LabNano3D", "ADS1115 OK", "Ready!");
#endif
  
  // Send ready message
  Serial.println("READY");
  Serial.println("=== Setup Complete ===\n");
}

void loop() {
  // Check for incoming commands
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    processCommand(command);
  }
}

void processCommand(String command) {
  if (command.startsWith("INFO")) {
    // Return device information
    sendDeviceInfo();
  }
  else if (command.startsWith("READ_ADS")) {
    // Parse channel and gain
    int firstSpace = command.indexOf(' ');
    int secondSpace = command.indexOf(' ', firstSpace + 1);
    
    if (firstSpace > 0 && secondSpace > 0) {
      int channel = command.substring(firstSpace + 1, secondSpace).toInt();
      int gain = command.substring(secondSpace + 1).toInt();
      
      readADS1115(channel, gain);
    } else {
      Serial.println("ERROR:Invalid READ_ADS command format");
    }
  }
  else {
    Serial.println("ERROR:Unknown command");
  }
}

void sendDeviceInfo() {
  // Send device info as JSON
  Serial.print("{\"id\":\"");
  Serial.print(DEVICE_ID);
  Serial.print("\",\"version\":\"");
  Serial.print(FIRMWARE_VERSION);
  Serial.println("\"}");
}

void readADS1115(int channel, int gain) {
  // Set gain
  adsGain_t adsGain;
  switch (gain) {
    case 0: adsGain = GAIN_TWOTHIRDS; break;  // +/- 6.144V
    case 1: adsGain = GAIN_ONE; break;        // +/- 4.096V
    case 2: adsGain = GAIN_TWO; break;        // +/- 2.048V
    case 3: adsGain = GAIN_FOUR; break;       // +/- 1.024V
    case 4: adsGain = GAIN_EIGHT; break;      // +/- 0.512V
    case 5: adsGain = GAIN_SIXTEEN; break;    // +/- 0.256V
    default: adsGain = GAIN_ONE; break;
  }
  
  ads.setGain(adsGain);
  
  // Read from specified channel
  int16_t adcValue;
  
  if (channel >= 0 && channel <= 3) {
    // Single-ended channel (A0, A1, A2, A3)
    adcValue = ads.readADC_SingleEnded(channel);
  }
  else if (channel >= 4 && channel <= 7) {
    // Differential channel
    switch (channel) {
      case 4: adcValue = ads.readADC_Differential_0_1(); break;  // A0-A1
      case 5: adcValue = ads.readADC_Differential_0_3(); break;  // A0-A3
      case 6: adcValue = ads.readADC_Differential_2_3(); break;  // A2-A3
      case 7: adcValue = ads.readADC_Differential_1_3(); break;  // A1-A3
      default: adcValue = 0; break;
    }
  }
  else {
    Serial.println("ERROR:Invalid channel");
    return;
  }
  
  // Send result
  Serial.print("OK:");
  Serial.println(adcValue);
  
#ifdef HAS_DISPLAY
  // Update display with reading
  String channelStr = "Ch" + String(channel);
  String valueStr = "Val: " + String(adcValue);
  updateDisplay("LabNano3D", channelStr, valueStr);
#endif
}
