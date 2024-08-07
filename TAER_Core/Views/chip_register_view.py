import wx
import wx.lib.scrolledpanel
import wx.lib.intctrl as wxInt
from TAER_Core.Views.auxiliar_view_base import AuxViewBase


class ChipRegisterView(AuxViewBase):
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            id=wx.NewId(),
            title="Chip registers",
            style=wx.DEFAULT_FRAME_STYLE ^ wx.MAXIMIZE_BOX,
        )
        self.SetMaxClientSize((600, 800))
        self.__create_layout()

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)
        # Sizers
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        self.hsizer.Add(self.vsizer, 1, wx.EXPAND | wx.ALL, 5)
        # Register bits panel
        self.panel_values = ChipRegisterBitPanel(self)
        self.vsizer.Add(self.panel_values, 1, wx.EXPAND | wx.ALL)
        # Buttons
        self.sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.vsizer.Add(self.sizer_buttons, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        # Apply button
        self.button_apply = wx.Button(self, wx.ID_APPLY, "Apply")
        self.sizer_buttons.Add(self.button_apply, 0, wx.ALL, 10)
        self.SetAutoLayout(True)
        self.SetSizerAndFit(self.hsizer)
        self.Layout()

    def update_values(self, values):
        self.panel_values.update_values(values)
        self.Fit()


class ChipRegisterBitPanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.SetMinClientSize((400, 400))
        self.SetMaxClientSize((600, 1000))
        self.SetAutoLayout(True)
        self.SetupScrolling()
        self.__create_layout()
        self.init_flag = False
        self.values_widgets = {}

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox.Add(self.vbox, 1, wx.EXPAND | wx.ALL, 1)
        # Set main sizer and fit
        self.SetSizer(self.hbox)
        self.Layout()

    def __init_values(self, values):
        for value in values.values():
            sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, value.label)
            grid_sizer = wx.FlexGridSizer(cols=2, vgap=3, hgap=10)
            grid_sizer.SetFlexibleDirection(wx.BOTH)
            sizer.Add(grid_sizer, 1, wx.ALL | wx.EXPAND, 5)
            if hasattr(value, "signals"):
                for signal in value.signals.values():
                    st1 = wx.StaticText(self, label=signal.label, style=wx.CENTER)
                    grid_sizer.Add(
                        st1,
                        1,
                        wx.ALL | wx.EXPAND | wx.LEFT | wx.ALIGN_CENTRE_VERTICAL,
                        5,
                    )
                    if signal.nbits == 1:
                        t1 = wx.CheckBox(self)
                        grid_sizer.Add(t1, 1, wx.ALL | wx.LEFT | wx.ALIGN_CENTRE_VERTICAL, 2)
                    else:
                        max_value = pow(2, signal.nbits) - 1
                        t1 = wxInt.IntCtrl(
                            self,
                            style=wx.TE_CENTRE | wx.TE_PROCESS_ENTER,
                            min=0,
                            max=max_value,
                            limited=True,
                        )
                        grid_sizer.Add(t1, 1, wx.ALL | wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL, 1)
                    # Save the widgets which contains the values
                    self.values_widgets[signal.label] = t1
            else:
                st1 = wx.StaticText(self, label="Value", style=wx.CENTER)
                grid_sizer.Add(st1, 1, wx.ALL | wx.EXPAND | wx.LEFT | wx.ALIGN_CENTRE_VERTICAL, 5)
                max_value = pow(2, 8) - 1
                t1 = wxInt.IntCtrl(
                    self,
                    style=wx.TE_CENTRE | wx.TE_PROCESS_ENTER,
                    min=0,
                    max=max_value,
                    limited=True,
                )
                grid_sizer.Add(t1, 1, wx.ALL | wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL, 1)
                # Save the widgets which contains the values
                self.values_widgets[value.label] = t1
            self.vbox.Add(sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.Fit()

    def update_values(self, values):
        if self.init_flag:
            for _, value in values.items():
                for _, signal in value.signals.items():
                    res = value.get_signal(signal.label)
                    self.values_widgets[signal.label].SetValue(res)
        else:
            self.__init_values(values)
            self.init_flag = True
        self.to_default_color()

    def on_text_change(self, widget):
        widget.SetBackgroundColour((128, 255, 0, 50))

    def to_default_color(self):
        [widget.SetBackgroundColour(wx.NullColour) for widget in self.values_widgets.values()]
        self.Refresh()
