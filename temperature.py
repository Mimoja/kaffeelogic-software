# coding:utf-8

from __future__ import division

import wx, operator, re, os, core_studio, bezier
from wx.lib.plot import PlotCanvas, PlotGraphics, PolyLine, PolyMarker

def getTemperatureUnit():
    return wx.App.Get().frame.temperature_unit

def setTemperatureUnit(temperature_unit):
    wx.App.Get().frame.temperature_unit = temperature_unit

def convertCelciusToSpecifiedUnit(temperature, to_unit=None, rounding=1, delta=False, keepZero=False):
    try:
        temperature = float(temperature)
    except:
        return temperature
    if keepZero and temperature == 0: return temperature
    if to_unit is None: to_unit = getTemperatureUnit()
    shift = 0.0 if delta else 32.0 # if we are dealing with a temperature delta, only the ratio part of the conversion applies
    t = temperature * 9.0 / 5.0 + shift if to_unit.upper().startswith('F') else temperature
    return t if rounding is None else round(t, rounding)

def convertCelciusPointToSpecifiedUnit(point, to_unit=None, rounding=1, delta=False):
    if to_unit is None: to_unit = getTemperatureUnit()
    shift = 0.0 if delta else 32.0 # if we are dealing with a temperature delta, only the ratio part of the conversion applies
    x, temperature = point
    t = float(temperature) * 9.0 / 5.0 + shift if to_unit.upper().startswith('F') else float(temperature)
    return (x, (t if rounding is None else round(t, rounding)))

def convertCelciusProfilePointToSpecifiedUnit(profilePoint, to_unit=None, rounding=1):
    x, y, c1x, c1y, c2x, c2y = profilePoint.toTuple()
    return bezier.ProfilePoint(x, convertCelciusToSpecifiedUnit(y, to_unit, rounding),
                        c1x, 0 if (c1x, c1y) == (0, 0) else convertCelciusToSpecifiedUnit(c1y, to_unit, rounding),
                        c2x, 0 if (c2x, c2y) == (0, 0) else convertCelciusToSpecifiedUnit(c2y, to_unit, rounding)
                        )

def convertSpecifiedUnitProfilePointToCelcius(profilePoint, from_unit=None, rounding=1):
    x, y, c1x, c1y, c2x, c2y = profilePoint.toTuple()
    return bezier.ProfilePoint(x, convertSpecifiedUnitToCelcius(y, from_unit, rounding),
                        c1x, 0 if (c1x, c1y) == (0, 0) else convertSpecifiedUnitToCelcius(c1y, from_unit, rounding),
                        c2x, 0 if (c2x, c2y) == (0, 0) else convertSpecifiedUnitToCelcius(c2y, from_unit, rounding)
                        )

def convertSpecifiedUnitProfileToCelcius(profile, from_unit=None, rounding=1):
    return [convertSpecifiedUnitProfilePointToCelcius(p, from_unit, rounding) for p in profile]

def convertCelciusListToSpecifiedUnit(l, to_unit=None, rounding=1, delta=False):
    return ','.join([str(convertCelciusToSpecifiedUnit(temperature, to_unit, rounding, delta)) for temperature in l.split(',')])

def convertSpecifiedUnitListToCelcius(l, from_unit=None, rounding=1, delta=False):
    return ','.join([str(convertSpecifiedUnitToCelcius(temperature, from_unit, rounding, delta)) for temperature in l.split(',')])

def convertCelciusEnvelopeToSpecifiedUnit(envelope, to_unit=None, rounding=1, delta=False):
    return [(
                convertCelciusToSpecifiedUnit(point[0], to_unit, rounding, delta),
                convertCelciusToSpecifiedUnit(point[1], to_unit, rounding, delta)
            ) for point in envelope]

def convertSpecifiedUnitEnvelopeToCelcius(envelope, from_unit=None, rounding=1, delta=False):
    return [(
                convertSpecifiedUnitToCelcius(point[0], from_unit, rounding, delta),
                convertSpecifiedUnitToCelcius(point[1], from_unit, rounding, delta)
            ) for point in envelope]

def convertSpecifiedUnitToCelcius(temperature, from_unit=None, rounding=1, delta=False, keepZero=False):
    try:
        temperature = float(temperature)
    except:
        return temperature
    if keepZero and temperature == 0: return temperature
    if from_unit is None: from_unit = getTemperatureUnit()
    shift = 0.0 if delta else 32.0 # if we are dealing with a temperature delta, only the ratio part of the conversion applies
    t = (temperature - shift) * 5.0 / 9.0 if from_unit.upper().startswith('F') else temperature
    return t if rounding is None else round(t, rounding)

def insertTemperatureUnit(s, unit=None):
    if unit is None: unit = getTemperatureUnit()
    return re.sub(u'°', u'°' + unicode(unit.upper()[0]), unicode(s))

def removeTemperatureUnit(s):
    return re.sub(u'°(C|F)', '', s)

def makeCelsiusAndApplyEnvelope(temperature, unit='C', rounding=None, envelopeFn=None):
    if temperature == '' or temperature is None: return '0'
    temperature = (float(temperature) - 32.0) * 5.0/9.0 if unit.startswith('F') else float(temperature)
    temperature = envelopeFn(temperature) if envelopeFn is not None else temperature
    return str(temperature) if rounding is None else str(round(temperature, rounding))

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

def textToEnvelope(s):
    s = [pair.split(',') for pair in re.sub(r'^\[\(|\)\]$', '', s).split('), (')]
    e = [(float(pair[0]), float(pair[1])) for pair in s if floatable(pair)]
    return e

class TemperatureEnvelopeApplier():
    """
    A conversion envelope consists of a list of (kaffelogicTemperature, otherTemperature) tuples.
    The first entry should be (ambient, ambient).
    """
    def __init__(self, temperatureEnvelope):
        self.enabled = True
        self.applyingEnvelope = False
        self.envelope = None
        self.ramps = None
        self.setEnvelope(temperatureEnvelope)

    def kaffelogicToOther(self, temperature):
        if not (self.enabled and self.applyingEnvelope): return temperature
        ramp = self._getRamp(temperature)
        if ramp is None: return temperature
        return (temperature - ramp["Xstart"]) * ramp["m"] + ramp["Ystart"]

    def otherToKaffelogic(self, temperature):
        if not (self.enabled and self.applyingEnvelope): return temperature
        ramp = self._getRamp(temperature, reverse=True)
        if ramp is None: return temperature
        return (temperature - ramp["Ystart"]) / ramp["m"] + ramp["Xstart"]

    def parseCelciusEnvelope(self, s):
        e = textToEnvelope(s)
        self.setEnvelope(convertCelciusEnvelopeToSpecifiedUnit(e))

    def getEnvelope(self):
        return self.envelope
    
    def getEnvelopeAsString(self):
        return str(self.envelope)

    def setEnvelope(self, temperatureEnvelope):
        if temperatureEnvelope is None or len(temperatureEnvelope) == 0:
            self.applyingEnvelope = False
            self.envelope = None
        else:
            self.applyingEnvelope = True
            self.envelope = sorted(temperatureEnvelope, key=operator.itemgetter(0, 1))
            self.ramps = []
            if len(self.envelope) == 1:
                ramp = {"Xstart": self.envelope[0][0], "Xend": self.envelope[0][0], "Ystart": self.envelope[0][1],
                        "Yend": self.envelope[0][1], "m": 1.0}
                self.ramps.append(ramp)
            else:
                for i in range(len(self.envelope) - 1):
                    ramp = {"Xstart": self.envelope[i][0], "Xend": self.envelope[i + 1][0],
                            "Ystart": self.envelope[i][1], "Yend": self.envelope[i + 1][1],
                            "m": (self.envelope[i + 1][1] - self.envelope[i][1]) / (
                                        self.envelope[i + 1][0] - self.envelope[i][0])}
                    self.ramps.append(ramp)

    def _getRamp(self, x, reverse=False):
        if reverse:
            if x < self.ramps[0]["Ystart"]:
                return None
            for i in range(len(self.ramps)):
                if x < self.ramps[i]["Yend"]:
                    return self.ramps[i]
            return self.ramps[-1]
        else:
            if x < self.ramps[0]["Xstart"]:
                return None
            for i in range(len(self.ramps)):
                if x < self.ramps[i]["Xend"]:
                    return self.ramps[i]
            return self.ramps[-1]

HELP_TEXT = "Enter temperatures for several events where you think the Kaffelogic profile corresponds to the [[targetSystem]] profile, " + \
            "for example first crack and roast end. Add additional points to fine tune the shape of the conversion envelope."

class temperatureEnvelopeDialog(wx.Dialog):
    
    def __init__(self, parent, frame, targetSystem, optionsName, default, envelopeApplier):
        super(temperatureEnvelopeDialog, self).__init__(parent) 
        self.SetTitle(u"Temperature conversion")
        self.parent = parent
        self.frame = frame
        self.targetSystem = targetSystem
        self.optionsName = optionsName
        self.envelopeApplier = envelopeApplier
        self.envelopeApplier.parseCelciusEnvelope(frame.options.getUserOption(optionsName, default=default))
        main = wx.BoxSizer(wx.HORIZONTAL)
        self.canvas = PlotCanvas(self, size=(500,400))
        self.canvas.SetEnableHiRes(True)
        self.canvas.SetEnableAntiAliasing(True)
        self.canvas.SetGridColour("gray")
        self.canvas.SetEnableLegend(True)
        self.canvas.SetEnableGrid(True)
        main.Add(self.canvas)
        box = wx.BoxSizer(wx.VERTICAL)
        self.grid = wx.GridBagSizer(0,3)
        self.grid.SetEmptyCellSize((0,0))
        self.grid.SetRows(self.grid.GetRows() + 1)
        self.addItems(self.grid, self.envelopeApplier.getEnvelope())
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, label='OK')
        cancelButton = wx.Button(self, label='Cancel')
        buttons.Add(okButton, 0, wx.ALL | wx.ALIGN_RIGHT, 7) # Mac buttons need 7-pixel borders or they overlap
        buttons.Add(cancelButton, 0, wx.ALL | wx.ALIGN_RIGHT, 7)
        helpText = wx.StaticText(self, -1, HELP_TEXT.replace('[[targetSystem]]', targetSystem))
        helpText.Wrap(350)
        box.Add(helpText, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.Add(self.envelopeControls(), 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.Add(self.grid, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.Add(buttons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        main.Add(box)
        main.SetSizeHints(self)
        self.SetSizerAndFit(main)
        okButton.Bind(wx.EVT_BUTTON, self.onOk)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
        okButton.SetDefault()
        self.reDraw()
        self.Fit()
        self.Layout()

    def envelopeControls(self):
        controls = wx.StaticBoxSizer(wx.StaticBox(self), wx.HORIZONTAL)
        label = wx.StaticText(self, -1, u"Envelope:")
        saveButton = wx.Button(self, -1, 'Save', style=wx.BU_EXACTFIT)
        loadButton = wx.Button(self, -1, 'Load', style=wx.BU_EXACTFIT)
        copyButton = wx.Button(self, -1, 'Copy', style=wx.BU_EXACTFIT)
        pasteButton = wx.Button(self, -1, 'Paste', style=wx.BU_EXACTFIT)
        controls.Add(label, 0, wx.ALL | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 7)
        controls.Add(saveButton, 0, wx.ALL | wx.ALIGN_RIGHT, 7)
        controls.Add(loadButton, 0, wx.ALL | wx.ALIGN_RIGHT, 7)
        controls.Add(copyButton, 0, wx.ALL | wx.ALIGN_RIGHT, 7)
        controls.Add(pasteButton, 0, wx.ALL | wx.ALIGN_RIGHT, 7)
        saveButton.Bind(wx.EVT_BUTTON, self.onSave)
        loadButton.Bind(wx.EVT_BUTTON, self.onLoad)
        copyButton.Bind(wx.EVT_BUTTON, self.onCopy)
        pasteButton.Bind(wx.EVT_BUTTON, self.onPaste)
        return controls

    def reDraw(self):
        if getTemperatureUnit() == 'F':
            line_length = 500
            axis_length = 600
        else:
            line_length = 250
            axis_length = 300
        envelope = self.getEnvelopeFromControls()
        if envelope is not None:
            points = PolyMarker(envelope, legend='Points', colour='black', marker='circle', size=0.4 * self.frame.lineWidth)
        else:
            points = None
        if envelope is None or len(envelope) == 0:
            envelope = [(0, 0)]
        kaffelogic = PolyLine(((envelope[0][0], envelope[0][0]), (line_length, line_length)), legend='Kaffelogic', colour='red', width=self.frame.lineWidth)
        lines = [kaffelogic]
        if len(envelope) >= 2:
            lines.append(PolyLine(envelope, legend=self.targetSystem, colour='blue', width=self.frame.lineWidth))
        if points is not None:
            lines.append(points)
        self.canvas.Draw(PlotGraphics(lines, "Temperature conversion envelope", "", ""),xAxis=(0,axis_length),yAxis=(0,axis_length))

    def onAdd(self, event):
        # wx.CallAfter not needed because no user interaction
        row = int(event.EventObject.GetName())
        self.addRow(self.grid, row)

    def addRow(self, grid, rowNumber):
        array = self.getTextFromControls()
        array.insert(rowNumber, ('',''))
        grid.Clear(True)
        self.addItems(grid, array)
        self.Fit()
        self.Layout()
        self.reDraw()
        
    def onDelete(self, event):
        # wx.CallAfter was tried but made things crash on the Mac
        row = int(event.EventObject.GetName())
        point = ", ".join(self.getTextFromControls()[row - 1])
        if wx.OK == wx.MessageBox("Deleting the point " + point, "Delete", wx.OK | wx.CANCEL):
            self.deleteRow(self.grid, row)
        
    def deleteRow(self, grid, rowNumber):
        array = self.getTextFromControls()
        array.pop(rowNumber - 1)
        grid.Clear(True)
        self.addItems(grid, array)        
        self.Fit()
        self.Layout()
        self.reDraw()

    def onTxtChange(self, event):
        event.Skip()
        self.reDraw()

    def addItems(self, grid, envelope):
        label0 = wx.StaticText(self, -1, insertTemperatureUnit(u"° Kaffelogic"))
        label1 = wx.StaticText(self, -1, insertTemperatureUnit(u"° ") + self.targetSystem)
        grid.Add(label0, pos=(0, 0), flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=1)
        grid.Add(label1, pos=(0, 1), flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=1)
        self.rowCount = 1
        self.controls = []
        if envelope is None or len(envelope) == 0:
            envelope = [('20', '20')]
        for pair in envelope:
            txt0 = wx.TextCtrl(self, -1,  str(pair[0]))
            txt1 = wx.TextCtrl(self, -1,  str(pair[1]))
            add = wx.Button(self, label='+', name=str(self.rowCount), size=(35,-1))
            delete = wx.Button(self, label='-', name=str(self.rowCount), size=(35,-1))
            grid.Add(txt0, pos=(self.rowCount, 0), flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=1)
            grid.Add(txt1, pos=(self.rowCount, 1), flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=1)
            grid.Add(add, pos=(self.rowCount, 2), flag=wx.TOP | wx.BOTTOM, border=1)
            grid.Add(delete, pos=(self.rowCount, 3), flag=wx.TOP | wx.BOTTOM, border=1)
            add.Bind(wx.EVT_BUTTON, self.onAdd)
            delete.Bind(wx.EVT_BUTTON, self.onDelete)
            txt0.Bind(wx.EVT_TEXT, self.onTxtChange)
            txt1.Bind(wx.EVT_TEXT, self.onTxtChange)
            self.rowCount += 1
            self.controls.append((txt0, txt1))
            if not grid.IsColGrowable(1): grid.AddGrowableCol(1, 1)

    def onLoad(self,event):
        openFileDialog = core_studio.myFileDialog(self, "Load Envelope", "", "",
                                      "Kaffelogic temperature envelope (*.kenvl)|*.kenvl",
                                      wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        result = openFileDialog.ShowModal()
        if result == wx.ID_CANCEL:
            return
        loadFileName = openFileDialog.GetPath()
        openFileDialog.Destroy()
        wx.CallAfter(self.loadEnvelope, loadFileName)

    def loadEnvelope(self, loadFileName):
        data = core_studio.openAndReadFile(loadFileName)
        array = convertCelciusEnvelopeToSpecifiedUnit(textToEnvelope(data))
        if len(array) > 1:
            self.grid.Clear(True)
            self.addItems(self.grid, array)
            self.reDraw()
            self.Fit()
            self.Layout()
            return
        wx.MessageBox(loadFileName + " does not contain envelope numbers.", "Load envelope", wx.OK)

    def onSave(self, event):
        saveFileDialog = core_studio.myFileDialog(self, "Save Envelope As", "", "",
                                      "Kaffelogic temperature envelope (*.kenvl)|*.kenvl",
                                      wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        result = saveFileDialog.ShowModal()
        saveFileName, ext = os.path.splitext(saveFileDialog.GetPath())
        print 'saveFileName, ext', saveFileName, ext
        saveFileName += ext
        if ext.lower() != '.kenvl':
            saveFileName += '.kenvl'
        saveFileDialog.Destroy()
        if result != wx.ID_CANCEL:
            wx.CallAfter(self.saveEnvelope, saveFileName)

    def saveEnvelope(self, saveFileName):
        print "saveFileName", saveFileName
        data = str(convertSpecifiedUnitEnvelopeToCelcius(self.getEnvelopeFromControls()))
        try:
            with open(saveFileName, 'w') as output:
                output.write(data.encode('utf8'))
        except IOError as e:
            dial = wx.MessageDialog(None, 'This file could not be saved.\n' + saveFileName + '\n' + e.strerror + '.', 'Error',
                                    wx.OK | wx.ICON_EXCLAMATION)
            dial.ShowModal()

    def onCopy(self, event):
        wx.CallAfter(self.onCopyAfter, event)
        
    def onCopyAfter(self, event):
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(str(self.getEnvelopeFromControls())))
            wx.TheClipboard.Close()
            wx.MessageBox("The envelope numbers have been copied to the clipboard.", "Copy to clipboard", wx.OK)

    def onPaste(self, event):
        wx.CallAfter(self.onPasteAfter, event)
        
    def onPasteAfter(self, event):
        # Test if text content is available
        not_empty = wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT))
        # Read some text
        if not_empty:
            text_data = wx.TextDataObject()
            success = None
            if wx.TheClipboard.Open():
                success = wx.TheClipboard.GetData(text_data)
                wx.TheClipboard.Close()
            if success:
                data = self.makeSenseOfWeirdEncoding(text_data.GetText())
                # on Mac the data is coming back incorrectly encoded as UTF-16, this needs to be dis-entangled
                array = textToEnvelope(data)
                if len(array) > 1:
                    if wx.OK == wx.MessageBox("Replace with " + str(len(array)) + " points", "Paste points", wx.OK | wx.CANCEL):
                        self.grid.Clear(True)
                        self.addItems(self.grid, array)        
                        self.reDraw()
                        self.Fit()
                        self.Layout()
                    return
        wx.MessageBox("The clipboard does not contain envelope numbers.", "Paste from clipboard", wx.OK)

    def makeSenseOfWeirdEncoding(self, text):
        b = bytearray(text, encoding='utf-16')
        if b[0] == 255:
            b = b[2:]
        result = ''
        for i in range(len(b)):
            if b[i] != 0:
                result += chr(b[i])
        return result

    def getEnvelopeFromControls(self):
        envelope = [(float(pair[0].GetValue()), float(pair[1].GetValue())) for pair in self.controls if floatable((pair[0].GetValue(), pair[1].GetValue()))]
        return envelope
    
    def getTextFromControls(self):
        """
        Used for adding and removing in the UI, so no need for any temperature conversion.
        """
        text = [(pair[0].GetValue(), pair[1].GetValue()) for pair in self.controls]
        return text
    
    def onOk(self, e):
        self.envelope = self.getEnvelopeFromControls()
        if self.envelope is not None:
            self.envelopeApplier.setEnvelope(self.envelope)
            self.frame.options.setUserOption(self.optionsName, str(convertSpecifiedUnitEnvelopeToCelcius(self.envelopeApplier.getEnvelope())))
        self.Close()
                
    def onCancel(self, e):
        self.envelope = None
        self.Close()

class widget():
    def __init__(self, parent, frame, targetSystem, optionsName, typeName, default, envelopeApplier):
        envelopeApplier.parseCelciusEnvelope(frame.options.getUserOption(optionsName, default=default))
        self.parent = parent
        self.frame = frame
        self.targetSystem = targetSystem
        self.optionsName = optionsName
        self.default = default
        self.envelopeApplier = envelopeApplier
        self.box = wx.BoxSizer(wx.VERTICAL)
        self.innerbox = wx.BoxSizer(wx.HORIZONTAL)
        self.box.Add(wx.StaticText(parent, -1, "Temperature conversion"), 0, wx.LEFT | wx.TOP | wx.ALIGN_LEFT, 10)
        editButton = wx.Button(parent, label='Edit conversion envelope')
        self.check = wx.CheckBox(parent, label="Convert temperature")
        enabled = self.frame.options.getUserOptionBoolean(typeName + "_temperature_conversion_on", default=False)
        self.check.SetValue(enabled)
        self.envelopeApplier.enabled = enabled
        self.innerbox.Add(self.check, 0, wx.LEFT | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        self.innerbox.Add(editButton, 0, wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        self.box.Add(self.innerbox)
        self.check.Bind(wx.EVT_CHECKBOX, self.onCheck)
        editButton.Bind(wx.EVT_BUTTON, self.onEdit)
    
    def onCheck(self, e):
        self.envelopeApplier.enabled = self.check.GetValue()

    def onEdit(self, e):
        dialog = temperatureEnvelopeDialog(self.parent, self.frame, self.targetSystem, self.optionsName, self.default, self.envelopeApplier)
        dialog.ShowModal()
        dialog.Destroy()
    
def calculate_xGiven_y(y, lowGuess, highGuess, fn):
    """
    y = fn(x)
    Note that the function must be well behaved, and lowGuess and highGuess must be well chosen.
    """
    MAX_ITERATIONS = 64
    THRESHOLD = 0.000001
    for i in range(0, MAX_ITERATIONS):
        currentGuess = (lowGuess + highGuess) / 2.0
        lowResult = fn(lowGuess)
        highResult = fn(highGuess)
        currentResult = fn(currentGuess)
        if (abs(currentResult - y) < THRESHOLD):
            return currentGuess
        else:
            if (currentResult < y):
                if highResult > lowResult:
                    lowGuess = currentGuess
                else:
                    highGuess = currentGuess
            else:
                if highResult > lowResult:
                    highGuess = currentGuess
                else:
                    lowGuess = currentGuess
    return currentGuess

"""
This code was released as v3.1.2 beta, but it doesn't do much of a job so has been deprecated in 3.1.3

class TemperatureConverter():
    def __init__(self, nominalKaffelogic, nominalOther, Ta=20.0):
        self.setTemperatureOfEvent(nominalKaffelogic, nominalOther, Ta)

    def kaffelogicToOther(self, temperature):
        return (temperature - self.Ta) / self.k + self.Ta

    def otherToKaffelogic(self, temperature):
        return (temperature - self.Ta) * self.k + self.Ta

    def setTemperatureOfEvent(self, nominalKaffelogic, nominalOther, Ta=20.0):
        self.Ta = Ta
        self.nominalKaffelogic = nominalKaffelogic
        self.nominalOther = nominalOther
        self.k = ((nominalKaffelogic - Ta) / (nominalOther - Ta))

    def setTambient(self, T):
        self.setTemperatureOfEvent(self.nominalKaffelogic, self.nominalOther, T)
"""


if __name__ == '__main__':
    #core_studio = __import__('Kaffelogic Studio')
    c=TemperatureEnvelopeApplier([(10, 10), (100, 150), (200, 200)])
    L = []
    for T in range(0,200, 10):
        print str(T) + "\t" + str(c.kaffelogicToOther(T))
        L.append(c.kaffelogicToOther(T))
    print "========================================================"
    for T in L:
        print str(T) + "\t" + str(c.otherToKaffelogic(T))
