import wx
import os
import sys
import TAER_App


class SelectConfigDialog(wx.Dialog):
    CONFIGS_PATH = os.path.join(os.path.dirname(TAER_App.__file__), ("chip_configs"))

    def __init__(self, parent):
        dlg_style = (wx.CAPTION | wx.STAY_ON_TOP) ^ wx.RESIZE_BORDER
        super().__init__(parent, style=dlg_style, title="Select chip configuration")

        self.__get_config_filenames()

        self.__create_layout()

        self.CentreOnScreen()

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)

        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        self.hsizer.Add(self.vsizer, 0, wx.ALIGN_CENTER_VERTICAL)

        self.combobox_select_config = wx.ComboBox(
            self,
            choices=self.choices_names,
            style=wx.CB_SIMPLE | wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT,
            size=wx.Size(-1, 25),
        )
        self.vsizer.Add(
            self.combobox_select_config,
            1,
            wx.ALIGN_CENTER_HORIZONTAL | wx.TOP | wx.BOTTOM,
            20,
        )

        self.button_sizer = self.CreateStdDialogButtonSizer(wx.OK ^ wx.CANCEL)
        self.button_ok = self.FindWindow(self.GetAffirmativeId())
        self.button_ok.Enable(False)
        self.vsizer.Add(
            self.button_sizer,
            0,
            wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM | wx.LEFT | wx.RIGHT,
            20,
        )

        # In this case the event handler is a lambda function to avoid write another method in this class
        self.combobox_select_config.Bind(
            wx.EVT_TEXT,
            lambda evt: evt.GetEventObject().GetParent().button_ok.Enable(True),
        )

        self.SetSizerAndFit(self.hsizer)
        self.Layout()

    def __get_config_filenames(self):
        self.config_paths = {}
        self.choices_names = []
        for path in os.scandir(self.CONFIGS_PATH):
            if path.is_file() and path.name.endswith(".yaml"):
                config_name = os.path.splitext(path.name)[0]
                self.config_paths[config_name] = path
                self.choices_names.append(config_name)

    def get_choice_selected(self) -> str:
        idx = self.combobox_select_config.GetSelection()
        config_name = self.combobox_select_config.GetString(idx)
        return self.config_paths[config_name].path
