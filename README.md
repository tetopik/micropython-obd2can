𝐌𝐢𝐜𝐫𝐨𝐩𝐲𝐭𝐡𝐨𝐧 𝐄𝐒𝐏𝟑𝟐 𝐮𝐬𝐢𝐧𝐠 𝐧𝐚𝐭𝐢𝐯𝐞 𝐓𝐖𝐀𝐈 𝐩𝐞𝐫𝐢𝐩𝐡𝐞𝐫𝐚𝐥 𝐭𝐨 𝐫𝐞𝐚𝐝 𝐎𝐁𝐃𝟐 𝐏𝐈𝐃𝐬 𝐥𝐢𝐤𝐞 𝐄𝐋𝐌𝟐𝟑𝟕 𝐝𝐞𝐯𝐢𝐜𝐞.
=====================================================

Made possible thanks to Viktor's [micropython-esp32-twai](https://github.com/straga/micropython-esp32-twai).

---
𝑯𝒐𝒘 𝒕𝒐:
---
Simply connect CAN tranceiver module like `TJA1050`, `SN65HVD230`, or `MCP2551` to the `can_rx` and `can_tx` pins of an ESP32. And then connect `CAN H` and `CAN L` of the module to the car's OBD2 port, usually pin 6 and 14 respectively with the common ground as well.


To make a pseudo ELM237 serial request, simply call:
-
```py
obd2.request(0x01, 0x0C)
```
`0x01` = SERVICE ID

`0x0C` = PID CODE for RPM


The return:
-
```py
memoryview(0x41, 0x0C, 0x0D, 0x98)
```
`0x01` = SERVICE ID for valid response (`request + 0x40`)

`0x0C` = PID CODE for RPM

`0x0D, 0x98` = 2 bytes MSB value for RPM / 4

---
𝑬𝒙𝒂𝒎𝒑𝒍𝒆 𝒄𝒐𝒅𝒆:
---

> Example `main.py` code:
```py
from obd2can import OBD2CAN, supported_pids

obd = OBD2CAN(rx=20, tx=21)

try:
    print(f'Supported PIDs: {obd.to_hex(obd.get_supported_pid())}\n')

    for pid_str in ['rpm', 'speed', 'maf', 'volt_module', 'coolant_temp']:
        val = obd.get_pid(pid_str)
        if val is not None:
            print(f'{pid_str.upper()}: {val} {supported_pids[pid_str][2]}\n')
except:
    pass
finally:
    obd.can.deinit()
```

> Expected output:
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

=============================

CAN: [DEBUG] REQUEST  | 02 01 00 CC CC CC CC CC
CAN: [DEBUG] RESPONSE | 06 41 00 BC 3F A8 03 AA
CAN: [DEBUG] REQUEST  | 02 01 20 CC CC CC CC CC
CAN: [DEBUG] RESPONSE | 06 41 20 80 07 B0 01 AA
CAN: [DEBUG] REQUEST  | 02 01 40 CC CC CC CC CC
CAN: [DEBUG] RESPONSE | 06 41 40 7A 90 00 00 AA
Supported PIDs: 01 03 04 05 06 0B 0C 0D 0E 0F 10 11 13 15 1F 21 2E 2F 30 31 33 34 42 43 44 45 47 49 4C

CAN: [DEBUG] REQUEST  | 02 01 0C CC CC CC CC CC
CAN: [DEBUG] RESPONSE | 04 41 0C 0C 94 AA AA AA
RPM: 805.0 rpm

CAN: [DEBUG] REQUEST  | 02 01 0D CC CC CC CC CC
CAN: [DEBUG] RESPONSE | 03 41 0D 34 AA AA AA AA
SPEED: 52 km/h

CAN: [DEBUG] REQUEST  | 02 01 10 CC CC CC CC CC
CAN: [DEBUG] RESPONSE | 04 41 10 37 ED AA AA AA
MAF: 143.17 g/s

CAN: [DEBUG] REQUEST  | 02 01 42 CC CC CC CC CC
CAN: [DEBUG] RESPONSE | 04 41 42 32 2E AA AA AA
VOLT_MODULE: 12.846 V

CAN: [DEBUG] REQUEST  | 02 01 05 CC CC CC CC CC
CAN: [DEBUG] RESPONSE | 03 41 05 9F AA AA AA AA
COOLANT_TEMP: 119 °C
```


---
𝑻𝒐-𝒅𝒐 𝒏𝒆𝒙𝒕:
---
- Multiframe request for getting VIN and DTC fault code
