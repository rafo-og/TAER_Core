import wx
from TAER_Core.Views.auxiliar_view_base import AuxViewBase
from wx.lib import plot as wxplot


class AdcView(AuxViewBase):
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            id=wx.NewId(),
            title="ADC signals",
            style=wx.DEFAULT_FRAME_STYLE ^ wx.MAXIMIZE_BOX,
        )
        self.SetMinSize(wx.Size(1000, 300))
        self.__create_layout()

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)

        self.panel_menu = AdcMenuPanel(self)
        self.panel_plot = AdcPlotPanel(self)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox.Add(self.hbox, 1, wx.EXPAND | wx.ALL, 5)

        self.hbox.Add(self.panel_menu, 0, wx.EXPAND)
        self.hbox.Add(self.panel_plot, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(self.vbox)
        self.Layout()

    def update_values(self, values, ts):
        self.panel_menu.update_channels(values, ts)
        self.panel_plot.update_subplots(values)

    def update_panels(self, values):
        self.panel_menu.update_isenabled(values)
        self.panel_plot.update_panels(values)

    def apply(self):
        self.panel_menu.to_default_color()

    def set_menus_state(self, state):
        self.panel_menu.Enable(state)


class AdcMenuPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.__create_layout()
        self.values_widgets = {}
        self.enable_widgets = {}
        self.init_flag = False

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.adc_box = wx.StaticBoxSizer(wx.HORIZONTAL, self, "ADC channels")
        self.grid_register = wx.FlexGridSizer(cols=3, hgap=0, vgap=0)
        self.adc_box.Add(self.grid_register, 0, wx.EXPAND | wx.ALL, 10)
        # Sample time
        self.sizer_sampletime = wx.StaticBoxSizer(wx.HORIZONTAL, self, "Sample time")
        self.sampletime_textbox = wx.TextCtrl(self, style=wx.TE_CENTRE)
        self.button_update = wx.Button(self, wx.ID_APPLY, "Update")
        self.sizer_sampletime.Add(self.sampletime_textbox, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        self.sizer_sampletime.Add(self.button_update, 0, wx.EXPAND | wx.ALL, 10)
        self.vbox.Add(self.adc_box, 0, wx.EXPAND | wx.ALL, 5)
        self.vbox.Add(self.sizer_sampletime, 0, wx.EXPAND | wx.ALL, 5)
        # Set main sizer and fit
        self.hbox.Add(self.vbox, 1, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(self.hbox)
        self.Layout()

    def __init_adc_values(self, values):
        for value in values.values():
            st1 = wx.StaticText(
                self,
                label="CH" + str(value.channel) + ": " + value.label,
                style=wx.CENTER,
            )
            t1 = wx.TextCtrl(self, value=str(value.value), style=wx.TE_READONLY)
            c1 = wx.CheckBox(self)
            c1.SetValue(value.IsEnabled)
            self.enable_widgets[value.label] = c1
            self.values_widgets[value.label] = t1
            self.grid_register.Add(st1, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.TOP, 5)
            self.grid_register.Add(t1, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT | wx.TOP, 5)
            self.grid_register.Add(c1, 1, wx.EXPAND | wx.LEFT | wx.TOP, 5)
        self.Fit()
        self.GetParent().Fit()

    def __inti_sampletime_value(self, ts):
        self.sampletime_textbox.SetValue(str(ts))

    def update_channels(self, values, ts):
        if self.init_flag:
            for channel in values.values():
                self.values_widgets[channel.label].SetValue(str(channel.data_y[-1]))
                # self.enable_widgets[channel.label].SetValue(channel.IsEnabled)
        else:
            self.__init_adc_values(values)
            self.__inti_sampletime_value(ts)
            self.init_flag = True

        self.to_default_color()

    def update_isenabled(self, values):
        for channel in values.values():
            channel.IsEnabled = self.enable_widgets[channel.label].GetValue()

    def on_text_change(self, widget):
        widget.SetBackgroundColour((128, 255, 0, 50))

    def to_default_color(self):
        [widget.SetBackgroundColour(wx.NullColour) for widget in self.values_widgets.values()]
        self.Refresh()


class AdcPlotPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.__create_layout()
        self.init_flag = False

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox.Add(self.vbox, 1, wx.EXPAND | wx.ALL, 5)
        self.canvas_list = {}
        self.SetSizer(self.hbox)
        self.Layout()

    def __init_subplots(self, values):
        for value in values.values():
            canvas = AdcPlotCanvas(self)
            self.canvas_list[value.label] = canvas
            self.vbox.Add(canvas, 1, wx.EXPAND | wx.ALL, 5)
        self.Fit()
        self.GetParent().Fit()

    def update_panels(self, values):
        for channel in values.values():  # Removing all panels
            if channel.IsEnabled:
                self.canvas_list[channel.label].Show()
            else:
                self.canvas_list[channel.label].Hide()
        self.Layout()

    def update_subplots(self, values):
        if self.init_flag:
            for channel in values.values():
                self.canvas_list[channel.label].update_plot(channel)
        else:
            self.__init_subplots(values)
            self.init_flag = True


class AdcPlotCanvas(wxplot.PlotCanvas):
    def __init__(self, parent):
        wxplot.PlotCanvas.__init__(self, parent)
        self.SetMinSize(wx.Size(300, 100))
        self.__create_layout()
        self.init_flag = False

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)
        self.enableLegend = True

    def update_plot(self, channel):
        # Minimum X-axis value
        if channel.data_t[-1] < 15:
            xmax = 15
            xmin = 0
        else:
            xmax = channel.data_t[-1]
            xmin = xmax - 15  # Time span is always 15 s

        # Clip data
        i_xmin = min(
            range(len(channel.data_t)), key=lambda i: abs(channel.data_t[i] - xmin)
        )  # Looking for the index of the value corresponding to t(xmin)
        x = channel.data_t[i_xmin::].copy()
        y = channel.data_y[i_xmin::].copy()

        # Minimum Y-axis value
        if max(y) == 0:
            ymax = 0.15
        elif max(y) > 0:
            ymax = 1.15 * max(y)
        else:
            ymax = 0.85 * max(y)

        if min(y) == 0:
            ymin = -0.15
        elif min(y) > 0:
            ymin = 0.85 * min(y)
        else:
            ymin = 1.15 * min(y)

        x = channel.data_t
        y = channel.data_y
        data = list(zip(x, y))
        trace = wxplot.PolySpline(data, legend="CH" + str(channel.channel), colour="blue", width=1)
        graphics = wxplot.PlotGraphics([trace], xLabel="Time (s)", yLabel=channel.label)
        self.Draw(graphics, xAxis=(xmin, xmax), yAxis=(ymin, ymax))
