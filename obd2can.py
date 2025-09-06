from time import ticks_diff, ticks_add, ticks_ms
from machine import Pin, Signal
import CAN


supported_pids: dict[str, tuple] = {
    'monitor_status': (0x01, lambda data: data, 'Bit encoded'),  # Monitor status since DTCs cleared
    'fuel_status': (0x03, lambda data: data, 'Bit encoded'),  # Fuel system status
    'engine_load': (0x04, lambda data: (data[0] * 100) / 255, '%'),  # Calculated engine load
    'coolant_temp': (0x05, lambda data: data[0] - 40, '°C'),  # Engine coolant temperature
    'stft_bank1': (0x06, lambda data: (data[0] * 100 / 128) - 100, '%'),  # Short term fuel trim—Bank 1
    'ltft_bank1': (0x07, lambda data: (data[0] * 100 / 128) - 100, '%'),  # Long term fuel trim—Bank 1
    'intake_press': (0x0B, lambda data: data[0], 'kPa'),  # Intake manifold absolute pressure
    'rpm': (0x0C, lambda data: ((data[0] << 8) + data[1]) / 4.0, 'rpm'),  # Engine speed
    'speed': (0x0D, lambda data: data[0], 'km/h'),  # Vehicle speed
    'timing_adv': (0x0E, lambda data: (data[0] / 2.0) - 64, '° before TDC'),  # Timing advance
    'intake_temp': (0x0F, lambda data: data[0] - 40, '°C'),  # Intake air temperature
    'maf': (0x10, lambda data: ((data[0] << 8) + data[1]) / 100.0, 'g/s'),  # Mass air flow sensor
    'throttle_pos': (0x11, lambda data: (data[0] * 100) / 255, '%'),  # Throttle position
    'o2_sensors': (0x13, lambda data: data, 'Bit encoded'),  # Oxygen sensors present
    'o2_s1_bank1': (0x14, lambda data: ((data[0] / 200.0), (data[1] * 100 / 128) - 100 if data[1] != 0xFF else None),
                    'V, %'),  # O2 Sensor 1 Bank 1: Voltage, Short term fuel trim
    'o2_s2_bank1': (0x15, lambda data: ((data[0] / 200.0), (data[1] * 100 / 128) - 100 if data[1] != 0xFF else None),
                    'V, %'),  # Oxygen Sensor 2: Voltage, Short term fuel trim
    'run_time': (0x1F, lambda data: (data[0] << 8) + data[1], 's'),  # Run time since engine start
    'mil_dist': (0x21, lambda data: (data[0] << 8) + data[1], 'km'),  # Distance traveled with MIL on
    'evap_purge': (0x2E, lambda data: (data[0] * 100) / 255, '%'),  # Commanded evaporative purge
    'fuel_level': (0x2F, lambda data: (data[0] * 100) / 255, '%'),  # Fuel Tank Level Input
    'warm_ups': (0x30, lambda data: data[0], 'count'),  # Warm-ups since codes cleared
    'clr_dist': (0x31, lambda data: (data[0] << 8) + data[1], 'km'),  # Distance traveled since codes cleared
    'baro_press': (0x33, lambda data: data[0], 'kPa'),  # Absolute Barometric Pressure
    'o2_s1_ratio': (0x34, lambda data: ((data[0] << 8) + data[1]) * 2 / 65536, 'ratio'),
    # Oxygen Sensor 1: Air-Fuel Equivalence Ratio
    'volt_module': (0x42, lambda data: ((data[0] << 8) + data[1]) / 1000.0, 'V'),  # Control module voltage
    'abs_load': (0x43, lambda data: ((data[0] << 8) + data[1]) * 100 / 255, '%'),  # Absolute load value
    'cmd_air_fuel': (0x44, lambda data: ((data[0] << 8) + data[1]) * 2 / 65536, 'ratio'),
    # Commanded Air-Fuel Equivalence Ratio
    'rel_throttle': (0x45, lambda data: (data[0] * 100) / 255, '%'),  # Relative throttle position
    'throttle_b': (0x47, lambda data: (data[0] * 100) / 255, '%'),  # Absolute throttle position B
    'accel_d': (0x49, lambda data: (data[0] * 100) / 255, '%'),  # Accelerator pedal position D
    'cmd_throttle': (0x4C, lambda data: (data[0] * 100) / 255, '%'),  # Commanded throttle actuator
    'time_run_mil': (0x41, lambda data: (data[0] << 8) + data[1], 'min'),  # Time run with MIL on
    'time_since_dtc': (0x4D, lambda data: (data[0] << 8) + data[1], 'min')  # Time since DTCs cleared
}

class OBD2CAN:
    def __init__(self,
                 rx: int,
                 tx: int,
                 mode: int = 0,
                 bitrate: int = 500_000,
                 extframe: bool = True,
                 debug: bool = True,
                 led_pin: int = 8,
                 ) -> None:

        self.led = Signal(Pin(led_pin, Pin.OUT, value=0), invert=True)
        self.debug = debug
        self.extframe = extframe

        if not extframe:
            self._reqs_id: int = 0x7DF
            self._resp_id: tuple[int, int] = (0x7E8, 0x7EF)  # 111 1110 1XXX
            self._filter_mask: int = 0x7F8  # 111 1111 1000
        else:
            self._reqs_id: int = 0x18DB33F1
            self._resp_id: tuple[int, int] = (0x18DAF110, 0x18DAF11F)  # 1 1000 1101 1010 1111 0001 0001 XXXX
            self._filter_mask: int = 0x1FFFFFF0  # 1 1111 1111 1111 1111 1111 1111 0000

        self.can = CAN(0, tx=tx, rx=rx, mode=mode, bitrate=bitrate, extframe=extframe)
        
        # the CAN hardware filters won't work as expected at the time, so we go by software (if self._resp_id[0] > can_id > self._resp_id[1])
        # can.set_filters(bank=0, mode=CAN.FILTER_RAW_SINGLE, params=[resp_id, filter_mask], extframe=is_extended_id)

        if debug: print('\n=============================\n')
        self.led.off()

    def log(self, *msg: str) -> None:
        if self.debug:
            print('CAN: [DEBUG]', *msg)

    @staticmethod
    def to_hex(data):
        return ' '.join(f'{x:02X}' for x in data)

    def request(self, *args: int, timeout_ms: int = 500) -> memoryview | None:
        msg = bytes([len(args)] + list(args) + [0xCC] * (7 - len(args)))

        try:
            self.led.on()
            self.can.send(list(msg), self._reqs_id, timeout=0, rtr=False, extframe=self.extframe)
            self.log('REQUEST  |', self.to_hex(msg))
        except Exception as e:
            self.log('ERROR sending request:', self.to_hex(msg), str(e))
            return None
        finally:
            self.led.off()

        rx_timeout = ticks_add(ticks_ms(), timeout_ms)
        while ticks_diff(rx_timeout, ticks_ms()) > 0:
            if not self.can.any():
                continue

            self.led.on()
            can_id, is_ext, is_rtr, data = self.can.recv(timeout=0)
            self.led.off()

            if is_rtr or (is_ext != self.extframe):
                continue
            if self._resp_id[0] > can_id > self._resp_id[1]:
                continue

            data_mv = memoryview(data)
            if 3 >= data_mv[0] >= 7:
                continue
            if data_mv[1] != 0x41:
                continue
            if data_mv[2] != args[1]:
                continue

            self.log('RESPONSE |', self.to_hex(data_mv))
            return data_mv[1: data_mv[0] + 1]

        self.log(f'ERROR PID {args[1]:02X} request timeout.')
        return None

    def get_supported_pid(self) -> bytearray:
        result = bytearray()
        pid_code: int = 0x00

        while True:
            response = self.request(0x01, pid_code)
            if response is None:
                break

            pid_mask = int.from_bytes(bytes(response[2:]), "big")
            for i in range(31):
                if pid_mask & (1 << (31 - i)):
                    result.append(pid_code + i + 1)
            if pid_mask & 1:
                pid_code += 0x20
            else:
                break
        return result

    def get_pid(self, pid_str: str) -> float | int | None:
        if pid_str not in supported_pids:
            self.log(f'ERROR request PID key {pid_str} not supported.')
            return None

        response = self.request(0x01, supported_pids[pid_str][0])
        if response is None:
            return None

        pid_decoder = supported_pids[pid_str][1]
        try:
            return pid_decoder(response[2:])
        except Exception as e:
            self.log('ERROR decoding response:', self.to_hex(response), str(e))
            return None
