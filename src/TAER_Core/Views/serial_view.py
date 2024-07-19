import wx

from TAER_Core.Views.auxiliar_view_base import AuxViewBase


class SerialView(AuxViewBase):
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            title="SERIAL debugger",
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

        self.panel_serial_control = SerialControlPanel(self)
        self.hsizer.Add(self.panel_serial_control, 0, wx.EXPAND)

        self.SetSizerAndFit(self.vsizer)

        self.Layout()


class SerialControlPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.__create_layout()

    def __create_layout(self):
        serial_tx_text = wx.StaticText(self, label="SERIAL TX data", style=wx.CENTER)
        self.serial_tx_box = wx.TextCtrl(self, value="", style=wx.TE_CENTER)
        serial_rx_text = wx.StaticText(self, label="SERIAL RX data", style=wx.CENTER)
        self.serial_rx_box = wx.TextCtrl(self, value="", style=wx.TE_CENTER | wx.TE_READONLY)
        self.btn_write = wx.Button(self, wx.ID_ANY, "Write SERIAL")

        self.vsizer = wx.BoxSizer(wx.VERTICAL)

        self.main_grid = wx.GridSizer(2, 0, 0)
        self.main_grid.Add(serial_tx_text, 0, wx.ALIGN_CENTER | wx.TOP, 5)
        self.main_grid.Add(
            self.serial_tx_box,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT | wx.TOP,
            5,
        )
        self.main_grid.Add(serial_rx_text, 0, wx.ALIGN_CENTER | wx.TOP, 5)
        self.main_grid.Add(
            self.serial_rx_box,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT | wx.TOP,
            5,
        )

        self.vsizer.Add(self.main_grid, 0, wx.ALL, 1)
        self.vsizer.Add(self.btn_write, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.SetSizer(self.vsizer)
