#coding:utf-8

import wx, numpy, sys, threading

import temperature
import viewmemstick, dialogs, utilities, kaffelogic_studio_defaults
import core_studio

########################################################################
class aboutDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        wx.App.Get().doRaise()
        super(aboutDialog, self).__init__(*args, **kw)
        self.InitUI()
        self.SetTitle("About " + core_studio.PROGRAM_NAME)
        self.isRunning = threading.Event()

    def checkForUpdates(self, target):
        if self.isRunning.is_set():
            return
        else:
            self.isRunning.set()
            worker = viewmemstick.GetURL_Thread(self, core_studio.displayUpdateStatus,
                                                [core_studio.SOFTWARE_RELEASE_NOTES_URL, core_studio.FIRMWARE_RELEASE_NOTES_URL], extra=False,
                                                flag=self.isRunning)
            worker.start()

    def InitUI(self):
        box = wx.BoxSizer(wx.VERTICAL)
        html = dialogs.wxHTML(self, -1, size=(550, 500))
        title = "<p><img src=\"" + utilities.getProgramPath() + "logo.png\"></p><p>&nbsp;</p>"
        para1 = "<p>" + core_studio.PROGRAM_NAME + " is an advanced roast profile manager for Kaffelogic personal coffee roasting systems.</p>"
        para2 = "<p>This version is designed for " + core_studio.MODEL_NAME + " firmware version " + core_studio.DESIGNED_FOR_FIRMWARE_VERSION + " and "
        para2 += "profile schema version " + core_studio.DESIGNED_FOR_PROFILE_SCHEMA_VERSION + ". See <i>File&nbsp;&gt;&nbsp;Properties</i> for more information about support for older schema versions.</p>"
        built = "<p><font size=-1>Built with Python " + sys.version + ",\nwx.Python " + wx.version() + ", Numpy " + numpy.version.full_version + \
                ". Running on " + utilities.fullPlatform() + ".</font></p>"
        trademarks = "<p>Kaffelogic is a trademark of Kaffelogic Ltd registered in NZ. Sonofresco is a trademark of Sonofresco Ltd registered in the US. "
        trademarks += "Kaffelogic is an independent company and this software has not been authorized, sponsored, or otherwise approved by Sonofresco.</p>"
        licence = "<h5>Licence</h5><p style='font-size:80%'>" + core_studio.PROGRAM_NAME + """ is free software; you can
redistribute it under the terms of the GNU Lesser General
Public License as published by the Free Software Foundation;
either version 3 of the License, or (at your option) any later version.</p>"""
        licence += "<p>" + core_studio.PROGRAM_NAME + """ is distributed in the hope
that it will be useful, but WITHOUT ANY WARRANTY; without even
the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Lesser General Public License
for more details.</p>
<p><font size=-1>Icon credits: 
<a href="https://www.flaticon.com/authors/good-ware" title="Good Ware">Good Ware</a>, 
<a href="https://www.flaticon.com/authors/smashicons" title="Smashicons">Smashicons</a>
from <a href="https://www.flaticon.com/" title="Flaticon"> www.flaticon.com</a></font></p>"""
        version = '<p>version ' + core_studio.PROGRAM_VERSION + ", " + core_studio.COPYRIGHT + "</p><p><a href='function:checkForUpdates'>check for updates</a></p>"
        website = '<p>Web site: <a href="https://kaffelogic.com">kaffelogic.com</a></p>'
        developer = '<p>Developer: Chris Hilder</p>'
        html.SetPage(title + version + para1 + para2 + website + developer + built + trademarks + licence)
        okButton = wx.Button(self, label='Close')
        box.Add(html, 1, wx.GROW)
        box.Add(okButton, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        box.SetSizeHints(self)
        self.SetSizerAndFit(box)
        okButton.Bind(wx.EVT_BUTTON, html.onOk)
        okButton.SetDefault()
        self.SetAutoLayout(True)
        if not core_studio.isLinux: self.Raise()

########################################################################
class transformDialog(wx.Dialog):
    HELP_TEXT = "This transformation will be applied to zones and corners only."

    def __init__(self, parent):
        super(transformDialog, self).__init__(parent)
        self.parent = parent
        where = self.parent.notebook.GetPage(self.parent.notebook.GetSelection())
        title = self.parent.notebook.GetPageText(self.parent.notebook.GetSelection()).lower()
        self.SetTitle("Transform the " + title)
        box = wx.BoxSizer(wx.VERTICAL)

        if title.endswith('settings'):
            helpText = wx.StaticText(self, -1, self.HELP_TEXT)
            helpText.Wrap(250)
            box.Add(helpText, 0, wx.ALL | wx.ALIGN_CENTRE, 10)

        grid = wx.FlexGridSizer(2, 4, 5, 5)
        label = wx.StaticText(self, -1, u"Time \u2715")
        grid.Add(label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.m_time = wx.TextCtrl(self, -1, "1.0", name='m_time')
        grid.Add(self.m_time, 0, wx.EXPAND)
        label = wx.StaticText(self, -1, "+")
        grid.Add(label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.c_time = wx.TextCtrl(self, -1, "0.0", name='c_time')
        grid.Add(self.c_time, 0, wx.EXPAND)

        if title != 'profile settings':
            if title == 'roast profile curve':
                label = wx.StaticText(self, -1, u"Temperature \u2715")
            if title == 'fan profile curve':
                label = wx.StaticText(self, -1, u"RPM \u2715")
            grid.Add(label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
            self.m_temperature = wx.TextCtrl(self, -1, "1.0", name='m_temperature')
            grid.Add(self.m_temperature, 0, wx.EXPAND)
            label = wx.StaticText(self, -1, "+")
            grid.Add(label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
            self.c_temperature = wx.TextCtrl(self, -1, "0.0", name='c_temperature')
            grid.Add(self.c_temperature, 0, wx.EXPAND)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        applyButton = wx.Button(self, label='Apply')
        cancelButton = wx.Button(self, label='Cancel')
        buttons.Add(applyButton, 1, wx.ALL, 7)  # Mac buttons need 7-pixel borders or they overlap
        buttons.Add(cancelButton, 1, wx.ALL, 7)
        box.Add(grid, 0, wx.ALL, 10)
        box.Add(buttons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.SetSizeHints(self)
        self.SetSizer(box)
        applyButton.Bind(wx.EVT_BUTTON, self.onApply)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
        applyButton.SetDefault()
        self.setFromString(parent.options.getUserOption("transformation", "1,0,1,0"))
        if not core_studio.isLinux: self.Raise()

    def setFromString(self, s):
        self.data = s.split(',')
        self.m_time.SetValue(self.data[0])
        self.c_time.SetValue(self.data[1])
        if hasattr(self, 'm_temperature'): self.m_temperature.SetValue(self.data[2])
        if hasattr(self, 'c_temperature'): self.c_temperature.SetValue(self.data[3])

    def getAsString(self):
        result = [self.m_time.GetValue(), self.c_time.GetValue()]
        if hasattr(self, 'm_temperature'):
            result.append(self.m_temperature.GetValue())
        else:
            result.append(self.data[2])
        if hasattr(self, 'c_temperature'):
            result.append(self.c_temperature.GetValue())
        else:
            result.append(self.data[3])
        return ','.join(result)

    def onApply(self, e):
        if self.parent.fileType == "log":
            return
        wx.App.Get().doRaise()
        try:
            m_x = float(self.m_time.GetValue())
        except:
            m_x = 1.0
        try:
            c_x = float(self.c_time.GetValue())
        except:
            c_x = 0.0
        try:
            m_y = float(self.m_temperature.GetValue())
        except:
            m_y = 1.0
        try:
            c_y = float(self.c_temperature.GetValue())
        except:
            c_y = 0.0
        if m_x != 1.0 or c_x != 0.0 or m_y != 1.0 or c_y != 0.0:
            where = self.parent.notebook.GetPage(self.parent.notebook.GetSelection())
            if hasattr(where, 'profilePoints'):
                self.parent.captureHistory(where, 'transform', True)
                last_time = where.profilePoints[-1].point.x
                for i in range(len(where.profilePoints)):
                    p = where.profilePoints[i]
                    if i not in self.parent.emulation_mode.profile_locked_points or where.title != 'Roast Profile Curve':
                        p.transform(m_x, c_x, m_y, c_y)
                        if self.parent.emulation_mode.profile_points_timelock_last and where.title == 'Roast Profile Curve':
                            if i == len(where.profilePoints) - 1 or p.point.x > last_time:
                                p.point.x = last_time
                        if i == 0 or p.point.x < 0.0:
                            p.point.x = 0.0
                self.parent.modified(True)
                where.setSpinners()
            else:
                for key in kaffelogic_studio_defaults.zoneAndCornerTimes:
                    control = where.configControls[key]
                    value = utilities.fromMinSec(control.GetValue())
                    try:
                        float(value)
                    except:
                        wx.MessageBox("Zone and corner times must be valid min:sec", "Warning", wx.OK)
                        self.Close()
                        return
                for key in kaffelogic_studio_defaults.zoneAndCornerTimes:
                    control = where.configControls[key]
                    value = utilities.fromMinSec(control.GetValue())
                    new = utilities.toMinSec(m_x * value + c_x)
                    control.SetFocus()
                    isBulkChange = True
                    if key == kaffelogic_studio_defaults.zoneAndCornerTimes[-1]:
                        isBulkChange = False
                    self.parent.focus(where, control, isBulkChange=isBulkChange)
                    control.ChangeValue(new)
                    self.parent.txtChange(where, control, isBulkChange=isBulkChange)  # captures it in history
                # print 'transform', m_x, c_x, m_y, c_y
        self.parent.options.setUserOption("transformation", self.getAsString())
        self.Close()

    def onCancel(self, e):
        self.Close()


########################################################################
class areaUnderCurveDialog(wx.Dialog):

    def __init__(self, parent):
        super(areaUnderCurveDialog, self).__init__(parent)
        self.parent = parent
        self.where = self.parent.notebook.GetPage(self.parent.notebook.GetSelection())
        self.title = self.parent.notebook.GetPageText(self.parent.notebook.GetSelection()).lower()
        if self.title in ['roast profile curve', 'log']:
            self.SetTitle("Area under the curve calculation for " + self.title)
            if self.title == 'log':
                self.points = self.parent.logData.ySeriesScaled[self.parent.logData.masterColumn]
            else:
                self.points = self.where.pointsAsGraphed
            box = wx.BoxSizer(wx.VERTICAL)

            grid = wx.GridBagSizer(5, 5)
            label = wx.StaticText(self, -1, u"Base time")
            grid.Add(label, pos=(0, 0), span=(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
            self.base_time = wx.TextCtrl(self, -1, "", name='base_time')
            grid.Add(self.base_time, pos=(0, 1), span=(1, 1), flag=wx.EXPAND)
            label = wx.StaticText(self, -1, "End time")
            grid.Add(label, pos=(0, 2), span=(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
            self.end_time = wx.TextCtrl(self, -1, "", name='end_time')
            grid.Add(self.end_time, pos=(0, 3), span=(1, 1), flag=wx.EXPAND)
            label = wx.StaticText(self, -1, u"Base Temperature")
            grid.Add(label, pos=(1, 0), span=(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
            self.base_temperature = wx.TextCtrl(self, -1, "", name='base_temperature')
            grid.Add(self.base_temperature, pos=(1, 1), span=(1, 1), flag=wx.EXPAND)
            self.from_curve = wx.CheckBox(self, label="from curve")
            grid.Add(self.from_curve, pos=(1, 2), span=(1, 2), flag=wx.EXPAND)
            self.answer = wx.StaticText(self, -1, u"AUC")
            font = self.answer.GetFont()
            font.SetWeight(wx.BOLD)
            self.answer.SetFont(font)
            buttons = wx.BoxSizer(wx.HORIZONTAL)
            closeButton = wx.Button(self, label='Close')
            buttons.Add(closeButton, 1, wx.ALL, 7)  # Mac buttons need 7-pixel borders or they overlap
            box.Add(grid, 0, wx.ALL, 10)
            box.Add(self.answer, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
            box.Add(buttons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
            box.SetSizeHints(self)
            self.SetSizer(box)
            self.base_time.Bind(wx.EVT_TEXT, self.recalculate)
            self.end_time.Bind(wx.EVT_TEXT, self.recalculate)
            self.base_temperature.Bind(wx.EVT_TEXT, self.recalculate)
            self.from_curve.Bind(wx.EVT_CHECKBOX, self.recalculate)
            closeButton.Bind(wx.EVT_BUTTON, self.onCloseButton)
            self.Bind(wx.EVT_CLOSE, self.onClose)
            closeButton.SetDefault()
            self.setFromString(self.parent.options.getUserOption("area_under_curve", ",,,yes"))
            if not core_studio.isLinux: self.Raise()
        else:
            wx.CallAfter(self.Close)

    def setFromString(self, s):
        baseTime, endTime, baseTemperature, fromCurve = s.split(',')
        self.base_time.SetValue(baseTime)
        self.end_time.SetValue(endTime)
        self.base_temperature.SetValue(baseTemperature)
        self.from_curve.SetValue(fromCurve == 'yes')
        self.recalculate(None)

    def getAsString(self):
        result = [self.base_time.GetValue(), self.end_time.GetValue(), self.base_temperature.GetValue(),
                  'yes' if self.from_curve.GetValue() else 'no']
        return ','.join(result)

    def getFromCurve(self):
        if self.from_curve.GetValue():
            self.base_temperature.Enable(False)
            time = utilities.floatOrNone(utilities.fromMinSec(self.base_time.GetValue()))
            self.base_temperature.ChangeValue(str(round(utilities.getYfromX(self.points, time), 1)))
        else:
            self.base_temperature.Enable(True)

    def recalculate(self, event):
        if not event is None: event.Skip()
        start = utilities.floatOrNone(utilities.fromMinSec(self.base_time.GetValue()))
        self.getFromCurve()
        end = utilities.floatOrNone(utilities.fromMinSec(self.end_time.GetValue()))
        base = utilities.floatOrNone(self.base_temperature.GetValue())
        if utilities.allNotNone([start, end, base]) and start < end:
            pointsForSumming = utilities.filterPointsX(self.points, (start, end))
            try:
                auc = utilities.sumY(pointsForSumming) / float(len(pointsForSumming)) * (end - start)
            except ZeroDivisionError as e:
                self.answer.SetLabel('')
                return
            auc -= (end - start) * base
            auc /= 60.0
            self.answer.SetLabel(str(round(auc, 1)) + temperature.insertTemperatureUnit(u" ° × min"))

    def onCloseButton(self, e):
        self.Close()

    def onClose(self, e):
        self.parent.options.setUserOption("area_under_curve", self.getAsString())
        e.Skip()


########################################################################
class captureImageDialog(wx.Dialog):
    """ gets the size of the image """

    def __init__(self, parent):
        super(captureImageDialog, self).__init__(parent)
        self.parent = parent
        self.where = self.parent.notebook.GetPage(self.parent.notebook.GetSelection())
        title = self.parent.notebook.GetPageText(self.parent.notebook.GetSelection()).lower()
        self.SetTitle("Capture " + title + " image")
        box = wx.BoxSizer(wx.VERTICAL)

        grid = wx.FlexGridSizer(1, 4, 5, 5)
        label = wx.StaticText(self, -1, u"Width")
        grid.Add(label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.width = wx.SpinCtrl(parent=self, min=100, max=1000000)
        grid.Add(self.width, 0, wx.EXPAND)
        label = wx.StaticText(self, -1, "Height")
        grid.Add(label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.height = wx.SpinCtrl(parent=self, min=100, max=1000000)
        grid.Add(self.height, 0, wx.EXPAND)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        saveButton = wx.Button(self, label='Save')
        cancelButton = wx.Button(self, label='Cancel')
        useScreenSizeButton = wx.Button(self, label='use current window size')
        buttons.Add(saveButton, 1, wx.ALL, 7)  # Mac buttons need 7-pixel borders or they overlap
        buttons.Add(cancelButton, 1, wx.ALL, 7)
        box.Add(grid, 0, wx.ALL, 10)
        box.Add(useScreenSizeButton, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.Add(buttons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.SetSizeHints(self)
        self.SetSizer(box)
        saveButton.Bind(wx.EVT_BUTTON, self.onSave)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
        useScreenSizeButton.Bind(wx.EVT_BUTTON, self.onUseScreenSize)
        self.setFromString(parent.options.getUserOption("capture_image_size"))
        saveButton.SetDefault()
        self.result = wx.ID_CANCEL
        if not core_studio.isLinux: self.Raise()

    def setFromString(self, s):
        self.data = s.split(',')
        self.width.SetValue(int(self.data[0]))
        self.height.SetValue(int(self.data[1]))

    def getAsString(self):
        result = [str(self.width.GetValue()), str(self.height.GetValue())]
        return ','.join(result)

    def onSave(self, e):
        self.parent.options.setUserOption("capture_image_size", self.getAsString())
        self.result = wx.ID_OK
        self.Close()

    def onCancel(self, e):
        self.result = wx.ID_CANCEL
        self.Close()

    def onUseScreenSize(self, e):
        storeSize = self.where.canvas.GetSize()
        string = str(storeSize[0]) + ',' + str(storeSize[1])
        self.setFromString(string)
########################################################################
