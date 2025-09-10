### Disclaimer
> [!CAUTION]
> Working with a vehicle’s CAN bus involves risks, including possible damage to the vehicle’s electronics and safety systems. Proceed entirely at your own risk!


# micropython-obd2can

- The `OBD2CAN` library is a lightweight MicroPython library to communicate with vehicle ECUs over **OBD-II CAN bus** using ESP32 native TWAI/CAN peripheral.
- Supports reading **PIDs**, **VIN**, and **DTCs**, with both 11-bit (standard) and 29-bit (extended) CAN IDs.  
- Handles **multi-frame ISO-TP responses**.
- The library supports both standard and extended CAN frame formats and includes debug logging for troubleshooting.

Made possible thanks to Viktor's [micropython-esp32-twai](https://github.com/straga/micropython-esp32-twai).

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
3. Ensure the `CAN` module (a custom CAN bus driver) is available on your device.
4. Install required MicroPython libraries: `machine` and `time`.

## Dependencies
- `machine` (for Pin and Signal handling)
- `time` (for timing functions like `ticks_ms`, `ticks_add`, `ticks_diff`, `sleep_ms`)
- `CAN` (custom module for CAN bus communication)

## Usage
Below is an example of how to use the OBD2CAN class to retrieve vehicle data:

Simply connect CAN tranceiver module like `TJA1050`, `SN65HVD230`, or `MCP2551` to the `can_rx` and `can_tx` pins of ESP32.\
Then connect the module's `CAN_H` and `CAN_L` pins to the car's OBD2 port, usually pin 6 and 14 respectively with the common ground as well.

![https://forum.arduino.cc/t/esp32-waveshare-sn65hvd230-can/1089185](https://europe1.discourse-cdn.com/arduino/original/4X/4/8/b/48b291219c72f8507d8c67aba5713d956c8bf9bf.jpeg)

### VIN Request
    ```
    Request: 09 02
    Response: 49 02 01 57 50 30 5A 5A 5A 39 39 39 39 39 39 39 39 39
    VIN: WP0ZZZ99999999999
    ```
### DTCs Request
    ```
    Request: 03
    Response: 43 02 01 43 91 92
    Decoded: ['P0143', 'B1192']
    ```

### RPM Request
    ```
    Request: 01 0C
    Response: 41 0C 1A F8
    Decoded: ((0x1A << 8) + 0xF8) / 4 = 1726 rpm
    ```
    
### Example code
```py
from obd2can import OBD2CAN

def main():
    # Initialize OBD2CAN with RX pin 20, TX pin 21, extended frame, and debug mode
    obd = OBD2CAN(rx=20, tx=21, extframe=True, debug=True)
    try:
        # Get VIN
        vin = obd.get_vin()
        print('VIN:', vin.decode())

        # Get DTCs
        dtcs = obd.get_dtcs()
        print('DTC:', ' '.join(dtc.decode() for dtc in dtcs))

        # Get supported PIDs
        supported_pids = obd.get_supported_pid()
        print('PID:', obd.to_hex(supported_pids))

        # Query specific PIDs
        for pid in ['rpm', 'speed', 'maf', 'volt_module', 'coolant_temp']:
            val = obd.get_pid(pid)
            if val is not None:
                print(f'{pid.upper()}: {val} {obd2can.supported_pids[pid][2]}')
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
CAN: [DEBUG] RESPONSE << 10 14 49 02 01 54 48 49
CAN: [DEBUG] REQUEST  >> 30 00 00 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 21 53 20 49 53 20 44 55
CAN: [DEBUG] RESPONSE << 22 4D 4D 59 20 56 49 4E
VIN: THIS IS DUMMY VIN

CAN: [DEBUG] REQUEST  >> 01 03 CC CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 10 08 43 03 01 43 81 92
CAN: [DEBUG] REQUEST  >> 30 00 00 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 21 C0 12 AA AA AA AA AA
DTC: [b'P0143', b'B0192', b'U0012']

CAN: [DEBUG] REQUEST  >> 02 01 00 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 06 41 00 BC 3F A8 03 AA
CAN: [DEBUG] REQUEST  >> 02 01 20 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 06 41 20 80 07 B0 01 AA
CAN: [DEBUG] REQUEST  >> 02 01 40 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 06 41 40 7A 90 00 00 AA
PID: 01 03 04 05 06 0B 0C 0D 0E 0F 10 11 13 15 1F 21 2E 2F 30 31 33 34 42 43 44 45 47 49 4C

CAN: [DEBUG] REQUEST  >> 02 01 0C CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 04 41 0C 0D 80 AA AA AA
RPM: 864.0 rpm

CAN: [DEBUG] REQUEST  >> 02 01 0D CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 0D 35 AA AA AA AA
SPEED: 53 km/h

CAN: [DEBUG] REQUEST  >> 02 01 10 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 04 41 10 3B 42 AA AA AA
MAF: 151.7 g/s

CAN: [DEBUG] REQUEST  >> 02 01 42 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 04 41 42 36 27 AA AA AA
VOLT_MODULE: 13.863 V

CAN: [DEBUG] REQUEST  >> 02 01 05 CC CC CC CC CC
CAN: [DEBUG] RESPONSE << 03 41 05 91 AA AA AA AA
COOLANT_TEMP: 105 °C


--------- CAN0 DOWN ---------
```

## Methods
```py
__init__(rx, tx, mode=CAN.NORMAL, bitrate=500_000, extframe=False, debug=False, led_pin=8)
```
Initializes the OBD2CAN interface.
- Parameters:
    - `rx (int)`: CAN receive pin number.
    - `tx (int)`: CAN transmit pin number.
    - `mode (int)`: CAN bus mode (e.g., CAN.NORMAL). Defaults to CAN.NORMAL.
    - `bitrate (int)`: CAN bus bitrate in bits per second. Defaults to 500000.
    - `extframe (bool)`: Use extended frame format if True. Defaults to False.
    - `debug (bool)`: Enable debug logging if True. Defaults to False.
    - `led_pin (int)`: Pin number for status LED. Defaults to 8.


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
get_supported_pid()
```
Retrieves the list of supported OBD-II Parameter IDs (PIDs).\
Returns: A `bytes` object containing the supported PID codes.


```py
get_dtcs()
```
Retrieves Diagnostic Trouble Codes (DTCs) from the vehicle.\
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
- [ ] Using CAN hardware filters instead of manual `if` statement:
    ```py
    if 0x7E8 > can_id > 0x7EF:
        continue
    ```

### Further readings
- [ESP32 Two-Wire Automotive Interface (TWAI)](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/twai.html)
- [Wiki OBD-II PIDs](https://en.wikipedia.org/wiki/OBD-II_PIDs)
- [OBD2 Explained](https://www.csselectronics.com/pages/obd2-explained-simple-intro)

### Contributing
Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

### License
This project is licensed under the MIT License.
