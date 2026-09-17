# ESP32 Firmware for ADS1115 ADC

This firmware enables the ESP32 to communicate with an ADS1115 16-bit ADC and relay readings to the Keithley LabNano3D application via serial/USB.

## Hardware Requirements

- ESP32 development board
- ADS1115 16-bit ADC module
- USB cable for ESP32
- (Optional) ESP32 board with built-in OLED display (e.g., Heltec WiFi Kit 32)

## Wiring

Connect the ADS1115 to the ESP32 as follows:

```
ESP32          ADS1115
-----          -------
3V3    ----->  VDD
GND    ----->  GND
GPIO21 (SDA) -> SDA
GPIO22 (SCL) -> SCL
```

For sensor connections to ADS1115:
```
ADS1115        Sensor
-------        ------
A0             Sensor signal
A1             Optional sensor 2
A2             Optional sensor 3
A3             Optional sensor 4
GND            Sensor GND (common)
```

## Software Setup

### 1. Install Arduino IDE

Download and install the Arduino IDE from: https://www.arduino.cc/en/software

### 2. Install ESP32 Board Support

1. Open Arduino IDE
2. Go to File > Preferences
3. Add this URL to "Additional Board Manager URLs":
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Go to Tools > Board > Boards Manager
5. Search for "esp32" and install "esp32 by Espressif Systems"

### 3. Install Required Libraries

1. Go to Sketch > Include Library > Manage Libraries
2. Search for and install:
   - "Adafruit ADS1X15" by Adafruit
   - (Optional) "Heltec ESP32 Dev-Boards" if using Heltec WiFi Kit 32 or similar boards with OLED

### 4. Configure for Your Hardware

**For ESP32 boards with built-in OLED display (e.g., Heltec WiFi Kit 32):**

1. Open `esp32_ads1115.ino` in Arduino IDE
2. Find line 29: `// #define HAS_DISPLAY`
3. Uncomment it (remove the `//`): `#define HAS_DISPLAY`
4. Find line 30: `// #include <HT_SSD1306Wire.h>`
5. Uncomment it: `#include <HT_SSD1306Wire.h>`
6. Save the file

**Important**: Initializing the display first is critical for some ESP32 boards (like Heltec) as it properly configures the I2C bus that the ADS1115 uses.

**For standard ESP32 boards without display:**

No changes needed - the firmware works as-is.

### 5. Upload Firmware

1. Open `esp32_ads1115.ino` in Arduino IDE (with display configuration if needed)
2. Select your ESP32 board:
   - Tools > Board > ESP32 Arduino > (your ESP32 model)
   - For Heltec boards: select "WiFi Kit 32" or "Wireless Stick"
3. Select the correct port:
   - Tools > Port > (your ESP32's serial port)
4. Click Upload button (right arrow icon)
5. Wait for "Done uploading" message

### 6. Test Communication

### 6. Test Communication

1. Open Serial Monitor (Tools > Serial Monitor)
2. Set baud rate to 115200
3. You should see:
   ```
   === ESP32 LabNano3D Starting ===
   Initializing display... (if display enabled)
   [OK] Display ready (if display enabled)
   Initializing ADS1115...
   [OK] ADS1115 initialized successfully
   READY
   === Setup Complete ===
   ```
4. Type `INFO` and press Enter
5. You should receive device information in JSON format

**If you see errors**: See the Troubleshooting section below.

## Serial Protocol

### Commands from PC to ESP32

1. **Get Device Info**
   ```
   INFO
   ```
   Response: `{"id":"ESP32_ADS1115","version":"1.0.0"}`

2. **Read ADC Value**
   ```
   READ_ADS <channel> <gain>
   ```
   - `channel`: 0-3 for single-ended (A0-A3), 4-7 for differential
   - `gain`: 0-5 (see gain table below)
   
   Response: `OK:<value>` where value is a 16-bit signed integer

### Channel Mapping

| Channel | Mode | Description |
|---------|------|-------------|
| 0 | Single-ended | A0 to GND |
| 1 | Single-ended | A1 to GND |
| 2 | Single-ended | A2 to GND |
| 3 | Single-ended | A3 to GND |
| 4 | Differential | A0 - A1 |
| 5 | Differential | A0 - A3 |
| 6 | Differential | A2 - A3 |
| 7 | Differential | A1 - A3 |

### Gain Settings

| Gain | Value | Range |
|------|-------|-------|
| 0 | 2/3x | ±6.144V |
| 1 | 1x | ±4.096V |
| 2 | 2x | ±2.048V |
| 3 | 4x | ±1.024V |
| 4 | 8x | ±0.512V |
| 5 | 16x | ±0.256V |

**Note**: Do not exceed VDD+0.3V on any input!

## Usage in LabNano3D

1. Upload this firmware to your ESP32
2. Connect ESP32 to PC via USB
3. Launch LabNano3D application
4. Select "Instrumento + ESP32" mode
5. Click "ESP32" tab in instrument management
6. Click "Buscar Dispositivos" to find your ESP32
7. Select the ESP32 port and click "Conectar Selecionado"
8. Click "⚙️ Calibrar ADS1115" to configure your sensor

## Sensor Calibration Example

### Humidity Sensor (e.g., capacitive soil moisture sensor)

1. Connect sensor to A0 and GND
2. In LabNano3D, open calibration dialog
3. Select channel A0
4. Select "Percentual (0-100%)" reading type
5. Place sensor in dry condition
6. Click "Atualizar Leitura" to see current value
7. Click "Definir como Mín" (or "Definir como Máx" depending on sensor)
8. Place sensor in wet condition
9. Click "Atualizar Leitura"
10. Click "Definir como Máx" (or "Definir como Mín")
11. Click "Aplicar Calibração"

The system will automatically detect if readings are inverted (min > max).

## Troubleshooting

### ESP32 not detected
- Check USB cable (must be data cable, not charge-only)
- Install CH340/CP2102 drivers if needed
- Try different USB port

### "Failed to read from ESP32" warnings in application
This warning occurs when the Python application cannot communicate with the ESP32. Common causes:

1. **WRONG FIRMWARE LOADED** - **MOST COMMON ISSUE**:
   - **Verify you uploaded `esp32_ads1115.ino` and NOT `GMS-SBPMat.ino`**
   - `GMS-SBPMat.ino` is a WiFi/MQTT example - it does NOT respond to serial commands
   - The application requires `esp32_ads1115.ino` for serial communication
   - Check Serial Monitor (115200 baud) - you should see:
     ```
     === ESP32 LabNano3D Starting ===
     Initializing ADS1115...
     [OK] ADS1115 initialized successfully
     READY
     === Setup Complete ===
     ```
   - Type `INFO` in Serial Monitor - should return JSON device info
   - If you see WiFi/MQTT messages, you have the wrong firmware!

2. **ESP32 not responding to commands**:
   - Re-upload `esp32_ads1115.ino` firmware
   - Press reset button on ESP32 after upload
   - Close any Serial Monitor windows before connecting from application
   - Check logs for "Empty response from ESP32" or "No response from ESP32"

3. **Serial port issues**:
   - Ensure no other program (Arduino IDE Serial Monitor, etc.) is using the serial port
   - Try disconnecting and reconnecting ESP32
   - Check application logs for detailed communication messages

4. **Baud rate mismatch**:
   - Firmware uses 115200 baud (default)
   - Application should match automatically

### ADS1115 not found / "ERROR:Failed to initialize ADS1115"
This error occurs when the ESP32 cannot communicate with the ADS1115. Try these solutions:

1. **FOR BOARDS WITH OLED DISPLAY (e.g., Heltec WiFi Kit 32)** - **MOST COMMON FIX**:
   - **You MUST enable display support in the firmware**
   - Open `esp32_ads1115.ino`
   - Uncomment line 29: `#define HAS_DISPLAY`
   - Uncomment line 30: `#include <HT_SSD1306Wire.h>`
   - Upload the modified firmware
   - **Why**: The display initialization properly configures the I2C bus that the ADS1115 uses
   - Without this, the I2C bus may not be initialized correctly on some ESP32 boards

2. **Check wiring connections**:
   - Verify SDA and SCL are connected correctly
   - Ensure VDD is connected to 3.3V (not 5V on ESP32)
   - Check all GND connections are solid

3. **Verify I2C address**:
   - Default ADS1115 address is 0x48
   - If ADDR pin is connected to VDD, address becomes 0x49
   - The firmware automatically tries both addresses

3. **Check I2C pullup resistors**:
   - Most ADS1115 modules have onboard pullup resistors
   - If not, add 4.7kΩ resistors from SDA to 3.3V and SCL to 3.3V

4. **Use I2C scanner** to verify the ADS1115 is detected:
   ```cpp
   // Upload this simple I2C scanner sketch to verify ADS1115 address
   #include <Wire.h>
   
   void setup() {
     Serial.begin(115200);
     Wire.begin();
     Serial.println("I2C Scanner");
   }
   
   void loop() {
     for(byte i = 0; i < 128; i++) {
       Wire.beginTransmission(i);
       if(Wire.endTransmission() == 0) {
         Serial.print("Found I2C device at 0x");
         Serial.println(i, HEX);
       }
     }
     delay(5000);
   }
   ```

5. **Power issues**:
   - Some ESP32 boards have limited 3.3V current
   - Try using external 3.3V power supply for ADS1115
   - Check if ADS1115 LED (if present) is lit

6. **Library version**:
   - Ensure you have the latest "Adafruit ADS1X15" library
   - Update via Arduino Library Manager

### Erratic readings
- Add decoupling capacitor (0.1µF) near ADS1115 VDD
- Keep sensor wires short
- Use twisted pair for long sensor cables
- Add common mode choke if necessary

## Example Application: Soil Moisture Monitoring

Connect a capacitive soil moisture sensor to A0:
- Red wire -> 3V3
- Black wire -> GND
- Yellow/Signal -> ADS1115 A0

Calibrate:
- Dry reading (in air): ~30000
- Wet reading (in water): ~15000
- Inverted: Yes (wet = low value)

The software will automatically convert to 0-100% scale.

## License

This firmware is part of the Keithley LabNano3D project and is distributed under the same license (MIT).
