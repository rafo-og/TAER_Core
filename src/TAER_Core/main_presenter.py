import sys
import os
import pickle
import logging
import logging.config
import threading
import time
import numpy as np
import wx
import wx.lib.intctrl as wxInt
from TAER_Core.main_model import MainModel
from TAER_Core.main_view import MainView
from TAER_Core.Views import SelectConfigDialog
from TAER_Core.Controllers import *
from TAER_Core.Libs import Config
import TAER_App
from TAER_App.Tools import *
from TAER_App.Tools.tool_base import ToolBase
from TAER_App.Initializers import *
from TAER_App.Initializers.initializer_base import InitializerBase


class MainPresenter:
    """
    This object describes the application behaviour.
    It also creates a "higher level language" in which you express what happens
    inside your application.
    """

    def __init__(self, model: MainModel, view: MainView, interactor: MainInteractor):
        """
        Initialize the MainPresenter with the given model, view, and interactor.

        Args:
            model (MainModel): The main model of the application.
            view (MainView): The main view of the application.
            interactor (MainInteractor): The main interactor of the application.
        """
        self.model = model
        self.view = view
        self.interactor = interactor

    def __install_interactors(self, interactor):
        """
        Install interactors for various views.

        Args:
            interactor (MainInteractor): The main interactor of the application.
        """
        interactor.install(self, self.view)
        interactor = InteractorEditMenuBase()
        view = self.view.edit_register_device_frame
        interactor.install(self.delegates_edit_register_device, view)
        interactor = InteractorEditRegisterChip()
        view = self.view.edit_register_chip_frame
        interactor.install(self.delegates_edit_register_chip, view)
        interactor = InteractorEditMenuBase()
        view = self.view.edit_dac_frame
        interactor.install(self.delegates_edit_dac, view)

    def __config(self):
        """
        Configure all the libraries and components.
        """
        self.__config_logging()
        self.__config_logic()
        self.__config_model()
        self.__config_initializer()
        self.__config_tools()
        self.__config_view()
        self.__config_delegates()

    def __config_logging(self):
        """
        Configure the logging module.
        """
        app_log_filepath = os.path.join(os.getcwd(), "config", "loggers.conf")
        if os.path.exists(app_log_filepath):
            log_filepath = app_log_filepath
        else:
            log_filepath = os.path.join(
                os.path.dirname(TAER_App.__file__), "config", "loggers.conf"
            )
        # Create logs folder if it isn't exist
        log_folder = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_folder, exist_ok=True)
        # Get logger configurations
        logging.config.fileConfig(log_filepath)
        # Get app logger from configuration
        self.logger = logging.getLogger(__name__)

    def __config_logic(self):
        """
        Initialize the application logic objects such as threads, mutexes, or semaphores.
        """
        self.stop_flag = True
        self.stop_cature_flag = True
        self.one_shot_flag = False
        self.img_thread_handler = None
        self.adc_thread_handler = None

    def __config_model(self):
        """
        Configure the model.
        """
        self.model.config()

    def __config_view(self):
        """
        Load the default values and update the view upon first start.
        """
        self.view.config()
        self.view.init_log_box()
        self.view.menu_bar.configure_tools(self.tools.keys())
        self.__update_view_on_gui_thread("init")

    def __config_delegates(self):
        """
        Configure the delegates for various views and register callbacks.
        """
        view = self.view
        self.delegates_main = DelegatesMain(self, view, self.model)
        self.delegates_edit_register_device = DelegatesEditMenuBase(
            self, self.view.edit_register_device_frame, self.model
        )
        self.delegates_edit_register_chip = DelegatesEditRegisterChip(
            self, self.view.edit_register_chip_frame, self.model
        )
        self.delegates_edit_dac = DelegatesEditMenuBase(
            self, self.view.edit_dac_frame, self.model
        )
        self.model.device.register_on_connection_change_callback(
            self.delegates_main.on_connection_change
        )
        self.model.register_on_model_update_cb(self.update_view)

    def __config_tools(self):
        """
        Configure the tools for the presenter.
        """
        self.tools = {}
        subclasses = ToolBase.__subclasses__()
        for subclass in subclasses:
            new_tool = subclass(self.model, self.view)
            if new_tool.is_enabled:
                self.tools[new_tool.name] = new_tool
            else:
                new_tool = None

    def __config_initializer(self):
        """
        Configure the initializer based on the model's chip name.
        """
        initializer_name = self.model.config.chip_name
        subclasses = InitializerBase.__subclasses__()
        self.initializer = None
        for subclass in subclasses:
            new_init = subclass(self.model)
            if new_init.chip_name == initializer_name:
                self.initializer = new_init
                if hasattr(self.initializer, "gen_serial_frame"):
                    self.model.gen_serial_frame = self.initializer.gen_serial_frame
                if hasattr(self.initializer, "parse_serial_frame"):
                    self.model.parse_serial_frame = self.initializer.parse_serial_frame
            else:
                new_init = None
        if self.initializer is None:
            self.logger.warning(
                "Default initializer loaded. Configured initializer not found."
            )
            self.initializer = InitializerBase(self.model)

    def start(self):
        """
        Start the application.
        """
        config_path = self.__show_select_config_dialog()

        if config_path != "":
            Config.CONFIG_PATH = config_path

            self.__config()
            self.view.open()
            self.__install_interactors(self.interactor)
            del self.interactor

            self.stop_flag = False

            self.model.device.start()
            self.__print_welcome_message()

            self.initializer.on_start_app()

            self.view.start_event_loop()
        else:
            self.view.close()

    def close(self):
        """
        Close the application.
        """
        self.initializer.on_close_app()
        self.stop()

    def stop(self):
        """
        Stop the application.
        """
        self.model.device.stop()
        self.stop_main_img_thread()
        self.stop_adc()
        self.stop_flag = True

    def __show_select_config_dialog(self) -> str:
        """
        Show the configuration selection dialog.

        Returns:
            str: The selected configuration path.
        """
        with SelectConfigDialog(self.view) as dlg:
            self.view.set_icon(dlg)
            if dlg.ShowModal() == wx.ID_OK:
                return dlg.get_choice_selected()
            else:
                return ""

    def __print_welcome_message(self):
        """
        Print the welcome message to the logger.
        """
        self.logger.info("TAER")
        self.logger.info("Python %s", sys.version)
        self.logger.info("wxPython %s", wx.version())

    def update_image(self):
        """
        Update the image on the GUI thread.
        """
        wx.CallAfter(self.__update_image_on_gui_thread)

    def __update_image_on_gui_thread(self):
        """
        Update the image on the GUI thread.
        """
        self.view.image = self.model.main_img
        self.view.image_histogram_frame.update_histogram(self.model.img_histogram)

    def update_view(self, id=""):
        """
        Update the view on the GUI thread.

        Args:
            id (str): The ID of the view to update.
        """
        wx.CallAfter(self.__update_view_on_gui_thread, id)

    def __update_view_on_gui_thread(self, id):
        """
        Update the view on the GUI thread.

        Args:
            id (str): The ID of the view to update.
        """
        if (
            id == "init"
            or (id == "" and self.view.IsShown())
            or self.view.GetId() == id
        ):
            self.view.set_menus_state(self.model.device.is_connected)
            # self.view.set_menus_state(True)
            if not self.model.adc_db.get_item_num():
                self.view.set_menus_state(False, id="ADCs")
            if not self.model.dacs_db.get_item_num():
                self.view.set_menus_state(False, id="DACs")

        view = self.view.edit_register_device_frame
        if id == "init" or (id == "" and view.IsShown()) or view.GetId() == id:
            registers = self.model.dev_reg_db
            self.view.edit_register_device_frame.update_values(
                registers.get_item_list()
            )

        view = self.view.edit_register_chip_frame
        if id == "init" or (id == "" and view.IsShown()) or view.GetId() == id:
            registers = self.model.chip_reg_db
            self.view.edit_register_chip_frame.update_values(registers.get_item_list())

        view = self.view.edit_dac_frame
        if id == "init" or (id == "" and view.IsShown()) or view.GetId() == id:
            dacs = self.model.dacs_db
            self.view.edit_dac_frame.update_values(dacs.get_item_list())

        view = self.view.adc_control_frame
        if id == "init" or (id == "" and view.IsShown()) or view.GetId() == id:
            adcs = self.model.adc_db
            self.view.adc_control_frame.update_values(
                adcs.get_item_list(), self.model.adc_tmeas
            )

        for _, tool in self.tools.items():
            if tool.is_shown() and id == "":
                tool.update_view()

    def update_model(self, id):
        """
        Update the model based on the view's ID.

        Args:
            id (str): The ID of the view to update.
        """
        if id == self.view.edit_register_device_frame.GetId():
            self.logger.info("Update registers")
            view = self.view.edit_register_device_frame
            widgets = view.panel_values.values_widgets
            register_dictionary = {}
            for key, widget in widgets.items():
                register_dictionary[key] = int(widget.GetValue(), 0)
            self.model.write_dev_registers(register_dictionary)

        if id == self.view.edit_dac_frame.GetId():
            self.logger.info("Update DACs")
            view = self.view.edit_dac_frame
            widgets = view.panel_values.values_widgets
            dac_dictionary = {}
            for key, widget in widgets.items():
                dac_dictionary[key] = int(widget.GetValue(), 0)
            self.model.write_dacs(dac_dictionary)

        if id == self.view.edit_register_chip_frame.GetId():
            widgets = self.view.edit_register_chip_frame.panel_values.values_widgets
            for label, widget in widgets.items():
                if isinstance(widget, wxInt.IntCtrl):
                    data = widget.GetValue()
                    self.model.write_signal(label, data)
                elif isinstance(widget, wx.CheckBox):
                    data = widget.GetValue()
                    if data:
                        data = 1
                    else:
                        data = 0
                    self.model.write_signal(label, data)
        self.logger.info("Updated.")

    def capture(self):
        """
        Capture an image.
        """
        if self.img_thread_handler is None:
            self.one_shot_flag = True
            self.img_thread_handler = threading.Thread(target=self.__img_thread)
            self.img_thread_handler.start()

    def toggle_main_img_thread(self):
        """
        Toggle the main image thread.
        """
        if self.stop_cature_flag:
            self.start_main_img_thread()
        else:
            self.stop_main_img_thread()

    def start_main_img_thread(self):
        """
        Start the main image thread.
        """
        self.stop_cature_flag = False
        self.view.set_capture_mode(self.stop_cature_flag)
        self.img_thread_handler = threading.Thread(target=self.__img_thread)
        self.img_thread_handler.start()

    def stop_main_img_thread(self):
        """
        Stop the main image thread.
        """
        self.stop_cature_flag = True
        self.view.set_capture_mode(self.stop_cature_flag)
        if self.img_thread_handler is not None:
            if self.img_thread_handler.is_alive():
                self.img_thread_handler.join()

    def __img_thread(self):
        """
        The main image thread function.
        """
        flags = not self.stop_cature_flag or self.one_shot_flag and not self.stop_flag
        self.initializer.on_init_capture()
        if self.model.FR_raw_mode_en:
            self.__continuous_FR_raw_loop(flags)
        elif self.model.TFS_raw_mode_en:
            self.__continuous_TFS_raw_loop(flags)
        else:
            self.__standard_loop(flags)

        self.initializer.on_end_capture()
        self.img_thread_handler = None
        self.logger.debug("Image thread finished")

    def __continuous_FR_raw_loop(self, flags):
        """
        Continuous FR raw loop for capturing images.

        Args:
            flags (bool): The flags to control the loop.
        """
        self.initializer.on_before_capture()
        self.model.device.actions.events_done()
        self.model.device.actions.start_capture()
        n_events = (self.model.read_dev_register("N_EVENTS") // 4) * 32
        while flags:
            read_flag = self.wait_until(
                self.model.device.actions.events_done,
                self.model.config.operation_timeout,
            )
            if not read_flag:
                self.logger.error("Image readout timeout.")
            else:
                t1 = time.time()
                self.logger.info(f"Events: {self.model.device.actions.get_evt_count()}")
                raw_data = self.model.read_raw_data(n_events)
                self.initializer.on_after_capture(raw_data)
                self.update_image()
                # log data
                if raw_data.size > 0:
                    event_rate = 0.125 * n_events / (raw_data[-1] - raw_data[1])
                    self.logger.info(
                        "New data appended. Event rate :"
                        + str(round(event_rate, 2))
                        + "Meps/s."
                    )
                addr_rd, addr_wr = self.model.device.actions.check_addr_ram()
                addr_diff = addr_wr - addr_rd
                if addr_diff > 2 * n_events:
                    self.logger.warning(
                        "WARNING! Data is arriving faster that time required for writting."
                    )
                self.logger.info("Execution time: " + str(round(time.time() - t1, 3)))
            if self.stop_flag:
                break
            elif self.one_shot_flag:
                self.one_shot_flag = False
                break
            flags = (
                not self.stop_cature_flag or self.one_shot_flag and not self.stop_flag
            )
        self.logger.info("ENDS.")
        self.model.device.actions.stop_capture()
        self.model.device.actions.reset_fifo()
        self.model.device.actions.reset_ram()
        self.model.device.actions.reset_aer()

    def __continuous_TFS_raw_loop(self, flags):
        """
        Continuous TFS raw loop for capturing images.

        Args:
            flags (bool): The flags to control the loop.
        """
        self.initializer.on_before_capture()
        self.model.device.actions.events_done()
        while flags:
            self.model.device.actions.start_capture()
            read_flag = self.wait_until(
                self.model.device.actions.is_captured,
                self.model.config.operation_timeout,
            )
            if not read_flag:
                self.logger.error("Image readout timeout.")
            else:
                t1 = time.time()
                self.model.device.actions.stop_capture()
                n_events = (self.model.device.actions.get_evt_count() // 4) * 32
                raw_data = self.model.read_raw_data(n_events)
                self.initializer.on_after_capture(raw_data)
                self.update_image()
                # log data
                if raw_data.size > 0:
                    event_rate = 0.125 * n_events / (raw_data[-1] - raw_data[1])
                    self.logger.info(
                        "New data appended. Event rate :"
                        + str(round(event_rate, 2))
                        + "Meps/s."
                    )
                addr_rd, addr_wr = self.model.device.actions.check_addr_ram()
                addr_diff = addr_wr - addr_rd
                if addr_diff > 2 * n_events:
                    self.logger.warning(
                        "WARNING! Data is arriving faster that time required for writting."
                    )
                self.logger.info("Execution time: " + str(round(time.time() - t1, 3)))
            if self.stop_flag:
                break
            elif self.one_shot_flag:
                self.one_shot_flag = False
                break
            flags = (
                not self.stop_cature_flag or self.one_shot_flag and not self.stop_flag
            )
        self.model.device.actions.stop_capture()
        self.model.device.actions.reset_fifo()
        self.model.device.actions.reset_ram()
        self.model.device.actions.reset_aer()

    def __standard_loop(self, flags):
        """
        Standard loop for capturing images.

        Args:
            flags (bool): The flags to control the loop.
        """
        nsamples = self.model.dev_reg_db.get_item_by_address(0x06).value
        if nsamples == 0:
            nsamples = 1
        while flags:
            t1 = time.time()
            self.initializer.on_before_capture()
            self.model.device.actions.start_capture()
            read_flag = self.wait_until(
                self.model.device.actions.is_captured,
                self.model.config.operation_timeout,
            )
            self.model.device.actions.stop_capture()
            if not read_flag:
                self.logger.error("Image readout timeout.")
            else:
                raw_data = self.model.read_image(nsamples)
                self.initializer.on_after_capture(raw_data)
                try:
                    self.process_img()
                except Exception as e:
                    self.logger.error(e)
                self.update_image()
            if self.stop_flag:
                break
            elif self.one_shot_flag:
                self.one_shot_flag = False
                break
            flags = (
                not self.stop_cature_flag or self.one_shot_flag and not self.stop_flag
            )
            self.logger.debug(f"Time: {(time.time()-t1)*1000} ms")

    def run_adc(self):
        """
        Run the ADC thread.
        """
        if self.adc_thread_handler is None:
            self.flag_adc_run = True
            self.adc_thread_handler = threading.Thread(target=self.__adc_thread)
            self.adc_thread_handler.start()
        # reset ADC data
        for channel in self.model.adc_db.d_item.values():
            channel.reset_data()

    def stop_adc(self):
        """
        Stop the ADC thread.
        """
        self.flag_adc_run = False
        if self.adc_thread_handler is not None:
            if self.adc_thread_handler.is_alive():
                self.adc_thread_handler.join()
            self.adc_thread_handler = None

    def process_img(self):
        """
        Process the image.
        """
        if self.view.image_histogram_frame.IsShown():
            self.__process_img_histogram()

    def wait_until(self, somepredicate, timeout, period=0.25, *args, **kwargs):
        """
        Wait until a condition is met or timeout occurs.

        Args:
            somepredicate (callable): The condition to wait for.
            timeout (float): The timeout period.
            period (float): The period to check the condition.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            bool: True if the condition is met, False otherwise.
        """
        mustend = time.time() + timeout
        while time.time() < mustend:
            if somepredicate(*args, **kwargs):
                return True
            time.sleep(period)
        return False

    def send_serial_data(self):
        """
        Send serial data.
        """
        raw_data = (
            self.view.serial_control_frame.panel_serial_control.serial_tx_box.GetValue()
        )
        serial_data_tx = [int(num, 0) for num in raw_data.replace(" ", "").split(",")]
        self.logger.debug(f"Serial data sent: {serial_data_tx}")
        self.model.device.actions.write_serial(serial_data_tx)  # Requesting RX data
        serial_data_rx = (
            self.model.device.actions.read_serial()
        )  # Reading RX data from FPGA FIFO
        self.logger.debug(f"Serial data read: {serial_data_rx}")
        if serial_data_rx is not None:
            self.view.serial_control_frame.panel_serial_control.serial_rx_box.SetValue(
                str(", ".join(str(s) for s in serial_data_rx))
            )
        else:
            self.view.serial_control_frame.panel_serial_control.serial_rx_box.SetValue(
                "No RX data received."
            )

    def update_adc_ts(self):
        """
        Update the ADC timestamp.
        """
        self.model.adc_tmeas = float(
            self.view.adc_control_frame.panel_menu.sampletime_textbox.GetValue()
        )

    def update_adc_panels(self):
        """
        Update the ADC panels.
        """
        adcs = self.model.adc_db
        self.view.adc_control_frame.update_panels(adcs.get_item_list())

    def set_mode(self, mode):
        """
        Set the mode of the model.

        Args:
            mode (str): The mode to set.
        """
        self.model.set_mode(mode)

    def save_preset(self):
        """
        Save the current preset.
        """
        to_save = self.model.get_preset()
        with wx.FileDialog(
            self.view,
            "Save preset as...",
            wildcard="Preset files (*.preset)|*.preset",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR,
        ) as fileDialog:
            if fileDialog.ShowModal() != wx.ID_CANCEL:
                save_path = fileDialog.GetPath()
                if not save_path.endswith(".preset"):
                    save_path = save_path + ".preset"
                with open(save_path, "wb") as fp:
                    pickle.dump(to_save, fp, pickle.HIGHEST_PROTOCOL)

    def load_preset(self):
        """
        Load a preset.
        """
        to_load = None
        with wx.FileDialog(
            self.view,
            "Load preset",
            wildcard="Preset files (*.preset)|*.preset",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR,
        ) as fileDialog:
            if fileDialog.ShowModal() != wx.ID_CANCEL:
                load_path = fileDialog.GetPath()
                with open(load_path, "rb") as fp:
                    to_load = pickle.load(fp)
        if to_load is not None:
            self.model.set_preset(to_load)
            self.view.set_mode(to_load["mode"])

    #
    # Processing routines
    #
    def __process_img_histogram(self):
        """
        Process the image histogram.
        """
        data = self.model.main_img_data.flatten()
        hist_settings = self.model.img_histogram
        bins = np.linspace(hist_settings.min, hist_settings.max, hist_settings.bins)
        hist = np.histogram(data, bins)
        self.model.img_histogram.value = hist

    def __adc_thread(self):
        """
        The ADC thread function.
        """
        t0 = time.time()
        id = self.view.adc_control_frame.GetId()
        while self.flag_adc_run:
            for adc in self.model.adc_db.d_item.values():
                t1 = time.time()
                adc_data = self.model.device.actions.read_adc(
                    adc.device_id, adc.channel
                )
                adc.add_data(t1 - t0, adc_data)
            self.update_view(id)
            if self.flag_adc_run:
                time.sleep(self.model.adc_tmeas)
        self.logger.debug("ADC thread finished")
