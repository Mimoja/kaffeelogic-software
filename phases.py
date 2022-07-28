#coding:utf-8

import wx, utilities, logpanel, core_studio, temperature


class PhasesPanel():
    def initPanel(self, parent, sizer):
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.phasesSizer = wx.BoxSizer(wx.VERTICAL)
        self.parent = parent
        self.panel = wx.lib.scrolledpanel.ScrolledPanel(parent,-1)
        self.panel.SetupScrolling(scroll_x=False)
        self.initPhasesSizer(self.panel)
        self.enableEventEditing()
        self.panel.Layout()
        panelSizer.Add(self.phasesSizer, 0, wx.LEFT | wx.RIGHT, 25)
        sizer.Add(self.panel, 0, wx.TOP | wx.BOTTOM, 5)
        self.panel.SetSizerAndFit(panelSizer)
        self.parent.configControls['expect_colrchange'] = self.phasesControls["colour_change_Temperature"]
        self.parent.configControls['expect_fc'] = self.phasesControls["first_crack_Temperature"]
        return self.panel

    def phasesAddRow(self, panel, grid, groupName, rowName):
        label = wx.StaticText(panel, -1, rowName, size=(100, -1))
        grid.Add(label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        name = groupName + "_" + rowName
        if name == "colour_change_Temperature":
            controlName = "expect_colrchange"
            bindFocus = True
        elif name == "first_crack_Temperature":
            controlName = "expect_fc"
            bindFocus = True
        else:
            controlName = rowName
            bindFocus = False
        TEXTCTRL_WIDTH = 70 if core_studio.isLinux else 65
        value = wx.TextCtrl(panel, -1, "", name=controlName, size=(TEXTCTRL_WIDTH, -1))
        self.phasesControls[name] = value
        value.Enable(False)
        grid.Add(value, 0, wx.EXPAND)
        if bindFocus:
            value.Bind(wx.EVT_KEY_DOWN, self.onFocus) # we use EVT_KEY_DOWN as a proxy for focus, esp Linux sends unwanted SET_FOCUS events which messes with the capture process!
            value.Bind(wx.EVT_KILL_FOCUS, self.onKillFocus)

    def onChangePhase(self, event):
        self.parent.frame.captureHistory(self.parent, 'capture', calledFromTextChange=True)
        self.parent.frame.txtChange(self.parent, event.EventObject, applyLinuxFix=True) # known issue for Linux insertion point in EVT_TEXT handler
        self.parent.frame.modified(True)
        self.parent.reDraw()

    def onKillFocus(self, event):
        if self.parent.focusObject is event.EventObject:
            self.parent.focusObject = None
        event.Skip()
        
    def onFocus(self, event):
        keycode = event.GetKeyCode()
        event.Skip() 
        if keycode in [0, 396, 306, 307, 308, 314, 315, 316, 317]: return # fn, Mac-control, shift, alt, control/command, arrow
        if self.parent.focusObject is event.EventObject: return
        self.parent.frame.captureHistory(self.parent, 'capture', calledFromTextChange=True)
        self.parent.frame.focus(self.parent, event.EventObject)

    def enableEventEditing(self):
        enable = self.parent.frame.fileType == 'profile' or self.parent.title == "Log"
        self.phasesControls["colour_change_Temperature"].Unbind(wx.EVT_TEXT)
        self.phasesControls["first_crack_Temperature"].Unbind(wx.EVT_TEXT)
        self.phasesControls["colour_change_Temperature"].Enable(enable)
        self.phasesControls["first_crack_Temperature"].Enable(enable)
        if enable:
            self.phasesControls["colour_change_Temperature"].Bind(wx.EVT_TEXT, self.onChangePhase)
            self.phasesControls["first_crack_Temperature"].Bind(wx.EVT_TEXT, self.onChangePhase)
        
    def phasesAddPhase(self, panel, sizer, phaseName, phaseTitle):
        phaseSizer = wx.BoxSizer(wx.VERTICAL)
        self.addLabelBold(panel, phaseSizer, phaseTitle)
        grid = wx.FlexGridSizer(3, 2, 5, 5)
        self.phasesAddRow(panel, grid, phaseName, "Duration")
        self.phasesAddRow(panel, grid, phaseName, "Percent")
        self.phasesAddRow(panel, grid, phaseName, "Increase")
        phaseSizer.Add(grid)
        sizer.Add(phaseSizer)
        self.phasesControls[phaseName] = phaseSizer
        return phaseSizer
        
    def phasesAddEvent(self, panel, sizer, eventName):
        grid = wx.FlexGridSizer(2, 2, 5, 5)
        self.phasesAddRow(panel, grid, eventName, "Temperature")
        self.phasesAddRow(panel, grid, eventName, "Time")
        sizer.Add(grid)
        return grid

    def addLabelBold(self, panel, sizer, text):
        label = wx.StaticText(panel, -1, text)
        font = label.GetFont()
        font.SetWeight(wx.BOLD)
        label.SetFont(font)
        sizer.Add(label, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
        return label

    def initPhasesSizer(self, panel):
        if isinstance(self.parent, logpanel.LogPanel):
            event_descriptor = "Logged"
            end_descriptor = "Logged"
        else:
            event_descriptor = "Expected"
            end_descriptor = "Recommended"
            
        self.phasesControls = {}
        self.phase1 = self.phasesAddPhase(panel, self.phasesSizer, "phase1", self.parent.frame.options.getUserOption("phase1_name"))
        self.addLabelBold(panel, self.phasesSizer, event_descriptor + " colour change")
        self.phasesAddEvent(panel, self.phasesSizer, "colour_change")
        self.phase2 = self.phasesAddPhase(panel, self.phasesSizer, "phase2", self.parent.frame.options.getUserOption("phase2_name"))
        self.addLabelBold(panel, self.phasesSizer, event_descriptor + " first crack")
        self.phasesAddEvent(panel, self.phasesSizer, "first_crack")
        self.phase3 = self.phasesAddPhase(panel, self.phasesSizer, "phase3", self.parent.frame.options.getUserOption("phase3_name"))
        self.addLabelBold(panel, self.phasesSizer, end_descriptor + " roast end")
        self.phasesAddEvent(panel, self.phasesSizer, "roast_end")

    def setPhasesFromLogData(self, initialising, updateColrChangeAndFC=True):
        colour_change_point = self.parent.frame.logData.roastEventData[self.parent.frame.logData.roastEventNames.index("colour_change")] if "colour_change" in self.parent.frame.logData.roastEventNames else None        
        colour_change_time = colour_change_point[0] if colour_change_point is not None else None
        colour_change_temperature = round(colour_change_point[1], 1) if colour_change_point is not None else None
        first_crack_point = self.parent.frame.logData.roastEventData[self.parent.frame.logData.roastEventNames.index("first_crack")] if "first_crack" in self.parent.frame.logData.roastEventNames else None        
        first_crack_time = first_crack_point[0] if first_crack_point is not None else None
        first_crack_temperature = round(first_crack_point[1], 1) if first_crack_point is not None else None
        roast_end_point = self.parent.frame.logData.roastEventData[self.parent.frame.logData.roastEventNames.index("roast_end")] if "roast_end" in self.parent.frame.logData.roastEventNames else None        
        roast_end_time = roast_end_point[0] if roast_end_point is not None else None
        roast_end_temperature = round(roast_end_point[1], 1) if roast_end_point is not None else None
        if roast_end_time is None and "development_percent" in self.parent.frame.configuration.keys():
            dtr = utilities.floatOrNone(self.parent.frame.configuration["development_percent"])
            fc = utilities.floatOrNone(utilities.fromMinSec(self.parent.frame.configuration["first_crack"]))
            if dtr is not None and fc is not None:
                roast_end_time = fc / (1.0 - dtr / 100.0)
                temperature_taken_from_time = roast_end_time - core_studio.MASTER_COLUMN_OFFSETS[self.parent.frame.logData.masterColumn]
                points = [point for point in self.parent.frame.logData.ySeriesRaw[self.parent.frame.logData.masterColumn] if point[0] >= temperature_taken_from_time]
                if len(points) > 0:
                        roast_end_temperature = round(points[0][1], 1)

        self.phasesControls["colour_change_Time"].ChangeValue(utilities.toMinSec(colour_change_time) if colour_change_time is not None else "")
        self.phasesControls["first_crack_Time"].ChangeValue(utilities.toMinSec(first_crack_time) if first_crack_time is not None else "")
        self.phasesControls["roast_end_Time"].ChangeValue(utilities.toMinSec(roast_end_time) if roast_end_time is not None else "")
        if updateColrChangeAndFC:
            self.phasesControls["colour_change_Temperature"].ChangeValue((unicode(colour_change_temperature) +
                                                                          temperature.insertTemperatureUnit(u'°')) if colour_change_temperature is not None else "")
            self.phasesControls["first_crack_Temperature"].ChangeValue((unicode(first_crack_temperature) +
                                                                        temperature.insertTemperatureUnit(u'°')) if first_crack_temperature is not None else "")
        self.phasesControls["roast_end_Temperature"].ChangeValue((unicode(roast_end_temperature) +
                                                                  temperature.insertTemperatureUnit(u'°')) if roast_end_temperature is not None else "")
        if initialising:
            self.initial_colour_change_temperature = colour_change_temperature
            self.initial_first_crack_temperature = first_crack_temperature
            self.initial_colour_change_time = colour_change_time
            self.initial_first_crack_time = first_crack_time
        start_temperature = self.parent.frame.page1.pointsAsGraphed[0][1]
        start_time = self.parent.frame.page1.pointsAsGraphed[0][0]
        self.recalculatePercentages(start_time, start_temperature, colour_change_time, colour_change_temperature, first_crack_time, first_crack_temperature, roast_end_time, roast_end_temperature)
        
    def setPhasesFromProfileData(self):
        colour_change_temp = utilities.replaceZeroWithBlank(self.parent.frame.configuration['expect_colrchange']) \
                             if 'expect_colrchange' in self.parent.frame.configuration.keys() else ''
        first_crack_temp = utilities.replaceZeroWithBlank(self.parent.frame.configuration['expect_fc']) \
                             if 'expect_fc' in self.parent.frame.configuration.keys() else ''
        if colour_change_temp == '':
            colour_change_temp = self.parent.frame.options.getUserOption("default_expect_colrchange")
        if first_crack_temp == '':
            first_crack_temp = self.parent.frame.options.getUserOption("default_expect_fc")
        self.setColourChange(colour_change_temp)
        self.setFirstCrack(first_crack_temp)
        self.recalculateProfilePhases()
        
    def setColourChange(self, colour_change_temp):
        self.phasesControls["colour_change_Temperature"].ChangeValue(temperature.removeTemperatureUnit(unicode(colour_change_temp)))

    def setFirstCrack(self, first_crack_temp):
        self.phasesControls["first_crack_Temperature"].ChangeValue(temperature.removeTemperatureUnit(unicode(first_crack_temp)))

    def getColourChangeControl(self):
        return self.phasesControls["colour_change_Temperature"]

    def getColourChange(self):
        return utilities.filterNumeric(self.phasesControls["colour_change_Temperature"].GetValue())

    def getColourChangeTime(self):
        return utilities.floatOrNone(utilities.fromMinSec(self.phasesControls["colour_change_Time"].GetValue()))

    def getFirstCrackControl(self):
        return self.phasesControls["first_crack_Temperature"]

    def getFirstCrack(self):
        return utilities.filterNumeric(self.phasesControls["first_crack_Temperature"].GetValue())

    def getFirstCrackTime(self):
        return utilities.floatOrNone(utilities.fromMinSec(self.phasesControls["first_crack_Time"].GetValue()))

    def getRoastEnd(self):
        return self.phasesControls["roast_end_Temperature"].GetValue()

    def getRoastEndTime(self):
        return utilities.floatOrNone(utilities.fromMinSec(self.phasesControls["roast_end_Time"].GetValue()))


    def profileTimeFromTemperature(self, temperature):
        if temperature is None: return ''
        for p in self.parent.pointsAsGraphed:
            if round(p[1],1) >= temperature:
                return p[0]
        return None

    def setPhaseData(self, phaseName, duration, overall, rise):
        self.phasesControls[phaseName + "_Duration"].SetValue(utilities.toMinSec(duration))
        self.phasesControls[phaseName + "_Percent"].SetValue((unicode(round(float(duration)/overall*100.0, 1)) + '%') if overall != 0.0 else '')
        self.phasesControls[phaseName + "_Increase"].SetValue(unicode(round(rise, 1)) + temperature.insertTemperatureUnit(u'°', self.parent.frame.temperature_unit))
        self.phasesControls[phaseName].ShowItems(True)
        self.panel.Layout()

    def clearPhaseData(self, phaseName):
        for control in ["_Duration", "_Percent", "_Increase"]:
            self.phasesControls[phaseName + control].SetValue('')
        self.phasesControls[phaseName].ShowItems(False)
        self.panel.Layout()

    def recalculateLogPhases(self):
        cc_temp = utilities.floatOrNone(utilities.filterNumeric(self.phasesControls["colour_change_Temperature"].GetValue()))
        fc_temp = utilities.floatOrNone(utilities.filterNumeric(self.phasesControls["first_crack_Temperature"].GetValue()))
        cc_time = None
        fc_time = None
        if cc_temp is not None:
            time_taken_from_temperature = cc_temp
            if self.initial_colour_change_temperature is not None and round(self.initial_colour_change_temperature, 1) == round(cc_temp, 1):
                cc_time = self.initial_colour_change_time # use the stored value just in case the temperature curve decreases at some point, this ensure the logged time is retained
            else:
                points = [point for point in self.parent.frame.logData.ySeriesRaw[self.parent.frame.logData.masterColumn] if point[1] >= time_taken_from_temperature - 0.05]
                if len(points) > 0:
                    point = points[0]            
                    cc_time = point[0]
        if fc_temp is not None:
            time_taken_from_temperature = fc_temp
            if self.initial_first_crack_temperature is not None and round(self.initial_first_crack_temperature, 1) == round(fc_temp, 1):
                fc_time = self.initial_first_crack_time
            else:
                points = [point for point in self.parent.frame.logData.ySeriesRaw[self.parent.frame.logData.masterColumn] if point[1] >= time_taken_from_temperature - 0.05]
                if len(points) > 0:
                    point = points[0]            
                    fc_time = point[0]

        if cc_temp is not None and cc_time is not None:
            if "colour_change" in self.parent.frame.logData.roastEventNames:
                self.parent.frame.logData.roastEventData[self.parent.frame.logData.roastEventNames.index("colour_change")] = (cc_time, cc_temp)
            else:
                self.parent.frame.logData.roastEventNames.append("colour_change")
                self.parent.frame.logData.roastEventData.append((cc_time, cc_temp))
        else:
            if "colour_change" in self.parent.frame.logData.roastEventNames:
                loc = self.parent.frame.logData.roastEventNames.index("colour_change")
                self.parent.frame.logData.roastEventNames.pop(loc)
                self.parent.frame.logData.roastEventData.pop(loc)

        if fc_temp is not None and fc_time is not None:
            if "first_crack" in self.parent.frame.logData.roastEventNames:
                self.parent.frame.logData.roastEventData[self.parent.frame.logData.roastEventNames.index("first_crack")] = (fc_time, fc_temp)
            else:
                self.parent.frame.logData.roastEventNames.append("first_crack")
                self.parent.frame.logData.roastEventData.append((fc_time, fc_temp))
        else:
            if "first_crack" in self.parent.frame.logData.roastEventNames:
                loc = self.parent.frame.logData.roastEventNames.index("first_crack")
                self.parent.frame.logData.roastEventNames.pop(loc)
                self.parent.frame.logData.roastEventData.pop(loc)
        
        self.setPhasesFromLogData(initialising=False, updateColrChangeAndFC=False)
    
    def recalculateProfilePhases(self):
        start_temp = self.parent.pointsAsGraphed[0][1]
        cc_temp = utilities.floatOrNone(self.phasesControls["colour_change_Temperature"].GetValue())
        fc_temp = utilities.floatOrNone(self.phasesControls["first_crack_Temperature"].GetValue())
        end_temp = utilities.floatOrNone(utilities.filterNumeric(self.parent.level_temperature.GetLabel()))
        start_time = self.profileTimeFromTemperature(start_temp)
        cc_time = self.profileTimeFromTemperature(cc_temp)
        fc_time = self.profileTimeFromTemperature(fc_temp)
        end_time = self.profileTimeFromTemperature(end_temp)
        
        #set the event times
        self.phasesControls["colour_change_Time"].SetValue(utilities.toMinSec(cc_time))
        self.phasesControls["first_crack_Time"].SetValue(utilities.toMinSec(fc_time))
        self.phasesControls["roast_end_Time"].SetValue(utilities.toMinSec(end_time))
        self.phasesControls["roast_end_Temperature"].SetValue((unicode(round(end_temp, 1)) +
                                    temperature.insertTemperatureUnit(u'°', self.parent.frame.temperature_unit)) if end_temp is not None else "")

        self.recalculatePercentages(start_time, start_temp, cc_time, cc_temp, fc_time, fc_temp, end_time, end_temp)

    def recalculatePercentages(self, start_time, start_temp, cc_time, cc_temp, fc_time, fc_temp, end_time, end_temp):
        #set the phase data
        if utilities.allNotNone([cc_time, start_time, end_time, cc_temp, start_temp]):
            self.setPhaseData("phase1", cc_time - start_time, end_time - start_time, cc_temp - start_temp)
        else:
            self.clearPhaseData("phase1")
        if utilities.allNotNone([fc_time, cc_time, start_time, end_time, fc_temp, cc_temp]):
            self.setPhaseData("phase2", fc_time - cc_time, end_time - start_time, fc_temp - cc_temp)
        else:
            self.clearPhaseData("phase2")
        if utilities.allNotNone([fc_time, start_time, end_time, end_temp, fc_temp]):
            self.setPhaseData("phase3", end_time - fc_time, end_time - start_time, end_temp - fc_temp)
        else:
            self.clearPhaseData("phase3")

    def displayPhaseData(self, nowTime, nowTemperature):
        startTime = self.parent.frame.page1.pointsAsGraphed[0][0]
        startTemp = self.parent.frame.page1.pointsAsGraphed[0][1]

        colourChangeTime = self.getColourChangeTime()
        firstCrackTime = self.getFirstCrackTime()
        colourChangeTemp = utilities.floatOrZero(self.getColourChange())
        firstCrackTemp = utilities.floatOrZero(self.getFirstCrack())
        refTime = None
        denominatorTime = None
        tempChange = 0
        result = ''
        if colourChangeTime is not None and nowTime < colourChangeTime:
            phaseName = self.parent.frame.options.getUserOption("phase1_name").strip() + " progress"
            refTime = startTime
            tempChange = nowTemperature - startTemp
            denominatorTime = colourChangeTime
        if colourChangeTime is not None and firstCrackTime is not None and nowTime >= colourChangeTime:
            phaseName = self.parent.frame.options.getUserOption("phase2_name").strip() + " progress"
            refTime = colourChangeTime
            tempChange = nowTemperature - colourChangeTemp
            denominatorTime = firstCrackTime - colourChangeTime
        if firstCrackTime is not None and nowTime >= firstCrackTime:
            phaseName = self.parent.frame.options.getUserOption("phase3_name").strip() + " (DTR)"
            refTime = firstCrackTime
            tempChange = nowTemperature - firstCrackTemp
            denominatorTime = nowTime
        if refTime is not None:
            result = "\n" + phaseName + "\n"
            result += utilities.toMinSec(nowTime - refTime) + " "
            result += str(round((nowTime - refTime) / denominatorTime * 100, 1)) + "% "
            if tempChange >= 0:
                result += "+"
            result += str(round(tempChange, 1)) + temperature.insertTemperatureUnit(u"°")
        return result

