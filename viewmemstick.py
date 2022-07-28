# -*- coding: utf-8 -*-
import os, sys, shutil, zipfile, threading, re, wx, urllib3
import core_studio, removabledrive, dialogs, utilities

########################################################################
PAGES = ["Logs", "Profiles", "Core profiles", "Firmware"]

def ellipsis(txt, ln):
    return re.sub(r'\s\S*$', ' ...', txt[:ln])

class showMemstickDialog(wx.Dialog):

    def saveCoreProfiles(self, obj, data, errorMessage, extra, flag):
        try:
            self.parent
        except wx.PyDeadObjectError:
            return

        self.dataFolder = self.parent.options.programDataFolder
        self.downloadsFolder = self.dataFolder + os.sep + 'downloads'

        if errorMessage is None:
            errorConnecting = False
            fileName = self.dataFolder + os.sep + 'downloaded.zip'
            try:
                with open(fileName, 'wb') as output:
                     output.write(data)
            except IOError as e:
                dial = wx.MessageDialog(None,
                                        'This file could not be saved.\n' + fileName + '\n' + e.strerror + '.',
                                        'Error',
                                        wx.OK | wx.ICON_EXCLAMATION)
                dial.ShowModal()
                flag.clear()
                return

            if os.path.exists(self.downloadsFolder):
                try:
                    shutil.rmtree(self.downloadsFolder)
                except:
                    errorMessage = "Unable to update all local copies of the files. At least one file is write protected or open in another app."
            try:
                zip = zipfile.ZipFile(fileName)
                zip.extractall(self.downloadsFolder)
                zip.close()
            except:
                if errorMessage is None:
                    errorMessage = 'Unzip failed.'
            if os.path.exists(self.downloadsFolder + os.sep + '__MACOSX'):
                shutil.rmtree(self.downloadsFolder + os.sep + '__MACOSX')
        else:
            errorConnecting = True
        flag.clear()
        self.displayCoreProfilesStatus(errorMessage, errorConnecting, extra)

    def useLocal(self, target):
        self.displayCoreProfilesStatus(None, False, self.notebook.GetPage(PAGES.index("Core profiles")).htmlObject)

    def downloadCoreProfiles(self, target):
        if self.coreProfilesIsRunning.is_set(): return
        self.coreProfilesIsRunning.set()
        htmlString = '<h2>Core profile set</h2>'
        htmlString += "<p>Downloading...</p>"
        self.notebook.GetPage(PAGES.index("Core profiles")).htmlObject.SetPage(htmlString)
        worker = GetURL_Thread(self, self.saveCoreProfiles,
                               core_studio.CORE_PROFILES_ZIP_URL,
                               extra=target,
                               flag=self.coreProfilesIsRunning)
        worker.start()

    def displayCoreProfilesStatus(self, errorMessage, errorConnecting, htmlObject):
        try:
            self.parent
        except wx.PyDeadObjectError:
            return
        """
        we assume the zip contains only one folder
        """
        if os.path.exists(self.downloadsFolder):
            zipFolderList = [x for x in os.listdir(self.downloadsFolder) if os.path.isdir(self.downloadsFolder + os.sep + x)]
        else:
            zipFolderList = []        
        self.zipFolder = zipFolderList[0] if len(zipFolderList) > 0 else ''
        self.unzippedFolder = self.downloadsFolder + os.sep + self.zipFolder
        manualsFolder = self.unzippedFolder + os.sep + 'manuals'
        USB_dir = core_studio.USB_PROFILE_DIR
        coreProfilesFolder = self.unzippedFolder + os.sep + USB_dir
        htmlString = '<h2>Core profile set</h2>'
        if errorMessage is None:
            htmlString += '<p><table width=100%><tr><td>'
            htmlString += 'The core profiles are a set of roast profiles that allow you to fine tune your roast '
            htmlString += 'profile to your coffee and your tastes. Read the guide and view the map:'
            htmlString += '</td><td><a href="function:downloadCoreProfilesAgain">Download again</a></td></tr></table></p>'
            htmlString += '<ul>'
            manuals = [os.path.basename(x) for x in os.listdir(manualsFolder) if 'core profile guide' in x.lower() or 'map of coffee' in x.lower()]
            for manual in manuals:
                htmlString += '<li><a href="function:sysOpen" target="' + manualsFolder + os.sep + manual + '">' + manual + '</a></li>'
            htmlString += '</ul>'
            suffix = 'kpro'
            tableColumns = ['profile_short_name', 'profile_modified']
            sort = True
            if self.parent.currentRemovableDrive is None:
                htmlString = '<p>No memory stick found</p>'
            else:
                thisDir = self.parent.currentRemovableDrive + core_studio.USB_KAFFELOGIC_DIR + os.sep + USB_dir
                if os.path.exists(thisDir):
                    usb_files = core_studio.dirToKeyValuesArray(thisDir, tableColumns, suffix, sort)
                else:
                    usb_files =[]
                if os.path.exists(coreProfilesFolder):
                    self.core_files = core_studio.dirToKeyValuesArray(coreProfilesFolder, tableColumns, suffix, sort)
                else:
                    core_files = []
                for core_f in self.core_files:
                    core_f['fname_matches'] = [x['profile_file_name'] for x in usb_files if x['profile_file_name'] == core_f['profile_file_name']]
                    core_f['short_matches'] = [x['profile_file_name'] for x in usb_files if x['profile_short_name'] == core_f['profile_short_name']]
                    if len(core_f['short_matches']) >= 1:
                        if len(core_f['fname_matches']) == 1:
                            if core_f['short_matches'][0] == core_f['fname_matches'][0]:
                                core_f['replace_me'] = core_f['short_matches'][0]
                                core_f['rename'] = False
                            else:
                                core_f['replace_me'] = core_f['short_matches'][0]
                                core_f['rename'] = True
                        else:
                            core_f['replace_me'] = core_f['short_matches'][0]
                            core_f['rename'] = False
                    else:
                        if len(core_f['fname_matches']) == 1:
                            core_f['replace_me'] = core_f['fname_matches'][0]
                            core_f['rename'] = False
                        else:
                            core_f['replace_me'] = ''
                            core_f['rename'] = False
                htmlString += '<hr>'
                htmlString += '<p><a href="function:copyCoreProfiles">Copy/replace all core profiles on ' +  self.memstick + '</a></p>'
                htmlString += '<p><table bgcolor="#e0e0e0"><tr><td><b>On Kaffelogic web site</b></td><td></td><td><b>On ' + self.memstick + '</b></td></tr>'
                for core_f in self.core_files:
                    htmlString += '<tr><td bgcolor="#c0c0c0">' + core_f['profile_file_name'] + u'</td><td>»</td><td bgcolor="#c0c0c0">' + core_f['replace_me'] + '</td></tr>'
                htmlString += '</table></p>'
        else:
            if errorConnecting:
                htmlString += UNABLE_TO_CONNECT_MESSAGE.replace('[[errorMessage]]', errorMessage)
            else:
                htmlString += errorMessage
            if os.path.exists(coreProfilesFolder):
                htmlString += '<p><a href="function:useLocal">Use local copy</a></p>'
        htmlObject.SetPage(htmlString)

    def copyCoreProfiles(self, target):
        htmlObj = self.notebook.GetPage(PAGES.index("Core profiles")).htmlObject
        htmlObj.SetPage('<p>copying files to ' + self.memstick + ' ...</p>')
        wx.CallAfter(self.copyCoreProfilesMain)
        
    def copyCoreProfilesMain(self):
        errorMessage = None
        if self.parent.currentRemovableDrive is not None:
            thisDir = self.parent.currentRemovableDrive + core_studio.USB_KAFFELOGIC_DIR + os.sep + core_studio.USB_PROFILE_DIR
            coreProfilesFolder = self.unzippedFolder + os.sep + core_studio.USB_PROFILE_DIR
            if self.parent.ensureFolderExists(thisDir):
                for core_f in self.core_files:
                    if core_f['replace_me'] != '' and os.path.exists(thisDir + os.sep + core_f['replace_me']):
                        try:
                            os.remove(thisDir + os.sep + core_f['replace_me'])
                        except:
                            pass
                    destination = thisDir + os.sep + core_f['profile_file_name']
                    if core_f['rename']:
                        n = 0
                        root, ext = os.path.splitext(destination)
                        while os.path.exists(destination):
                            n += 1
                            destination = root + ' (' + str(n) + ')' + ext
                    try:
                        shutil.copy(coreProfilesFolder + os.sep + core_f['profile_file_name'], destination)
                    except Exception as e:
                        errorMessage = str(e)
            else:
                dial = wx.MessageDialog(None, 'There was a problem creating the profiles folder.', 'Error',
                                        wx.OK | wx.ICON_EXCLAMATION)
                dial.ShowModal()
        self.displayCoreProfilesStatus(errorMessage, False, self.notebook.GetPage(PAGES.index("Core profiles")).htmlObject)

    def sysOpen(self, target):
        utilities.system_open(target)

    def saveDownload(self, obj, data, errorMessage, extra, flag):
        try:
            self.parent
        except wx.PyDeadObjectError:
            return
        if errorMessage is None:
            d = self.parent.currentRemovableDrive + core_studio.USB_KAFFELOGIC_DIR + os.sep + core_studio.USB_FIRMWARE_DIR
            if self.parent.ensureFolderExists(d):
                fileName = d + os.sep + core_studio.MODEL_NUMBER + '-' + extra + '.bin'
                try:
                    with open(fileName, 'wb') as output:
                        output.write(data)
                except IOError as e:
                    dial = wx.MessageDialog(None,
                                            'This file could not be saved.\n' + fileName + '\n' + e.strerror + '.',
                                            'Error',
                                            wx.OK | wx.ICON_EXCLAMATION)
                    dial.ShowModal()
                    flag.clear()
                    return
            worker = GetURL_Thread(self, self.displayFirmwareStatus, url=core_studio.FIRMWARE_RELEASE_NOTES_URL,
                                   extra=self.notebook.GetPage(PAGES.index("Firmware")).htmlObject)
            worker.start()
            flag.clear()
        else:
            dial = wx.MessageDialog(None, 'There was a problem downloading the update.\n' + errorMessage, 'Error',
                                    wx.OK | wx.ICON_EXCLAMATION)
            dial.ShowModal()
            flag.clear()

    def downloadFirmware(self, target):
        if self.downloadIsRunning.is_set(): return
        self.downloadIsRunning.set()
        htmlString = '<h2>' + core_studio.FULL_MODEL_NAME + ' firmware updates</h2>'
        htmlString += "<p>Downloading...</p>"
        self.notebook.GetPage(PAGES.index("Firmware")).htmlObject.SetPage(htmlString)
        worker = GetURL_Thread(self, self.saveDownload,
                               core_studio.FIRMWARE_RELEASE_FOLDER + '/' + core_studio.MODEL_NUMBER + '-' + target + '.bin', extra=target,
                               flag=self.downloadIsRunning)
        worker.start()

    def displayFirmwareStatus(self, obj, data, errorMessage, htmlObject):
        try:
            self.parent
        except wx.PyDeadObjectError:
            return
        htmlString = '<h2>' + core_studio.FULL_MODEL_NAME + ' firmware updates</h2>'
        existingVersion = core_studio.getFirmwareVersionFromDrive(self.parent.currentRemovableDrive)
        if errorMessage is None:
            newVersion = core_studio.extractVersionFromNotes(data)
            htmlString += "<p>The latest firmware update available is Version " + newVersion + "</p>"
            status = core_studio.compareVersions(existingVersion, newVersion) if existingVersion is not None else None
            if status == -1:
                htmlString += "<p>The latest firmware update on " + self.memstick + " is Version " + existingVersion + " and is older than the latest available.</p>"
                htmlString += "<p><a href='function:downloadFirmware' target='" + newVersion + "'>Copy the latest firmware update to " + self.memstick + "</a> (Recommended)</p>"
            elif status == 0:
                htmlString += "<p>The firmware update on " + self.memstick + " is the latest.</p>"
                htmlString += "<p>When you update the firmware the default profile is loaded. If you have been using a different profile or level, make a note of this before you update.</p>"
                htmlString += "<p><i>Update the firmware on your " + core_studio.FULL_MODEL_NAME + " personal coffee roaster:</i></p>"
                htmlString += "<ol><li>Remove the memory stick and put it into the roaster.</li>"
                htmlString += "<li>Hold the roaster's start button down while you turn the roaster on.</li>"
                htmlString += "<li>You should see a message confirming that the roaster is Reflashing. This confirms that the update is being applied.</li></ol>"
            elif status == 1:
                htmlString += "<p>The latest firmware update on " + self.memstick + " is Version " + existingVersion + "</p>"
                htmlString += "<p>The firmware update on " + self.memstick + " is newer than the latest release and is intended for beta testing.</p>"
            elif status is None:
                htmlString += "<p>There is no firmware update on " + self.memstick + "</p>"
                htmlString += "<p><a href='function:downloadFirmware' target='" + newVersion + "'>Copy the latest firmware update to " + self.memstick + "</a> (Recommended)</p>"
        else:
            htmlString += UNABLE_TO_CONNECT_MESSAGE.replace('[[errorMessage]]', errorMessage)
            if existingVersion is not None:
                htmlString += "<p>The firmware update on " + self.memstick + " is Version " + existingVersion + "</p>"
        htmlString += u"<p><i>Verify the firmware version that is installed on your roaster:</i></p>"
        htmlString += u"<ol><li>Press ≡ until you see the option for technical info.</li>"
        htmlString += u"<li>Press › until you see the firmware version displayed.</li></ol>"

        htmlObject.SetPage(htmlString)

    def openLinkFile(self, target):
        self.result = wx.ID_OK
        if self.parent.openDroppedFile(target):
            wx.CallAfter(self.Close)

    def __init__(self, parent):
        super(showMemstickDialog, self).__init__(parent)
        self.parent = parent
        self.coreProfilesDownloaded = False
        self.memstick = removabledrive.volumeDescriptor(
            self.parent.currentRemovableDrive) if self.parent.currentRemovableDrive is not None else None
        pageTitles = PAGES
        self.initNotebook(pageTitles)
        self.onNotebookChange(None)
        self.downloadIsRunning = threading.Event()
        firmwareWorker = GetURL_Thread(self, self.displayFirmwareStatus, url=core_studio.FIRMWARE_RELEASE_NOTES_URL,
                               extra=self.notebook.GetPage(PAGES.index("Firmware")).htmlObject)
        firmwareWorker.start()

    def onNotebookChange(self, event):
        where = self.notebook.GetPage(self.notebook.GetSelection())
        self.updateTitle(where)
        if not self.coreProfilesDownloaded and self.notebook.GetPage(PAGES.index("Core profiles")) is where:
            self.coreProfilesDownloaded = True
            self.coreProfilesIsRunning = threading.Event()
            self.downloadCoreProfilesAgain(None)
        where.htmlObject.SetFocus()

    def downloadCoreProfilesAgain(self, target):
        self.downloadCoreProfiles(target=self.notebook.GetPage(PAGES.index("Core profiles")).htmlObject)

    def updateTitle(self, where):
        if where.pageTitle == "Logs":
            if self.parent.currentRemovableDrive is not None:
                name = " on " + self.memstick
            else:
                name = ""
            self.SetTitle("Logs saved" + name)
        elif where.pageTitle == "Profiles":
            if self.parent.currentRemovableDrive is not None:
                name = " from " + self.memstick
            else:
                name = ""
            self.SetTitle("Profiles available for loading into the Nano 7" + name)
        elif where.pageTitle == "Core profiles":
            if self.parent.currentRemovableDrive is not None:
                name = " on " + self.memstick
            else:
                name = ""
            self.SetTitle("Core profiles" + name)
        elif where.pageTitle == "Firmware":
            if self.parent.currentRemovableDrive is not None:
                name = " on " + self.memstick
            else:
                name = ""
            self.SetTitle("Firmware updates" + name)

    def initNotebook(self, panelList):
        self.panel = wx.Panel(self, wx.ID_ANY)
        if core_studio.isWindows:
            self.notebook = wx.Notebook(self.panel)
        else:
            self.notebook = wx.aui.AuiNotebook(self.panel, style=wx.aui.AUI_NB_TOP)
        for panelName in panelList:
            self.notebook.AddPage(self.initPage(self.notebook, panelName), panelName)
        sizer = wx.BoxSizer()
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.panel.SetSizerAndFit(sizer)
        self.panel.Layout()
        sizer.SetSizeHints(self.panel)
        self.panel.SetAutoLayout(True)
        self.notebook.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.onNotebookChange)
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onNotebookChange)

    def initPage(self, notebook, pageTitle):
        page = wx.Panel(notebook, wx.ID_ANY)
        self.expandDescription = False
        self.expandNotes = False
        if pageTitle == "Logs":
            page.USB_dir = core_studio.USB_LOG_DIR
            page.suffix = 'klog'
            page.columnHeadings = ['File name', 'Profile name', 'Profile Designer', 'Profile modified', 'Level', 'Length',
                              'Notes']
            page.tableColumns = ['profile_short_name', 'profile_designer', 'profile_modified', 'roasting_level', 'roast_end',
                            'tasting_notes']
            page.sort = True
        elif pageTitle == "Profiles":
            page.USB_dir = core_studio.USB_PROFILE_DIR
            page.suffix = 'kpro'
            page.columnHeadings = ['File name', 'Display name', 'Description', 'Designer', 'Date modified']
            page.tableColumns = ['profile_short_name', 'profile_description', 'profile_designer', 'profile_modified']
            page.sort = False
        elif pageTitle == "Core profiles":
            page.USB_dir = core_studio.USB_PROFILE_DIR
            page.suffix = 'kpro'
            page.columnHeadings = []
            page.tableColumns = []
            page.sort = False
        elif pageTitle == "Firmware":
            page.USB_dir = core_studio.USB_FIRMWARE_DIR
            page.suffix = 'bin'
            page.columnHeadings = []
            page.tableColumns = []
            page.sort = False

        if not core_studio.isLinux: wx.App.Get().doRaise()
        page.pageTitle = pageTitle
        outX, outY = self.parent.GetPosition()
        inX, inY = self.GetPosition()
        sizeX, sizeY = self.parent.GetSize()
        box = wx.BoxSizer(wx.VERTICAL)
        page.htmlObject = dialogs.wxHTML(page, -1, size=(sizeX - inX + outX - 30, sizeY - inY + outY - 100))
        if pageTitle == "Firmware":
            htmlString = "<p>Looking for firmware updates...</p>"
        elif pageTitle == "Core profiles":
                htmlString = "<p>Downloading official core profile set...</p>"
        else:
            if self.parent.currentRemovableDrive is None:
                htmlString = '<p>No memory stick found</p>'
            else:
                page.thisDir = self.parent.currentRemovableDrive + core_studio.USB_KAFFELOGIC_DIR + os.sep + page.USB_dir
                if os.path.exists(page.thisDir):

                    htmlString = self.buildTableOfFileNames(page.pageTitle, page.columnHeadings, page.tableColumns, page.thisDir, page.suffix, page.sort)

                else:
                    htmlString = '<p>Memory stick has no ' + page.USB_dir + ' folder</p>'
        page.htmlObject.SetPage(htmlString)
        okButton = wx.Button(page, label='Close')
        box.Add(page.htmlObject, 1, wx.GROW)
        box.Add(okButton, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        box.SetSizeHints(self)
        page.SetSizerAndFit(box)
        okButton.Bind(wx.EVT_BUTTON, page.htmlObject.onOk)
        okButton.SetDefault()
        if not core_studio.isLinux: self.Raise()
        return page

    def buildTableOfFileNames(self, pageTitle, columnHeadings, tableColumns, thisDir, suffix, sort):
        htmlString = u'<p align="right">' + core_studio.REFRESH_CHAR + '<a href="function:refresh">' \
                     u'Refresh</a> &nbsp; &nbsp; '
        # weird layout bug on Mac with unicode chars, so don't include refresh char in the link text
        if pageTitle == 'Logs':
            if not self.expandNotes:
                htmlString += '+<a href="function:refresh" target="toggle_expansion">Expand'
            else:
                htmlString += '-<a href="function:refresh" target="toggle_expansion">Collapse'
            htmlString += '&nbsp;notes'
        elif pageTitle == 'Profiles':
            if not self.expandDescription:
                htmlString += u'+<a href="function:refresh" target="toggle_expansion">Expand'
            else:
                htmlString += '-<a href="function:refresh" target="toggle_expansion">Collapse'
            htmlString += '&nbsp;descriptions'
        htmlString += '</a>&nbsp;</p>'
        htmlString += '<table border=0 cellspacing=1 cellpadding=5 width=100%>'
        htmlString += '<tr>'
        for col in columnHeadings:
            htmlString += '<th align="left">' + col + '</th>'
        htmlString += '</tr>'
        odd = True
        filesData = core_studio.dirToKeyValuesArray(thisDir, tableColumns, suffix, sort)
        if filesData is None:
            return '<p>' + thisDir + ' not found</p>'
        for fil in filesData:
            if odd:
                htmlString += '<tr bgcolor=#F0F0F0>'
                odd = False
            else:
                htmlString += '<tr bgcolor=#E0E0E0>'
                odd = True
            for col in ['profile_file_name'] + tableColumns:
                try:
                    info = fil[col]
                    if col == 'profile_short_name':
                        info = core_studio.extractShortName(fil['profile_file_name'], fil['profile_short_name'])
                except:
                    info = ''
                    if col == 'profile_short_name':
                        info = core_studio.DEFAULT_PROFILE  # there was no 'profile_short_name' row in the profile file
                if (col == 'profile_description' and not self.expandDescription) or (col == 'tasting_notes' and not self.expandNotes):
                    info = ellipsis(info, 35)
                htmlString += '<td valign=top>'
                if col == 'profile_file_name':
                    htmlString += '<a href="function:openLinkFile" target="' + thisDir + os.sep + info + '">'
                htmlString += re.sub(r"\\v", r"<br>", info)
                if col == 'profile_file_name':
                    htmlString += '</a>'
                htmlString += '</td>'
            htmlString += '</tr>'
        htmlString += '</table>'
        return htmlString

    def refresh(self, target):
        page = self.notebook.GetPage(self.notebook.GetSelection())
        if page.pageTitle == "Logs":
            if target == 'toggle_expansion':
                self.expandNotes = not self.expandNotes
            htmlString = self.buildTableOfFileNames(page.pageTitle, page.columnHeadings, page.tableColumns, page.thisDir, page.suffix, page.sort)
            page.htmlObject.SetPage(htmlString)
        elif page.pageTitle == "Profiles":
            if target == 'toggle_expansion':
                self.expandDescription = not self.expandDescription
            htmlString = self.buildTableOfFileNames(page.pageTitle, page.columnHeadings, page.tableColumns, page.thisDir, page.suffix, page.sort)
            page.htmlObject.SetPage(htmlString)
            
########################################################################
UNABLE_TO_CONNECT_MESSAGE = \
    '<p>Unable to contact the Kaffelogic web server. <font color="gray">[[errorMessage]]</font></p>' + \
    '<p>Try:<p>' \
    '<ul>' \
    '<li>Reconnecting to Wi-Fi</li>' \
    '<li>Checking the network cables, modem and router</li></ul>'


class GetURL_Thread(threading.Thread):

    def __init__(self, obj, callback, url, extra=None, flag=None):
        threading.Thread.__init__(self)
        # guarantee url is a list of urls
        if not isinstance(url, list):
            url = [url]
        self.url = url
        self.extra = extra
        self.callback = callback
        self.flag = flag
        self.obj = obj
        self.canJoin = True
        self.setName('GetURL')

    def run(self):
        """Overrides Thread.run. Don't call this directly its called internally
        when you call Thread.start().
        """
        timeToKill = self.obj.app.timeToKillThreads.isSet() if hasattr(self.obj, 'app') else wx.App.Get().timeToKillThreads.isSet()
        if not timeToKill:
            http = urllib3.PoolManager()
            urllib3.disable_warnings()
            errorMessage = None
            data = None
            for U in self.url:
                if errorMessage is None:
                    try:
                        response = http.request('GET', U)
                        if response.status == 200:
                            errorMessage = None
                            if data is None:
                                data = response.data
                            else:
                                if isinstance(data, list):
                                    data.append(response.data)
                                else:
                                    data = [data, response.data]
                        else:
                            errorMessage = response.reason
                    except Exception as e:
                        if hasattr(e, '__module__') and e.__module__ == 'urllib3.exceptions':
                            errorMessage = e.__class__.__name__
                            if hasattr(e, 'reason'):
                                errorMessage += ', ' + e.reason.__class__.__name__
                        else:
                            errorMessage = str(sys.exc_info()[1][0])
            if self.flag is None:
                wx.CallAfter(self.callback, self.obj, data, errorMessage, self.extra)
            else:
                wx.CallAfter(self.callback, self.obj, data, errorMessage, self.extra, self.flag)

########################################################################
