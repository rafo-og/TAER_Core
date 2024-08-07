import wx
import wx.lib.intctrl as wxInt


class MainInteractor:
    """
    This class translates the low level events into the "higher level language" of the presenter
    """

    def install(self, presenter, view):
        self.presenter = presenter
        self.delegates = presenter.delegates_main
        self.view = view

        self.__config_delegates()

    def __config_delegates(self):
        self.view.Bind(wx.EVT_CLOSE, self.__on_close)
        self.view.edit_register_device_frame.Bind(wx.EVT_CLOSE, self.__on_close)
        self.view.edit_register_chip_frame.Bind(wx.EVT_CLOSE, self.__on_close)
        self.view.edit_dac_frame.Bind(wx.EVT_CLOSE, self.__on_close)
        self.view.device_info_frame.Bind(wx.EVT_CLOSE, self.__on_close)
        self.view.image_histogram_frame.Bind(wx.EVT_CLOSE, self.__on_close)
        self.view.serial_control_frame.Bind(wx.EVT_CLOSE, self.__on_close)
        self.view.adc_control_frame.Bind(wx.EVT_CLOSE, self.__on_close)

        self.__config_control_button_delegates()
        self.__config_menu_bar_delegates()
        self.__config_other_delegates()
        self.__config_adc_delegates()

    def __config_control_button_delegates(self):
        panel = self.view.panel_control

        panel.button_start_stop.Bind(wx.EVT_BUTTON, self.__on_start_stop)
        panel.button_capture.Bind(wx.EVT_BUTTON, self.__on_capture)
        panel.button_reset.Bind(wx.EVT_BUTTON, self.__on_reset)
        panel.button_reset_periphery.Bind(wx.EVT_BUTTON, self.__on_reset_periphery)
        panel.button_reset_chip.Bind(wx.EVT_BUTTON, self.__on_reset_chip)
        # Mode radio boxes
        panel.modes_box.Bind(wx.EVT_RADIOBOX, self.__on_mode_change)

    def __config_menu_bar_delegates(self):
        self.view.Bind(
            wx.EVT_MENU,
            self.__on_menu_edit,
            self.view.menu_bar.menu_edit.item_save_preset,
        )
        self.view.Bind(
            wx.EVT_MENU,
            self.__on_menu_edit,
            self.view.menu_bar.menu_edit.item_load_preset,
        )
        self.view.Bind(wx.EVT_MENU, self.__on_menu_edit, self.view.menu_bar.menu_edit.item_reg_dev)
        self.view.Bind(wx.EVT_MENU, self.__on_menu_edit, self.view.menu_bar.menu_edit.item_reg_chip)
        self.view.Bind(wx.EVT_MENU, self.__on_menu_edit, self.view.menu_bar.menu_edit.item_dac)

        self.view.Bind(
            wx.EVT_MENU,
            self.__on_menu_device,
            self.view.menu_bar.menu_device.item_program,
        )
        self.view.Bind(wx.EVT_MENU, self.__on_menu_device, self.view.menu_bar.menu_device.item_info)

        self.view.Bind(
            wx.EVT_MENU_RANGE,
            self.__on_menu_device_file_history,
            id=wx.ID_FILE1,
            id2=wx.ID_FILE9,
        )

        self.view.Bind(
            wx.EVT_MENU,
            self.__on_menu_image,
            self.view.menu_bar.menu_image.item_histogram,
        )

        for item in self.view.menu_bar.menu_tools.items.values():
            self.view.Bind(wx.EVT_MENU, self.__on_menu_tools, item)

    def __config_other_delegates(self):
        view = self.view.image_histogram_frame
        view.panel_histogram_plot.button_scale.Bind(wx.EVT_BUTTON, self.__on_image_histogram_scale)
        view = self.view.serial_control_frame
        view.panel_serial_control.btn_write.Bind(wx.EVT_BUTTON, self.__on_write_spi)

    def __config_adc_delegates(self):
        view = self.view.adc_control_frame
        view.panel_menu.button_update.Bind(wx.EVT_BUTTON, self.__on_update_adc_ts)
        enable_widgets = view.panel_menu.enable_widgets
        for widget in enable_widgets.values():
            widget.Bind(wx.EVT_CHECKBOX, self.__on_update_adc_panels)

    # Interactor delegates

    #
    # Main view
    #
    def __on_close(self, evt):
        self.delegates.on_close(evt.GetEventObject())

    def __on_start_stop(self, evt):
        self.delegates.on_start_stop()

    def __on_capture(self, evt):
        self.delegates.on_capture()

    def __on_reset(self, evt):
        self.delegates.on_reset()

    def __on_reset_periphery(self, evt):
        self.delegates.on_reset_periphery()

    def __on_reset_chip(self, evt):
        self.delegates.on_reset_chip()

    def __on_mode_change(self, evt):
        widget = evt.GetEventObject()
        sel = widget.GetSelection()
        self.delegates.on_mode_change(widget.GetItemLabel(sel))

    #
    # Menu bar
    #
    def __on_menu_edit(self, evt):
        item = self.view.menu_bar.menu_edit.item_save_preset
        if evt.GetId() == item.GetId():
            self.delegates.on_save_preset()
        item = self.view.menu_bar.menu_edit.item_load_preset
        if evt.GetId() == item.GetId():
            self.delegates.on_load_preset()
        item = self.view.menu_bar.menu_edit.item_reg_dev
        if evt.GetId() == item.GetId():
            self.delegates.on_show_registers_device()
        item = self.view.menu_bar.menu_edit.item_reg_chip
        if evt.GetId() == item.GetId():
            self.delegates.on_show_registers_chip()
        item = self.view.menu_bar.menu_edit.item_dac
        if evt.GetId() == item.GetId():
            self.delegates.on_show_dacs()

    def __on_menu_device(self, evt):
        item = self.view.menu_bar.menu_device.item_program
        if evt.Id == item.GetId():
            self.delegates.on_program()
        item = self.view.menu_bar.menu_device.item_info
        if evt.Id == item.GetId():
            self.delegates.on_show_device_info()

    def __on_menu_device_file_history(self, evt):
        fileNum = evt.GetId() - wx.ID_FILE1
        self.delegates.on_program_recent_file(fileNum)

    def __on_menu_image(self, evt):
        item = self.view.menu_bar.menu_image.item_histogram
        if evt.Id == item.GetId():
            self.delegates.on_show_histogram()

    def __on_menu_tools(self, evt):
        item = self.view.menu_bar.menu_tools.items["Write SPI"]
        if evt.Id == item.GetId():
            self.delegates.on_show_write_spi()
            return
        item = self.view.menu_bar.menu_tools.items["ADCs"]
        if evt.Id == item.GetId():
            self.delegates.on_show_adcs()
            return
        item = self.view.menu_bar.menu_tools.items["Execute test"]
        if evt.Id == item.GetId():
            self.delegates.on_test()
            return
        for key, tool in self.presenter.tools.items():
            item = self.view.menu_bar.menu_tools.items[key]
            if evt.Id == item.GetId():
                self.delegates.on_show_tools(tool)
                # tool.open()

    #
    # Histogram
    #
    def __on_image_histogram_scale(self, evt):
        self.delegates.on_scale_histogram()

    #
    # Debug SPI
    #
    def __on_write_spi(self, evt):
        self.delegates.on_write_spi()

    #
    # Debug ADC
    #
    def __on_update_adc_ts(self, evt):
        self.delegates.on_update_adc_ts()

    def __on_update_adc_panels(self, evt):
        self.delegates.on_update_adc_panels()


class InteractorEditMenuBase:
    def install(self, delegates, view):
        self.delegates = delegates
        self.view = view
        self.config_delegates()

    def config_delegates(self):
        self.view.panel_values.button_apply.Bind(wx.EVT_BUTTON, self.on_apply)
        widgets = self.view.panel_values.values_widgets.values()
        for widget in widgets:
            widget.Bind(wx.EVT_TEXT, self.on_text_change)
            widget.Bind(wx.EVT_TEXT_ENTER, self.on_apply)

    # Interactor delegates
    def on_text_change(self, evt):
        self.delegates.on_text_change(evt.GetEventObject())

    def on_apply(self, evt):
        self.delegates.on_apply()


class InteractorEditRegisterChip(InteractorEditMenuBase):
    def config_delegates(self):
        self.view.button_apply.Bind(wx.EVT_BUTTON, self.on_apply)
        widgets = self.view.panel_values.values_widgets.values()
        for widget in widgets:
            if isinstance(widget, wx.CheckBox):
                widget.Bind(wx.EVT_CHECKBOX, self.__on_check_box)
            elif isinstance(widget, wxInt.IntCtrl):
                widget.Bind(wx.EVT_TEXT, self.on_text_change)
                widget.Bind(wx.EVT_TEXT_ENTER, self.on_apply)

    def __on_check_box(self, evt):
        widget = evt.GetEventObject()
        self.delegates.on_check_box_change(widget)
