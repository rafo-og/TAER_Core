import platform
import ctypes
import os
from importlib.metadata import version
import wx
import threading
import re
import logging
import cv2 as cv
from TAER_Core.Views import (
    ValuesView,
    DeviceInfoView,
    HistogramView,
    SerialView,
    ChipRegisterView,
    AdcView,
    BufferedCanvas,
    MainMenuBar,
)
from logging import StreamHandler
import TAER_Core
from TAER_Core.Libs.config import ViewConfig
import TAER_App


class MainView(wx.Frame):
    """
    This class holds the main view
    """

    def __init__(self):
        """Create the wx.App and then we put together all the widgets"""
        self.app = wx.App()
        tag = self.__get_current_version()
        wx.Frame.__init__(self, None, title=f"TAER {tag}")
        self.set_icon()

    def config(self):
        self.config_data = ViewConfig()
        self.SetMinSize(
            wx.Size(
                self.config_data.main_panel_size.w, self.config_data.main_panel_size.h
            )
        )
        self.__create_layout()
        self.__init_logic()

    def __create_layout(self):
        """Create the view layout"""
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)
        # Menu bar
        self.menu_bar = MainMenuBar(self)
        self.SetMenuBar(self.menu_bar)
        # Sizers
        self.main_box = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        # Panels
        self.panel_control = ControlPanel(self)
        self.panel_image = ImagePanel(self)
        self.logging_panel = LogPanel(self)

        self.hbox.Add(self.panel_control, 1, wx.EXPAND)
        self.hbox.Add(self.panel_image, 3, wx.EXPAND)

        self.main_box.Add(self.hbox, 2, wx.EXPAND)
        self.main_box.Add(self.logging_panel, 1, wx.EXPAND)

        self.SetSize(
            wx.Size(
                self.config_data.main_panel_size.w, self.config_data.main_panel_size.h
            )
        )
        self.SetSizer(self.main_box)
        self.Layout()

        self.__init_other_frames()

    def __init_other_frames(self):
        self.edit_register_device_frame = ValuesView(self, "Registers")
        self.edit_register_chip_frame = ChipRegisterView(self)
        self.edit_dac_frame = ValuesView(self, "DACs")
        self.device_info_frame = DeviceInfoView(self)
        self.image_histogram_frame = HistogramView(self)
        self.serial_control_frame = SerialView(self)
        self.adc_control_frame = AdcView(self)

    def __init_logic(self):
        self.imgLock = threading.Lock()

    def __get_current_version(self):
        return "v" + version("TAER_Core")

    def start_event_loop(self):
        self.app.MainLoop()

    def open(self):
        """
        Upon start we just show the frame and enter the MainLoop
        """
        self.Layout()
        self.CenterOnScreen()
        self.Show()

    def close(self, destroy=True):
        if destroy:
            self.Destroy()
        else:
            self.Hide()

    def init_log_box(self):
        logger_names = self.__get_logger_keys()
        txtHandler = CustomConsoleHandler(self.logging_panel.logging_box)
        for name in logger_names:
            logger = logging.getLogger(name)
            logger.addHandler(txtHandler)

    def __get_logger_keys(self):
        app_log_filepath = os.path.join(os.getcwd(), "config", "loggers.conf")
        if os.path.exists(app_log_filepath):
            log_filepath = app_log_filepath
        else:
            log_filepath = os.path.join(
                os.path.dirname(TAER_App.__file__), "config", "loggers.conf"
            )

        with open(log_filepath, "r") as f:
            lines = f.read()
            pattern_str = r"(?<=keys=)(.*)"
            pattern = re.compile(pattern_str, re.MULTILINE | re.IGNORECASE)
            match = pattern.search(lines)
            return match.groups()[0].split(",")

    def set_menus_state(self, state, id=None):
        for submenu in self.menu_bar.menu_device.GetMenuItems():
            if id is None or submenu.ItemLabelText == id:
                submenu.Enable(state)

        for submenu in self.menu_bar.menu_edit.GetMenuItems():
            if id is None or submenu.ItemLabelText == id:
                submenu.Enable(state)

        for submenu in self.menu_bar.menu_tools.GetMenuItems():
            if id is None or submenu.ItemLabelText == id:
                submenu.Enable(state)

        self.panel_control.Enable(state)

        self.edit_register_device_frame.set_menus_state(state)

    def set_capture_mode(self, state):
        panel = self.panel_control
        if state:
            panel.button_start_stop.SetLabel("Start")
            panel.button_capture.Enable(True)
        else:
            panel.button_start_stop.SetLabel("Stop")
            panel.button_capture.Enable(False)

    def set_mode(self, mode):
        self.panel_control.set_selected_mode(mode)

    def set_icon(self, frame: wx.Frame | None = None):
        # Set frame icon
        if platform.system() == "Windows":
            myappid = "TAER-App.TAER-Core.icon.string"  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        icon_path = os.path.join(os.path.dirname(__file__), "Data/taer_small_icon.png")
        if frame is None:
            self.SetIcon(wx.Icon(icon_path))
        else:
            frame.SetIcon(wx.Icon(icon_path))

    @property
    def image(self):
        with self.imgLock:
            return self.panel_image.img_ctrl.img

    @image.setter
    def image(self, value):
        with self.imgLock:
            h, w = value.shape[:2]  # The array shape is H, W
            valueRGB = cv.cvtColor(value, cv.COLOR_BGR2RGB)
            self.panel_image.img_ctrl.img = wx.ImageFromBuffer(w, h, valueRGB)
        self.panel_image.img_ctrl.update()


#
# Main panels
#


class ControlPanel(wx.Panel):
    """
    Panel to show buttons and control widgets
    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.__create_layout()

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)

        config_modes = self.parent.config_data.control_panel.modes
        modes = [mode[0] for mode in config_modes]

        # Sensor Mode
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.modes_box = wx.RadioBox(
            self,
            label="Select mode:",
            choices=modes,
            style=wx.RA_VERTICAL,
        )
        self.vbox.Add(self.modes_box, 0, wx.EXPAND | wx.ALL, 20)

        # Control Buttons
        self.control_box = wx.StaticBoxSizer(wx.HORIZONTAL, self, "Sensor Control")
        self.control_grid = wx.GridSizer(2, 0, 0)
        self.control_box.Add(self.control_grid, 0, wx.ALL, 5)
        self.place_buttons()
        self.vbox.Add(
            self.control_box, 0, wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT, 20
        )

        self.SetSizerAndFit(self.vbox)
        self.Layout()

    def place_buttons(self):
        grid = self.control_grid

        button = wx.Button(self, label="Start")
        grid.Add(button, 0, wx.ALL, 5)
        self.button_start_stop = button

        button = wx.Button(self, label="Capture")
        grid.Add(button, 0, wx.ALL, 5)
        self.button_capture = button

        button = wx.Button(self, label="Reset device")
        grid.Add(button, 0, wx.ALL, 5)
        self.button_reset = button

        button = wx.Button(self, label="Reset AER")
        grid.Add(button, 0, wx.ALL, 5)
        self.button_reset_periphery = button

        button = wx.Button(self, label="Reset Chip")
        grid.Add(button, 0, wx.ALL, 5)
        self.button_reset_chip = button

    def set_selected_mode(self, mode):
        n = self.modes_box.FindString(mode)
        if n is not wx.NOT_FOUND:
            self.modes_box.SetSelection(n)


class ImagePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.__create_layout()

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)
        # Create the widget for the image
        self.img_ctrl = ImageCtrl(self)
        # Sizers
        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.hsizer.Add(
            self.img_ctrl, 1, wx.SHAPED | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10
        )
        self.vsizer.Add(
            self.hsizer, 1, wx.SHAPED | wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10
        )

        self.SetSizer(self.vsizer)
        self.Layout()


class LogPanel(wx.Panel):
    """
    Panel to show logger messages
    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.SetMinSize(wx.Size(100, 200))

        self.__create_layout()

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)

        self.sizer = wx.BoxSizer()

        txt_style = (
            wx.TE_MULTILINE
            | wx.TE_READONLY
            | wx.TE_RICH
            | wx.TE_WORDWRAP
            | wx.TE_NOHIDESEL
        )
        self.logging_box = wx.TextCtrl(self, style=txt_style)

        font1 = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, "Consolas")
        self.logging_box.SetFont(font1)
        self.logging_box.SetMinSize(wx.Size(100, 20))

        self.sizer.Add(self.logging_box, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(self.sizer)


#
# Custom controls
#


class CustomConsoleHandler(StreamHandler):
    """
    Console handler to display logging messages in ctrlTxt
    """

    def __init__(self, textctrl: wx.TextCtrl):
        """Constructor"""
        StreamHandler.__init__(self)
        self.txt_control = textctrl
        self.__config()

    def __config(self):
        format_string = "[%(asctime)s.%(msecs)03d] %(levelname)s [%(filename)s:%(lineno)d] %(message)s"
        format = logging.Formatter(format_string, datefmt="%H:%M:%S")
        self.setFormatter(format)
        colour = self.txt_control.GetDefaultStyle().TextColour
        self.color_default = colour

    def emit(self, record: logging.LogRecord):
        """
        Send message to text control
        """
        wx.CallAfter(self.thread_safe_emit, record)

    def thread_safe_emit(self, record: logging.LogRecord):
        msg = self.format(record)
        style = self.__get_text_style(record.levelname)
        self.txt_control.SetDefaultStyle(style)
        self.txt_control.AppendText(msg + "\n")
        self.flush()

    def __get_text_style(self, x: str) -> wx.TextAttr:
        """
        Get the text colour regarding with the debug level
        """
        return {
            "DEBUG": wx.TextAttr(self.color_default),
            "INFO": wx.TextAttr(wx.Colour(0, 87, 233)),
            "WARNING": wx.TextAttr(wx.Colour(227, 177, 0)),
            "ERROR": wx.TextAttr(wx.Colour(225, 24, 69)),
            "CRITICAL": wx.TextAttr(wx.Colour(205, 4, 49)),
        }[x]


class ImageCtrl(BufferedCanvas):
    """
    Panel to show an image without flickering
    """

    def __init__(self, parent):
        self.parent = parent

        self.__create_layout()

    def __create_layout(self):
        # Get the panel configuration
        config_data = self.parent.GetParent().config_data.image_panel_size
        # Create image
        self.img = wx.Image(config_data.w, config_data.h)
        # Initialize buffered canvas class
        panelSize = wx.Size(config_data.w, config_data.h)
        BufferedCanvas.__init__(self, self.parent, size=panelSize)
        self.Fit()

    def draw(self, dc):
        W, H = self.GetClientSize()
        if W > 0 and H > 0:
            self.bitmap = self.img.Scale(W, H).ConvertToBitmap()
            dc.DrawBitmap(self.bitmap, 0, 0)
