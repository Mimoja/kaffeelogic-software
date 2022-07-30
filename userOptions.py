# -*- coding: utf-8 -*-

import core_studio
import os
import re
import utilities, dialogs, temperature
import wx
import threading
from time import sleep

DEFAULT_OPTIONS = {
    "difficulty":                   "basic",
    "linewidth":                    "1",
    "tipnumber":                    "1",
    "phase1_name":                  "Drying",
    "phase2_name":                  "Maillard",
    "phase3_name":                  "Development",
    "zoom_on_mouse_wheel":          "no" if core_studio.isMac else "yes",
    "automatic_check_for_updates":  "yes",
    "ror_multiplier":               "1",
    "ror_smoothing":                "1",
    "legend_font_size":             "10" if core_studio.isMac else "8",
    "capture_image_size":           "1024,768"
}

COMPARE_COLUMN_NAMES = ['spot_temp','temp','mean_temp','profile','profile_ROR','actual_ROR','desired_ROR','power_kW','volts-9','Kp','Ki','Kd','fan_speed','events','zones']
COMPARE_COLUMN_DEFAULTS = 'mean_temp,profile,events'
COMPARE_COLUMN_ALWAYS = []

def floatable(x):
    try:
        float(x)
        return True
    except:
        try:
            a, b = x
            float(a)
            float(b)
            return True
        except:
            return False

def textToListOf2Tuples(s):
    s = [pair.split(',') for pair in re.sub(r'^\[\(|\)\]$', '', s).split('), (')]
    e = [(float(pair[0]), float(pair[1])) for pair in s if floatable(pair)]
    return e

def listOfStringsToText(l):
    if l == []: return "[]"
    return "['" + "', '".join([utilities.ensureUnicode(s).encode('utf-8').encode('string_escape') for s in l]) + "']"
    
def textToListOfStrings(s, allowDoubleQuotes=False):
    if s == "" or s == "[]" or s is None:
        return []
    q = "\"'" if allowDoubleQuotes else "'"
    return [x.decode('string_escape').decode('utf-8') for x in re.split(r"[" + q + r"],\s*u?[" + q + r"]", re.sub(r"^\[u?[" + q + "]|[" + q + "]\]$", "", s))]

def messageIfUpdated(window):
    if "version" in list(window.options.options.keys()) and window.options.options["version"] != core_studio.PROGRAM_VERSION:
        change = 'updated' if core_studio.compareVersions(window.options.options["version"], core_studio.PROGRAM_VERSION) < 0 else 'rolled back'
        wx.MessageBox(core_studio.PROGRAM_NAME + " has been " + change + " to version " + core_studio.PROGRAM_VERSION, "Update", wx.OK)
    window.options.options["version"] = core_studio.PROGRAM_VERSION
    window.options.saveUserOptions()            

def handleTips(window, tips, asHelp = False):
    if "showtips" not in list(window.options.options.keys()) or window.options.options["showtips"] == "yes" or asHelp:
        userPref = wx.adv.ShowTip(window, tips, "showtips" not in list(window.options.options.keys()) or window.options.options["showtips"] == "yes" )
        tipNumber = tips.CurrentTip
        #print "tips were shown, number =", tipNumber
        window.options.options["tipnumber"] = str(tipNumber)
        if userPref:
            window.options.options["showtips"] = "yes"
        else:
            window.options.options["showtips"] = "no"
        window.options.saveUserOptions()
    
class editOptionsDialog(wx.Dialog):
    
    def __init__(self, parent, options, optionGroup):
        super(editOptionsDialog, self).__init__(parent) 
        self.parent = parent
        self.options = options
        self.optionGroup = optionGroup
        if optionGroup == 'general':
            self.InitGeneralUI()
            self.SetTitle("Edit general options")
        elif optionGroup == 'compare':
            self.InitCompareUI()
            self.SetTitle("Edit compare options")
        else:
            raise('Must be general or compare options')

    def InitCompareUI(self):
        box = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(vgap=5, hgap=5)
        self.column_name_checkboxes = []

        label = wx.StaticText(self, -1, "Select which log lines appear when comparing files")
        grid.Add(label, (0, 0), (1, 2), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)

        self.selected_compare_columns = self.options.getUserOption("compare_columns", COMPARE_COLUMN_DEFAULTS).split(',')
        rowNumber = 1
        for col in COMPARE_COLUMN_NAMES:
            label = wx.StaticText(self, -1, utilities.replaceUnderscoreWithSpace(col))
            grid.Add(label, (rowNumber,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
            check = wx.CheckBox(self, -1)
            self.column_name_checkboxes.append(check)
            grid.Add(check, (rowNumber,1), flag=wx.ALIGN_LEFT)
            check.SetValue(col in self.selected_compare_columns)
            if col in COMPARE_COLUMN_ALWAYS:
                check.Disable()
                check.SetValue(True)
            rowNumber += 1

        self.addButtons(box, grid, self.onCompareApply)

    def onCompareApply(self, e):
        self.selected_compare_columns = []
        index = 0
        for check in self.column_name_checkboxes:
            if check.GetValue():
                self.selected_compare_columns.append(COMPARE_COLUMN_NAMES[index])
            index += 1
        self.options.options["compare_columns"] = ','.join(self.selected_compare_columns)
        self.options.refreshPanelsFromOptions(self.parent)
        self.options.saveUserOptions()
        self.Close()

    def InitGeneralUI(self):
        box = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(vgap=5, hgap=5)
        self.temperature_labels = []
        self.temperature_ctrls = []

        label = wx.StaticText(self, -1, "Phase 1 name")
        grid.Add(label, (0,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.phase1 = wx.TextCtrl(self, -1, self.options.getUserOption("phase1_name"))
        grid.Add(self.phase1, (0,1), flag=wx.EXPAND)
        label = wx.StaticText(self, -1, "Phase 2 name")
        grid.Add(label, (1,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.phase2 = wx.TextCtrl(self, -1, self.options.getUserOption("phase2_name"))
        grid.Add(self.phase2, (1,1), flag=wx.EXPAND)
        label = wx.StaticText(self, -1, "Phase 3 name")
        grid.Add(label, (2,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.phase3 = wx.TextCtrl(self, -1, self.options.getUserOption("phase3_name"))
        grid.Add(self.phase3, (2,1), flag=wx.EXPAND)
        
        if core_studio.isLinux:
            spinWidth = 120
        else:
            spinWidth = 40
            
        label = wx.StaticText(self, -1, temperature.insertTemperatureUnit("Default temperatures (°)"))
        self.temperature_labels.append(label)
        grid.Add(label, (3,0), span=(1,2), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)

        #default_expect_colrchange
        label = wx.StaticText(self, -1, "    Expected colour change")
        grid.Add(label, (4,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.colourChangeCtrl = wx.TextCtrl(self, -1, str(self.options.getUserOption("default_expect_colrchange")))
        self.temperature_ctrls.append(self.colourChangeCtrl)
        grid.Add(self.colourChangeCtrl, (4,1), flag=wx.EXPAND)
        
        #default_expect_fc
        label = wx.StaticText(self, -1, "    Expected first crack")
        grid.Add(label, (5,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.firstCrackCtrl = wx.TextCtrl(self, -1, str(self.options.getUserOption("default_expect_fc")))
        self.temperature_ctrls.append(self.firstCrackCtrl)
        grid.Add(self.firstCrackCtrl, (5,1), flag=wx.EXPAND)
        
        label = wx.StaticText(self, -1, "Line width")
        grid.Add(label, (6,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.lineWidthCtrl = wx.SpinCtrl(self, size=(spinWidth,-1),min=1, max=10, value=str(self.options.getUserOption("linewidth")))
        grid.Add(self.lineWidthCtrl, (6,1))
        
        label = wx.StaticText(self, -1, "ROR y-axis multiplier")
        grid.Add(label, (7,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.rorMultiplierCtrl = wx.SpinCtrl(self, size=(spinWidth,-1),min=1, max=20, value=str(self.options.getUserOption("ror_multiplier")))
        grid.Add(self.rorMultiplierCtrl, (7,1))
        
        label = wx.StaticText(self, -1, "ROR smoothing of logs (secs)")
        grid.Add(label, (8,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.rorSmoothingCtrl = wx.SpinCtrl(self, size=(spinWidth,-1),min=1, max=90, value=str(self.options.getUserOption("ror_smoothing")))
        grid.Add(self.rorSmoothingCtrl, (8,1))

        label = wx.StaticText(self, -1, "Show second derivative with ROR")
        grid.Add(label, (9,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.showSecondDerivative = wx.CheckBox(self, -1)
        grid.Add(self.showSecondDerivative, (9,1), flag=wx.ALIGN_LEFT)
        self.showSecondDerivative.SetValue(self.options.getUserOption("show_second_derivative") == "yes")

        label = wx.StaticText(self, -1, "Legend font size (points)")
        grid.Add(label, (10,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.legendFontSizeCtrl = wx.SpinCtrl(self, size=(spinWidth,-1),min=6, max=18, value=str(self.options.getUserOption("legend_font_size")))
        grid.Add(self.legendFontSizeCtrl, (10,1))
        
        label = wx.StaticText(self, -1, "Show tips at startup")
        grid.Add(label, (11,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.tipsCtrl = wx.CheckBox(self, -1)
        if "showtips" not in list(self.options.options.keys()) or self.options.options["showtips"] == "yes":
            self.tipsCtrl.SetValue(True)
            self.originalShowTips = True
        else:
            self.tipsCtrl.SetValue(False)
            self.originalShowTips = False
        grid.Add(self.tipsCtrl, (11,1), flag=wx.ALIGN_LEFT)

        label = wx.StaticText(self, -1, "Zoom on mouse wheel and scroll gesture")
        grid.Add(label, (12,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.zoomOnWheelCtrl = wx.CheckBox(self, -1)
        grid.Add(self.zoomOnWheelCtrl, (12,1), flag=wx.ALIGN_LEFT)
        self.zoomOnWheelCtrl.SetValue(self.options.getUserOption("zoom_on_mouse_wheel") == "yes")

        label = wx.StaticText(self, -1, "Automatically check for updates")
        grid.Add(label, (13,0), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.automaticUpdateCheck = wx.CheckBox(self, -1)
        grid.Add(self.automaticUpdateCheck, (13,1), flag=wx.ALIGN_LEFT)
        self.automaticUpdateCheck.SetValue(self.options.getUserOption("automatic_check_for_updates") == "yes")

        label = wx.StaticText(self, -1, "Temperature unit")
        box.Add(label, 0, wx.LEFT | wx.TOP | wx.ALIGN_LEFT, 10)
        self.radioCelcius = wx.RadioButton(self, style=wx.RB_GROUP, label="Celcius", name="celcius")
        self.radioFahrenheit = wx.RadioButton(self, label="Fahrenheit", name="fahrenheit")
        box.Add(self.radioCelcius, 0, wx.LEFT | wx.ALIGN_LEFT, 20)
        box.Add(self.radioFahrenheit, 0, wx.LEFT | wx.ALIGN_LEFT, 20)
        self.temperature_unit = self.options.getUserOption("temperature_unit", default="C")
        if self.temperature_unit == "C":  self.radioCelcius.SetValue(True)
        else: self.radioFahrenheit.SetValue(True)
        self.radioCelcius.Bind(wx.EVT_RADIOBUTTON, self.onTemperatureUnitChange)
        self.radioFahrenheit.Bind(wx.EVT_RADIOBUTTON, self.onTemperatureUnitChange)

        label = wx.StaticText(self, -1, "Position of USB save button")
        box.Add(label, 0, wx.LEFT | wx.TOP | wx.ALIGN_LEFT, 10)
        self.radioInToolbar = wx.RadioButton(self, style=wx.RB_GROUP, label="In tabs", name="usb-top")
        self.radioBottomRight = wx.RadioButton(self, label="Bottom right corner", name="usb-bottom")
        box.Add(self.radioInToolbar, 0, wx.LEFT | wx.ALIGN_LEFT, 20)
        box.Add(self.radioBottomRight, 0, wx.LEFT | wx.ALIGN_LEFT, 20)
        usb_pos = self.options.getUserOption("usb-button-position", default="bottom")
        if usb_pos == "top":  self.radioInToolbar.SetValue(True)
        else: self.radioBottomRight.SetValue(True)

        label = wx.StaticText(self, -1, "Position of phases panel")
        box.Add(label, 0, wx.LEFT | wx.TOP | wx.ALIGN_LEFT, 10)
        self.radioPhasesLeft = wx.RadioButton(self, style=wx.RB_GROUP, label="Left", name="phases-left")
        self.radioPhasesRight = wx.RadioButton(self, label="Right", name="phases-right")
        box.Add(self.radioPhasesLeft, 0, wx.LEFT | wx.ALIGN_LEFT, 20)
        box.Add(self.radioPhasesRight, 0, wx.LEFT | wx.ALIGN_LEFT, 20)
        phases_pos = self.options.getUserOption("phases-panel-position", default="right")
        if phases_pos == "left":  self.radioPhasesLeft.SetValue(True)
        else: self.radioPhasesRight.SetValue(True)

        self.addButtons(box, grid, self.onGeneralApply)

    def addButtons(self, box, grid, apply_func):
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        applyButton = wx.Button(self, label='OK')
        cancelButton = wx.Button(self, label='Cancel')
        buttons.Add(applyButton, 1, wx.ALL, 7) # Mac buttons need 7-pixel borders or they overlap
        buttons.Add(cancelButton, 1, wx.ALL, 7)
        box.Add(grid, 0, wx.ALL, 10)
        box.Add(buttons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.SetSizeHints(self)
        self.SetSizer(box)
        applyButton.Bind(wx.EVT_BUTTON, apply_func)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
        applyButton.SetDefault()
        if not core_studio.isLinux: self.Raise()

    def onTemperatureUnitChange(self, e):
        """
        Just update this dialog box, because the user has not yet pressed ok.
        Any updating of the actual data and the rest of the UI will take place
        in the onGeneralApply function.
        """
        previous = self.temperature_unit
        if self.radioCelcius.GetValue():
            self.temperature_unit = "C"
        else:
            self.temperature_unit = "F"
        for widget in self.temperature_labels:
            txt = widget.GetLabel()
            txt = re.sub('°(C|F)', '°' + self.temperature_unit, txt)
            widget.SetLabel(txt)
        for widget in self.temperature_ctrls:
            val = widget.GetValue()
            if val != '':
                celcius = temperature.convertSpecifiedUnitToCelcius(val, previous)
                converted = temperature.convertCelciusToSpecifiedUnit(celcius, self.temperature_unit)
                widget.SetValue(str(converted))
        e.Skip()

    def onGeneralApply(self, e):
        self.options.options["default_expect_colrchange"] = str(self.colourChangeCtrl.GetValue()) if utilities.floatOrNone(self.colourChangeCtrl.GetValue()) is not None else ''
        self.options.options["default_expect_fc"] = str(self.firstCrackCtrl.GetValue()) if utilities.floatOrNone(self.firstCrackCtrl.GetValue()) is not None else ''
        self.options.options["phase1_name"] = self.phase1.GetValue()
        self.options.options["phase2_name"] = self.phase2.GetValue()
        self.options.options["phase3_name"] = self.phase3.GetValue()
        if self.radioFahrenheit.GetValue():
            temperature_unit = "F"
        else:
            temperature_unit = "C"
        temperature_unit_has_changed = self.options.options["temperature_unit"] != temperature_unit
        if self.radioInToolbar.GetValue():
            self.options.options["usb-button-position"] = "top"
        else:
            self.options.options["usb-button-position"] = "bottom"
        if self.radioPhasesLeft.GetValue():
            self.options.options["phases-panel-position"] = "left"
        else:
            self.options.options["phases-panel-position"] = "right"
        if self.zoomOnWheelCtrl.GetValue():
            self.options.options["zoom_on_mouse_wheel"] = "yes"
        else:
            self.options.options["zoom_on_mouse_wheel"] = "no"
        if self.showSecondDerivative.GetValue():
            self.options.options["show_second_derivative"] = "yes"
        else:
            self.options.options["show_second_derivative"] = "no"
        if self.automaticUpdateCheck.GetValue():
            self.options.options["automatic_check_for_updates"] = "yes"
        else:
            self.options.options["automatic_check_for_updates"] = "no"

        if self.tipsCtrl.GetValue():
            self.options.options["showtips"] = "yes"
        else:
            self.options.options["showtips"] = "no"
        if not self.originalShowTips and self.tipsCtrl.GetValue():
            wx.CallAfter(handleTips, self.parent, self.parent.TipOfTheDay)

        self.options.options["linewidth"] = str(self.lineWidthCtrl.GetValue())
        self.options.options["ror_multiplier"] = str(self.rorMultiplierCtrl.GetValue())
        self.options.options["ror_smoothing"] = str(self.rorSmoothingCtrl.GetValue())
        self.options.options["legend_font_size"] = str(self.legendFontSizeCtrl.GetValue())
        if temperature_unit_has_changed:
            updateTemperatureUnit(self.parent, temperature_unit)
            self.options.options["temperature_unit"] = temperature_unit
        self.options.refreshPanelsFromOptions(self.parent)
        self.options.saveUserOptions()
        self.Close()
                
    def onCancel(self, e):
        self.Close()
        
def updateTemperatureUnit(frame, temperature_unit):
    tab = frame.notebook.GetSelection()
    if frame.fileType == "profile":
        datastring = core_studio.dataObjectsToString(frame)
    else:
        datastring = frame.appendUserEnteredDataToLogData()
    temperature.setTemperatureUnit(temperature_unit)
    frame.openFromString(frame, core_studio.DEFAULT_DATA, datastring)
    frame.loadComparisons()
    frame.updateWithNewTemperatureUnit()
    frame.notebook.SetSelection(tab)


########################################################################

class UserOptions():
    def __init__(self, frame):
        self.frame = frame
        self.options = {}
        projectname = core_studio.PROGRAM_NAME
        formerprojectname = core_studio.PROGRAM_FORMERLY_KNOWN_AS
        if core_studio.isWindows:
            homedir = "{}\\".format(os.getenv('APPDATA'))
            projectdir = "{0}{1}".format(homedir,projectname)
            formerprojectdir = "{0}{1}".format(homedir,formerprojectname)
        else:
            homedir = "{}/".format(os.path.expanduser("~"))
            projectdir = "{0}.{1}".format(homedir,projectname)
            formerprojectdir = "{0}.{1}".format(homedir,formerprojectname)

        # migrate from former         
        if os.path.isdir(formerprojectdir):
            try:
                os.rename(formerprojectdir, projectdir)
            except:
                pass

        if not os.path.isdir(projectdir):
            try:
                os.mkdir(projectdir)
            except:
                pass

        self.fileName = projectdir + os.sep + 'config'
        self.programDataFolder = projectdir
        # print self.fileName
        with fileCheckingLock:
            self.optionsFileTimeStamp = None
        self.refreshOptionsFromFile()

    def refreshOptionsFromFile(self):
        try:
            with open(self.fileName, 'r') as infile:
                datastring = infile.read().decode('utf-8')
            with fileCheckingLock:
                self.optionsFileTimeStamp = os.path.getmtime(self.fileName)
        except:
            datastring = ""
        for line in datastring.split("\n"):
            elements = line.split(":")
            if len(elements) >= 2:
                key = elements[0]
                value = ":".join(elements[1:])
                self.options[key] = value
        # print self.options

    def refreshOptionsFull(self):
        self.refreshOptionsFromFile()
        temperature_unit = self.frame.options.options["temperature_unit"]
        if temperature.getTemperatureUnit() != temperature_unit:
            updateTemperatureUnit(self.frame, temperature_unit)
        self.refreshPanelsFromOptions(self.frame)

    def refreshPanelsFromOptions(self, frame):
        frame.page1.phasesObject.phase1.GetItem(0).GetWindow().SetLabel(frame.options.options["phase1_name"])
        frame.page1.phasesObject.phase2.GetItem(0).GetWindow().SetLabel(frame.options.options["phase2_name"])
        frame.page1.phasesObject.phase3.GetItem(0).GetWindow().SetLabel(frame.options.options["phase3_name"])
        if frame.fileType == 'log':
            frame.logPanel.phasesObject.phase1.GetItem(0).GetWindow().SetLabel(frame.options.options["phase1_name"])
            frame.logPanel.phasesObject.phase2.GetItem(0).GetWindow().SetLabel(frame.options.options["phase2_name"])
            frame.logPanel.phasesObject.phase3.GetItem(0).GetWindow().SetLabel(frame.options.options["phase3_name"])
        where = frame.notebook.GetPage(frame.notebook.GetSelection())

        panelIndex = 1 if frame.options.options["phases-panel-position"] == "right" else 0
        if not isinstance(frame.page1.chartSizer.GetItem(panelIndex).GetWindow(), wx.lib.scrolledpanel.ScrolledPanel):
            # swap the two items in the sizer
            if panelIndex == 0:
                panel = frame.page1.chartSizer.GetItem(1).GetWindow()
                frame.page1.chartSizer.Detach(1)
                frame.page1.chartSizer.Insert(0, panel)
            if panelIndex == 1:
                panel = frame.page1.chartSizer.GetItem(0).GetWindow()
                frame.page1.chartSizer.Detach(0)
                frame.page1.chartSizer.Add(panel)
            frame.page1.chartSizer.Layout()
            if frame.fileType == 'log':
                frame.updateLogPanels()

        frame.setupMouseWheel()

        frame.recentFileList = textToListOfStrings(frame.options.getUserOption("recentfiles"))
        frame.buildRecentFileMenu()


        if hasattr(frame, 'datastring') and frame.datastring is not None and frame.datastring != '':
            eventNames = frame.logData.roastEventNames
            eventData = frame.logData.roastEventData
            profile, log = core_studio.splitProfileFromLog(frame.datastring) # also picks up any incidentals from the log and appends them to the profile
            frame.logData = core_studio.stringToLogData(log, frame) # this re-scales the RoR elements, also gives them default enable state
            frame.logData.roastEventNames = eventNames
            frame.logData.roastEventData = eventData
            if hasattr(frame, 'logPanel') and frame.logPanel is not None: frame.logPanel.updateEnableStatusOfAllPlotLines()

        frame.lineWidth = int(frame.options.getUserOption("linewidth"))
        frame.legendFontSize = int(frame.options.getUserOption("legend_font_size"))
        frame.temperature_unit = frame.options.getUserOption("temperature_unit", default="C")

        if hasattr(where, 'reDraw'):
            where.reDraw()
        frame.onResize(None)

        frame.updateDifficulty()

    def editGeneralOptions(self, frame):
        dialog = editOptionsDialog(frame, self, 'general')
        dialog.ShowModal()
        dialog.Destroy()

    def editCompareOptions(self, frame):
        dialog = editOptionsDialog(frame, self, 'compare')
        dialog.ShowModal()
        dialog.Destroy()

    def saveUserOptions(self):
        newstring = "\n".join([key + ':' + self.options[key] for key in list(self.options.keys())])
        try:
            with fileCheckingLock:
                with open(self.fileName, 'w') as output:
                    output.write(newstring.encode('utf8'))
                self.optionsFileTimeStamp = os.path.getmtime(self.fileName)
        except:
            pass


    def getUserOption(self, name, default=None):
        """
        The default is used for when the user has never set this particular option i.e. a new install or an option that is new to the latest release.
        If default is not given as a parameter it comes from DEFAULT_OPTIONS, and failing that it comes back as the empty string.
        If the default is used the option is also saved.
        """
        if name in list(self.options.keys()):
            return self.options[name]
        else:
            if default is None:
                if name in list(DEFAULT_OPTIONS.keys()):
                    default = DEFAULT_OPTIONS[name]
                else:
                    default = ''
            self.setUserOption(name, default)
            return default

    def getUserOptionBoolean(self, name, default=False):
        opt = self.getUserOption(name, default=str(default))
        if opt.lower() == 'true': return True
        else: return False
        
    def setUserOptionBoolean(self, name, value):
        self.setUserOption(name, 'True' if value else 'False')
        
    def setUserOption(self, name, value):
        """
        Sets and saves.
        """
        if name not in list(self.options.keys()) or self.options[name] != value:
            # print 'saving', name, '='
            # print self.options[name]
            # print value
            self.options[name] = value
            self.saveUserOptions()

"""
Usage: don't use : in option names

myOptions = UserOptions()
myOptions.options["test"] = "testing:123"
myOptions.options["test two"] = "testing: 123"
myOptions.saveUserOptions()
"""

def getPosSizeFromOptions(options):
    defaultPos = (10, 30) if core_studio.isMac else (0, 0)
    defaults = [defaultPos, (wx.DisplaySize()[0]*0.75, wx.DisplaySize()[1]*0.75)]
    dims = options.getUserOption("window-dims", default=str(defaults))
    dims = textToListOf2Tuples(dims)
    # is window off screen?
    if len(dims) >=2:
        if dims[0][0] + 30 > wx.DisplaySize()[0] or dims[0][1] + 50 > wx.DisplaySize()[1] or \
            dims[0][0] + dims[1][0] < 30 or dims[0][1] + dims[1][1] < 50:
            dims = defaults
        return dims
    else:
        return defaults
    
def saveSizeToOptions(window, options):
    if window.IsIconized():
        return
    if window.IsMaximized() or window.fullscreen or (core_studio.isMac and window.GetScreenPositionTuple()[1] <= 0):
        options.setUserOption("window-maximized", "True")
        return
    pos = window.GetScreenPosition()
    siz = window.GetSize()
    dims = str([pos.Get(), siz.Get()])
    options.setUserOption("window-maximized", "False")
    options.setUserOption("window-dims", dims)

fileCheckingLock = threading.Lock()
fileCheckingWorker = None

def startFileCheckingThread(frame, obj, callbackOptionsChange, callbackFileChange):
    global fileCheckingWorker
    fileCheckingWorker = (frame, obj, callbackOptionsChange, callbackFileChange, FileCheckingThread(frame, obj, callbackOptionsChange, callbackFileChange))
    fileCheckingWorker[4].start()
    frame.fileCheckingWatchdogTimer = utilities.SafeTimer(frame)
    frame.Bind(wx.EVT_TIMER, onFileCheckingWatchdogTimer, frame.fileCheckingWatchdogTimer)
    frame.fileCheckingWatchdogTimer.Start(5000)

def onFileCheckingWatchdogTimer(e):
    """
    There is a suspicion that during sleep the thread might sometimes close. This check prevents that possibility,
    however remote a probability, without doing any harm.
    """
    if not fileCheckingWorker[4].isAlive():
        frame = fileCheckingWorker[0]
        obj = fileCheckingWorker[1]
        callbackOptionsChange = fileCheckingWorker[2]
        callbackFileChange = fileCheckingWorker[3]
        frame.fileCheckingWatchdogTimer.Stop()
        frame.fileCheckingWatchdogTimer = None
        startFileCheckingThread(frame, obj, callbackOptionsChange, callbackFileChange)

class FileCheckingThread(threading.Thread):

    def __init__(self, frame, optionsObj, callbackOptionsChange, callbackFileChange):
        threading.Thread.__init__(self)
        self.setName('FileChecking')
        self.callbackOptionsChange = callbackOptionsChange
        self.callbackFileChange = callbackFileChange
        self.optionsObj = optionsObj
        self.frame = frame
        self.canJoin = True

    def run(self):
        """Overrides Thread.run. Don't call this directly its called internally
        when you call Thread.start().
        """
        while not self.frame.app.timeToKillThreads.isSet():
            if core_studio.isMac and self.frame.fullscreen and not self.frame.fullscreenWasActive:
                self.frame.fullscreenWasActive = True
                wx.CallAfter(dialogs.handleFullscreen, self.frame)
            optionsChange = False
            with fileCheckingLock:
                if self.optionsObj.optionsFileTimeStamp is not None:
                    try:
                        optionsChange = os.path.getmtime(self.optionsObj.fileName) > self.optionsObj.optionsFileTimeStamp + 0.1
                    except:
                        pass
            if optionsChange:
                wx.CallAfter(self.callbackOptionsChange)
            fileChange = False
            with fileCheckingLock:
                if self.frame.fileTimeStamp is not None and self.frame.fileName is not None and self.frame.fileName != '':
                    try:
                        fileChange = os.path.getmtime(self.frame.fileName) > self.frame.fileTimeStamp + 0.1
                    except:
                        pass
            if fileChange:
                wx.CallAfter(self.callbackFileChange)
            self.frame.app.timeToKillThreads.wait(0.25)
            try:
                self.frame.GetName()  # terminate the thread when the calling wxPython object has been destroyed
            except wx.PyDeadObjectError:
                break

if __name__ == 'core_studio' and False:
    core_studio = __import__('Kaffelogic Studio')
    core_studio.PROGRAM_NAME = 'test-options'
    class MyFrame(wx.Frame):

        def __init__(self, parent):
            wx.Frame.__init__(self, parent, -1, "Demo")
            self.book = wx.Notebook(self, wx.ID_ANY)
            self.book.AddPage(wx.Panel(self.book), "Hello")
            self.book.AddPage(wx.Panel(self.book), "World")
            self.Bind(wx.EVT_SIZE, self.OnResize)
            self.Bind(wx.EVT_MOVE, self.OnResize)
            self.myOptions = UserOptions()

        def OnResize(self, event):
            saveSizeToOptions(self, self.myOptions)
            event.Skip()

    # our normal wxApp-derived class, as usual

    app = wx.App(0)

    frame = MyFrame(None)
    app.SetTopWindow(frame)
    frame.Show()

    app.MainLoop()
