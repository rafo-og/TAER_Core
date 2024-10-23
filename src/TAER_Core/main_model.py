""" Application model """

import cv2 as cv
import numpy as np
import logging
from TAER_Core.Libs.config import ModelConfig
from TAER_Core.Libs import Device


class ItemBase:
    def __init__(self, label, address, defaultValue=0) -> None:
        self.label = label
        self.default_value = defaultValue
        self.value = defaultValue
        self.address = address


class DeviceRegister(ItemBase):
    def __init__(self, label, address, defaultValue=0) -> None:
        super().__init__(label, address, defaultValue)


class DbBase:
    def __init__(self):
        super().__init__()
        self.d_item = {}
        self.logger = logging.getLogger(__name__)

    def add(self, item: ItemBase):
        """Add an item to the database

        Args:
            item (ItemBase): The item to add
        """
        self.d_item[item.label] = item

    def remove(self, item_label: str):
        """Remove an item from the database

        Args:
            item_label (str): The label assigned to the item
        """
        for _, item in self.d_item:
            if item_label == item.label:
                del self.d_item[item.label]
                break

    def get_item(self, item_label: str) -> ItemBase:
        """Get a item from the database

        Args:
            item_label (str): The label assigned to the item

        Returns:
            ItemBase: The item with the requested label if any
        """
        for _, item in self.d_item.items():
            if item.label == item_label:
                return item

    def get_item_by_address(self, address: int) -> ItemBase:
        for _, item in self.d_item.items():
            if item.address == address:
                return item

    def set_item_value(self, item_label: str, value: int):
        """Set the value of an item

        Args:
            item_label (str): The label assigned to the item
            value (int): The value to set
        """
        item = self.get_item(item_label)
        if item is not None:
            item.value = value
        else:
            self.logger.warning(f"Item {item_label} not exists.")

    def get_item_list(self) -> dict:
        """Get all the items in the database as dict

        Returns:
            dict: A dictionary with item labels as keys and items as values
        """
        return self.d_item

    def set_all_item_values_by_address(self, item_values: dict):
        """Set all the item values from an dictionary with address and values. This is implemented only for some specific items which contain address as one of their attributes.

        Args:
            item_values (dict): A dictionary containing item address as keys and item values as values

        Raises:
            AttributeError: If the item doesn't contain an attribute called \"address\"
        """
        # Check if the item has an attribute called address
        if not hasattr(self.d_item[next(iter(self.d_item))], "address"):
            raise AttributeError
        for _, item in self.d_item.items():
            if item.address in item_values:
                item.value = item_values[item.address]

    def get_item_value_list(self) -> dict:
        return {key: item.value for key, item in self.d_item.items()}

    def get_item_num(self) -> int:
        return len(self.d_item)


class ChipRegister(ItemBase):
    def __init__(self, label, address, defaultValue=0, signals=None) -> None:
        super().__init__(label, address, defaultValue)
        self.size = 8
        if signals is not None:
            self.signals = {}
            self.size = 0
            # Create dictionary with signals
            for signal in signals:
                new_signal = ChipSignal(signal[2], int(signal[0], 0), int(signal[1], 0))
                self.signals[new_signal.label] = new_signal
                self.size = self.size + new_signal.nbits

    def set_signal(self, signal_label: str, value: int):
        """Set the value of the signal

        Args:
            signal_label (str): The label assigned to the signal
            value (int): The value to set
        """
        signal = self.signals[signal_label]
        masked_value = self.value & ~signal.mask  # Clean value before set it
        self.value = ((value << signal.bit) & signal.mask) | masked_value

    def get_signal(self, signal_label: str) -> int:
        """Get the value of the signal

        Args:
            signal_label (str): The label assigned to the signal

        Returns:
            int: The value of the signal
        """
        signal = self.signals[signal_label]
        curr_value = (self.value & signal.mask) >> signal.bit
        return curr_value


class ChipSignal:
    def __init__(self, label, bit, nbits=1):
        self.label = label
        self.bit = bit
        self.nbits = nbits
        self.mask = (pow(2, nbits) - 1) << bit


class ChipRegisterDb(DbBase):
    def __init__(self):
        super().__init__()

    def set_signal(self, reg_label: str, signal_label: str):
        register = self.get_item(reg_label)
        register.set_signal(signal_label)

    def get_signal(self, reg_label: str, signal_label: str) -> ChipSignal:
        register = self.get_item(reg_label)
        return register.get_signal(signal_label)

    def get_signal_list(self) -> dict:
        regs = self.get_item_list()
        signals = {}
        for _, reg in regs.items():
            tmp = {key: reg.get_signal(key) for key, item in reg.signals.items()}
            signals.update(tmp)
        return signals


class Dac(ItemBase):
    def __init__(self, label, address, channel, defaultValue=0) -> None:
        super().__init__(label, defaultValue)
        self.channel = channel
        self.address = address


class Adc(ItemBase):
    def __init__(self, label, device_id, channel, offset, slope, defaultValue=0) -> None:
        super().__init__(label, defaultValue)
        self.channel = channel
        self.device_id = device_id
        self.offset = offset
        self.slope = slope
        self.data_t = []
        self.data_y = []
        self.IsEnabled = True

    def add_data(self, t_meas, adc_out, keep_old_data=False):
        'Append one point to the (t,y) list. If "keep_old_data" is set to False, the first element of the list will be removed if t > 15 s.'
        self.data_t.append(t_meas)
        self.data_y.append(float(adc_out) * self.slope + self.offset)
        if (not keep_old_data) & (self.data_t[-1] > 15):
            self.__remove_data()

    def __remove_data(self):
        "Remove first element (oldest point)"
        self.data_t.pop(0)
        self.data_y.pop(0)

    def reset_data(self):
        self.data_t = []
        self.data_y = []


class Histogram:
    def __init__(self) -> None:
        self.value = np.histogram(0, [1, 2])
        self.bins = 100
        self.max = 65535
        self.min = 100

    def set_settings(self, max, min, bins):
        self.bins = bins
        self.max = max
        self.min = min


class MainModel:
    """An object where the TAER data is stored."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.device = Device()

    def config(self):
        """Configure the model"""
        self.config = ModelConfig()
        self.__config_default_values()
        self.__config_modes()
        self.__config_reg_device_db()
        self.__config_reg_chip_db()
        self.__config_dac_db()
        self.__config_adc_db()

    def __config_modes(self):
        """Configure the chip modes from the configuration file"""
        modes = self.config.modes
        self.modes = {}
        for mode in modes:
            self.modes[mode[0]] = int(mode[1], 0)
        self.current_mode = self.modes[next(iter(self.modes))]

    def __config_reg_device_db(self):
        """Configure the device registers from the configuration file"""
        self.dev_reg_db = DbBase()
        registers = self.config.device_registers
        for register in registers:
            new_register = DeviceRegister(register[0], int(register[1], 0), int(register[2], 0))
            self.dev_reg_db.add(new_register)

    def __config_reg_chip_db(self):
        """Configure the chip register list from the configuration file"""
        self.chip_reg_db = ChipRegisterDb()
        registers = self.config.chip_registers
        for register in registers.__dict__.values():
            if hasattr(register, "signals"):
                new_register = ChipRegister(register.label, int(register.address, 0), signals=register.signals)
            else:
                new_register = ChipRegister(register.label, int(register.address, 0))
            self.chip_reg_db.add(new_register)

    def __config_dac_db(self):
        """Configure the DAC devices from the configuration file"""
        self.dacs_db = DbBase()
        if hasattr(self.config, 'dacs'):
            dacs = self.config.dacs
            for dac in dacs:
                new_dac = Dac(dac[0], int(dac[1], 0), int(dac[2], 0), int(dac[3], 0))
                self.dacs_db.add(new_dac)

    def __config_adc_db(self):
        """Configure the ADC devices from the configuration file"""
        self.adc_db = DbBase()
        if hasattr(self.config, 'adc_tmeas'):
            self.adc_tmeas = self.config.adc_tmeas
        else:
            self.adc_tmeas = 1
        if hasattr(self.config, 'adcs'):
            adcs = self.config.adcs
            for adc in adcs:
                new_adc = Adc(adc[4], int(adc[0], 0), int(adc[1], 0), float(adc[2]), float(adc[3]))
                self.adc_db.add(new_adc)

    def __config_default_values(self):
        self.main_img_data = np.zeros((self.config.img.w, self.config.img.h), np.uint16)
        self.img_histogram = Histogram()
        self.binary_file = str()
        self.on_model_update_cb = None
        self.FR_raw_mode_en = False
        self.TFS_raw_mode_en = False

    def write_dev_register(self, reg_label: str, value: int):
        """Write a device register (FPGA or microcontroller)

        Args:
            reg_label (str): The label assigned to the register
            value (int): The value to write
        """
        self.dev_reg_db.set_item_value(reg_label, value)
        register = self.dev_reg_db.get_item(reg_label)
        self.device.actions.write_register(register.address, register.value)
        self.__on_model_update()

    def read_dev_register(self, reg_label: str) -> int:
        """Read a register from the device

        Args:
            reg_label (str): The label assigned to the register

        Returns:
            int: The register value
        """
        register = self.dev_reg_db.get_item(reg_label)
        return self.device.actions.read_register(register.address)

    def write_dev_registers(self, registers: dict):
        """Write the registers in the device

        Args:
            registers (dict): A dictionary containing the register labels as keys and register values as values
        """
        for label, value in registers.items():
            self.dev_reg_db.set_item_value(label, value)
        self.device.actions.write_registers(self.dev_reg_db.get_item_list())
        self.__on_model_update()

    def read_dev_registers(self):
        """Read the device registers from the device and update the model"""
        model_registers = self.dev_reg_db.get_item_list()
        chip_registers = self.device.actions.read_registers(model_registers)
        self.dev_reg_db.set_all_item_values_by_address(chip_registers)
        self.__on_model_update()

    def write_signal(self, signal_label: str, value: int):
        """Write a signal in the chip

        Args:
            signal_label (str): The label assigned to the signal
            value (int): The signal value to write
        """
        registers = self.chip_reg_db.get_item_list()
        for _, register in registers.items():
            for _, signal in register.signals.items():
                if signal.label == signal_label:
                    register.set_signal(signal_label, value)
                    data = self.gen_serial_frame("write", register)
                    self.logger.debug(f"SPI write -> bytes -> {data}")
                    self.device.actions.write_serial(data)
        self.__on_model_update()

    def read_signal(self, signal_label: str) -> int:
        """Read a particular signal. First all the signals are updated and then the requested signal is returned

        Args:
            signal_label (str): The label assigned to the signal

        Returns:
            int: The signal value requested
        """
        self.read_signals()
        registers = self.chip_reg_db.get_item_list()
        for _, register in registers.items():
            for _, signal in register.signals.items():
                if signal.label == signal_label:
                    return register.get_signal(signal_label)

    def write_signals(self, signals: dict):
        """Write several signals in the chip

        Args:
            signals (dict): A dictionary containing the signal labels as keys and signal values as values
        """
        for label, value in signals.items():
            self.write_signal(label, value)
        self.__on_model_update()

    def read_signals(self):
        """Read signals from the chip and updates the model"""
        registers = self.chip_reg_db.get_item_list()
        for _, register in registers.items():
            data = self.gen_serial_frame("read", register)
            self.logger.debug(f"SPI read -> bytes -> {data}")
            self.device.actions.write_serial(data)
            serial_data = self.device.actions.read_serial()
            register.value = self.parse_serial_frame(serial_data, register)
        self.__on_model_update()

    def write_dacs(self, dacs: dict):
        """Write the DACs

        Args:
            dacs (dict): A dictionary containing the DAC labels as keys and DAC values as values
        """
        for label, value in dacs.items():
            self.dacs_db.set_item_value(label, value)
        self.device.actions.write_dacs(self.dacs_db.get_item_list())
        self.__on_model_update()

    def reset_image(self):
        """Set the image data array to zero (black)"""
        self.main_img_data = np.zeros((self.config.img.w, self.config.img.h), np.uint16)

    def read_data(self, ndata: int):
        raw_data = self.device.actions.read_ram(ndata)
        raw_data = np.frombuffer(raw_data, np.uint32)
        return raw_data

    def read_raw_data(self, ndata: int):
        raw_data = self.device.actions.read_ram_raw(ndata)
        raw_data = np.frombuffer(raw_data, np.uint32)
        return raw_data

    def read_image(self, nsamples=1):
        """Read the image from the chip through the device

        Returns:
            numpy array: An array with a shape equal to the image resolution
        """
        # Each pixel is represented by 32-bit unsigned integer
        npix = self.config.img.w * self.config.img.h * 4 * nsamples
        img_data = self.read_data(npix)
        img = img_data.astype(np.uint32, casting="unsafe")
        return img

    def register_on_model_update_cb(self, callback: object):
        self.on_model_update_cb = callback

    def get_current_mode_name(self, mode):
        for key, value in self.modes.items():
            if value == mode:
                return key
        return ""

    def __on_model_update(self):
        if self.on_model_update_cb is not None:
            self.on_model_update_cb()

    def gen_serial_frame(self, operation: str, register: ChipRegister):
        """Generate the SPI data frame to send depending on several parameters

        Args:
            operation (str): It could be \"write\" or \"read\"
            mode (int): It represents different protocols to communicate with the chip over SPI. Currently, only mode 1 and mode 2 are defined.
            register (ChipRegister): An object with all the data related with the register properties

        Returns:
            numpy array: The data frame to send over SPI
        """
        # The default operation consists of a SPI interface that sends the address of the register to be written. MSB = 1 for writting.
        # E.g.: Writing 0x3C to register 0x17 -> TX = {0x17 | 0x80, 0x3C}
        # E.g.: Reading register 0x17 -> TX = {0x17, 0x3C}
        data = None
        if operation == "write":
            data = [(register.address & 0x7F) | 0x80, register.value]
        elif operation == "read":
            data = [(register.address & 0x7F), 0]
        else:
            self.logger.error("Operation not allowed.")
        return data

    def parse_serial_frame(self, data: list, register: ChipRegister) -> list:
        """Parse the incoming data from SPI depending on several parameters

        Args:
            data (list): The data to parse
            mode (int): It represents different protocols to communicate with the chip over SPI. Currently, only mode 1 and mode 2 are defined.
            register (ChipRegister): An object with all the data related with the register properties

        Returns:
            list: The parsed data
        """
        # The default operation consists of a SPI interface that returns the register value after receiving the address in the first byte
        # E.g.: Reading register 0x17 -> TX = {0x17, 0x00} -> RX = {0x00, DATA}
        return data[1]

    def set_mode(self, mode):
        if self.modes[mode] > 7:
            self.logger.warning("The mode ID is higher than the maximum allowed (3bits - 7)")
        self.current_mode = self.modes[mode]
        self.device.actions.set_mode(self.current_mode & 7)

    def get_preset(self):
        params = {}
        for name, code in self.modes.items():
            if code == self.current_mode:
                params["mode"] = name
                break
        params["dev_reg"] = self.dev_reg_db.get_item_value_list()
        params["chip_reg"] = self.chip_reg_db.get_signal_list()
        params["dacs"] = self.dacs_db.get_item_value_list()
        return params

    def set_preset(self, preset):
        self.set_mode(preset["mode"])
        self.write_dev_registers(preset["dev_reg"])
        self.write_dacs(preset["dacs"])
        self.write_signals(preset["chip_reg"])

    def __rotate_and_flip(self, data):
        rotate = self.config.img.rotate
        flip = self.config.img.flip

        if rotate == "R0":
            pass
        elif rotate == "R90":
            data = np.rot90(data, 1)
        elif rotate == "R180":
            data = np.rot90(data, 2)
        elif rotate == "R270":
            data = np.rot90(data, 3)
        else:
            raise Exception("The rotate flag has invalid value. Valid values are: R0, R90, R180 or R270.")

        if flip == "None":
            pass
        elif flip == "MX":
            data = np.flipud(data)
        elif flip == "MY":
            data = np.fliplr(data)
        else:
            raise Exception("The mirror flag has invalid value. Valid values are: MX or MY")

        return data

    @property
    def main_img(self):
        """Main image object"""
        return self.__main_img

    @property
    def main_img_data(self):
        """Main image raw data"""
        return self.__main_img_data

    @main_img_data.setter
    def main_img_data(self, value):
        self.__main_img_data = np.copy(value)
        need_conversion = value.dtype != "uint8"
        if need_conversion:
            vmin = value.min()
            vmax = value.max()
            if vmax - vmin > 0:
                value = (value - vmin) / (vmax - vmin) * 255
            value = value.astype("uint8")

        need_reshape = len(value.shape) == 1
        if need_reshape:
            value = np.reshape(value[0 : self.config.img.w * self.config.img.h], (self.config.img.w, self.config.img.h))
        need_remapping = len(value.shape) == 2
        if need_remapping:
            value = cv.cvtColor(np.uint8(value), cv.COLOR_GRAY2BGR)

        value = self.__rotate_and_flip(value)
        self.__main_img = value
