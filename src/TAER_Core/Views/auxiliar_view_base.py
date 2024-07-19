import wx
import logging


class AuxViewBase(wx.Frame):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.logger = logging.getLogger(__name__)

    def open(self):
        self.Show()

    def close(self, destroy=False):
        self.logger.debug(f"On close frame {self.GetTitle()}")
        if destroy:
            self.Destroy()
        else:
            self.Hide()
