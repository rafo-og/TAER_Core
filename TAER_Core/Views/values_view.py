import wx
from TAER_Core.Views.auxiliar_view_base import AuxViewBase


class ValuesView(AuxViewBase):
    def __init__(self, parent, title):
        super().__init__(
            parent=parent,
            id=wx.NewId(),
            title=title,
            style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX,
        )
        self.SetMinSize(wx.Size(0, 0))
        self.__create_layout()

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)

        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.vsizer.Add(self.hsizer, 0, wx.ALL, 5)

        self.panel_values = ValuesPanel(self)

        self.hsizer.Add(self.panel_values, 0, wx.EXPAND)

        self.SetSizerAndFit(self.vsizer)

        self.Layout()

    def update_values(self, values):
        self.panel_values.update_values(values)
        self.Fit()

    def apply(self):
        self.panel_values.to_default_color()

    def set_menus_state(self, state):
        self.panel_values.Enable(state)


class ValuesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.__create_layout()

        self.values_widgets = {}

        self.init_flag = False

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)

        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox.Add(self.vbox, 0, wx.ALL, 1)
        self.grid_register = wx.GridSizer(2, 0, 0)
        self.vbox.Add(self.grid_register, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        # Buttons
        self.sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox.Add(self.sizer_buttons, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        # Apply button
        self.button_apply = wx.Button(self, wx.ID_APPLY, "Apply")
        self.sizer_buttons.Add(self.button_apply, 0, wx.ALL, 5)
        # # Set main sizer and fit
        self.SetSizer(self.hbox)
        self.Layout()

    def __init_values(self, values):
        for value in values.values():
            st1 = wx.StaticText(self, label=value.label, style=wx.CENTER)
            t1 = wx.TextCtrl(self, value=str(value.value), style=wx.TE_CENTRE | wx.TE_PROCESS_ENTER)

            self.values_widgets[value.label] = t1

            self.grid_register.Add(st1, 0, wx.ALIGN_CENTER | wx.TOP, 5)
            self.grid_register.Add(t1, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT | wx.TOP, 5)

    def update_values(self, values):
        if self.init_flag:
            for register in values.values():
                self.values_widgets[register.label].SetValue(str(register.value))
        else:
            self.__init_values(values)
            self.init_flag = True

        self.to_default_color()

    def on_text_change(self, widget):
        widget.SetBackgroundColour((128, 255, 0, 50))

    def to_default_color(self):
        [widget.SetBackgroundColour(wx.NullColour) for widget in self.values_widgets.values()]
        self.Refresh()
