""" Opal Kelly device class """

import logging
import time
import ok
from threading import Lock


class Device(ok.FrontPanelManager):
    """Class to interface with AER readers."""

    def __init__(self):
        # Monitor connection and disconnections
        ok.FrontPanelManager.__init__(self)
        # Handler to open the device
        self.__handler = ok.okCFrontPanel()
        # Device info
        self.vendor_info = ok.okTDeviceInfo()
        self.info = DeviceInfo()
        # Logic
        self.lock = Lock()
        self.is_connected = False
        self.on_connection_change_callback = None
        # Logging
        self.logger = logging.getLogger(__name__)
        # Actions
        self.actions = DeviceActions(self, self.logger)

    @property
    def interface(self):
        return self.__handler

    def __get_device_info(self) -> bool:
        """Get some general information about the device.

        Returns:
            bool: True if the information is gathered correctly, False otherwise
        """
        self.vendor_info = ok.okTDeviceInfo()

        if self.__handler is not None:
            self.__get_lock__()
            err_code = self.__handler.GetDeviceInfo(self.vendor_info)
            self.__release_lock__()
            if self.__handler.NoError != err_code:
                self.logger.info("Unable to retrieve device information.")
                return False

        self.info.set_values_from_OK(self.vendor_info)

        return True

    def start(self):
        """Start the device operation."""
        self.StartMonitoring()

    def stop(self):
        """Stop the device operation."""
        self.StopMonitoring()

    def program(self, bitstream: str):
        """Configure the Opal Kelly FPGA as well as load the bitstream

        Args:
            bitstream (str): The path where it is the bitstream
        """
        self.config(bitstream)

        self.initialize()

    def initialize(self):
        """A method to initialize the FPGA, not used at the moment"""
        pass

    def __get_lock__(self):
        """Get the mutex to implement thread-safe operation"""
        self.lock.acquire(timeout=5)

    def __release_lock__(self):
        """Release the mutex to implement thread-safe operation"""
        self.lock.release()

    #
    # Device configuration
    #
    def config(self, bit_stream_path: str = "") -> bool:
        """Configure the device"""
        self.__get_lock__()
        self.__handler.LoadDefaultPLLConfiguration()
        err_code = self.__handler.ConfigureFPGA(bit_stream_path)
        self.__release_lock__()
        if self.__handler.NoError != err_code:
            self.logger.error("FPGA configuration failed.")
            return False
        self.logger.info("Device %s configuration success.", self.vendor_info.productName)
        self.__get_lock__()
        is_enable = self.__handler.IsFrontPanelEnabled()
        self.__release_lock__()
        if not is_enable:
            self.logger.error("Front Panel isn't enabled.")
            return False
        time.sleep(1.5)
        if not self.actions.check_calibration():
            self.logger.error("Device RAM isn't calibrated.")
            return False
        self.actions.reset_device()
        return True

    def register_on_connection_change_callback(self, callback):
        self.on_connection_change_callback = callback

    def launch_on_connection_change_callback(self):
        if self.on_connection_change_callback is not None:
            self.on_connection_change_callback()

    def OnDeviceAdded(self, serial: str) -> None:
        """Callback called when the device is connected"""
        self.logger.debug("On device %s connected.", serial)

        if self.is_connected:
            return

        self.__get_lock__()
        self.__handler = self.Open(serial)
        self.__release_lock__()
        if not self.__handler:
            self.logger.error("A device could not be opened.")
        else:
            flag = self.__get_device_info()
            if flag:
                self.logger.info("Device %s connected.", self.vendor_info.productName)
                self.is_connected = True
                self.launch_on_connection_change_callback()

    def OnDeviceRemoved(self, serial: str) -> None:
        """Callback called when the device is disconnected"""
        self.__get_lock__()
        is_open = self.__handler.IsOpen()
        self.__release_lock__()
        if not is_open:
            self.logger.debug("On device %s disconnected.", self.vendor_info.productName)
            del self.__handler
            self.__handler = None
            self.is_connected = False
            self.logger.info("Device %s disconnected.", self.vendor_info.productName)
            self.launch_on_connection_change_callback()
        else:
            self.logger.debug("On device %s disconnected.", serial)


class DeviceInfo:
    def __init__(self) -> None:
        self.vendor = str()
        self.product_name = str()
        self.serial_number = str()
        self.dev_version = str()

    def set_values_from_OK(self, values: ok.okTDeviceInfo):
        self.vendor = "Opal Kelly"
        self.product_name = str(values.productName)
        self.serial_number = str(values.serialNumber)
        self.dev_version = ".".join([str(values.deviceMajorVersion), str(values.deviceMinorVersion)])


class DeviceActions:

    #
    # DAC constants
    #
    DAC_WRITE_MODE = 0x01

    #
    # RAM constants
    #
    RAM_BLOCK_SIZE = 32  # Addres count must be a multiple of block size
    RAM_READBUF_SIZE = 1024 * 1024

    def __init__(self, device: Device, logger=logging.getLogger(__name__)) -> None:
        self.device = device
        self.links = DeviceLinkAddress()
        self.logger = logger

    #
    # Actions
    #
    def write_register(self, address, value):
        self.device.__get_lock__()
        self.device.interface.WriteRegister(address, value)
        self.device.__release_lock__()

    def read_register(self, address):
        self.device.__get_lock__()
        value = self.device.interface.ReadRegister(address)
        self.device.__release_lock__()
        # No error code for this function
        err_code = self.device.interface.NoError
        self.__check_err_code(err_code, f"Reading register address {address} -> value {value}")
        return value

    def write_registers(self, registers):
        entries = ok.okTRegisterEntries()
        for register in registers.values():
            entry = ok.okTRegisterEntry()
            entry.address = register.address
            entry.data = register.value
            entries.append(entry)

        self.device.__get_lock__()
        error_code = self.device.interface.WriteRegisters(entries)
        self.device.__release_lock__()
        if self.device.interface.NoError == error_code:
            self.logger.info("Device register write success.")
        else:
            self.logger.error("Device register write failed with code %s.", error_code)

    def read_registers(self, registers) -> dict:
        entries = ok.okTRegisterEntries()

        for register in registers.values():
            entry = ok.okTRegisterEntry()
            entry.address = register.address
            entries.append(entry)

        self.device.__get_lock__()
        error_code = self.device.interface.ReadRegisters(entries)
        self.device.__release_lock__()
        if self.device.interface.NoError == error_code:
            self.logger.info("Device register read success.")
            chip_registers = {}
            for entry in entries:
                chip_registers[entry.address] = entry.data
            return chip_registers
        else:
            self.logger.error("Device register read failed with code %s.", error_code)
            return {}

    def write_dac(self, address, channel, value):
        self.__set_wire__(self.links.win_dac, address, WIRE_IN_DAC.DAC_SEL)
        self.__set_wire__(self.links.win_dac, self.DAC_WRITE_MODE, WIRE_IN_DAC.DAC_MODE)
        self.__set_wire__(self.links.win_dac, channel, WIRE_IN_DAC.DAC_CHANNEL)
        self.__set_wire__(self.links.win_dac, value, WIRE_IN_DAC.DAC_VALUE)
        self.__update_wires__()
        self.__set_trigger__(self.links.trig_in, TRIGGER_IN_0.TRIG_DAC)

    def write_dacs(self, dacs):
        for dac in dacs.values():
            self.write_dac(dac.address, dac.channel, dac.value)

    def read_adc(self, address, channel) -> int:
        self.__set_wire__(self.links.win_adc, address, WIRE_IN_ADC.ADC_ID)
        self.__set_wire__(self.links.win_adc, channel, WIRE_IN_ADC.ADC_CHANNEL)
        self.__update_wires__()
        self.__set_trigger__(self.links.trig_in, TRIGGER_IN_0.TRIG_ADC)

        data_valid = self.__wait_until(self.is_adc_done, 1)
        if data_valid:
            adc_data = self.__read_wire__(self.links.wout_adc, WIRE_OUT_ADC.ADC_DATA)
        else:
            adc_data = 0
        return adc_data
        # return random.randint(0,10)

    def is_adc_done(self) -> bool:
        trigger_out = self.__read_trigger__(self.links.trig_out, TRIGGER_OUT_0.ADC_DATA_VALID)
        return trigger_out

    def start_capture(self):
        self.reset_fifo()
        self.reset_ram()
        self.__set_wire__(self.links.win0, 1, WIRE_IN_0.WRITE_EN_RAM)
        self.__update_wires__()
        self.__set_trigger__(self.links.trig_in, TRIGGER_IN_0.START)

    def stop_capture(self):
        self.__set_trigger__(self.links.trig_in, TRIGGER_IN_0.STOP)

    def is_captured(self) -> bool:
        trigger_out = self.__read_trigger__(self.links.trig_out, TRIGGER_OUT_0.VIDEO_DONE)
        return trigger_out

    def events_done(self) -> bool:
        """Returns a logic 1 if there is a set of events to be read out."""
        trigger_out = self.__read_trigger__(self.links.trig_out, TRIGGER_OUT_0.EVENTS_DONE)
        return trigger_out

    def reset_chip(self):
        self.__set_wire_as_trigger__(self.links.win0, WIRE_IN_0.RESET_CHIP)
        self.__update_wires__()

    def reset_aer(self):
        self.__set_wire_as_trigger__(self.links.win0, WIRE_IN_0.RESET_PERIPH)
        self.__update_wires__()

    def reset_device(self):
        self.__set_wire_as_trigger__(self.links.win0, WIRE_IN_0.RESET)
        self.__update_wires__()

    def reset_fifo(self):
        self.__set_wire__(self.links.win0, 0, WIRE_IN_0.READ_EN_RAM)
        self.__set_wire__(self.links.win0, 0, WIRE_IN_0.WRITE_EN_RAM)
        self.__set_wire_as_trigger__(self.links.win0, WIRE_IN_0.RESET_FIFO)
        self.__update_wires__()

    def reset_ram(self):
        self.__set_wire_as_trigger__(self.links.win0, WIRE_IN_0.RESET_RAM)
        self.__update_wires__()

    def check_calibration(self):
        value = self.__read_wire__(self.links.wout_calib, WIRE_OUT_CALIB.CALIB)
        if value == 0:
            return False
        else:
            return True

    def enable_clk_chip(self, is_enabled):
        if is_enabled:
            self.__set_wire__(self.links.win0, 1, WIRE_IN_0.CLK_20M_EN)
        else:
            self.__set_wire__(self.links.win0, 0, WIRE_IN_0.CLK_20M_EN)
        self.__update_wires__()

    def read_aer(self):
        addr_x = self.__read_wire__(self.links.wout_xy, WIRE_OUT_XY.X)
        addr_y = self.__read_wire__(self.links.wout_xy, WIRE_OUT_XY.Y)
        return addr_x, addr_y

    def read_ram(self, ndata):
        self.reset_fifo()
        self.reset_ram()
        data = self.__read_ram_block(ndata)
        self.__set_wire__(self.links.win0, 0, WIRE_IN_0.READ_EN_RAM)
        self.__update_wires__()
        return data

    def read_ram_raw(self, ndata):
        data = self.__read_ram_block(ndata)
        self.__set_trigger__(self.links.trig_in, TRIGGER_IN_0.EVENTS_READ)
        return data

    def __read_ram_block(self, ndata):
        self.__set_wire__(self.links.win0, 1, WIRE_IN_0.READ_EN_RAM)
        self.__update_wires__()
        # The pipe out read method needs a multiple of 16
        ndata = (ndata // 16) * 16
        ndata_read = 0
        data = bytearray()
        while ndata_read < ndata:
            ndata_to_read = min([self.RAM_READBUF_SIZE, ndata])
            data_tmp = self.__read_block_pipe_out__(self.links.pipe_out0, ndata_to_read)
            data.extend(data_tmp)
            ndata_read = ndata_read + ndata_to_read
        return data

    def check_addr_ram(self):
        addr_rd = self.__read_wire__(self.links.wout_ram_read, WIRE_OUT_RAM_READ.ADDR_RD)
        addr_wr = self.__read_wire__(self.links.wout_ram_write, WIRE_OUT_RAM_WRITE.ADDR_WR)
        return addr_rd, addr_wr

    def write_serial(self, data_tx):
        """This function writes 'data' into the TX FIFO of the FPGA's serial controller. Operation is as follows:
        1) The number of bytes to be transmitted is updated as len(data). 2) FPGA serial FIFOs are reset
        (RX data is lost if not read out). 3) Data is loaded to input FIFO and the FPGA automaticatelly sends this data
        4) A delay of 500 us is implemented to wait for data to be received.

            Args:
                data (bytes): List/tuple of bytes containing data to be transmitted. 'data[0] is the first byte
                that is transmitted."""
        self.__write_serial_fifo(data_tx)

    def read_serial(self):
        """This function reads the RX FIFO of the FPGA's serial controller. Operation is as follows:
        1) If RX FIFO is iniatilly empty, 'None' is returned. This occurs when the slave did not answer
        any query or delay between writing and reading opeartion was too short. 2) RX data is read out until the
        FIFO is empty. For a safe operation, FIFO must have received all data before starting the read process.
        4) A delay of 500 us is implemented to wait for data to be received.

            Returns:
                data (bytes): List of bytes containing RX data (little endian).
                None if RX FIFO is initially empty.
        """
        # self.__write_serial_fifo(data_tx)
        # time.sleep(0.001) # Waiting for RX data to be received
        data_rx = self.__read_serial_fifo()
        return data_rx

    def set_test_mode(self, is_enabled):
        if is_enabled:
            self.__set_wire__(self.links.win0, 1, WIRE_IN_0.TEST_TFS_EN)
            self.__set_wire__(self.links.win0, 1, WIRE_IN_0.CLK_TFS_EN)
            self.__update_wires__()
        else:
            self.__set_wire__(self.links.win0, 0, WIRE_IN_0.TEST_TFS_EN)
            self.__set_wire__(self.links.win0, 0, WIRE_IN_0.CLK_TFS_EN)
            self.__update_wires__()

    def set_mode(self, mode):
        self.__set_wire__(self.links.win0, mode, WIRE_IN_0.MODES)
        self.__update_wires__()

    def set_aux_signal(self, signal, value):
        if signal == 0:
            self.__set_wire__(self.links.win0, value, WIRE_IN_0.AUX0)
        elif signal == 1:
            self.__set_wire__(self.links.win0, value, WIRE_IN_0.AUX1)
        elif signal == 2:
            self.__set_wire__(self.links.win0, value, WIRE_IN_0.AUX2)
        elif signal == 3:
            self.__set_wire__(self.links.win0, value, WIRE_IN_0.AUX3)
        elif signal == 4:
            self.__set_wire__(self.links.win0, value, WIRE_IN_0.AUX4)
        elif signal == 5:
            self.__set_wire__(self.links.win0, value, WIRE_IN_0.AUX5)
        self.__update_wires__()

    def set_pcb_switch(self, switch_bit, value):
        if switch_bit == 0:
            self.__set_wire__(self.links.win_pcb, value, WIRE_IN_PCBSWITCHES.BIT0)
        elif switch_bit == 1:
            self.__set_wire__(self.links.win_pcb, value, WIRE_IN_PCBSWITCHES.BIT1)
        elif switch_bit == 2:
            self.__set_wire__(self.links.win_pcb, value, WIRE_IN_PCBSWITCHES.BIT2)
        elif switch_bit == 3:
            self.__set_wire__(self.links.win_pcb, value, WIRE_IN_PCBSWITCHES.BIT3)
        elif switch_bit == 4:
            self.__set_wire__(self.links.win_pcb, value, WIRE_IN_PCBSWITCHES.BIT4)
        elif switch_bit == 5:
            self.__set_wire__(self.links.win0, value, WIRE_IN_PCBSWITCHES.BIT5)
        self.__update_wires__()

    def get_evt_count(self) -> int:
        evt_cnt = self.__read_wire__(self.links.wout_evt_count, WIRE_OUT_EVT_COUNT.EVT_COUNT)
        return evt_cnt

    def __write_serial_fifo(self, data):
        """This function writes 'data' into the TX FIFO of the FPGA's serial controller. Operation is as follows:
        1) The number of bytes to be transmitted is updated as len(data). 2) FPGA serial FIFOs are reset
        (RX data is lost if not read out). 3) Data is loaded to input FIFO and the FPGA automaticatelly sends this data.
        4) A delay of 500 us is implemented to wait for data to be received.

            Args:
                data (bytes): List/tuple of bytes containing data to be transmitted. 'data[0] is the first
                byte that is transmitted."""
        # 'data' must be a list/tuple of bytes. The LSB is the first byte that is transmitted.
        if data is not None:
            n_bytes = len(data)  # number of bytes to be sent.
            data.reverse()
            self.__set_register__(self.links.reg_spi, n_bytes)
            self.__set_trigger__(self.links.trig_in, TRIGGER_IN_0.SERIAL_RX_RST_FIFO)
            # Note that if 'n_bytes' is not a multiple of 4, 'data[-x]' will be sent to the FPGA, but will be ignored
            while n_bytes > 0:
                fifo_full = self.__read_wire__(self.links.wout0, WIRE_OUT_0.SERIAL_TX_FULL)
                while fifo_full:
                    fifo_full = self.__read_wire__(self.links.wout0, WIRE_OUT_0.SERIAL_TX_FULL)
                    time.sleep(0.01)

                if n_bytes > 0:
                    self.__set_wire__(self.links.win_spi, data[n_bytes - 1], WIRE_SPI.BYTE3)
                if n_bytes > 1:
                    self.__set_wire__(self.links.win_spi, data[n_bytes - 2], WIRE_SPI.BYTE2)
                if n_bytes > 2:
                    self.__set_wire__(self.links.win_spi, data[n_bytes - 3], WIRE_SPI.BYTE1)
                if n_bytes > 3:
                    self.__set_wire__(self.links.win_spi, data[n_bytes - 4], WIRE_SPI.BYTE0)
                self.__update_wires__()
                self.__set_trigger__(self.links.trig_in, TRIGGER_IN_0.SERIAL_TX_WEN)
                n_bytes = n_bytes - 4
            self.logger.debug(f"{len(data)} bytes sent to the serial driver.")
            time.sleep(0.0005)  # Waiting for RX data
        else:
            self.logger.error("Serial TX data is None.")

    def __read_serial_fifo(self):
        """This function reads the RX FIFO of the FPGA's serial controller. Operation is as follows:
        1) If RX FIFO is iniatilly empty, 'None' is returned. This occurs when the slave did not answer
        any query or delay between writing and reading opeartion was too short. 2) RX data is read out until the
        FIFO is empty. For a safe operation, FIFO must have received all data before starting the read process.
        4) A delay of 500 us is implemented to wait for data to be received.

            Returns:
                data (bytes): List of bytes containing RX data (little endian).
                None if RX FIFO is initially empty.
        """
        data_read = list()
        fifo_empty = self.__read_wire__(self.links.wout0, WIRE_OUT_0.SERIAL_RX_EMPTY)
        if fifo_empty:
            self.logger.error(
                "No RX data found in serial fifo. Make sure the device is answering or delay is long enough."
            )
            return None
        else:
            while not fifo_empty:
                self.__set_trigger__(self.links.trig_in, TRIGGER_IN_0.SERIAL_RX_REN)
                byte_rx = self.__read_wire__(self.links.wout0, WIRE_OUT_0.SERIAL_RX_BYTE)
                data_read.append(byte_rx)
                fifo_empty = self.__read_wire__(self.links.wout0, WIRE_OUT_0.SERIAL_RX_EMPTY)
            self.logger.debug(f"{len(data_read)} bytes read from the serial driver.")
            # data_read.reverse()
            return data_read

    #
    # Device IO functions
    #
    def __set_trigger__(self, address, trigger):
        self.device.__get_lock__()
        err_code = self.device.interface.ActivateTriggerIn(address, trigger.offset)
        self.device.__release_lock__()
        self.__check_err_code(err_code, f"Activate trigger address {address} bit {trigger.offset}")

    def __read_trigger__(self, address, trigger):
        self.device.__get_lock__()
        err_code = self.device.interface.UpdateTriggerOuts()
        self.__check_err_code(err_code, "Update trigger out")
        trigger_out = self.device.interface.IsTriggered(address, trigger.mask)
        self.device.__release_lock__()
        return trigger_out

    def __set_wire_as_trigger__(self, address, wire):
        self.__set_wire__(address, 1, wire)
        self.__update_wires__()
        self.__set_wire__(address, 0, wire)
        self.__update_wires__()

    def __read_wire__(self, address, wire):
        self.device.__get_lock__()
        err_code = self.device.interface.UpdateWireOuts()
        self.__check_err_code(err_code, f"Read wire out {address}")
        wire_data = self.device.interface.GetWireOutValue(address)
        self.device.__release_lock__()
        return (wire_data & wire.mask) >> wire.offset

    def __set_wire__(self, address, value, wire):
        self.device.__get_lock__()
        to_write_value = value << wire.offset
        err_code = self.device.interface.SetWireInValue(address, to_write_value, wire.mask)
        self.device.__release_lock__()
        self.__check_err_code(
            err_code,
            f"Set wire -> bits {format(to_write_value, '#032b')} -> mask {format(wire.mask,'#032b')} in address {address}",
        )

    def __update_wires__(self):
        self.device.__get_lock__()
        err_code = self.device.interface.UpdateWireIns()
        self.device.__release_lock__()
        self.__check_err_code(err_code, "Update wire in")

    def __read_block_pipe_out__(self, address, length):
        out = bytearray(length)
        self.device.__get_lock__()
        err_code = self.device.interface.ReadFromBlockPipeOut(address, self.RAM_BLOCK_SIZE, out)
        self.device.__release_lock__()
        if err_code < 0:
            self.__check_err_code(err_code, f"Read pipe block with address {address}")
        else:
            self.logger.debug(f"Query {length} bytes \t Read {err_code} bytes")

        return out

    def __set_register__(self, address, value):
        self.device.__get_lock__()
        err_code = self.device.interface.WriteRegister(address, value)
        self.device.__release_lock__()
        self.__check_err_code(err_code, f"Writing register address {address} value {value}")

    #
    # Auxiliar functions
    #
    def __check_err_code(self, err_code, msg=""):
        if err_code != self.device.interface.NoError:
            self.logger.error(msg + f" failed with code({err_code}).")
            self.logger.error(f"Opal kelly error message: {self.device.interface.GetLastErrorMessage()}")
        else:
            self.logger.debug(msg + " OK.")

    def __wait_until(self, somepredicate, timeout, period=0.01, *args, **kwargs):
        mustend = time.time() + timeout
        while time.time() < mustend:
            if somepredicate(*args, **kwargs):
                return True
            time.sleep(period)
        return False


class DeviceLinkAddress:
    def __init__(self) -> None:
        #
        # Links
        #
        self.win0 = 0x00
        self.win_spi = 0x01
        self.win_adc = 0x02
        self.win_pcb = 0x03
        self.win_dac = 0x04
        self.reg_spi = 0x08
        self.wout_calib = 0x20
        self.wout0 = 0x21
        self.wout_xy = 0x22
        self.wout_adc = 0x23
        self.wout_evt_count = 0x27
        self.wout_ram_read = 0x28
        self.wout_ram_write = 0x29
        self.trig_in = 0x41
        self.trig_out = 0x60
        self.pipe_out0 = 0xA0


class LINK_VALUE_DEF:
    def __init__(self, offset, end=0) -> None:
        if end != 0:
            self.size = end - offset + 1
        else:
            self.size = 1
        self.offset = offset
        self.mask = (pow(2, self.size) - 1) << offset


class TRIGGER_DEF(LINK_VALUE_DEF):
    def __init__(self, offset) -> None:
        super().__init__(offset)


class WIRE_IN_0:
    RESET = LINK_VALUE_DEF(0)
    RESET_FIFO = LINK_VALUE_DEF(1)
    RESET_RAM = LINK_VALUE_DEF(2)
    READ_EN_RAM = LINK_VALUE_DEF(3)
    WRITE_EN_RAM = LINK_VALUE_DEF(4)
    RESET_PERIPH = LINK_VALUE_DEF(5)

    SHORT_MODE = LINK_VALUE_DEF(7)
    TEST_TFS_EN = LINK_VALUE_DEF(8)
    TEST_TFS_MODE = LINK_VALUE_DEF(9)

    RESET_CHIP = LINK_VALUE_DEF(10)

    AUX0 = LINK_VALUE_DEF(20)
    AUX1 = LINK_VALUE_DEF(21)
    AUX2 = LINK_VALUE_DEF(22)
    AUX3 = LINK_VALUE_DEF(23)
    AUX4 = LINK_VALUE_DEF(24)
    AUX5 = LINK_VALUE_DEF(25)

    CLK_20M_EN = LINK_VALUE_DEF(26)
    CLK_TFS_EN = LINK_VALUE_DEF(27)

    MODES = LINK_VALUE_DEF(29, 31)


class WIRE_IN_PCBSWITCHES:
    BIT0 = LINK_VALUE_DEF(0)
    BIT1 = LINK_VALUE_DEF(1)
    BIT2 = LINK_VALUE_DEF(2)
    BIT3 = LINK_VALUE_DEF(3)
    BIT4 = LINK_VALUE_DEF(4)
    BIT5 = LINK_VALUE_DEF(5)
    BIT6 = LINK_VALUE_DEF(6)


class WIRE_SPI:
    BYTE0 = LINK_VALUE_DEF(0, 7)
    BYTE1 = LINK_VALUE_DEF(8, 15)
    BYTE2 = LINK_VALUE_DEF(16, 23)
    BYTE3 = LINK_VALUE_DEF(24, 31)
    ALL_BYTES = LINK_VALUE_DEF(0, 31)


class WIRE_IN_ADC:
    ADC_CHANNEL = LINK_VALUE_DEF(0, 1)
    ADC_ID = LINK_VALUE_DEF(2, 3)


class WIRE_IN_DAC:
    DAC_VALUE = LINK_VALUE_DEF(0, 11)
    DAC_CHANNEL = LINK_VALUE_DEF(12, 13)
    DAC_MODE = LINK_VALUE_DEF(14, 15)
    DAC_SEL = LINK_VALUE_DEF(16, 17)


class WIRE_OUT_CALIB:
    CALIB = LINK_VALUE_DEF(0)


class WIRE_OUT_0:
    SERIAL_RX_BYTE = LINK_VALUE_DEF(0, 7)
    SERIAL_RX_EMPTY = LINK_VALUE_DEF(8)
    SERIAL_TX_FULL = LINK_VALUE_DEF(10)
    CTRL_OVERFLOW = LINK_VALUE_DEF(9)


class WIRE_OUT_ADC:
    ADC_DATA = LINK_VALUE_DEF(0, 11)


class WIRE_OUT_EVT_COUNT:
    EVT_COUNT = LINK_VALUE_DEF(0, 31)


class WIRE_OUT_RAM_READ:
    ADDR_RD = LINK_VALUE_DEF(0, 31)


class WIRE_OUT_RAM_WRITE:
    ADDR_WR = LINK_VALUE_DEF(0, 31)


class WIRE_OUT_XY:
    X = LINK_VALUE_DEF(0, 15)
    Y = LINK_VALUE_DEF(16, 31)


class TRIGGER_IN_0:
    START = TRIGGER_DEF(0)
    TRIG_DAC = TRIGGER_DEF(1)
    SERIAL_TX_WEN = TRIGGER_DEF(2)
    SERIAL_RX_RST_FIFO = TRIGGER_DEF(3)
    SERIAL_RX_REN = TRIGGER_DEF(4)
    TRIG_ADC = TRIGGER_DEF(5)
    STOP = TRIGGER_DEF(6)
    EVENTS_READ = TRIGGER_DEF(7)


class TRIGGER_OUT_0:
    FRAME_DONE = TRIGGER_DEF(0)
    VIDEO_DONE = TRIGGER_DEF(1)
    ADC_DATA_VALID = TRIGGER_DEF(2)
    EVENTS_DONE = TRIGGER_DEF(3)
