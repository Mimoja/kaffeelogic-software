
# coding=utf-8

import core_studio
import wx
import wx.html

import utilities

labelSave = None

class HtmlPopup(wx.Panel):
    def __init__(self, parent, style, html_body_content, bgcolor, size, position):
        self.parent = parent
        if core_studio.isWindows:
            this_style = wx.FRAME_FLOAT_ON_PARENT | wx.TRANSPARENT_WINDOW
        else:
            this_style = style
        wx.Panel.__init__(self, parent, pos=position, style=this_style)
        self.SetBackgroundColour(bgcolor)
        self.bgcolor = bgcolor
        self.html_window = wx.html.HtmlWindow(self, wx.ID_ANY, size=size)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.html_window, 0, wx.ALL, 0)
        self.SetSizer(self.sizer)
        self.setContents(html_body_content)
        self.sizer.Fit(self)
        parent.GetParent().Bind(wx.EVT_LEAVE_WINDOW, on_info_unhover) 
        self.Bind(wx.EVT_LEAVE_WINDOW, on_info_unhover) # This event doesn't fire in Windows, which is why we also bind to the html_window.
        self.html_window.Bind(wx.EVT_LEAVE_WINDOW, on_info_unhover) 
        
    def setContents(self, contents):
        self.html_window.SetPage('<body bgcolor="' + self.bgcolor + '">' + contents + '</body>')
        internal = self.html_window.GetInternalRepresentation()
        if core_studio.isLinux:
            extra = 30
        else:
            extra = 0
        maxHeight = self.parent.GetClientSize()[1] - 20
        desiredHeight = internal.GetHeight()
        chosenHeight = min(desiredHeight, maxHeight)
        self.html_window.SetSize((-1, extra + chosenHeight))
        self.SetSize((-1, chosenHeight))
        self.Layout()
        self.html_window.Refresh()
        
def on_info_hover(event):
    global labelSave
    if type(event) is wx._misc.TimerEvent:
        label = labelSave
        if label is None: return
    else:
        label = event.GetEventObject()
        if label == labelSave: return
    try:
        key = utilities.replaceSpaceWithUnderscore(label.GetLabel())
        parent = label.GetParent()
    except wx.PyDeadObjectError as e:
        return
    parent.hover.setContents(parent.frame.appendRecommendations(key, formatHint(parent.frame.hints, key)))
    labelSave = label
    shift_x = 2
    shift_y = 10
    label_position = label.GetPosition()
    label_size = label.GetSize()
    parent_size = parent.GetSize()
    hover_size = parent.hover.html_window.GetSize()
    label_lowest_viable_Y = parent_size[1] - hover_size[1]
    if label_position[1] > label_lowest_viable_Y:
        label_position[1] = label_lowest_viable_Y
    parent.hover.SetPosition((label_position[0] + label_size[0] + shift_x, label_position[1] - shift_y))
    parent.hover.Raise()
    parent.hover.Show()
    if core_studio.isMac and isinstance(parent.focusObject, wx.TextCtrl) and isScrolledIntoView(parent, parent.focusObject):
        parent.hover.SetFocus()
        
    # This jiggery-pokery takes place because in Windows the TextCtrl has a border that sometimes sits on top of the hover Panel. After
    # extensive experimentation this technique appears to work fixing the bug (apart from the unwanted flicker),
    # and at the same time will not cause any issues wherever the bug is not present except for Ubuntu.
    if core_studio.isWindows and type(event) is not wx._misc.TimerEvent:
        
        parent.ontimer = utilities.SafeTimer(parent)
        parent.Bind(wx.EVT_TIMER, on_info_hover)
        parent.ontimer.Start(700, oneShot=wx.TIMER_ONE_SHOT)
        event.Skip()

def isScrolledIntoView(parent, child):
    return child.GetRect()[1] + child.GetRect()[3] >= 0 and child.GetRect()[1] < parent.GetRect()[3]

def on_info_unhover(event):
    global labelSave
    label = labelSave
    if label is None: return
    try:
        parent = label.GetParent() # label may have disappeared due to tab change, etc
    except:
        event.Skip()
        return
    # Now that we have the parent, we can assess the hover. If the mouse is still over the hover then don't hide it yet.
    if parent.hover.GetScreenRect().Contains(wx.GetMousePosition()):
        event.Skip()
        return
    try:
        parent.ontimer.Stop()
    except:
        pass
    if core_studio.isMac and isinstance(parent.focusObject, wx.TextCtrl) and isScrolledIntoView(parent, parent.focusObject):
        parent.focusObject.SetFocus()
    parent.hover.Hide()
    labelSave = None
    event.Skip()

def formatHint(hints, key):
    if key in hints.keys():
        hint = hints[key]
        html = "<p><b>" + utilities.replaceUnderscoreWithSpace(key) + "</b> <i>" + hint["difficulty"] + "</i>"
        unit = hint["unit"] if hint["unit"] != 'no unit' else ''
        default = utilities.trimTrailingPointZero(unicode(wx.App.Get().frame.defaults[key])) if hint["key"] in wx.App.Get().frame.defaults.keys() else ""
        if len(default) > 0 and hint["key"] != 'profile_schema_version':
            html += "<p>Default: " + default + " " + unit
        else:
            if len(unit)  > 0:
                html += "<p>" + unit
        html += "<p>" + hint["text"]
    else:
        html = "<p><i>" + utilities.replaceUnderscoreWithSpace(key) + "</i> is not recognised as part of profile schema version " + core_studio.DESIGNED_FOR_PROFILE_SCHEMA_VERSION + ". "
        html += "It is recommended that you update " + core_studio.PROGRAM_NAME + "."
    return html
    """{"key": entry[0], "difficulty": entry[1], "unit": entry[2], "text": entry[3]}"""

