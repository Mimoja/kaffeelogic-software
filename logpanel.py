#coding:utf-8

import wx, phases, utilities, bezier, math, core_studio

import temperature
from plot_enhancements import EnhancedPlotCanvas as PlotCanvas
from wx.lib.plot import PlotGraphics, PolyLine, PolyMarker
from plot_enhancements import FilledPolyLine, FilledPolygon

class LogPanel(wx.Panel):

    def __init__(self, parent, frame):
        self.frame = frame
        self.title = "Log"
        wx.Panel.__init__(self, parent)
        self.closest_point = None
        self.closest_distance = None
        self.closest_legend = None
        self.displaySelectedText = None
        self.configControls = {}
        self.resetHistory()
        self.focusObject = None

        # initialise zooming variables
        self.zoomScale = 1
        self.zoomXAxis = None
        self.zoomYAxis = None
        self.expandY = False

        # create some sizers
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.chartSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.optionsSizer = wx.BoxSizer(wx.VERTICAL)
        checkSizer = wx.BoxSizer(wx.HORIZONTAL)

        # create the widgets
        self.standardize = True
        self.canvas = core_studio.myPlotCanvas(self)
        self.canvas.SetEnableHiRes(True)
        self.canvas.SetEnableAntiAliasing(True)
        self.canvas.SetGridColour(core_studio.GRID_COLOUR)

        if frame.options.getUserOption("phases-panel-position") != "left":
            self.chartSizer.Add(self.canvas, 1, wx.EXPAND)
        self.phasesObject = phases.PhasesPanel()
        self.phasesPanel = self.phasesObject.initPanel(self, self.chartSizer)
        self.phasesObject.setPhasesFromLogData(initialising=True)
        self.toggleGrid = self.makeCheckBox("Grid", self.onToggleGrid, default=False)
        self.toggleLegend = self.makeCheckBox("Legend", self.onToggleLegend, default=True)
        self.togglePhases = self.makeCheckBox("Phases", self.onTogglePhases, default=False)
        self.toggleStandardize = self.makeCheckBox("Standard axes", self.onToggleStandardize, default=True)

        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_CTRL | wx.ACCEL_ALT, ord('='), frame.EXPANDYIN_ID)
        ])
        self.canvas.SetAcceleratorTable(accel_tbl)

        self.canvas.canvas.Bind(wx.EVT_LEFT_DOWN, self.onClick)

        # layout the widgets
        if frame.options.getUserOption("phases-panel-position") == "left":
            self.chartSizer.Add(self.canvas, 1, wx.EXPAND)

        self.frame.logOptionsControls = []
        for col in frame.logData.columnHeadings:
            togglePlotLine = wx.CheckBox(self, label=utilities.replaceUnderscoreWithSpace(col))
            togglePlotLine.SetValue(frame.logData.enabled[col])
            togglePlotLine.Bind(wx.EVT_CHECKBOX, self.onTogglePlotLine)
            self.optionsSizer.Add(togglePlotLine, 0, wx.ALL, 5)
            self.frame.logOptionsControls.append(togglePlotLine)
        if frame.logData.hasFanProfile:
            togglePlotLine = wx.CheckBox(self, label='fan speed')
            frame.logData.enabled['fan_speed'] = False
            togglePlotLine.SetValue(False)
            togglePlotLine.Bind(wx.EVT_CHECKBOX, self.onTogglePlotLine)
            self.optionsSizer.Add(togglePlotLine, 0, wx.ALL, 5)
            self.frame.logOptionsControls.append(togglePlotLine)
        if frame.logData.hasFanProfile:
            togglePlotLine = wx.CheckBox(self, label='zones')
            frame.logData.enabled['zones'] = False
            togglePlotLine.SetValue(False)
            togglePlotLine.Bind(wx.EVT_CHECKBOX, self.onTogglePlotLine)
            self.optionsSizer.Add(togglePlotLine, 0, wx.ALL, 5)
            self.frame.logOptionsControls.append(togglePlotLine)
        # Log options are already enabled/disabled according to what was set in the log file.
        # Now we over-ride those settings with saved settings, but only if it applies to the current options.
        allLogOptions = self.frame.options.getUserOption('allLogOptions', '').split(',')
        enabledLogOptions = self.frame.options.getUserOption('enabledLogOptions', '').split(',')
        for cntrl in self.frame.logOptionsControls:
            if cntrl.GetLabel() in allLogOptions:
                cntrl.SetValue(cntrl.GetLabel() in enabledLogOptions)
                self.frame.logData.enabled[utilities.replaceSpaceWithUnderscore(cntrl.GetLabel())] = cntrl.GetValue()

        self.chartSizer.Add(self.optionsSizer, 0, wx.ALL, 5)
        self.chartSizer.Hide(self.optionsSizer)
        self.toggleOptions = self.makeCheckBox("Check boxes", self.onToggleOptions,
                                               default=False)  # Options AKA check boxes. Will show the optionSizer if required by saved user options
        checkSizer.Add(self.toggleGrid, 0, wx.ALL, 5)
        checkSizer.Add(self.toggleLegend, 0, wx.ALL, 5)
        checkSizer.Add(self.togglePhases, 0, wx.ALL, 5)
        checkSizer.Add(self.toggleOptions, 0, wx.ALL, 5)
        checkSizer.Add(self.toggleStandardize, 0, wx.ALL, 5)
        self.mainSizer.Add(self.chartSizer, 1, wx.EXPAND)
        self.mainSizer.Add(checkSizer, 0)
        self.SetSizerAndFit(self.mainSizer)
        self.resetHistoryPart2()
        self.reDraw()

    def resetHistoryPart2(self):
        for control in self.configControls.keys():
            if self.configControls[control].IsEnabled():
                self.history = [core_studio.HistoryConfigEntry(self.configControls[control], isFocusEvent=True)]
                self.historyIndex = 0
                self.historyCanUndo = False
                self.captureFocusEvents = True
                break

    def resetHistory(self):
        self.history = [core_studio.HistoryNullConfigEntry()]
        self.historyIndex = 0
        self.historyCanUndo = False
        self.captureFocusEvents = True

    def reDraw(self):
        frame = self.frame
        colours = frame.logData.colourList
        styles = frame.logData.eventStyles
        self.canvas.SetFontSizeLegend(frame.legendFontSize)
        linesToGraph = []
        if frame.logData.enabled.get('zones'):
            linesToGraph += core_studio.drawZones(self, frame.page1.pointsAsGraphed)

        if hasattr(self, 'phasesObject') and hasattr(self, 'togglePhases') and self.togglePhases.IsChecked():
            self.phasesObject.recalculateLogPhases()
        for col in frame.logData.columnHeadings:
            if col in frame.logData.ySeriesScaled.keys():
                if frame.logData.enabled[col]:
                    linesToGraph.append(PolyLine(frame.logData.ySeriesScaled[col], legend=frame.logData.legends[col],
                                                 colour=colours[0][0], style=colours[0][1], width=frame.lineWidth))
                    frame.logData.colours[col] = colours[0][0]
                colours = colours[1:]

        if frame.logData.enabled.get('fan_speed'):
            points = core_studio.calculatePointsFromProfile(frame, frame.fanProfilePoints, True, 'fit')
            linesToGraph.append(PolyLine(points, legend='fan speed', colour=wx.Colour(0,0,255), style=wx.PENSTYLE_LONG_DASH, width=self.frame.lineWidth))

        if self.closest_point is not None:
            linesToGraph.append(PolyMarker([self.closest_point.toTuple()],
                                           legend='',
                                           colour=frame.logData.legendToColour(frame.logData.legendToColumnName(self.closest_legend),
                                                                 styles),
                                           marker='cross', size=1.5 * self.frame.markerSize, fillstyle=wx.TRANSPARENT))
        for i in range(len(frame.logData.roastEventNames)):
            name = frame.logData.roastEventNames[i]
            if name != 'roast_end' or frame.options.getUserOption("difficulty") != 'basic':
                linesToGraph.append(
                    PolyMarker([frame.logData.roastEventData[i]], legend=utilities.replaceUnderscoreWithSpace(name),
                               colour=styles[name]["colour"],
                               marker=styles[name]["marker"], size=styles[name]["size"],
                               fillstyle=styles[name]["fillstyle"]))
        if self.zoomScale == 1 and not self.expandY:
            if self.standardize and frame.logData.columnHeadings[0] in frame.logData.ySeriesScaled.keys():
                # expand the standard X axis if the data goes off the right edge, but trim unwanted cooling data
                roastEndX = frame.logData.roastEventData[frame.logData.roastEventNames.index('roast_end')][
                    0] if 'roast_end' in frame.logData.roastEventNames else float('inf')
                maxX_value = max(core_studio.STANDARD_X_AXIS[1],
                                 min(30 + utilities.maximumX(frame.logData.ySeriesScaled[frame.logData.columnHeadings[0]]),
                                     90 + roastEndX))
                maxX_value = math.ceil(maxX_value / 60.0) * 60.0
                standardX = (core_studio.STANDARD_X_AXIS[0], maxX_value)
                standardY = temperature.convertCelciusPointToSpecifiedUnit(core_studio.STANDARD_Y_AXIS)
            else:
                standardX = None
                standardY = None
        else:
            standardX = self.zoomXAxis
            standardY = self.zoomYAxis

        if self.displaySelectedText is not None:
            self.displaySelectedText.Destroy()
            self.displaySelectedText = None

        linesToGraph += core_studio.drawComparisons(self, self.title)

        if len(linesToGraph) > 0:
            self.canvas.Draw(PlotGraphics(linesToGraph, self.title, frame.logData.xAxis, ""), xAxis=standardX,
                             yAxis=standardY)
            self.zoomXAxis = (self.canvas.GetXCurrentRange()[0], self.canvas.GetXCurrentRange()[1])  # must be a tuple
            self.zoomYAxis = (self.canvas.GetYCurrentRange()[0], self.canvas.GetYCurrentRange()[1])

        if self.closest_point is not None:
            parts = utilities.replaceUnderscoreWithSpace(self.closest_legend).split(':')
            if len(parts) == 2:
                detail = ': ' + parts[1]
            else:
                detail = ''
            legend = frame.logData.legendToColumnName(parts[0])
            scale = frame.logData.yScaleFactors[legend] if legend in frame.logData.yScaleFactors.keys() else \
                frame.logData.yScaleFactors[frame.logData.masterColumn]
            decimal_points = int(1 + math.log(scale, 10))
            if legend in ['fan_speed', 'Fan_speed']:
                y = int(round(core_studio.convertFanRPMfromFitTemperatureScale(frame, self.closest_point.y) / core_studio.FAN_PROFILE_YSCALE, -1))
            else:
                y = round(self.closest_point.y / scale, decimal_points)
            thisLabel = utilities.replaceUnderscoreWithSpace(legend) + detail + "\n" + str(
                y) + " at " + utilities.toMinSec(int(self.closest_point.x))
            if hasattr(self, 'phasesObject') and legend in ['profile', 'roast_end', frame.logData.masterColumn] and len(parts) == 1:
                thisLabel += self.phasesObject.displayPhaseData(nowTime=self.closest_point.x,
                                                                nowTemperature=self.closest_point.y / scale)
            self.displaySelectedText = core_studio.initialiseDisplaySelectedText(self, thisLabel)

    def makeCheckBox(self, label, handler, default=False):
        check = wx.CheckBox(self, label=label)
        self.frame.checkBoxControls["Log_" + label] = check
        check.SetValue(self.frame.options.getUserOptionBoolean("Log_" + label, default=default))
        handler(None, check)
        check.Bind(wx.EVT_CHECKBOX, handler)
        return check

    def onToggleGrid(self, event, obj=None):
        self.canvas.SetEnableGrid(event.EventObject.IsChecked() if obj is None else obj.IsChecked())
        if self.closest_point is not None:
            self.reDraw()

    def onToggleLegend(self, event, obj=None):
        self.canvas.SetEnableLegend(event.EventObject.IsChecked() if obj is None else obj.IsChecked())
        if self.closest_point is not None:
            self.reDraw()

    def onTogglePhases(self, event, obj=None):
        if (obj is not None and obj.IsChecked()) or (obj is None and event.IsChecked()):
            self.phasesPanel.Show()
            self.chartSizer.Layout()
        else:
            self.phasesPanel.Hide()
            self.chartSizer.Layout()
        self.reDraw()

    def onToggleOptions(self, event, obj=None):
        if event.EventObject.IsChecked() if obj is None else obj.IsChecked():
            self.chartSizer.Show(self.optionsSizer)
            self.chartSizer.Layout()
        else:
            self.chartSizer.Hide(self.optionsSizer)
            self.chartSizer.Layout()
        if self.closest_point is not None:
            self.reDraw()

    def onToggleStandardize(self, event, obj=None):
        self.standardize = event.EventObject.IsChecked() if obj is None else obj.IsChecked()
        self.reDraw()

    def updateEnableStatusOfAllPlotLines(self):
        for item in self.optionsSizer.GetChildren():
            self.frame.logData.enabled[
                utilities.replaceSpaceWithUnderscore(item.GetWindow().GetLabel())] = item.GetWindow().GetValue()

    def onTogglePlotLine(self, event):
        checkBox = event.GetEventObject()
        self.frame.logData.enabled[utilities.replaceSpaceWithUnderscore(checkBox.Label)] = event.IsChecked()
        if self.closest_legend == utilities.replaceSpaceWithUnderscore(checkBox.Label):
            core_studio.destroySelectedText(self)
        self.reDraw()

    def onClick(self, event):
        self.canvas.SetFocus()
        PROXIMITY_THRESHOLD = 5
        # GetClosestPoints returns list with [curveNumber, legend, index of closest point, pointXY, scaledXY, distance]
        self.mouseWentDownAt = self.canvas.PositionScreenToUser(event.GetPosition())
        data = self.canvas.GetClosestPoints(self.mouseWentDownAt)
        # print data
        self.closest_point = None
        self.closest_distance = None
        self.closest_legend = None
        for curve in data:
            legend = curve[1]
            distance = curve[5]
            closest = bezier.Point(curve[3][0], curve[3][1])
            distance = bezier.distanceBetweenTwoPoints(bezier.pointFromTuple(self.mouseWentDownAt), closest)
            if utilities.replaceSpaceWithUnderscore(legend) in self.frame.logData.roastEventNames:
                distance *= 0.5  # give advantage to the events
            if (self.closest_distance is None or distance <= self.closest_distance) and legend != "Selection[hidden]":
                self.closest_distance = distance
                self.closest_point = closest
                self.closest_legend = utilities.replaceSpaceWithUnderscore(legend)
        if self.closest_distance > PROXIMITY_THRESHOLD:
            self.closest_point = None
            self.closest_distance = None
            self.closest_legend = None
        self.reDraw()
