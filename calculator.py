#coding:utf-8
from __future__ import division
from utilities import toMinSec, fromMinSec, trimTrailingPointZero
from core_studio import isLinux
import wx, re, userOptions

########################################################################
def setText(obj, txt):
    if hasattr(obj, 'SetValue'):
        obj.ChangeValue(txt)
    else:
        obj.SetLabel(txt)

def getText(obj):
    if hasattr(obj, 'GetValue'):
        return obj.GetValue()
    else:
        return obj.GetLabel()        
########################################################################

class calculateDialog(wx.Dialog):
    
    def __init__(self, parent):
        super(calculateDialog, self).__init__(parent) 
        self.InitUI(parent)
        self.SetTitle("Time calculator")
        
    def InitUI(self, parent):
        self.parent = parent
        box = wx.BoxSizer(wx.VERTICAL)
        grid = wx.FlexGridSizer(3, 3, 5, 5)
        self.grid = grid

        TEXTCRL_WIDTH = 150
        label = wx.StaticText(self, -1, u"Mem")
        grid.Add(label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.store_min_sec = wx.TextCtrl(self, -1, '', name='store_min_sec', size=(TEXTCRL_WIDTH, -1))
        self.store_min_sec.Disable()
        grid.Add(self.store_min_sec, 0, wx.EXPAND)
        self.store_sec = wx.TextCtrl(self, -1, '', name='store_sec', size=(TEXTCRL_WIDTH, -1))
        self.store_sec.Disable()
        grid.Add(self.store_sec, 0, wx.EXPAND)

        self.parenthesisLabel = wx.StaticText(self, -1, u"")
        grid.Add(self.parenthesisLabel, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.intermediate_min_sec = wx.TextCtrl(self, -1, '', name='intermediate_min_sec', size=(TEXTCRL_WIDTH, -1))
        self.intermediate_min_sec.Disable()
        grid.Add(self.intermediate_min_sec, 0, wx.EXPAND)
        self.intermediate_sec = wx.TextCtrl(self, -1, '', name='intermediate_sec', size=(TEXTCRL_WIDTH, -1))
        self.intermediate_sec.Disable()
        grid.Add(self.intermediate_sec, 0, wx.EXPAND)

        label = wx.StaticText(self, -1, u"")
        grid.Add(label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.answer_min_sec = wx.TextCtrl(self, -1, '', name='answer_min_sec', style=wx.TE_PROCESS_ENTER, size=(TEXTCRL_WIDTH, -1)) 
        self.answer_min_sec.Bind(wx.EVT_TEXT_ENTER, self.onEnter)

        grid.Add(self.answer_min_sec, 0, wx.EXPAND)
        self.answer_sec = wx.TextCtrl(self, -1, '', name='answer_sec', size=(TEXTCRL_WIDTH, -1))
        self.answer_sec.Disable()
        grid.Add(self.answer_sec, 0, wx.EXPAND)

        buttonGrid = wx.FlexGridSizer(6, 2, 1, 1)
        for txt in ['+','-',u'×', u'÷', 'Mem Sto','Mem Rcl','(',')','Clr','Mem Clr', '%','=']: self.addButton(buttonGrid, txt)
        
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        closeButton = wx.Button(self, label='Close')
        buttons.Add(closeButton, 1, wx.ALL, 7)
        box.Add(grid, 0, wx.ALL, 10)
        label = wx.StaticText(self, -1, u"Times can be entered in min:sec format, or as seconds.")
        box.Add(label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 10)

        box.Add(buttonGrid, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.Add(buttons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.SetSizeHints(self)
        self.SetSizer(box)
        
        closeButton.Bind(wx.EVT_BUTTON, self.onClose)
        self.Bind(wx.EVT_CLOSE, self.onCloseEvent)
        
        self.answer_min_sec.Bind(wx.EVT_KEY_DOWN, self.onKey)
        self.answer_min_sec.Bind(wx.EVT_CHAR, self.onChar)

        presets = userOptions.textToListOfStrings(self.parent.options.getUserOption("time-calculator"))
        if len(presets) >= 1: setText(self.store_min_sec, presets[0])
        if len(presets) >= 2: setText(self.intermediate_min_sec, presets[1])
        if len(presets) >= 3: setText(self.answer_min_sec, presets[2])
        
        self.isAnswerDisplayed = False
        self.parenthesisStack = []
        
        if not isLinux: self.Raise()
        self.updateSecsElements()
        wx.CallAfter(self.answer_min_sec.SetFocus)

    def addButton(self, grid, label):
        button = wx.Button(self, label=label, size=(80, -1))
        grid.Add(button, 1, wx.ALL, 1) # Mac buttons need 7-pixel borders or they overlap
        button.Bind(wx.EVT_BUTTON, self.onButton)
        if label == '(':
            self.leftParenthesisButton = button

    def focusAndClearSelection(self, ctrl):
        self.answer_min_sec.SetFocus()
        a, b = self.answer_min_sec.GetSelection()
        if a != b: self.answer_min_sec.SetSelection(b, b)
        
    def onButton(self, event):
        label =event.EventObject.GetLabel()
        if label.lower().endswith('sto'): char = 'S'
        elif label.lower().endswith('rcl'): char = 'R'
        else: char = label[0]
        self.processChar(None, char)
        self.focusAndClearSelection(self.answer_min_sec)

    def updateSecsElement(self, minSec, secs, isPercent=False):
        txt = re.sub(r'\D?$', '', getText(minSec), 1)
        sec = fromMinSec(self.filterString(self.makeNumericString(txt)))
        if sec == '' or sec is None:
            sec = ''
        else:
            if isPercent:
                sec = str(float(sec) * 100.0) + ' %'
            else:
                sec = str(float(sec)) + ' secs'
        setText(secs, sec)
        setText(self.parenthesisLabel, '(' * len(self.parenthesisStack))
        self.grid.Layout()
        if len(self.parenthesisStack) > 0:
            self.leftParenthesisButton.SetForegroundColour('red')
        else:
            self.leftParenthesisButton.SetForegroundColour(wx.NullColour)

    def updateSecsElements(self, isPercent=False):
        self.updateSecsElement(self.answer_min_sec, self.answer_sec, isPercent)            
        self.updateSecsElement(self.intermediate_min_sec, self.intermediate_sec)
        self.updateSecsElement(self.store_min_sec, self.store_sec)

    def makeNumericString(self, s):
        return re.sub(r"[^0123456789:.-]", "", s)

    def filterString(self, s):
        s = s.strip()
        while len(re.findall(':', s)) > 1:
            s = re.sub(':', '', s, 1)
        while len(re.findall(r'\.', s)) > 1:
            s = re.sub(r'\.', '', s, 1)
        while len(re.findall('(?<!^)-', s)) > 0:
            s = re.sub('(^.+?)-', r'\g<1>', s)
        if s is None or s == '': return ''
        if s[0] == ':': s = '0' + s
        if s[-1] == ':': s = s + '00'
        if s[-1] == '.': s = s + '0'
        if s == '-': s = '-0'
        return s
        
    def onEnter(self, event):
        self.onEqual(None)
        self.focusAndClearSelection(self.answer_min_sec)

    def onKey(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER:
            self.onEqual(None)
            self.focusAndClearSelection(self.answer_min_sec)
        elif keycode == wx.WXK_ESCAPE:
            self.processChar(event, 'C')
        elif keycode in [wx.WXK_UP, wx.WXK_DOWN]:
            return
        else:
            event.Skip()

    def onChar(self, event):
        unikeycode = event.GetUnicodeKey()
        if unikeycode == wx.WXK_NONE:
            event.Skip()
            return
        char = unichr(unikeycode)
        self.processChar(event, char)

    def processChar(self, event, char):
        if char in '%=': 
            self.onEqual(None, isPercent=(char=='%'))
            return
        if char == ')':
            self.compute()
            if len(self.parenthesisStack) > 0:
                setText(self.intermediate_min_sec, self.parenthesisStack.pop())
                self.isAnswerDisplayed = False
        wx.CallAfter(self.updateSecsElements)
        if char == '(':
            if self.isAnswerDisplayed or getText(self.answer_min_sec) != '':
                self.isAnswerDisplayed = False
                setText(self.intermediate_min_sec, '')
                self.parenthesisStack = []
            setText(self.answer_min_sec, '')
            self.parenthesisStack.append(getText(self.intermediate_min_sec))
            setText(self.intermediate_min_sec, '')
        if char == 'C':
            setText(self.answer_min_sec, '')
            setText(self.intermediate_min_sec, '')
            self.parenthesisStack = []
            return
        if char == 'M':
            setText(self.store_min_sec, '')
            return
        elif char == 'S':
            setText(self.store_min_sec, getText(self.answer_min_sec))
            return
        elif char == 'R':
            setText(self.answer_min_sec, getText(self.store_min_sec))
            return
        if char not in u"()+-*×x/÷%=":
            if char == chr(wx.WXK_NONE) or ord(char) < ord(' ') or char in "0123456789.:":
                if self.isAnswerDisplayed:
                    setText(self.answer_min_sec, '')
                    self.isAnswerDisplayed = False
                if event is not None:
                    event.Skip()
        if char == '-' and getText(self.answer_min_sec) == '':
            self.isAnswerDisplayed = False
            if event is not None: event.Skip()
            return
        if char in u"-+*×x/÷" and getText(self.answer_min_sec) != '':
            if char in '*x': char = u'×'
            if char == '/': char = u'÷'
            if getText(self.intermediate_min_sec) != '':
                self.compute()
                self.focusAndClearSelection(self.answer_min_sec)
            setText(self.intermediate_min_sec, trimTrailingPointZero(toMinSec(self.filterString(self.makeNumericString(getText(self.answer_min_sec))), wholeSecs = False)) + char)
            setText(self.answer_min_sec, '')
        
    def onEqual(self, e, isPercent=False):
        self.compute(isPercent)
        while len(self.parenthesisStack) > 0:
            setText(self.intermediate_min_sec, self.parenthesisStack.pop())
            self.compute(isPercent)

    def compute(self, isPercent=False):
        try:
            time = float(fromMinSec(self.filterString(getText(self.answer_min_sec))))
        except:
            time = 0
        s = getText(self.intermediate_min_sec)
        if s != '':
            intermediate = float(fromMinSec(s[:-1]))
            op = s[-1]
            if op == '+':
                answer = intermediate + time
            elif op == '-':
                answer =  intermediate - time
            elif op == '*' or op == u'×':
                answer =  intermediate * time
            elif op == '/' or op == u'÷':
                if time == 0.0:
                    answer = 0.0
                else:
                    answer =  intermediate / time
        else:
            answer = time
        setText(self.answer_min_sec, trimTrailingPointZero(toMinSec(answer, wholeSecs = False)))
        self.isAnswerDisplayed = True
        setText(self.intermediate_min_sec, '')
        self.updateSecsElements(isPercent)
        
    def onClose(self, e):
        self.Close()

    def onCloseEvent(self, event):
        presets = [getText(self.store_min_sec), getText(self.intermediate_min_sec), getText(self.answer_min_sec)]
        self.parent.options.setUserOption("time-calculator", userOptions.listOfStringsToText(presets))
        event.Skip()
