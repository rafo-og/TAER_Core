from os import path
import wx
from TAER_Core.main_model import MainModel


class DelegatesMain:
    def __init__(self, presenter, view, model: MainModel) -> None:
        self.presenter = presenter
        self.view = view
        self.model = model

    #
    # Main view
    #
    def on_start_stop(self):
        self.presenter.logger.debug("On start or stop")
        self.presenter.toggle_main_img_thread()

    def on_capture(self):
        self.presenter.capture()
        self.presenter.logger.info("Start capture.")

    def on_reset(self):
        self.model.device.actions.reset_device()
        self.model.device.actions.reset_fifo()
        self.model.device.actions.reset_ram()
        self.presenter.logger.debug("Reset device.")

    def on_reset_periphery(self):
        self.presenter.logger.debug("Reset periphery.")
        self.model.device.actions.reset_aer()

    def on_reset_chip(self):
        self.presenter.logger.info("Reset chip.")
        self.model.device.actions.reset_chip()

    def on_mode_change(self, mode):
        self.presenter.set_mode(mode)

    #
    # Device and device menu views
    #
    def on_connection_change(self):
        if not self.model.device.is_connected:
            self.presenter.logger.info("Device disconnected")
            self.model.binary_file = ""
            self.presenter.stop_main_img_thread()
            self.model.reset_image()
            self.presenter.update_image()
        else:
            self.presenter.logger.info("On connection")
        self.presenter.update_view()

    def on_program(self):
        with wx.FileDialog(
            self.view,
            "Open bitstream file",
            wildcard="Bitstream files (*.bit)|*.bit",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR,
        ) as fileDialog:
            if fileDialog.ShowModal() != wx.ID_CANCEL:
                self.model.binary_file = fileDialog.GetPath()
                self.model.device.program(self.model.binary_file)
                # Just read the FPGA registers because the chip register maybe need
                # clock activation
                self.model.read_dev_registers()
                file_history = self.view.menu_bar.menu_device.program_history
                file_history.AddFileToHistory(self.model.binary_file)
                file_history.Save(self.view.menu_bar.menu_device.program_history_config)
                self.view.menu_bar.menu_device.program_history_config.Flush()

    def on_program_recent_file(self, idx):
        file_history = self.view.menu_bar.menu_device.program_history
        bin_path = file_history.GetHistoryFile(idx)

        if path.exists(bin_path):
            file_history.AddFileToHistory(bin_path)
            self.model.binary_file = bin_path
            self.model.device.program(bin_path)
            # Just read the FPGA registers because the chip register maybe need
            # clock activation
            self.model.read_dev_registers()
        else:
            self.presenter.logger.error("The file %s doesn't exist.", bin_path)
            file_history.RemoveFileFromHistory(idx)

        file_history.Save(self.view.menu_bar.menu_device.program_history_config)
        self.view.menu_bar.menu_device.program_history_config.Flush()

    def on_show_device_info(self):
        view = self.view.device_info_frame
        view.update_info(self.model.device.info)
        view.open()

    #
    # Edit menu views
    #
    def on_save_preset(self):
        self.presenter.save_preset()

    def on_load_preset(self):
        self.presenter.load_preset()

    def on_show_registers_device(self):
        view = self.view.edit_register_device_frame
        self.model.read_dev_registers()
        view.open()

    def on_show_registers_chip(self):
        view = self.view.edit_register_chip_frame
        self.model.read_signals()
        view.open()

    def on_show_dacs(self):
        view = self.view.edit_dac_frame
        self.presenter.update_view(view.GetId())
        view.open()

    #
    # Image menu views
    #
    def on_show_histogram(self):
        view = self.view.image_histogram_frame
        view.open()

    def on_scale_histogram(self):
        view = self.view.image_histogram_frame
        max, min, bins = view.get_bin_settings()
        self.model.img_histogram.set_settings(max, min, bins)
        view.scale()
        self.presenter.process_img()
        self.presenter.update_image()

    #
    # Tools menu views
    #
    def on_show_write_spi(self):
        view = self.view.serial_control_frame
        view.open()

    def on_show_adcs(self):
        view = self.view.adc_control_frame
        self.presenter.run_adc()
        view.open()

    def on_write_spi(self):
        self.presenter.send_serial_data()

    def on_update_adc_ts(self):
        self.presenter.update_adc_ts()

    def on_update_adc_panels(self):
        self.presenter.update_adc_panels()

    def on_show_tools(self, tool):
        if tool.chip_reg_update:
            self.model.read_signals()
        if tool.dev_reg_update:
            self.model.read_dev_registers()
        if not tool.is_shown():
            tool.open()

    def on_test(self):
        self.presenter.initializer.on_test()

    #
    # General close method
    #
    def on_close(self, view):
        if view.GetId() == self.view.adc_control_frame.GetId():
            self.presenter.stop_adc()

        if view.GetId() == self.view.GetId():
            self.presenter.close()
            view.close()
        else:
            view.close()


class DelegatesEditMenuBase:
    def __init__(self, presenter, view, model) -> None:
        self.presenter = presenter
        self.view = view
        self.model = model

    def on_text_change(self, widget):
        self.view.panel_values.on_text_change(widget)

    def on_apply(self):
        self.presenter.update_model(self.view.GetId())
        self.view.panel_values.to_default_color()

    def on_close(self):
        self.view.close()


class DelegatesEditRegisterChip(DelegatesEditMenuBase):
    def __init__(self, presenter, view, model) -> None:
        super().__init__(presenter, view, model)

    def on_check_box_change(self, evt_widget):
        check_value = int(evt_widget.GetValue())
        widgets = self.view.panel_values.values_widgets
        for label, widget in widgets.items():
            if evt_widget.GetId() == widget.GetId():
                self.model.write_signal(label, check_value)
                break
