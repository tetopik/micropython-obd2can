# micropython-obd2can
ESP32 TWAI Controller to read OBD2 PIDs like ELM237 running Micropython

Made possible thanks to Straga https://github.com/straga/micropython-esp32-twai

> Example code:
```py
from obd2can import OBD2CAN, supported_pids


obd = OBD2CAN(20, 21)

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

> Example output:
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


To-do next:
- Get VIN (multiframe request)
- Get DTC (possible multiframe request)
