# micropython-obd2can
A micropython class to retrieve car's PID live parameter using ESP32 native TWAI/CAN peripheral.\
Made possible thanks to Viktor's [micropython-esp32-twai](https://github.com/straga/micropython-esp32-twai).

## How to
Simply connect CAN tranceiver module like `TJA1050`, `SN65HVD230`, or `MCP2551` to the `can_rx` and `can_tx` pins of ESP32.\
Then connect the module's `CAN_H` and `CAN_L` pins to the car's OBD2 port, usually pin 6 and 14 respectively with the common ground as well.

![https://forum.arduino.cc/t/esp32-waveshare-sn65hvd230-can/1089185](https://europe1.discourse-cdn.com/arduino/original/4X/4/8/b/48b291219c72f8507d8c67aba5713d956c8bf9bf.jpeg)

### Pseudo ELM237 serial `request` for RPM `0x0C`
```py
obd.request(0x01, 0x0C) # service_id, pid_code
```
### `response`
```py
memoryview(0x41, 0x0C, 0x0D, 0x98) # service_id + 0x40, pid_code, 2-bytes MSB-firts data for RPM
```

## Example code
### `main.py`
```py
from obd2can import OBD2CAN, supported_pids

def main() -> None:
    obd = OBD2CAN(rx=20, tx=21, extframe=True, debug=True)

    try:
        print(f'VIN: {obd.get_vin()}\n')
        print(f'DTC: {obd.get_dtcs()}\n')
        print(f'PID: {obd.to_hex(obd.get_supported_pid())}\n')

        for pid_str in ['rpm', 'speed', 'maf', 'volt_module', 'coolant_temp']:
            val = obd.get_pid(pid_str)
            if val is not None:
                print(f'{pid_str.upper()}: {val} {supported_pids[pid_str][2]}\n')

    except KeyboardInterrupt:
        pass
    finally:
        obd.deinit()
```
### `console`
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

### Disclaimer
> [!CAUTION]
> Working with a vehicle’s CAN bus involves risks, including possible damage to the vehicle’s electronics and safety systems. Proceed entirely at your own risk!
