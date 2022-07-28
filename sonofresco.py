# coding=utf-8
import os, re, copy
import xml.etree.ElementTree as ET
import wx

from kaffelogic_studio_defaults import *
import temperature, core_studio

defaults = [(20.0, 20.0), (207.0, 180.0), (230.0, 196.0), (290.0, 250.0)]

# Kaffelogic FC @ 205 deg C, Sonofresco FC @ 180 deg C (according to Sf help files)
# Kaffelogic SC @ 227.5, Sonofresco SC @ 200 deg C (according to Sf help files)

_applier = temperature.TemperatureEnvelopeApplier(defaults)


def applyEnvelopeSonofrescoToKaffelogicTemp(temperature):
    return round(_applier.otherToKaffelogic(temperature), 1)

def applyEnvelopeKaffelogicToSonofrescoTempExact(temperature):
    return _applier.kaffelogicToOther(temperature)

def applyEnvelopeKaffelogicToSonofrescoTemp(temperature):
    return round(applyEnvelopeKaffelogicToSonofrescoTempExact(temperature), 1)


EMULATE_KAFFELOGIC = 0

def getProfilesFilename(self):
    profilePath = self.options.getUserOption("sonofresco_profile_path")
    if profilePath != '':
        return profilePath
    appdata = os.getenv("APPDATA")
    if appdata is None:
        # Mac version
        appdata = os.path.expanduser('~')
        if appdata == '~':
            return ''
    filepath = '/Applications/Advanced Definition Roasting(ADR).app/Contents/Resources/Java/profiles.xml'
    if os.path.exists(filepath):
        return filepath
    else:
        filepath = appdata + os.sep + '.profiles.xml'
        if os.path.exists(filepath):
            return filepath
        else:
            filepath = appdata + os.sep + 'Application Support' + os.sep + 'Sonofresco' + os.sep + 'profiles.xml'
            if os.path.exists(filepath):
                return filepath
            else:
                filepath = appdata + os.sep + '.Sonofresco' + os.sep + 'profiles.xml'
                if os.path.exists(filepath):
                    return filepath
                else:
                    return ''    

"""
Minimum rise of 2.0  C/min.
Maximum rise of 25.0 C/min.
Minimum 30 seconds between data points.
"""
MIN_RISE_PER_MINUTE = 2.0
MAX_RISE_PER_MINUTE = 25.0
MAX_TEMPERATURE = 242.0
SONOFRESCO_KAFFELOGIC_TIME_OFFSET = 15 # see comment at timeShiftKaffelogicToSonofresco

def verify(self, points):
    max_temperature_permitted = temperature.convertCelciusToSpecifiedUnit(MAX_TEMPERATURE, rounding=None, delta=False)
    alternative_max_temperature_permitted = temperature.convertCelciusToSpecifiedUnit(MAX_TEMPERATURE + 0.5, rounding=None, delta=False)
    min_rise_permitted = temperature.convertCelciusToSpecifiedUnit(MIN_RISE_PER_MINUTE, rounding=None, delta=True)
    # Documentation by Sonofresco says 2.0, but profiles edited in ADR sometimes demonstrate 1.9 is accepted.
    alternative_min_rise_permitted = min_rise_permitted - temperature.convertCelciusToSpecifiedUnit(0.1, rounding=None,
                                                                                                    delta=True)
    max_rise_permitted = temperature.convertCelciusToSpecifiedUnit(MAX_RISE_PER_MINUTE, rounding=None, delta=True)
    for i in range(len(points) - 1):
        adjust = SONOFRESCO_KAFFELOGIC_TIME_OFFSET if i == 1 else 0
        timegap = (points[i+1].point.x - points[i].point.x + adjust) / 60.0
        rise_per_minute = (applyEnvelopeKaffelogicToSonofrescoTemp(points[i + 1].point.y) -
                           applyEnvelopeKaffelogicToSonofrescoTemp(points[i].point.y)) / timegap
        min_rise = applyEnvelopeSonofrescoToKaffelogicTemp(
            applyEnvelopeKaffelogicToSonofrescoTemp(points[i].point.y) + min_rise_permitted * timegap)
        max_rise = applyEnvelopeSonofrescoToKaffelogicTemp(
            applyEnvelopeKaffelogicToSonofrescoTemp(points[i].point.y) + max_rise_permitted * timegap)
        if  rise_per_minute < alternative_min_rise_permitted: # Documentation by Sonofresco says 2.0, but profiles edited in ADR sometimes demonstrate 1.9 is accepted.
            self.notebook.SetSelection(0)
            self.page1.selectedIndex = i
            self.page1.setSpinners()
            self.page1.reDraw()
            message = u"Sonofresco™ profiles have minimum rates of rise between profile points. The temperature after the point indicated needs to reach at least " + \
                          str(min_rise) + temperature.insertTemperatureUnit(u"° at the next profile point")
            if _applier.enabled:
                message += " (before temperature conversion)"
            message += "."
            wx.MessageBox(message, "Warning", wx.OK)
            return False
        if  i > 0 and rise_per_minute > max_rise_permitted:
            self.notebook.SetSelection(0)
            self.page1.selectedIndex = i
            self.page1.setSpinners()
            self.page1.reDraw()
            message = u"Sonofresco™ profiles have maximum rates of rise between profile points. The temperature after the point indicated needs to reach no more than " + \
                          str(max_rise) + temperature.insertTemperatureUnit(u"° at the next profile point")
            if _applier.enabled:
                message += " (before temperature conversion)"
            message += "."
            wx.MessageBox(message, "Warning", wx.OK)
            return False
    for i in range(len(points)):
        if  applyEnvelopeKaffelogicToSonofrescoTemp(points[i].point.y) > alternative_max_temperature_permitted:
            self.notebook.SetSelection(0)
            self.page1.selectedIndex = i
            self.page1.setSpinners()
            self.page1.reDraw()
            message = "The temperature at the point indicated is higher than the maximum allowed of " + \
                      str(applyEnvelopeSonofrescoToKaffelogicTemp(max_temperature_permitted)) + \
                      temperature.insertTemperatureUnit(u"°")
            if _applier.enabled:
                message += " (before temperature conversion)"
            message += "."
            wx.MessageBox(message, "Warning", wx.OK)
            return False

def canExportSonofresco(self):
    return getProfilesXml(self) is not None
    
def setLimits(self, limits):
    limits.description = u" [Sonofresco™ mode]"
    limits.canExportSonofresco_fn = canExportSonofresco
    limits.level_min_val = 0
    limits.level_max_val = 9
    limits.level_increment = 1
    limits.level_decimal_places = 0
    limits.levels_count = 10
    limits.levels_pattern = r"^\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*$"
    limits.levels_min_separation = 1.0
    limits.levels_min_temperature = applyEnvelopeSonofrescoToKaffelogicTemp(175.0)
    limits.levels_max_temperature = applyEnvelopeSonofrescoToKaffelogicTemp(224.5)
    limits.profile_points_edit_max = 8
    limits.profile_points_edit_min = 5
    limits.profile_points_save_min = 5
    limits.profile_points_only_insert_after_index = 1
    limits.profile_locked_points = [0, 1]
    limits.profile_points_timelock_last = True
    limits.profile_min_time_interval = 30.0
    limits.profile_custom_verify_fn = verify
    
def getProfilesXml(self):
    try:
        result = ET.parse(getProfilesFilename(self))
    except IOError as e:
        return None
    if len(result.findall('profile/name')) == 0:
        return None
    return result

def addLetter(index, name, separator):
    if index > 5:
        return name
    else:
        return "ABCDEF"[index] + separator + name
    
def getProfileNames(doc):
    if doc is None: return ['Sonofresco Default']
    return [addLetter(i, n.text, " - ") for i, n in enumerate(doc.findall('profile/name'))]
        
def getSonofrescoProfile(doc, index):
    if doc is None: return None
    profile = doc.findall('profile')[index]
    name = profile.find('name').text
    times = profile.find('time').text.strip(',').split(',')
    temps = profile.find('temperature').text.strip(',').split(',')
    description = profile.find('notes').text
    if description is None: description = ""
    levels = profile.find('roast').text.strip(',').split(',')
    levels = [float(L) for L in levels]
    profile_points = [
        (float(times[i]), float(temps[i])) for i in range(len(times))
        ]
    return {
        "index" : index,
        "name" : name,
        "description" : description,
        "profile_points" : profile_points,
        "levels" : levels
        }

def updateSonofrescoProfile(doc, newdata):
    profile = doc.findall('profile')[newdata["index"]]
    profile.find('name').text           = newdata["name"]
    profile.find('time').text           = ",".join([str(int(round(p[0]))) for p in newdata["profile_points"]]) + ","
    profile.find('temperature').text    = ",".join([str(p[1]) for p in newdata["profile_points"]]) + ","
    profile.find('roast').text          = ",".join([str(L) for L in newdata["levels"]]) + ","
    profile.find('notes').text          = newdata["description"]

def convertSonofrescoToKaffelogic(profile):
    """
    The import process uses string to data functions that automatically convert to deg F if required.
    So there is no temperature conversion done here, and there must not be any done else there would be double conversion!
    """
    if profile is None: return ""
    result = ""
    profile_points = timeShiftSonofrescoToKaffelogic(profile["profile_points"])
    result += "roast_profile:" + ",".join([str(p[0]) + "," + str(applyEnvelopeSonofrescoToKaffelogicTemp(p[1])) + ",0,0,0,0" for p in profile_points]) + "\n"
    result += "roast_levels:" + ",".join([str(applyEnvelopeSonofrescoToKaffelogicTemp(L)) for L in profile["levels"]]) + "\n"
    result += "profile_description:" + re.sub(r"\r\n|\r|\n", r"\\v", profile["description"]) + "\n"
    result += "profile_short_name:" + addLetter(profile["index"], profile["name"].replace("Sonofresco", "Sf"), "-")[:15]
    return result    

def convertKaffelogicToSonofresco(frame):
    """
    This is a bespoke export process, which has to look after its own conversion from deg F if required.
    That's why there *is* temperature conversion done here.
    """
    profile_points = timeShiftKaffelogicToSonofresco([(p.point.x, temperature.convertSpecifiedUnitToCelcius(applyEnvelopeKaffelogicToSonofrescoTemp(p.point.y), rounding=None)) for p in frame.page1.profilePoints])
    levels = [temperature.convertSpecifiedUnitToCelcius(applyEnvelopeKaffelogicToSonofrescoTemp(float(L)), rounding=None) for L in frame.page4.configControls["roast_levels"].GetValue().split(",")]
    description = frame.page3.configControls["profile_description"].GetValue()
    return {
        "description" : description,
        "profile_points" : profile_points,
        "levels" : levels
        }

def getSonofrescoDefaultAsKaffelogic():
    return convertSonofrescoToKaffelogic(getSonofrescoProfile(ET.fromstring(SONOFRESCO_DEFAULT_XML), 0))

def timeShiftKaffelogicToSonofresco(points, reverse=False):
    """
    Sonofresco points 1 and 2 are actually interpreted strangely in the Sonofrescp firmware, they are treated as...
        point number     point value        plotted and interpreted as
        #1               0,20               15,20
        #2               60,92              75,92
        #3               moveable - max slope calculated off the point values, so MAX_RISE_PER_MINUTE calculated using non-offset time values
    This results in effectively bringing the points after #2  15 secs closer to points #1 and #2.
    This is compensated for by adding/subtracting 15 sec when exporting/importing
    """
    adjust = -1 * SONOFRESCO_KAFFELOGIC_TIME_OFFSET if reverse else SONOFRESCO_KAFFELOGIC_TIME_OFFSET
    result = []
    for i in range(len(points)):
        result.append(points[i] if i <= 1 else (points[i][0] + adjust, points[i][1]))
    return result

def timeShiftSonofrescoToKaffelogic(points):
    return timeShiftKaffelogicToSonofresco(points, reverse=True)


########################################################################
class importDialog(wx.Dialog):
    
    def __init__(self, parent):
        super(importDialog, self).__init__(parent) 
        self.InitUI(parent)
        self.SetTitle(u"Import from Sonofresco™")
        
    def refreshTreeAndDoc(self):
        self.profilesTree = getProfilesXml(self.parent)
        if self.profilesTree is None:
            self.profilesDoc = ET.fromstring(SONOFRESCO_DEFAULT_XML)
        else:
            self.profilesDoc = self.profilesTree.getroot()        

    def InitUI(self, parent):
        self.parent = parent
        self.refreshTreeAndDoc()
        
        box = wx.BoxSizer(wx.VERTICAL)
        self.box = box
        
        box.Add(wx.StaticText(self, -1, "Location of Sonofresco profiles"), 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.ALIGN_LEFT, 10, 10)
        profilePath = getProfilesFilename(self.parent)
        self.profilePathFileCtrl = wx.FilePickerCtrl(self, path=profilePath, message="Select ADR profile xml file (it may be in a hidden folder)", size=(300,-1),
                                                   wildcard="Sonofresco profile files (*.xml)|*.xml", style=wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST | wx.FLP_USE_TEXTCTRL | wx.FLP_SMALL)
        box.Add(self.profilePathFileCtrl, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.ALIGN_LEFT, 10)
        self.profilePathFileCtrl.SetInitialDirectory(self.parent.options.getUserOption("working_directory"))
        if core_studio.isLinux: self.profilePathFileCtrl.GetTextCtrl().ChangeValue(profilePath) # seems to be needed in Linux
        self.profilePathFileCtrl.Bind(wx.EVT_FILEPICKER_CHANGED, self.onFileCtrlChange)
        
        box.Add(wx.StaticText(self, -1, "Profile to import"), 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.ALIGN_LEFT, 10, 10)
        self.listControl = wx.ListBox(self, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize,
            choices=getProfileNames(self.profilesDoc),
            style=0, validator=wx.DefaultValidator, name="profile_names")
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        importButton = wx.Button(self, label='Import')
        cancelButton = wx.Button(self, label='Cancel')
        buttons.Add(importButton, 0, wx.ALL | wx.ALIGN_RIGHT, 7) # Mac buttons need 7-pixel borders or they overlap
        buttons.Add(cancelButton, 0, wx.ALL | wx.ALIGN_RIGHT, 7)
        self.onlyDefaultMessage = wx.StaticText(self, -1, u"Sonofresco™ Advanced Definition Roasting (ADR) profiles not\nfound at that location. Only the default profile is available.")
        box.Add(self.onlyDefaultMessage, 0, wx.ALL, 10)
        if self.profilesTree is not None:
            self.onlyDefaultMessage.Hide()
        box.Add(self.listControl, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.Add(temperature.widget(self, self.parent, "Sonofresco", u"kaffelogic/sonofresco_envelope_temperatures", "sonofresco", str(defaults), _applier).box)
        box.Add(buttons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.SetSizeHints(self)
        self.SetSizerAndFit(box)
        importButton.Bind(wx.EVT_BUTTON, self.onImport)
        self.listControl.Bind(wx.EVT_LISTBOX_DCLICK, self.onImport)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
        self.listControl.SetFocus()
        importButton.SetDefault()
        
    def onImport(self, e):
        index = self.listControl.GetSelection()
        if index == wx.NOT_FOUND: return
        sonofrescoProfile = getSonofrescoProfile(self.profilesDoc, index)
        self.parent.fileName = ""
        self.parent.openFromString(self.parent, SONOFRESCO_DEFAULT_DATA, convertSonofrescoToKaffelogic(sonofrescoProfile))
        self.parent.datastring = ""
        self.parent.updateMenu()
        self.parent.options.setUserOptionBoolean("sonofresco_temperature_conversion_on", _applier.enabled)
        self.Close()
                
    def onFileCtrlChange(self, e):
        path = self.profilePathFileCtrl.GetPath()
        if not os.path.isfile(path):
            return
        self.parent.options.setUserOption("sonofresco_profile_path", path)
        self.refreshTreeAndDoc()
        self.listControl.Clear()
        for item in getProfileNames(self.profilesDoc):
            self.listControl.Append(item)
        self.parent.updateMenu()
        if self.profilesTree is None:
            self.onlyDefaultMessage.Show()
        else:
            self.onlyDefaultMessage.Hide()
        self.Layout()
        self.SetSizerAndFit(self.box)
            
    def onCancel(self, e):
        self.Close()
########################################################################
class exportDialog(wx.Dialog):
    
    def __init__(self, parent):
        self.parent = parent
        if parent.configuration["emulation_mode"] == EMULATE_KAFFELOGIC or self.parent.fileType == "log":
            return
        self.profilesTree = getProfilesXml(self.parent)
        super(exportDialog, self).__init__(parent) 
        if self.profilesTree is None:
            wx.MessageBox(u"Sonofresco™ Advanced Definition Roasting (ADR) profiles not found for current user.", "Not found",
                       wx.OK, self)
            wx.CallAfter(self.Close)
            return
        else:
            self.profilesDoc = self.profilesTree.getroot()
        self.InitUI()
        self.SetTitle(u"Export to Sonofresco™")
                    
    def InitUI(self):
        box = wx.BoxSizer(wx.VERTICAL)
        self.listControl = wx.ListBox(self, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize,
            choices=getProfileNames(self.profilesDoc),
            style=0, validator=wx.DefaultValidator, name="profile_names")
        newButtons = wx.BoxSizer(wx.HORIZONTAL)
        newButton = wx.Button(self, label='+', style=wx.BU_EXACTFIT)
        self.newName = wx.TextCtrl(self, -1)
        newButtons.Add(newButton, 0, wx.ALIGN_LEFT)
        newButtons.Add(self.newName, 1, wx.EXPAND | wx.RESERVE_SPACE_EVEN_IF_HIDDEN)
        exportButtons = wx.BoxSizer(wx.HORIZONTAL)
        exportButton = wx.Button(self, label='Export')
        cancelButton = wx.Button(self, label='Cancel')
        exportButtons.Add(exportButton, 1, wx.ALL, 7)
        exportButtons.Add(cancelButton, 1, wx.ALL, 7)
        box.Add(self.listControl, 0, wx.ALIGN_CENTRE | wx.ALL, 10)
        box.Add(newButtons, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        box.Add(temperature.widget(self, self.parent, "Sonofresco", u"kaffelogic/sonofresco_envelope_temperatures", "sonofresco", str(defaults), _applier).box)
        box.Add(exportButtons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.SetSizeHints(self)
        self.SetSizerAndFit(box)
        newButton.Bind(wx.EVT_BUTTON, self.onAdd)
        exportButton.Bind(wx.EVT_BUTTON, self.onExport)
        self.listControl.Bind(wx.EVT_LISTBOX_DCLICK, self.onExport)
        self.listControl.Bind(wx.EVT_LISTBOX, self.onClick)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
        exportButton.SetDefault()
        self.onAdd(None)
        _applier.parseCelciusEnvelope(self.parent.options.getUserOption(u"kaffelogic/sonofresco_envelope_temperatures", default=str(defaults)))
        
    def onClick(self, e):
        self.newName.Clear()
        self.newName.Show(False)
        
    def onExport(self, e):
        if not self.parent.validation(exporting=True):
            return
        index = self.listControl.GetSelection()
        newName = self.newName.GetValue().strip()
        lookup = self.listControl.FindString(newName)
        if lookup == wx.NOT_FOUND:
            existingNames = [n.text.lower() for n in self.profilesDoc.findall('profile/name')]
            if newName.lower() in existingNames:
                lookup = existingNames.index(newName.lower())
        if index == 0 or lookup == 0: return
        if index == wx.NOT_FOUND and lookup == wx.NOT_FOUND:
            if newName == '': return
            new = True
            index = self.listControl.GetCount()
            newElem = copy.deepcopy(self.profilesDoc.findall('profile')[0]) # Grab the default profile, cos we have all the required elements in one hit.
            """
            ASSUMPTION: We assume all of the license elements follow all of the profile elements, and there are no other elements following the profiles.
            """
            licenses = self.profilesDoc.findall('license')
            licensesCopy = copy.deepcopy(licenses)
            for lic in licenses: self.profilesDoc.remove(lic)
            self.profilesDoc.append(newElem)
            for lic in licensesCopy: self.profilesDoc.append(lic)
        else:
            if index == wx.NOT_FOUND:
                index  = lookup
            newName = getSonofrescoProfile(self.profilesDoc, index)["name"]
            new = False
        newProfile = convertKaffelogicToSonofresco(self.parent)
        newProfile["name"] = newName
        newProfile["index"] = index
        updateSonofrescoProfile(self.profilesDoc, newProfile)
        if not new:
            answer = wx.MessageBox("Replace " + addLetter(index, newName, " - ") + "?", "Confirm",
                       wx.OK | wx.CANCEL, self)
            if answer == wx.CANCEL:
                return
        #print ET.tostring(self.profilesDoc)
        try:
            self.profilesTree.write(getProfilesFilename(self.parent))
        except IOError as e:
            dial = wx.MessageDialog(None, 'This file could not be saved.\n' + getProfilesFilename(self.parent) + '\n' + e.strerror + '.', 'Error', 
                    wx.OK | wx.ICON_EXCLAMATION)
            dial.ShowModal()
            return
        if self.parent.fileName == "": self.parent.modified(False)
        self.parent.options.setUserOptionBoolean("sonofresco_temperature_conversion_on", _applier.enabled)
        self.Close()
                
    def onCancel(self, e):
        self.Close()
        
    def onAdd(self, e):
        self.listControl.SetSelection(wx.NOT_FOUND)
        self.newName.Show(True)
        self.newName.SetFocus()

########################################################################

