import wx


class MainMenuBar(wx.MenuBar):
    def __init__(self, view):
        wx.MenuBar.__init__(self)
        self.view = view
        self.__add_menus()

    def __add_menus(self):
        self.menu_device = MainDeviceMenu()
        self.Append(self.menu_device, "&Device")
        self.menu_edit = MainEditMenu()
        self.Append(self.menu_edit, "&Edit")
        self.menu_image = MainImageMenu()
        self.Append(self.menu_image, "&Image")
        self.menu_tools = MainToolsMenu()
        self.Append(self.menu_tools, "&Tools")

    def configure_tools(self, tools):
        self.menu_tools.configure_tools(tools)


class MainEditMenu(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)

        self.__config()

    def __config(self):
        self.item_save_preset = wx.MenuItem(self, wx.NewId(), "&Save preset as...")
        self.Append(self.item_save_preset)
        self.item_load_preset = wx.MenuItem(self, wx.NewId(), "&Load preset...")
        self.Append(self.item_load_preset)
        self.item_reg_dev = wx.MenuItem(self, wx.NewId(), "&Device registers")
        self.Append(self.item_reg_dev)
        self.item_reg_chip = wx.MenuItem(self, wx.NewId(), "&Chip registers")
        self.Append(self.item_reg_chip)
        self.item_dac = wx.MenuItem(self, wx.NewId(), "&DACs")
        self.Append(self.item_dac)


class MainDeviceMenu(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)

        self.__config()

    def __config(self):
        self.item_info = wx.MenuItem(self, wx.NewId(), "&Info")
        self.Append(self.item_info)

        self.item_program = wx.MenuItem(self, wx.NewId(), "&Program...")
        self.Append(self.item_program)

        self.program_history = wx.FileHistory()
        self.program_history.SetMenuPathStyle(wx.FH_PATH_SHOW_ALWAYS)
        self.program_history_config = wx.Config(
            "TAER",
            localFilename="./tmp/.TAER_recent_files",
            style=wx.CONFIG_USE_LOCAL_FILE | wx.CONFIG_USE_SUBDIR | wx.CONFIG_USE_RELATIVE_PATH,
        )
        self.program_history.Load(self.program_history_config)

        self.item_program_history = wx.Menu()
        self.program_history.UseMenu(self.item_program_history)
        self.program_history.AddFilesToMenu()
        self.AppendSubMenu(self.item_program_history, "Recent binary files")


class MainImageMenu(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)

        self.__config()

    def __config(self):
        self.item_histogram = wx.MenuItem(self, wx.NewId(), "&Histogram")
        self.Append(self.item_histogram)


class MainToolsMenu(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)
        self.__config()

    def __config(self):
        self.items = {}
        item_name = "Write SPI"
        self.items[item_name] = wx.MenuItem(self, wx.NewId(), f"&{item_name}")
        self.Append(self.items[item_name])
        item_name = "ADCs"
        self.items[item_name] = wx.MenuItem(self, wx.NewId(), f"&{item_name}")
        self.Append(self.items[item_name])
        item_name = "Execute test"
        self.items[item_name] = wx.MenuItem(self, wx.NewId(), f"&{item_name}")
        self.Append(self.items[item_name])

    def configure_tools(self, tools):
        for tool in tools:
            item_name = tool
            self.items[item_name] = wx.MenuItem(self, wx.NewId(), f"&{item_name}")
            self.Append(self.items[item_name])
