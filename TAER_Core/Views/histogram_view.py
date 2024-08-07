import matplotlib

matplotlib.use("WXAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas

import wx
import wx.lib.intctrl as wxInt

from TAER_Core.Views.auxiliar_view_base import AuxViewBase


class HistogramView(AuxViewBase):
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            title="Histogram",
            style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX,
        )

        self.SetMinSize(wx.Size(0, 0))
        self.__create_layout()
        self.scale_flag = False

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)

        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.vsizer.Add(self.hsizer, 0, wx.ALL, 5)

        self.panel_histogram_plot = HistogramPlotPanel(self)
        self.hsizer.Add(self.panel_histogram_plot, 0, wx.EXPAND)

        self.SetSizerAndFit(self.vsizer)

        self.Layout()

    def update_histogram(self, hist):
        if hist != None and self.IsShown():
            counts = hist.value[0]
            bins = hist.value[1]
            self.panel_histogram_plot.update(counts, bins)
            self.Refresh()

    def scale(self):
        self.scale_flag = True

    def get_bin_settings(self):
        max = self.panel_histogram_plot.txt_bin_max.GetValue()
        min = self.panel_histogram_plot.txt_bin_min.GetValue()
        step = self.panel_histogram_plot.txt_bin_step.GetValue()
        return max, min, step


class HistogramPlotPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.__create_layout()

    def __create_layout(self):
        # Avoid color on background in Windows OS
        self.SetBackgroundColour(wx.NullColour)

        self.figure = Figure(figsize=[3.2, 2.4])
        self.canvas = FigCanvas(self, -1, self.figure)

        self.axes = self.figure.add_subplot(111)

        self.sizer_main = wx.BoxSizer(wx.VERTICAL)
        self.sizer_main.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)

        self.sizer_buttons = wx.StaticBoxSizer(wx.HORIZONTAL, self, "Settings")
        self.sizer_main.Add(self.sizer_buttons, 0, wx.EXPAND | wx.TOP, 10)

        self.button_scale = wx.Button(self, label="Scale")
        self.button_scale.Enable(False)
        self.sizer_buttons.Add(self.button_scale, 1, wx.EXPAND | wx.ALL, 5)

        self.sizer_bins = wx.StaticBoxSizer(wx.HORIZONTAL, self, "Bins definition")

        local_sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, label="Minimum", style=wx.LEFT)
        local_sizer.Add(label, 0, wx.EXPAND | wx.BOTTOM, 1)
        self.txt_bin_min = wxInt.IntCtrl(self, min=0, max=65535, limited=True)
        local_sizer.Add(self.txt_bin_min, 1, wx.EXPAND)
        self.sizer_bins.Add(local_sizer, 0, wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT, 5)

        local_sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, label="Maximum", style=wx.LEFT)
        local_sizer.Add(label, 0, wx.EXPAND | wx.BOTTOM, 1)
        self.txt_bin_max = wxInt.IntCtrl(self, min=0, max=65535, limited=True)
        local_sizer.Add(self.txt_bin_max, 1, wx.EXPAND)
        self.sizer_bins.Add(local_sizer, 0, wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT, 5)

        local_sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, label="Number of bins", style=wx.LEFT)
        local_sizer.Add(label, 0, wx.EXPAND | wx.BOTTOM, 1)
        self.txt_bin_step = wxInt.IntCtrl(self, min=0, max=1000, limited=True)
        local_sizer.Add(self.txt_bin_step, 1, wx.EXPAND)
        self.sizer_bins.Add(local_sizer, 0, wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT, 5)

        self.sizer_buttons.Add(self.sizer_bins, 3, wx.EXPAND)

        self.SetSizerAndFit(self.sizer_main)
        self.Layout()

    def update(self, count, bins):
        if len(count) <= 0 or len(bins) <= 0:
            return

        if not hasattr(self, "bar_plot") or self.GetParent().scale_flag:
            self.button_scale.Enable(True)
            self.axes.cla()
            _, _, self.bar_plot = self.axes.hist(bins[:-1], bins, weights=count)
            self.axes.relim()
            self.txt_bin_max.ChangeValue(int(bins[-1]))
            self.txt_bin_min.ChangeValue(int(bins[0]))
            self.txt_bin_step.ChangeValue(len(bins))
            self.GetParent().scale_flag = False
        else:
            bar_plot = self.bar_plot
            for height, rect in zip(count, bar_plot.patches):
                rect.set_height(height)
            self.axes.autoscale_view()
        self.canvas.draw()
