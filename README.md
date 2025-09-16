### Disclaimer
> [!CAUTION]
> Working with a vehicle’s CAN bus involves risks, including possible damage to the vehicle’s electronics and safety systems. Proceed entirely at your own risk!
---

# micropython-obd2can

A lightweight MicroPython library to communicate with vehicle ECUs over **OBD-II CAN bus** using ESP32 native TWAI/CAN peripheral.
- Supports reading **PIDs**, **VIN**, and **DTCs**, with both 11-bit (standard) and 29-bit (extended) CAN IDs.  
- Handles **multi-frame ISO-TP responses**.
- The library supports both standard and extended CAN frame formats and includes debug logging for troubleshooting.

Made possible thanks to Viktor's [micropython-esp32-twai](https://github.com/straga/micropython-esp32-twai).

---

## Features
- Query supported OBD-II Parameter IDs (PIDs)
- Retrieve Diagnostic Trouble Codes (DTCs)
- Fetch Vehicle Identification Number (VIN)
- Access real-time vehicle data (e.g., RPM, speed, coolant temperature)
- Support for standard (11-bit) and extended (29-bit) CAN identifiers
- LED status indication and debug logging

## Installation
1. Ensure you have a MicroPython-compatible microcontroller with CAN bus support.
2. Copy the `obd2can.py` file to your microcontroller's filesystem: `ampy put obd2can.py`.
3. Ensure the `CAN` module (a CAN bus native driver) is available on your device.

## Dependencies
- [micropython-esp32-twai](https://github.com/straga/micropython-esp32-twai)

## Usage
Simply connect CAN tranceiver module like `TJA1050`, `SN65HVD230`, or `MCP2551` to the `can_rx` and `can_tx` pins of ESP32.\
Then connect the module's `CAN_H` and `CAN_L` pins to the car's OBD2 port, usually pin 6 and 14 respectively with the common ground as well.

![https://forum.arduino.cc/t/esp32-waveshare-sn65hvd230-can/1089185](https://europe1.discourse-cdn.com/arduino/original/4X/4/8/b/48b291219c72f8507d8c67aba5713d956c8bf9bf.jpeg)

### VIN Request
    Request: 09 02
    Response: 49 02 01 57 50 30 5A 5A 5A 39 39 39 39 39 39 39 39 39
    VIN: WP0ZZZ99999999999

### DTCs Request
    Request: 03
    Response: 43 02 01 43 91 92
    Decoded: ['P0143', 'B1192']

### RPM Request
    Request: 01 0C
    Response: 41 0C 1A F8
    Decoded: ((0x1A << 8) + 0xF8) / 4 = 1726 rpm
    
### Example code
```py
from obd2can import OBD2CAN

def main():
    # Initialize OBD2CAN with RX pin 20, TX pin 21, extended frame, and debug mode
    obd = OBD2CAN(rx=20, tx=21, extframe=False, debug=True, led_pin=8)

    try:
        # Get VIN
        vin = obd.get_vin()
        print(f'VIN: {vin.decode()}\n')

        # Get DTCs
        dtcs = obd.get_dtcs()
        print(f'DTC: {' '.join(dtc.decode() for dtc in dtcs)}\n')

        # Get supported PIDs
        supported_pids = obd.get_supported_pid()
        print(f'PID: {obd.to_hex(supported_pid)}\n')

        # Query all known PIDs
        for pid in supported_pids:
            val = obd.get_pid(pid_str)
            if val is not None:
                if isinstance(val, memoryview): val = obd.to_hex(val)
                print(f'{pid_str.upper()}: {val} {supported_pids[pid_str][2]}\n')

        # Live streaming some important PIDs
        obd.debug = False
        while True:
            print(
                int(obd.get_pid('coolant_temp')), 'C |',
                round(obd.get_pid('volt_module'), 1), 'V |',
                int(obd.get_pid('rpm')), 'RPM',
                end='\r')
            sleep_ms(100)

    finally:
        obd.deinit()

if __name__ == '__main__':
    main()
```
### `Console`
```
CAN: TIMING
CAN: timing brp=0
CAN: timing tseg_1=15
CAN: timing tseg_2=4
CAN: timing sjw=3
CAN: timing triple_sampling=0
CAN: BRP_MIN=2, BRP_MAX=16384
CAN: bitrate 500000kb
CAN: Mode 0
CAN: Loopback flag 0

---------- CAN0 UP ----------

CAN: [DEBUG] REQUEST  >> 02 09 02 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << --------TIMEOUT--------
CAN: [DEBUG] ERROR no response for VIN package.
VIN: 

CAN: [DEBUG] REQUEST  >> 01 03 CC CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 02 43 00 55 55 55 55 55
DTC: 

CAN: [DEBUG] REQUEST  >> 02 01 00 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 06 41 00 BC 3F A8 03 55
CAN: [DEBUG] REQUEST  >> 02 01 20 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 06 41 20 80 05 B0 01 55
CAN: [DEBUG] REQUEST  >> 02 01 40 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 06 41 40 7A D0 00 00 55
PID: 01 03 04 05 06 0B 0C 0D 0E 0F 10 11 13 15 1F 21 2E 30 31 33 34 42 43 44 45 47 49 4A 4C

CAN: [DEBUG] REQUEST  >> 02 01 2E CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 2E 2E 55 55 55 55
EVAP_PURGE: 18.03922 %

CAN: [DEBUG] REQUEST  >> 02 01 07 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << --------TIMEOUT--------
CAN: [DEBUG] ERROR no response for PID LTFT_BANK1.

CAN: [DEBUG] REQUEST  >> 02 01 01 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 06 41 01 00 04 60 00 55
MONITOR_STATUS: 00 04 60 00 Bit encoded

CAN: [DEBUG] REQUEST  >> 02 01 10 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 04 41 10 00 CF 55 55 55
MAF: 2.07 g/s

CAN: [DEBUG] REQUEST  >> 02 01 0B CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 0B 1A 55 55 55 55
INTAKE_PRESS: 26 kPa

CAN: [DEBUG] REQUEST  >> 02 01 03 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 04 41 03 02 00 55 55 55
FUEL_STATUS: 02 00 Bit encoded

CAN: [DEBUG] REQUEST  >> 02 01 11 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 11 27 55 55 55 55
THROTTLE_POS: 15.29412 %

CAN: [DEBUG] REQUEST  >> 02 01 14 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << --------TIMEOUT--------
CAN: [DEBUG] ERROR no response for PID O2_S1_BANK1.

CAN: [DEBUG] REQUEST  >> 02 01 15 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 04 41 15 2F 78 55 55 55
O2_S2_BANK1: (0.235, -6.25) V, %

CAN: [DEBUG] REQUEST  >> 02 01 1F CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 04 41 1F 01 6A 55 55 55
RUN_TIME: 362 s

CAN: [DEBUG] REQUEST  >> 02 01 21 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 04 41 21 00 00 55 55 55
MIL_DIST: 0 km

CAN: [DEBUG] REQUEST  >> 02 01 0D CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 0D 00 55 55 55 55
SPEED: 0 km/h

CAN: [DEBUG] REQUEST  >> 02 01 0F CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 0F 4A 55 55 55 55
INTAKE_TEMP: 34 °C

CAN: [DEBUG] REQUEST  >> 02 01 2F CC CC CC CC CC
CAN: [DEBUG] RESPONSE << --------TIMEOUT--------
CAN: [DEBUG] ERROR no response for PID FUEL_LEVEL.

CAN: [DEBUG] REQUEST  >> 02 01 04 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 04 39 55 55 55 55
ENGINE_LOAD: 22.35294 %

CAN: [DEBUG] REQUEST  >> 02 01 0E CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 0E 99 55 55 55 55
TIMING_ADV: 12.5 ° before TDC

CAN: [DEBUG] REQUEST  >> 02 01 33 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 33 64 55 55 55 55
BARO_PRESS: 100 kPa

CAN: [DEBUG] REQUEST  >> 02 01 34 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 06 41 34 7F 97 7F FE 55
O2_S1_RATIO: 0.9967957 ratio

CAN: [DEBUG] REQUEST  >> 02 01 30 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 30 02 55 55 55 55
WARM_UPS: 2 count

CAN: [DEBUG] REQUEST  >> 02 01 42 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 04 41 42 37 C3 55 55 55
VOLT_MODULE: 14.275 V

CAN: [DEBUG] REQUEST  >> 02 01 06 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 06 78 55 55 55 55
STFT_BANK1: -6.25 %

CAN: [DEBUG] REQUEST  >> 02 01 43 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 04 41 43 00 2C 55 55 55
ABS_LOAD: 17.2549 %

CAN: [DEBUG] REQUEST  >> 02 01 44 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 04 41 44 7D AB 55 55 55
CMD_AIR_FUEL: 0.981781 ratio

CAN: [DEBUG] REQUEST  >> 02 01 45 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 45 0B 55 55 55 55
REL_THROTTLE: 4.313725 %

CAN: [DEBUG] REQUEST  >> 02 01 47 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 47 52 55 55 55 55
THROTTLE_B: 32.15686 %

CAN: [DEBUG] REQUEST  >> 02 01 49 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 49 2F 55 55 55 55
ACCEL_D: 18.43137 %

CAN: [DEBUG] REQUEST  >> 02 01 4C CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 4C 0C 55 55 55 55
CMD_THROTTLE: 4.705883 %

CAN: [DEBUG] REQUEST  >> 02 01 31 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 04 41 31 00 27 55 55 55
CLR_DIST: 39 km

CAN: [DEBUG] REQUEST  >> 02 01 41 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 06 41 41 00 04 00 00 55
TIME_RUN_MIL: 4 min

CAN: [DEBUG] REQUEST  >> 02 01 4D CC CC CC CC CC
CAN: [DEBUG] RESPONSE << --------TIMEOUT--------
CAN: [DEBUG] ERROR no response for PID TIME_SINCE_DTC.

CAN: [DEBUG] REQUEST  >> 02 01 0C CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 04 41 0C 0C 08 55 55 55
RPM: 770.0 rpm

CAN: [DEBUG] REQUEST  >> 02 01 13 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 13 03 55 55 55 55
O2_SENSORS: 03 Bit encoded

CAN: [DEBUG] REQUEST  >> 02 01 05 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 05 6C 55 55 55 55
COOLANT_TEMP: 68 °C


--------- CAN0 DOWN ---------
```

## Methods
```py
__init__(rx, tx, mode=CAN.NORMAL, bitrate=500_000, extframe=False, debug=False, led_pin=-1)
```
Initializes the OBD2CAN interface.
- Parameters:
    - `rx (int)`: CAN receive pin number.
    - `tx (int)`: CAN transmit pin number.
    - `mode (int)`: CAN bus mode (e.g., CAN.NORMAL). Defaults to CAN.NORMAL.
    - `bitrate (int)`: CAN bus bitrate in bits per second. Defaults to 500000.
    - `extframe (bool)`: Use extended frame format if True. Defaults to False.
    - `debug (bool)`: Enable debug logging if True. Defaults to False.
    - `led_pin (int)`: Pin number for status LED. Defaults to -1.


```py
deinit()
```
Deinitializes the `CAN` bus and turns off the status LED.


```py
log(*msg)
```
Logs debug messages if debug mode is enabled.
- Parameters:
    `*msg`: Variable number of message strings to log.


```py
to_hex(data)
```
Converts data to a hexadecimal string representation.
- Parameters:
    `data`: Data to convert (`bytes` or list of `integers`).\
Returns: Space-separated hexadecimal string.


```py
send(*payload, retries=3)
```
Sends a `CAN` message with the specified payload.
- Parameters:
    - `*payload`: Variable number of `integers` to send as payload.
    - `retries (int)`: Number of retry attempts. Defaults to `3`.
Returns: `True` if the message was sent successfully, `False` otherwise.


```py
request(*payload, timeout_ms=500)
```
Sends an OBD-II request and waits for a response.
- Parameters:
    - `*payload`: Variable number of integers representing the request payload.
    - `timeout_ms (int)`: Response timeout in `milliseconds`. Defaults to `500`.
Returns: Response data as a `memoryview`, or `None` if no valid response.


```py
get_supported_pid(vehicle=False)
```
Retrieves the list of supported OBD-II Parameter IDs (PIDs).
- Parameters:
    - `vehicle (bool)`: Retrieve vehicle specific PIDs instead of standard PIDs.
Returns: A `bytes` object containing the supported PID codes.


```py
get_dtcs(clear=False)
```
Retrieves Diagnostic Trouble Codes (DTCs) from the vehicle.
- Parameters:
    - `clear (bool)`: Clearing all DTC's fault codes.
Returns: A list of DTCs encoded as `ASCII strings`.


```py
get_vin()
```
Retrieves the Vehicle Identification Number (VIN).\
Returns: The VIN as a `bytes` object, or empty `bytes` if invalid.


```py
get_pid(pid_str, freeze_frame=False)
```
Retrieves the value of a specific OBD-II Parameter ID (PID).
- Parameters:
    - `pid_str (str)`: The PID key (e.g., `'rpm'`, `'speed'`).
    - `freeze_frame (bool)`: If True, query freeze frame data. Defaults to `False`.
Returns: The decoded PID value (`float` or `int`), or `None` if the request fails.


## Miscs
### To-do list
- [x] Tested on some `ISO 15765-4 CAN` compliant vehicle with 500kbaud
- [x] Retieve all supported PIDs: `pid_code 0x00, 0x20, 0x40, ...`
- [x] Multiframe request for getting VIN and DTC fault code
- [x] Using both CAN hardware filter and manual `if` statement:
    ```py
    if 0x7E8 > can_id > 0x7EF:
        continue
    ```

### Further readings
- [ESP32 Two-Wire Automotive Interface (TWAI)](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/twai.html)
- [Wiki OBD-II PIDs](https://en.wikipedia.org/wiki/OBD-II_PIDs)
- [OBD2 Explained](https://www.csselectronics.com/pages/obd2-explained-simple-intro)

---

## Contributing
Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License
This project is licensed under the MIT License.
