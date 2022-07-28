import wx
import wx.adv
import threading
import os
import platform
from timeit import default_timer as timer

import utilities
from global_strings import *

IS_MAC = platform.platform().lower().startswith('darwin')
if IS_MAC:
    import subprocess

class myCommandEvent(wx.PyCommandEvent):
    def GetActive(self):
        return True

########################################################################
class mySplash():
    def __init__(self):
        # create, show and return the splash screen
        bitmap = wx.Bitmap(utilities.getProgramPath() + 'splash.png')
        self._splash = wx.adv.SplashScreen(bitmap, wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_NO_TIMEOUT, 0, None, -1, style=wx.BORDER_SIMPLE|wx.FRAME_NO_TASKBAR|wx.STAY_ON_TOP)
        self.start = timer()
        self._splash.Show()
        wx.Yield()

    def fadeOut(self):
        try:
            # Another Mac weirdness - sometimes HideWithEffect is throwing
            # PyAssertionError: C++ assertion "event" failed at /BUILD/wxPython-src-3.0.2.0/src/common/event.cpp(1248) in QueueEvent(): NULL event can't be posted
            self._splash.HideWithEffect(wx.SHOW_EFFECT_BLEND, 1000)
        except wx.PyAssertionError:
            pass
        except RuntimeError:
            return
        self._splash.Destroy()

    def destroy(self):
        frame = wx.App.Get().frame
        if IS_MAC and not utilities.getProgramPath().lower().startswith('/users/'):
            subprocess.Popen(['osascript', '-e', '''\
                tell application "''' + PROGRAM_NAME + '''" to activate
            '''])
            # Note: nothing else worked!! Macs are weird.
        wx.App.Get().doRaise()
        self.end = timer()
        MINIMUM = 3.0 #secs
        elapsed = self.end - self.start
        extra = 300 # millisecs
        wait = extra if elapsed >= MINIMUM else int((MINIMUM - elapsed) * 1000) + extra
        wx.CallLater(wait, self.fadeOut)
########################################################################

class myApp(wx.App):
    def __init__(self, *args, **kwargs):
        self.timeToKillThreads = threading.Event()
        wx.App.__init__(self, *args, **kwargs)

    def doRaise(self):
        top = self.GetTopWindow()
        top.Iconize(False)
        top.Show(True)
        top.Raise()
        dialogs = [w for w in self.GetTopWindow().GetChildren() if w.GetName() == 'dialog']
        for dialog in dialogs:
            dialog.Raise()

    def onActivate(self, event):
        # if this is an activate event, rather than something else, like iconize.
        if DEBUG_MACEVENTS and event.GetActive():
            wx.MessageBox("You activated.")
        if event.GetActive():
            try:
                self.doRaise()
            except:
                pass
        event.Skip()

    def MacReopenApp(self):
        if DEBUG_MACEVENTS:
            wx.MessageBox("You reopened.")
        self.doRaise()

    def MacOpenFiles(self, filenames):
        """
        This method is called when a file is dropped, and the app is already open.
        If the app is not open when the file is dropped, then the normal argv parameter is provided.
        """
        if DEBUG_MACEVENTS:
            wx.MessageBox("You requested to open this file by dropping it:\n\"%s\"" % filenames[0])
        if len(filenames) > 0:
            f = utilities.ensureUnicode(filenames[0])
            if os.path.isfile(f):
                self.frame.openDroppedFile(f)

    def killThreads(self):
        self.timeToKillThreads.set()
        # doesn't actively kill anything, instead wait for all threads to terminate
        main_thread = threading.current_thread()
        for t in threading.enumerate():
            if t is main_thread:
                continue
            if hasattr(t, 'canJoin') and t.canJoin is True:
                # print('joining', t.getName())
                t.join()

    def onSize(self, e):
        """
        Weird Mac full screen bug workaround,
        this variable is monitored in a different thread from userOptions.py
        """
        self.frame.fullscreen = e.GetSize()[1] + self.frame.GetPosition()[1] >= wx.GetDisplaySize()[1] and \
                                e.GetSize()[0] == wx.GetDisplaySize()[0]
        e.Skip()

def myInit(self, splash):
    self.SetAppDisplayName(core_studio.PROGRAM_NAME)
    self.SetAppName(core_studio.PROGRAM_NAME)
    self.frame = core_studio.MyGraph(self)
    self.frame.fullscreen = False
    self.frame.fullscreenWasActive = False
    self.SetTopWindow(self.frame)
    # This catches events when the app is asked to activate by some other process
    self.Bind(wx.EVT_ACTIVATE_APP, self.onActivate)
    if IS_MAC:
        self.frame.Bind(wx.EVT_SIZE, self.onSize)
    splash.destroy()

app = myApp(False)
app.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
splash = mySplash()
import core_studio
myInit(app, splash)
app.MainLoop()
