#coding:utf-8
import webbrowser

import wx, re
import core_studio


########################################################################
class saveIfModifiedDialog(wx.Dialog):

    def __init__(self, *args, **kw):
        super(saveIfModifiedDialog, self).__init__(*args, **kw)
        self.InitUI()
        self.SetTitle("You have unsaved changes")

    def InitUI(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        saveButton = wx.Button(self, label='Save')
        discardButton = wx.Button(self, label='Discard changes')
        cancelButton = wx.Button(self, label='Cancel')
        box.Add(saveButton, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)
        box.Add(discardButton, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)
        box.Add(cancelButton, 0, wx.ALL, 15)
        box.SetSizeHints(self)
        self.SetSizer(box)
        saveButton.Bind(wx.EVT_BUTTON, self.onSave)
        discardButton.Bind(wx.EVT_BUTTON, self.onDiscard)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
        self.result = "cancel"
        if not core_studio.isLinux: self.Raise()

    def onSave(self, e):
        self.result = "save"
        self.Close()

    def onDiscard(self, e):
        self.result = "discard"
        self.Close()

    def onCancel(self, e):
        self.Close()

########################################################################
def handleFullscreen(obj):
    wx.CallLater(1000, handleFullscreenAfter, obj)

def handleFullscreenAfter(obj):
    """
    weird Mac workaround to prevent black screen
    """
    dialog = enteringFullscreenDialog(obj, style=0)
    dialog.ShowModal()
    dialog.Destroy()

class enteringFullscreenDialog(wx.Dialog):

    def __init__(self, *args, **kw):
        super(enteringFullscreenDialog, self).__init__(*args, **kw)
        self.InitUI()
        self.SetTitle("")
        wx.CallLater(1000, self.Close)

    def InitUI(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Full screen")
        box.Add(label, 0, wx.ALL, 15)
        box.SetSizeHints(self)
        self.SetSizer(box)
        self.Raise()

########################################################################
class externallyModifiedDialog(wx.Dialog):

    def __init__(self, parent, modified):
        super(externallyModifiedDialog, self).__init__(parent)
        self.modified = modified
        self.InitUI()
        self.SetTitle("File edited in another window or by another app")

    def InitUI(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        outerBox = wx.BoxSizer(wx.VERTICAL)
        updateButton = wx.Button(self, label='Update to match the other window or app')
        discardButton = wx.Button(self, label='Ignore the other window or app')
        box.Add(updateButton, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)
        box.Add(discardButton, 0, wx.ALL, 15)
        if self.modified:
            outerBox.Add(wx.StaticText(self,
                                       -1,
                                       'The most recent changes you have made in this window will be lost if you update to match the other window.'),
                         0,
                         wx.CENTER | wx.ALL,
                         5)
        outerBox.Add(box, 0, wx.CENTER, 0)
        outerBox.SetSizeHints(self)
        self.SetSizer(outerBox)
        updateButton.Bind(wx.EVT_BUTTON, self.onUpdate)
        discardButton.Bind(wx.EVT_BUTTON, self.onDiscard)
        self.result = "discard"
        if not core_studio.isLinux: self.Raise()

    def onUpdate(self, e):
        self.result = "update"
        self.Close()

    def onDiscard(self, e):
        self.result = "discard"
        self.Close()

class wxHTML(wx.html.HtmlWindow):
    def __init__(self, *args, **kwargs):
        wx.html.HtmlWindow.__init__(self, *args, **kwargs)
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)

    def OnLinkClicked(self, link):
        """
        Opens the link in the browser.
        Unless href is "function:" in which case it calls the named function, and
        if target is specified it is passed to the named function as the first parameter, otherwise None is passed.
        """
        href = link.GetHref()
        target = link.GetTarget()
        if href.startswith('function:'):
            if len(target) == 0:
                target = None
            functionName = re.sub('^function:', '', href).strip()
            p = self.GetParent()
            while (not hasattr(p, functionName)) and (not p.IsTopLevel()):
                p = p.GetParent()
            if (not hasattr(p, functionName)) and (p.IsTopLevel()): raise Exception(functionName + " not found in any parent object")
            getattr(p, functionName)(target) # execute the function with one parameter          
        else:
            webbrowser.open(href, new=2)
        if hasattr(self.GetParent(), 'exitOnLinkClick') and self.GetParent().exitOnLinkClick: self.onOk(None)
        
    def onKeyPress(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN:
            self.onOk(event)
        event.Skip()

    def onOk(self, e):
        p = self.GetParent()
        while not p.IsTopLevel():
            p = p.GetParent()
        p.result = wx.ID_OK
        p.Close()

    def onMiddle(self, e):
        self.GetParent().result = wx.ID_APPLY
        self.GetParent().Close()

    def onCancel(self, e):
        self.GetParent().result = wx.ID_CANCEL
        self.GetParent().Close()

########################################################################
class enhancedMessageDialog(wx.Dialog):    
    def __init__(self, *args, **kwargs):
        try:
            wx.App.Get().doRaise()
        except:
            pass
        super(enhancedMessageDialog, self).__init__(*args, **kwargs)

    def init(self, messageText, messageTitle,
             okButtonText='Close', allowCancel=False,
             middleButtonText=None,
             checkBox=None, checkBoxText='', wideFormat=False, exitOnLinkClick=False):
        """
        If messageText is a list of strings containing HTML, then multiple text boxes are created with
        lines separating them, one checkbox is assigned to each text box.
        
        messageText     -   HTML
        messageTitle    -   Window title
        okButtonText    -   If specified the text on the button will be changed, it will still function as an OK button and return wx.ID_OK
        middleButtonText-   If specified there will be a button using this text that returns wx.ID_APPLY
        allowCancel     -   If true there will also be a cancel button that returns wx.ID_CANCEL
        checkBox        -   If None there will not be a checkbox, if True/False the check box will appear and initialised to Checked/Unchecked
        checkBoxText    -   If a check box appears this text will be used to label it

        results:
        self.result     -   Set to wx.ID_OK or wx.ID_CANCEL
        self.getCheckBox()  Returns None if there is no check box, True/False if there is a check box corresponding to Checked/Unchecked
        """
        maxWidth, maxHeight = wx.GetDisplaySize()
        self.SetTitle(messageTitle)
        self.result = wx.ID_CANCEL
        self.checkBoxes = []
        self.exitOnLinkClick = exitOnLinkClick
        box = wx.BoxSizer(wx.VERTICAL)
        if not isinstance(messageText, list):
            messageText = [messageText]
        if not isinstance(checkBox, list):
            checkBox = [checkBox]
        if checkBoxText is None:
            checkBoxText = ''
        if not isinstance(checkBoxText, list):
            checkBoxText = [checkBoxText]
        while len(checkBox) < len(messageText):
            checkBox.append(None)

        htmlObjList = []
        DEFAULT_HEIGHT = 0
        for index in range(len(messageText)):
            html = wxHTML(self, -1, size=(maxWidth * 0.90 if wideFormat else 550, DEFAULT_HEIGHT))
            message = "<body><p>" + messageText[index] + "</p></body>"
            htmlObjList.append((html, message))
            box.Add(html, 1, wx.GROW | wx.TOP | wx.LEFT | wx.RIGHT, 10)
            checkBoxItem = checkBox[index]
            if checkBoxItem is not None:
                checks = wx.BoxSizer(wx.HORIZONTAL)
                self.checkBoxes.append(wx.CheckBox(self, -1))
                self.checkBoxes[index].SetValue(checkBoxItem)
                label = wx.StaticText(self, -1, checkBoxText[index])
                checks.Add(self.checkBoxes[index], 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
                checks.Add(label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
                box.Add(checks, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.ALIGN_LEFT, 10)

        okButton = wx.Button(self, label=okButtonText)
        if middleButtonText is None and not allowCancel:
            box.Add(okButton, 0 , wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        else:
            buttons = wx.BoxSizer(wx.HORIZONTAL)
            buttons.Add(okButton, 1, wx.ALL, 7) # Mac buttons need 7-pixel borders or they overlap
            if middleButtonText is not None:
                middleButton = wx.Button(self, label=middleButtonText)
                buttons.Add(middleButton, 1, wx.ALL, 7)
                middleButton.Bind(wx.EVT_BUTTON, html.onMiddle)
            if allowCancel:
                cancelButton = wx.Button(self, label='Cancel')
                buttons.Add(cancelButton, 1, wx.ALL, 7) # Mac buttons need 7-pixel borders or they overlap
                cancelButton.Bind(wx.EVT_BUTTON, html.onCancel)
            box.Add(buttons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        okButton.Bind(wx.EVT_BUTTON, html.onOk)
        okButton.SetDefault()
        self.SetSizer(box)
        overallDesiredHeight = 0
        for obj in htmlObjList:
            html, message = obj
            html.SetPage(message)
            internal = html.GetInternalRepresentation()
            if core_studio.isLinux:
                extra = 15
            else:
                extra = 0
            desiredHeight = min(extra + internal.GetHeight() * 1.2, maxHeight * 0.70)
            html.SetSize((-1, desiredHeight))
            overallDesiredHeight += desiredHeight
            self.Fit()
            self.SetSize((maxWidth * 0.90 if wideFormat else -1, self.GetSize()[1] - DEFAULT_HEIGHT * len(htmlObjList) + overallDesiredHeight))
            self.Layout()
        if not core_studio.isLinux: self.Raise()

    def getCheckBox(self, index=0):
        if index is None or len(self.checkBoxes) == 0 or index >= len(self.checkBoxes) or self.checkBoxes[index] is None: return None
        return self.checkBoxes[index].GetValue()
