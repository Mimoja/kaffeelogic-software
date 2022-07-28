#coding:utf-8

import sys, wx, core_studio, utilities
thismodule = sys.modules[__name__]

VERSIONS = [
    {
        "schema": "1.4",
        "firmware": "v 7.2+",
        "notes": "",
        "new_settings" : []
    },
    {
        "schema": "1.5",
        "firmware": "v 7.3.5+",
        "notes": "short name can be blank",
        "new_settings" : []
    },
    {
        "schema": "1.6",
        "firmware": "v 7.4.5+",
        "notes": "zones one and two can use power profiling, zone three available with boost only",
        "new_settings" : ["zone3_time_start", "zone3_time_end","zone3_multiplier_Kp","zone3_multiplier_Kd","zone3_boost"]
    },
    {
        "schema": "1.7",
        "firmware": "v 7.4.6+",
        "notes": "zone three can use multipliers and power profiling",
        "new_settings": []
    }
]

VERSION_SCHEMA_NUMBER_LIST = [x["schema"] for x in VERSIONS]

def filterOutUnsupportedSettings(configList, schemaVersion):
    versionIndex = VERSION_SCHEMA_NUMBER_LIST.index(schemaVersion)
    unwanted = []
    for i in range(versionIndex + 1, len(VERSIONS)):
        unwanted += VERSIONS[i]["new_settings"]
    for config in unwanted:
        if config in configList:
            configList.remove(config)
    
def updateSchemaVersion(frame):
    new_schema = calculateSchemaVersion(frame)["schema"]
    frame.page4.configControls['profile_schema_version'].ChangeValue(new_schema)
    return new_schema

def calculateSchemaVersion(frame):
    for version in reversed(VERSIONS):
        functionName = ("requires." + version["schema"]).replace('.', '_')
        if not hasattr(thismodule, functionName):
            raise Exception('Missing function in fileproperties.py', functionName)
        if getattr(thismodule, functionName)(frame)["requirement"]:
            return version
    raise Exception('At least one "requires_" function must always return "requirement":True')

def calculateSchemaHelp(frame, versionWanted):
    helpFor = VERSION_SCHEMA_NUMBER_LIST.index(versionWanted) + 1
    functionName = ("requires." + VERSION_SCHEMA_NUMBER_LIST[helpFor]).replace('.', '_')
    if not hasattr(thismodule, functionName):
        raise Exception('Missing function in fileproperties.py', functionName)
    return getattr(thismodule, functionName)(frame)["help"]
        
def requires_1_4(frame):
    """
    Must return True as this is the lowest schema number ever supported in production.
    """
    return {"requirement": True, "help": ""}

def requires_1_5(frame):
    shortName = frame.page3.configControls["profile_short_name"].GetValue().strip()
    requirement = shortName == ""
    return {"requirement":requirement, "help": "A short name must be specified to allow schema version 1.4"}
    
def requires_1_6(frame):
    requirement = False
    helpText = ""
    # zone3_start can validly == 0.0 so it is not used in testing.
    zone3_end = utilities.fromMinSec(frame.page4.configControls["zone3_time_end"].GetValue())
    zone3_Kp = frame.page4.configControls["zone3_multiplier_Kp"].GetValue()
    zone3_Kd = frame.page4.configControls["zone3_multiplier_Kd"].GetValue()
    zone3_boost = frame.page4.configControls["zone3_boost"].GetValue()
    if utilities.floatOrZero(zone3_end) != 0.0 and (utilities.floatOrZero(zone3_Kp) != 1.0 or  utilities.floatOrZero(zone3_Kd) != 1.0 or utilities.floatOrZero(zone3_boost) != 0.0):
        helpText = "There are non-default zone3 settings. The zone3 settings must all be at their default values to allow schema version 1.5.\n\n"
        requirement = True
    for zone in ['zone1', 'zone2']:
        # zone_start can validly == 0.0 when the zone is in use, so it is not used in testing.
        zone_end = utilities.fromMinSec(frame.page4.configControls[zone + "_time_end"].GetValue())
        zone_Kp = frame.page4.configControls[zone + "_multiplier_Kp"].GetValue()
        zone_Kd = frame.page4.configControls[zone + "_multiplier_Kd"].GetValue()
        zone_boost = frame.page4.configControls[zone + "_boost"].GetValue()
        if utilities.floatOrZero(zone_end) != 0.0 and utilities.floatOrZero(zone_Kp) == 0.0 and  \
           utilities.floatOrZero(zone_Kd) == 0.0 and utilities.floatOrZero(zone_boost) != 0.0:
            helpText += zone + " is a 'power profile' zone because both " + zone + " multipliers are zero. " + \
                          "To allow schema version 1.5 all 'power profile' zones must have a boost of zero.\n\n" + \
                          "You could set " + zone + " boost to zero, or set one of the " + zone + " multipliers to non-zero.\n\n" + \
                          "(Multipliers are an 'Expert' feature.)"
            requirement = True
    return {"requirement":requirement, "help":helpText}

def requires_1_7(frame):
    requirement = False
    helpText = ""
    # zone3_start can validly == 0.0 so it is not used in testing.
    zone3_end = utilities.fromMinSec(frame.page4.configControls["zone3_time_end"].GetValue())
    zone3_Kp = frame.page4.configControls["zone3_multiplier_Kp"].GetValue()
    zone3_Kd = frame.page4.configControls["zone3_multiplier_Kd"].GetValue()
    zone3_boost = frame.page4.configControls["zone3_boost"].GetValue()
    if utilities.floatOrZero(zone3_end) != 0.0 and (utilities.floatOrZero(zone3_Kp) != 1.0 or  utilities.floatOrZero(zone3_Kd) != 1.0):
        helpText = "There are non-default zone3 multiplier settings. The zone3 multiplier settings must all be at their default values to allow schema version 1.6.\n\n" + \
                   "(Multipliers are an 'Expert' feature.)"
        requirement = True
    return {"requirement":requirement, "help":helpText}

class propertiesDialog(wx.Dialog):

    HELP_TEXT = """
The schema version tells the roaster what firmware is needed for this profile.
It may change when you edit the profile settings. It is used by the roaster to
alert when you have used settings that require a firmware update.
"""

    HEADINGS = [
        "Schema\nVersion",
        "Firmware\nCompatibility",
        "New\nFeatures"
    ]
    
    def __init__(self, parent):
        super(propertiesDialog, self).__init__(parent) 
        self.parent = parent
        self.SetTitle("File properties")
        self.box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, -1, "Profile schema version")
        font = label.GetFont()
        font.SetWeight(wx.BOLD)
        label.SetFont(font)
        self.box.Add(label,  0, wx.LEFT | wx.TOP | wx.ALIGN_LEFT, 20)
        self.NUMCOLS = 4
        grid = wx.FlexGridSizer(cols=self.NUMCOLS, vgap=5, hgap=0)
        self.firstRadio = True
        self.radioList = []
        self.versionList = []
        updateSchemaVersion(self.parent)
        self.currentSchema = self.parent.page4.configControls['profile_schema_version'].GetValue()
        heading_count = 0
        for heading in self.HEADINGS:
            label = wx.StaticText(self, -1, heading)
            font = label.GetFont()
            font.SetWeight(wx.BOLD)
            label.SetFont(font)
            grid.Add(label,  0, wx.LEFT | wx.ALIGN_LEFT, 20)
            heading_count += 1
        while heading_count < self.NUMCOLS:
            grid.Add(wx.StaticText(self, -1, ""),  0, wx.LEFT | wx.ALIGN_LEFT, 20)
            heading_count += 1
            
        self.addSeparatorRow(grid)
        for data in VERSIONS:
            self.addRow(grid, data, self.currentSchema)
            self.addSeparatorRow(grid)
        if self.currentSchema not in self.versionList:
            self.addRow(grid, {"schema": self.currentSchema, "firmware": "", "notes": "unrecognised version"}, self.currentSchema)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, label='OK')
        buttons.Add(okButton, 1, wx.ALL, 7) # Mac buttons need 7-pixel borders or they overlap
        okButton.SetDefault()
        self.box.Add(wx.StaticText(self, -1, self.HELP_TEXT),  0, wx.ALL | wx.ALIGN_LEFT, 20)
        self.box.Add(grid, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        self.box.Add(buttons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        self.box.SetSizeHints(self)
        self.SetSizer(self.box)
        okButton.Bind(wx.EVT_BUTTON, self.onOk)

    def addSeparatorRow(self, grid):
        for i in range(self.NUMCOLS):
            # 1 pixel high controls don't get borders in OSX or Linux, so use a coloured background
            label = wx.StaticText(self, -1, '', size=(-1,1), style=wx.BORDER_NONE)
            label.SetBackgroundColour("grey")
            grid.Add(label,  0, wx.EXPAND, 0)

    def addRow(self, grid, data, currentSchema):
        radio = wx.RadioButton(self, style=wx.RB_GROUP if self.firstRadio else 0, label=data["schema"], name=data["schema"])
        self.firstRadio = False
        grid.Add(radio, 0, wx.LEFT | wx.ALIGN_LEFT, 20)
        self.radioList.append(radio)
        self.versionList.append(data["schema"])
        if currentSchema == data["schema"]:
            radio.SetValue(True)
        else:
            radio.Disable()
        grid.Add(wx.StaticText(self, -1, data["firmware"]),  0, wx.LEFT | wx.ALIGN_LEFT, 20)
        grid.Add(wx.StaticText(self, -1, data["notes"]),  0, wx.LEFT | wx.ALIGN_LEFT, 20)
        comparison = core_studio.compareProfileSchemaVersions(currentSchema, data["schema"])
        if comparison > 0:
            help_button = wx.Button(self, id=wx.ID_HELP, name=data["schema"])
            grid.Add(help_button,  0, wx.LEFT | wx.ALIGN_LEFT, 20)
            help_button.Bind(wx.EVT_BUTTON, self.onHelp)
        else:
            grid.Add(wx.StaticText(self, -1, ""),  0, wx.LEFT | wx.ALIGN_LEFT, 20)

    def onHelp(self, event):
        wx.MessageBox(calculateSchemaHelp(self.parent, event.EventObject.Name), "Changing schema version", wx.OK, self.parent)        

    def onOk(self, event):
        self.Close()
