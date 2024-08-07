import wx

from TAER_Core.Views.auxiliar_view_base import AuxViewBase


class DeviceInfoView(AuxViewBase):
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            title="Device info",
            style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX,
        )

        self.__create_layout()

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        self.grid = wx.GridSizer(2, 5, 0)
        self.hsizer.Add(self.vsizer, 0, wx.ALL, 1)
        self.vsizer.Add(self.grid, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 20)

        self.__create_info_table()

        self.SetSizerAndFit(self.hsizer)
        self.Layout()

    def __create_info_table(self):
        self.txt_label_vendor = wx.StaticText(self, style=wx.CENTER, label="Vendor:")
        self.txt_value_vendor = wx.StaticText(self, style=wx.LEFT)
        self.grid.Add(self.txt_label_vendor, 0, wx.ALIGN_RIGHT | wx.RIGHT, 10)
        self.grid.Add(self.txt_value_vendor, 0, wx.ALIGN_LEFT)

        self.txt_label_model = wx.StaticText(self, style=wx.CENTER, label="Model:")
        self.txt_value_model = wx.StaticText(self, style=wx.LEFT)
        self.grid.Add(self.txt_label_model, 0, wx.ALIGN_RIGHT | wx.RIGHT, 10)
        self.grid.Add(self.txt_value_model, 0, wx.ALIGN_LEFT)

        self.txt_label_sn = wx.StaticText(self, style=wx.CENTER, label="Serial number:")
        self.txt_value_sn = wx.StaticText(self, style=wx.LEFT)
        self.grid.Add(self.txt_label_sn, 0, wx.ALIGN_RIGHT | wx.RIGHT, 10)
        self.grid.Add(self.txt_value_sn, 0, wx.ALIGN_LEFT)

        self.txt_label_dev_version = wx.StaticText(self, style=wx.CENTER, label="Device version:")
        self.txt_value_dev_version = wx.StaticText(self, style=wx.LEFT)
        self.grid.Add(self.txt_label_dev_version, 0, wx.ALIGN_RIGHT | wx.RIGHT, 10)
        self.grid.Add(self.txt_value_dev_version, 0, wx.ALIGN_LEFT)

    def update_info(self, info):
        self.txt_value_vendor.SetLabel(info.vendor)
        self.txt_value_model.SetLabel(info.product_name)
        self.txt_value_sn.SetLabel(info.serial_number)
        self.txt_value_dev_version.SetLabel(info.dev_version)
