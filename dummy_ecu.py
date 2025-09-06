from machine import Pin, Signal
from random import randint

try:
    import CAN
except ImportError:
    from CAN import CAN


class DummyEcu:
    def __init__(self,
            rx: int,
            tx: int,
            mode: int = 0,
            bitrate: int = 500_000,
            extframe: bool = True,
            debug: bool = False,
            led_pin: int = 8
        ) -> None:
        
        self.supported_pids: list[int] = [1, 3, 4, 5, 6, 11, 12, 13, 14, 15, 16, 17, 19, 21, 31, 33, 46, 47, 48, 49, 51, 52, 66, 67, 68, 69, 71, 73, 76]
        self.led = Signal(Pin(led_pin, Pin.OUT, value=0), invert=True)
        self.debug = debug
        self.extframe = extframe

        if not extframe:
            self._reqs_id: int = 0x7DF
            self._resp_id: tuple[int,int] = (0x7E8, 0x7EF) # 111 1110 1XXX
            self._filter_mask: int = 0x7F8                 # 111 1111 1000
        else:
            self._reqs_id: int = 0x18DB33F1
            self._resp_id: tuple[int,int] = (0x18DAF110, 0x18DAF11F) # 1 1000 1101 1010 1111 0001 0001 XXXX
            self._filter_mask: int = 0x1FFFFFF0                      # 1 1111 1111 1111 1111 1111 1111 0000

        self.can = CAN(0, tx=tx, rx=rx, mode=mode, bitrate=bitrate, extframe=extframe)
        # can.set_filters(bank=0, mode=CAN.FILTER_RAW_SINGLE, params=[resp_id, filter_mask], extframe=is_extended_id)
        
        if debug: print('\n=============================\n')
        self.led.off()

    def log(self, *msg: str):
        if self.debug:
            print('CAN: [DEBUG]', *msg)

    @staticmethod
    def to_hex(data):
        return ' '.join(f'{x:02X}' for x in data)

    def process(self) -> None:
        if not self.can.any():
            return None

        self.led.on()
        can_id, is_ext, is_rtr, data = self.can.recv(timeout=0)
        self.led.off()

        if is_rtr or (is_ext != self.extframe):
            return None
        if can_id != self._reqs_id:
            return None

        data_mv = memoryview(data)
        if (data_mv[0] != 2) or (data_mv[1] != 0x01):
            return None

        pid_code = data_mv[2]
        self.log('REQUEST  |', self.to_hex(data_mv))

        if (pid_code % 0x20 == 0) and (pid_code < 0xC0):
            value = 0
            for i in range(pid_code, pid_code + 31):
                if (i + 1) in self.supported_pids:
                    value |= (1 << (pid_code + 31 - i))
            for pid in self.supported_pids:
                if pid > (pid_code + 0x20):
                    value |= 1
                    break
            value = value.to_bytes(4, 'big')
        elif pid_code == 0x0C:
            value = int(randint(770, 880) * 4).to_bytes(2, 'big')
        elif pid_code == 0x0D:
            value = bytes([randint(50, 60)])
        elif pid_code == 0x42:
            value = randint(12000, 14000).to_bytes(2, 'big')
        elif pid_code == 0x05:
            value = bytes([randint(90, 120) + 40])
        elif pid_code == 0x10:
            value = randint(10000, 20000).to_bytes(2, 'big')
        else:
            return None

        msg = bytes([len(value) + 2, 0x41, pid_code] + list(value) + [0xAA] * (5 - len(value)))
        try:
            self.led.on()
            self.can.send(list(msg), self._resp_id[0] + 0x01, timeout=0, rtr=False, extframe=self.extframe)
            self.can.send(list(msg), self._resp_id[0] + 0x0D, timeout=0, rtr=False, extframe=self.extframe)
            self.log('RESPONSE |', self.to_hex(msg))
        except Exception as e:
            self.log('ERROR sending response:', self.to_hex(msg), str(e))
            return None
        finally:
            self.led.off()


def main(debug: bool = False) -> None:
    ecu = DummyEcu(20, 21, debug=debug)

    try:
        while True:
            ecu.process()
    except KeyboardInterrupt:
        pass
    finally:
        ecu.can.deinit()

if __name__ == '__main__':
    main(debug=True)