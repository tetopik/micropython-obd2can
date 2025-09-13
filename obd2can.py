"""
OBD2CAN MicroPython Library
===========================

This module provides an interface for querying OBD-II data
over CAN bus using MicroPython. It supports single-frame and
multi-frame ISO-TP responses, and can read PIDs, VIN, and
diagnostic trouble codes (DTCs).

Author: Taufiq
License: MIT
"""


from time import ticks_diff, ticks_add, ticks_ms, sleep_ms
from machine import Pin, Signal

try:
    import CAN
except ImportError:
    from CAN import CAN


#: Dictionary of supported PIDs mapped to
#: (PID code, decode function, unit string).
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
    """
    OBD-II over CAN bus interface.

    Provides methods to:
      • Query PIDs (live data, freeze frame).
      • Read Diagnostic Trouble Codes (DTCs).
      • Get Vehicle Identification Number (VIN).
      • Handle ISO-TP multi-frame responses.

    Args:
        rx (int): GPIO pin for CAN RX.
        tx (int): GPIO pin for CAN TX.
        mode (int): CAN mode (default CAN.NORMAL).
        bitrate (int): CAN bitrate (default 500000).
        extframe (bool): Use extended (29-bit) identifiers.
        debug (bool): Print debug logs.
        led_pin (int): LED indicator GPIO pin.
    """
    
    def __init__(self,
                 rx: int,
                 tx: int,
                 mode: int = CAN.NORMAL,
                 bitrate: int = 500_000,
                 extframe: bool = False,
                 debug: bool = False,
                 led_pin: int = 8,
                 ) -> None:
        """Initialize CAN interface and OBD-II settings."""
                     
        self.led = Signal(Pin(led_pin, Pin.OUT, value=0), invert=True)
        self.debug = debug
        self.extframe = extframe

        if not extframe:
            self._reqs_id: int = 0x7DF
            self._resp_id: tuple[int, int] = (0x7E8, 0x7EF)  # 111 1110 1XXX
            self._filter_mask: int = 0x7F8                   # 111 1111 1000
        else:
            self._reqs_id: int = 0x18DB33F1
            self._resp_id: tuple[int, int] = (0x18DAF110, 0x18DAF11F)  # 1 1000 1101 1010 1111 0001 0001 XXXX
            self._filter_mask: int = 0x1FFFFFF0                        # 1 1111 1111 1111 1111 1111 1111 0000

        self.can = CAN(0, tx=tx, rx=rx, mode=mode, bitrate=bitrate, extframe=extframe)

        # CAN hardware filters won't work as expected at the time, so we go by software instead (if self._resp_id[0] > can_id > self._resp_id[1])
        # can.set_filters(bank=0, mode=CAN.FILTER_RAW_SINGLE, params=[resp_id, filter_mask], extframe=is_extended_id)

        print(f'\n{' CAN0 UP ':-^29}\n')
        self.led.off()

    def deinit(self):
        """Shut down CAN interface and turn off LED."""
        self.can.deinit()
        if self.led.value():
            self.led.off()
        print(f'\n{' CAN0 DOWN ':-^29}\n')

    def log(self, *msg: str) -> None:
        """Print debug messages if debug mode is enabled."""
        if self.debug:
            print('CAN: [DEBUG]', *msg)

    @staticmethod
    def to_hex(data):
        """Convert byte sequence into hex string."""
        return ' '.join(f'{x:02X}' for x in data)

    def send(self, *payload: int, retries: int = 3) -> bool:
        """
        Send a CAN frame with padding.

        Args:
            payload: Variable length data to send.
            retries (int): Retry attempts if sending fails.

        Returns:
            bool: True if send succeeded, False otherwise.
        """
        msg: bytes = bytes(list(payload) + [0xCC] * (8 - len(payload)))
        success: bool = False
        while not success:
            self.led.on()
            try:
                self.can.clear_rx_queue()
                self.can.send(list(msg), self._reqs_id, rtr=False, extframe=self.extframe)
                self.log('REQUEST  >>', self.to_hex(msg))
                success = True
            except Exception as e:
                if retries > 1:
                    retries -= 1
                    self.led.off()
                    sleep_ms(50)
                else:
                    self.log('ERROR sending request:', self.to_hex(msg), str(e))
                    break
        self.led.off()
        return success

    def request(self, *payload: int, timeout_ms: int = 1000) -> memoryview | None:
        """
        Send a request and wait for response.

        Args:
            payload: Service ID and optional PID code.
            timeout_ms (int): Response timeout in milliseconds.

        Returns:
            memoryview | None: Response payload, or None on timeout/error.
        """
        if not self.send(len(payload), *payload):
            return None

        multiframe_seq: int = 0
        rx_timeout = ticks_add(ticks_ms(), timeout_ms)
        while ticks_diff(rx_timeout, ticks_ms()) > 0:
            if not self.can.any():
                continue

            can_id, is_ext, is_rtr, data = self.can.recv()
            if self._resp_id[0] > can_id > self._resp_id[1]:
                continue
            if is_rtr or (is_ext != self.extframe):
                continue

            self.led.on()
            data_mv = memoryview(data)
            self.led.off()

            pci = data_mv[0] >> 4
            if multiframe_seq: # wait for consecutive frame (CF)
                if pci != 2:
                    continue
                seq = data_mv[0] & 0x0F
                if seq != multiframe_seq:
                    continue
                self.log('RESPONSE <<', self.to_hex(data_mv))
                multiframe_seq = (multiframe_seq + 1) & 0x0F # wrap at 15
                multiframe_buf.extend(data_mv[1:])
                if len(multiframe_buf) < multiframe_len:
                    rx_timeout = ticks_add(ticks_ms(), timeout_ms)
                    continue
                return memoryview(multiframe_buf[:multiframe_len])

            elif pci == 0: # single frame (SF)
                if len(payload) >= data_mv[0] >= 8:
                    continue
                if data_mv[1] != (payload[0] + 0x40): # response service_id
                    continue
                try:
                    if data_mv[2] != payload[1]: # pid_code
                        continue
                except IndexError:
                    pass
                self.log('RESPONSE <<', self.to_hex(data_mv))
                return data_mv[1:1 + data_mv[0]]

            elif pci == 1: # first frame (FF)
                multiframe_len = ((data_mv[0] & 0x0F) << 8) | data_mv[1]
                multiframe_buf = bytearray()
                multiframe_seq = 1
                if multiframe_len <= 7:
                    continue
                if data_mv[2] != (payload[0] + 0x40): # response service_id
                    continue
                try:
                    if data_mv[3] != payload[1]: # pid_code
                        continue
                except IndexError:
                    pass
                self.log('RESPONSE <<', self.to_hex(data_mv))
                multiframe_buf.extend(data_mv[2:])
                if not self.send(0x30, 0x00, 0x00): # flow control
                    return None
                rx_timeout = ticks_add(ticks_ms(), timeout_ms)

        self.log(f'RESPONSE << {'TIMEOUT':-^23}')
        return None

    def get_supported_pid(self) -> bytes:
        """
        Get all supported PIDs from the ECU.

        Returns:
            bytes: List of supported PID codes.
        """
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
        return bytes(result)

    def get_dtcs(self) -> list[bytes]:
        """
        Get Diagnostic Trouble Codes (DTCs).

        Returns:
            list[bytes]: List of 5-character ASCII codes (e.g. b'P0143').
        """
        response = self.request(0x03)
        if response is None:
            self.log('ERROR no response for DTCs package.')
            return []

        dtc_bytes = bytes(response[2:])
        if len(dtc_bytes) % 2 != 0:
            self.log("ERROR: DTC bytes is not in pairs (2 bytes per code)")
            return []

        base_map = ['P', 'C', 'B', 'U']
        codes = []
        for i in range(0, len(dtc_bytes), 2):
            a, b = dtc_bytes[i], dtc_bytes[i+1]
            codes.append(f'{base_map[a >> 6]}{(a >> 4) & 3}{a & 0xF}{b >> 4}{b & 0xF}'.encode('ascii'))
        return codes

    def get_vin(self) -> bytes:
        """
        Get the Vehicle Identification Number (VIN).

        Returns:
            bytes: VIN (17 bytes) or empty bytes on error.
        """
        response = self.request(0x09, 0x02)
        if response is None:
            self.log('ERROR no response for VIN package.')
            return b''

        # response: service_id 0x09, pid_code 0x02, nodi(1), vin(17)
        vin = bytes(response[3:])
        if len(vin) != 17: # standard VIN length
            self.log(f"ERROR invalid VIN length: {len(vin)} ({self.to_hex(vin)})")
            return b''

        try:
            return vin
        except UnicodeDecodeError:
            self.log(f"ERROR decoding VIN package ({self.to_hex(vin)})")
            return b''

    def get_pid(self, pid_str: str, freeze_frame: bool = False) -> float | int | None:
        """
        Get decoded PID value by name.

        Args:
            pid_str (str): PID key from supported_pids.
            freeze_frame (bool): If True, read freeze-frame data.

        Returns:
            float | int | None: Decoded value or None if unavailable.
        """
        if pid_str not in supported_pids:
            self.log(f'ERROR PID key {pid_str} not supported.')
            return None

        response = self.request(0x02 if freeze_frame else 0x01, supported_pids[pid_str][0]) # service_id, pid_code
        if response is None:
            self.log(f'ERROR no response for PID {pid_str.upper()}.')
            return None

        try:
            return supported_pids[pid_str][1](response[2:]) # pid sepecific lambda function call
        except Exception as e:
            self.log('ERROR decoding response:', self.to_hex(response), str(e))
            return None


# ============= EXAMPLE MAIN CODE =============== #

def main() -> None:
    obd = OBD2CAN(rx=20, tx=21, extframe=True, debug=True)

    try:
        vin = obd.get_vin()
        print('VIN:', vin.decode())

        dtcs = obd.get_dtcs()
        print('DTC:', ' '.join(dtc.decode() for dtc in dtcs))
        
        supported_pid = obd.get_supported_pid()
        print('PID:', obd.to_hex(supported_pid))

        for pid_str in ['rpm', 'speed', 'maf', 'volt_module', 'coolant_temp']:
            val = obd.get_pid(pid_str)
            if val is not None:
                print(f'{pid_str.upper()}: {val} {supported_pids[pid_str][2]}\n')

    except KeyboardInterrupt:
        pass
    finally:
        obd.deinit()

if __name__ == '__main__':
    main()
    
