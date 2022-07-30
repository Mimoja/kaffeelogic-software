# -*- coding: utf-8 -*-
import sys, re, utilities

isWindows = sys.platform == 'win32'
isMac = sys.platform == 'darwin'
isLinux = sys.platform.startswith('linux')
argv = sys.argv

if isLinux:
    import pyudev.wx
    from pyudev import Context, Monitor
    import subprocess
    from json import loads
    from os.path import expanduser

    context = Context()
    monitor = Monitor.from_netlink(context)
    observer = pyudev.wx.MonitorObserver(monitor)


    def eject(drive):
        result = subprocess.check_output("eject '" + drive + "'; exit 0", stderr=subprocess.STDOUT, shell=True)
        return re.search('failed$', result) is None


    def rootDrive():
        return expanduser("~") + '/'


    def drives():
        return [rootDrive()] + removableDrives()


    _unnamedVolumes = []


    def removableDrives():
        global _unnamedVolumes
        lsblk = loads(subprocess.check_output(['lsblk -O -J'], shell=True))
        mountpoints = []
        _unnamedVolumes = []
        for dev in lsblk['blockdevices']:
            if dev['tran'] is not None and dev['tran'].lower() == 'usb' and 'children' in list(dev.keys()) and dev[
                'children'] is not None:
                children = dev['children']
                for child in children:
                    if child['hotplug'] in ['1', True, 'True', 'true'] and child['fstype'] == 'vfat' and child['mountpoint'] is not None:
                        mountpoints.append(child['mountpoint'] + '/')
                        if child['label'] is None:
                            _unnamedVolumes.append(mountpoints[-1])
        return mountpoints


    def extractDriveFromPath(path):
        m = re.match('^(/media/.+?/.+?/)', path)
        return m.group(1) if m else ''

    def volumeSerialNumber(drive):
        drive = re.sub('/$', '', drive)
        try:
            lsblk = loads(subprocess.check_output(['lsblk -o MOUNTPOINT,UUID -J'], shell=True))
            vsn = [dic['uuid'] for dic in lsblk['blockdevices'] if dic['mountpoint']==drive][0]
        except:
            return 'USB Drive'
        if vsn is None or vsn == '':
            return 'USB Drive'
        else:
            return vsn

    def volumeLabel(d):
        """ logical drive to label """
        label = re.sub('^/media/.+?/', '', d)
        label = re.sub('/$', '', label)
        if d in _unnamedVolumes:
            label = 'USB Drive (' + label + ')'
        return label


    def volumeDescriptor(d):
        """ logical drive to descriptor """
        return volumeLabel(d)


    _driveList = drives()


    def whatDeviceChanged():
        global _driveList
        latest = drives()
        if _driveList == latest: return []
        new = set(latest) - set(_driveList)
        old = set(_driveList) - set(latest)
        _driveList = latest
        return [('+', n) for n in new] + [('-', o) for o in old]


    if __name__ == '__main__':
        print(drives())

if isWindows:
    from ctypes import *
    from ctypes.wintypes import LPWSTR, LPCWSTR
    import win32api, win32con, win32file, struct
    from time import sleep
    import subprocess
    import _subprocess
    from win32com import *

    # This works around <http://bugs.python.org/issue2128>.
    # This is necessary to ensure argv is unicode and not some strange Windows encoding
    GetCommandLineW = WINFUNCTYPE(LPWSTR)(("GetCommandLineW", windll.kernel32))
    CommandLineToArgvW = WINFUNCTYPE(POINTER(LPWSTR), LPCWSTR, POINTER(c_int)) \
        (("CommandLineToArgvW", windll.shell32))

    argc = c_int(0)
    argv_unicode = CommandLineToArgvW(GetCommandLineW(), byref(argc))
    argv = [str(argv_unicode[i]) for i in range(0, argc.value)]

    if not hasattr(sys, 'frozen'):
        # If this is an executable produced by py2exe or bbfreeze, then it will
        # have been invoked directly. Otherwise, unicode_argv[0] is the Python
        # interpreter, so skip that.
        argv = argv[1:]

        # Also skip option arguments to the Python interpreter.
        while len(argv) > 0:
            arg = argv[0]
            if not arg.startswith("-") or arg == "-":
                break
            argv = argv[1:]
            if arg == '-m':
                # sys.argv[0] should really be the absolute path of the module source,
                # but never mind
                break
            if argv[0] == "__import__('idlelib.run').run.main(True)":
                argv = sys.argv
                break
            if arg == '-c':
                argv[0] = '-c'
                break

    #
    # Device change events (WM_DEVICECHANGE wParam)
    #
    DBT_DEVICEARRIVAL = 0x8000
    DBT_DEVICEQUERYREMOVE = 0x8001
    DBT_DEVICEQUERYREMOVEFAILED = 0x8002
    DBT_DEVICEMOVEPENDING = 0x8003
    DBT_DEVICEREMOVECOMPLETE = 0x8004
    DBT_DEVICETYPESSPECIFIC = 0x8005
    DBT_CONFIGCHANGED = 0x0018

    #
    # type of device in DEV_BROADCAST_HDR
    #
    DBT_DEVTYP_OEM = 0x00000000
    DBT_DEVTYP_DEVNODE = 0x00000001
    DBT_DEVTYP_VOLUME = 0x00000002
    DBT_DEVTYPE_PORT = 0x00000003
    DBT_DEVTYPE_NET = 0x00000004

    #
    # media types in DBT_DEVTYP_VOLUME
    #
    DBTF_MEDIA = 0x0001
    DBTF_NET = 0x0002

    WORD = c_ushort
    DWORD = c_ulong


    class DEV_BROADCAST_HDR(Structure):
        _fields_ = [
            ("dbch_size", DWORD),
            ("dbch_devicetype", DWORD),
            ("dbch_reserved", DWORD)
        ]


    class DEV_BROADCAST_VOLUME(Structure):
        _fields_ = [
            ("dbcv_size", DWORD),
            ("dbcv_devicetype", DWORD),
            ("dbcv_reserved", DWORD),
            ("dbcv_unitmask", DWORD),
            ("dbcv_flags", WORD)
        ]


    def getUsbDriveList():
        """
        returns a list of single letters, e.g. ['E', 'F']
        """
        usb_drivelist = []
        disk_to_drive = {}
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = _subprocess.SW_HIDE
        try:
            raw = str(subprocess.check_output('wmic path win32_logicalDisktopartition get Antecedent,Dependent',
                                              startupinfo=startupinfo))
        except (IOError, WindowsError):
            return None
        raw = re.sub(r'\r', '', raw)
        raw = re.sub(r'\n\n', '\n', raw)
        raw = re.sub(r' ', '', raw)
        table = raw.split('\n')[1:]
        for row in table:
            # print row
            disk = re.sub(r'.*?DiskPartition.DeviceID="Disk#', '', row)
            disk = re.sub(r'(\d+)(.*)', r'\1', disk)
            drive = re.sub(r'.*?LogicalDisk.DeviceID="', '', row)
            drive = re.sub(r':"', '', drive)
            disk_to_drive[disk] = drive
        try:
            raw = str(subprocess.check_output('wmic diskdrive get interfacetype,index', startupinfo=startupinfo))
        except (IOError, WindowsError):
            return None
        raw = re.sub(r'\r', '', raw)
        raw = re.sub(r'\n\n', '\n', raw)
        raw = re.sub(r' +', ' ', raw)
        table = raw.split('\n')[1:]
        for row in table:
            # print row
            row = row.strip().split(' ')
            if len(row) == 2:
                if row[1].lower() == 'usb' and row[0] in list(disk_to_drive.keys()):
                    usb_drivelist.append(disk_to_drive[row[0]])
        return usb_drivelist


    def drive_from_mask(mask):
        n_drive = 0
        while 1:
            if (mask & (2 ** n_drive)):
                return n_drive
            else:
                n_drive += 1


    def extractDriveFromPath(path):
        m = re.match('^([A-Za-z]:\\\\)', path)
        return m.group(1).upper() if m else ''

    def volumeSerialNumber(drive):
        try:
            info = win32api.GetVolumeInformation(drive)
            raw = info[1]
            hex_str = re.sub('L$','',re.sub('^0x','', hex(struct.unpack('L',struct.pack('l', raw))[0]))).upper()
            return hex_str[:4] + '-' + hex_str[4:]
        except:
            return 'USB Drive'

    def whatDeviceChanged(wparam, lparam):
        #
        # WM_DEVICECHANGE:
        #  wParam - type of change: arrival, removal etc.
        #  lParam - what's changed?
        #    if it's a volume then...
        #  lParam - what's changed more exactly
        #
        # Returns a tuple, '+' or '-' with logical drive for volume arrival or removal and None for other changes.
        # 
        #
        dev_broadcast_hdr = DEV_BROADCAST_HDR.from_address(lparam)
        if wparam == DBT_DEVICEARRIVAL or wparam == DBT_DEVICEREMOVECOMPLETE:
            if dev_broadcast_hdr.dbch_devicetype == DBT_DEVTYP_VOLUME:
                dev_broadcast_volume = DEV_BROADCAST_VOLUME.from_address(lparam)
                drive_letter = chr(ord("A") + drive_from_mask(dev_broadcast_volume.dbcv_unitmask))
                if wparam == DBT_DEVICEARRIVAL:
                    usb_drives = getUsbDriveList()
                    try:
                        info = win32api.GetVolumeInformation(drive_letter + ":\\")
                        if info[4].lower().startswith('fat') and (usb_drives is None or drive_letter in usb_drives):
                            return [('+', drive_letter + ":\\")]
                    except:
                        pass
                else:
                    return [('-', drive_letter + ":\\")]
        return []


    def rootDrive():
        return drives()[0]


    def drives():
        """
        returns a list of logical drives, e.g. ['C:\', 'F:\']
        """
        return win32api.GetLogicalDriveStrings().upper().split('\000')[:-1]


    def removableDrives():
        usb_drives = getUsbDriveList()
        removable_drives = []
        for dr in drives():
            if win32file.GetDriveType(dr) == win32file.DRIVE_REMOVABLE:
                try:
                    info = win32api.GetVolumeInformation(dr)
                    if info[4].lower().startswith('fat') and (usb_drives is None or dr[0] in usb_drives):
                        removable_drives.append(dr)
                except:
                    pass
        return removable_drives


    def volumeLabel(d):
        """ logical drive to label """
        try:
            label = win32api.GetVolumeInformation(d)[0]
        except:
            label = ""
        return label


    def volumeDescriptor(d):
        """ logical drive to descriptor """
        label = volumeLabel(d)
        if label == '': label = 'USB Drive'
        return label + " (" + d.replace("\\", "") + ")"


    def eject(drive):
        """ logical drive, returns if safe to remove as boolean """
        FSCTL_LOCK_VOLUME = 0x0090018
        FSCTL_DISMOUNT_VOLUME = 0x00090020
        IOCTL_STORAGE_MEDIA_REMOVAL = 0x002D4804
        IOCTL_STORAGE_EJECT_MEDIA = 0x002D4808
        if drive is None:
            return

        lpFileName = "\\\\.\\" + drive.replace("\\", "")
        dwDesiredAccess = win32con.GENERIC_READ | win32con.GENERIC_WRITE
        dwShareMode = win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE
        dwCreationDisposition = win32con.OPEN_EXISTING

        try:
            hVolume = win32file.CreateFile(lpFileName, dwDesiredAccess, dwShareMode, None, dwCreationDisposition, 0,
                                           None)
            win32file.DeviceIoControl(hVolume, FSCTL_LOCK_VOLUME, "", 0, None)
            win32file.DeviceIoControl(hVolume, FSCTL_DISMOUNT_VOLUME, "", 0, None)
            win32file.DeviceIoControl(hVolume, IOCTL_STORAGE_MEDIA_REMOVAL, struct.pack("B", 0), 0, None)
            win32file.DeviceIoControl(hVolume, IOCTL_STORAGE_EJECT_MEDIA, "", 0, None)
            ejected = True
        except:
            ejected = False
        finally:
            try:
                win32file.CloseHandle(hVolume)
                if ejected:
                    sleep(0.1)  # seems to be necessary to allow Windows to catch up with the play
                    shell.SHChangeNotify(shellcon.SHCNE_DRIVEREMOVED, shellcon.SHCNF_PATH, drive + ":")
            except:
                pass
        return ejected


    if __name__ == '__main__':
        print(getUsbDriveList())
        """
        import win32gui  
        class Notification:
            def __init__(self):          
                wc = win32gui.WNDCLASS()
                hinst = wc.hInstance = win32api.GetModuleHandle(None)
                wc.lpszClassName = "DeviceChangeDemo"
                wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
                wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
                wc.hbrBackground = win32con.COLOR_WINDOW
                wc.lpfnWndProc = self.wndProc
                classAtom = win32gui.RegisterClass(wc)
                style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
                print "creating a window..."
                self.hwnd = win32gui.CreateWindow(
                    classAtom,
                    "Device Change Demo",
                    style,
                    0, 0,
                    win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
                    0, 0,
                    hinst, None
                )
                win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNORMAL)
                win32gui.UpdateWindow(self.hwnd)

            def doDeviceChange(self, wParam, lParam):
                change = whatDeviceChanged(wParam, lParam)
                if change != None:
                    print change
                return True # does not disable autorun even if you return False, so the explorer window will open regardless

            def wndProc(self, hWnd, message, wParam, lParam):
                if message == win32con.WM_DESTROY:
                    print 'Being destroyed'
                    win32gui.PostQuitMessage(0)
                    return 0
                if message == win32con.WM_DEVICECHANGE:
                    self.doDeviceChange(wParam, lParam)
                    return win32gui.DefWindowProc(hWnd, message, wParam, lParam)
                else:
                    return win32gui.DefWindowProc(hWnd, message, wParam, lParam)
            def devChange(self, drive):
                print volumeDescriptor(drive)
            
        w = Notification()
        for rd in removableDrives():
            print rd
            print volumeDescriptor(rd)
        win32gui.PumpMessages()
        """

if isMac:
    argv = [utilities.ensureUnicode(x) for x in sys.argv]
    from plistlib import readPlistFromString
    from xml.parsers.expat import ExpatError
    from subprocess import Popen, PIPE
    from time import sleep
    from wx import PyDeadObjectError, CallAfter
    from os.path import expanduser

    import threading


    def rPFS(s):
        try:
            return readPlistFromString(s)
        except ExpatError as e:
            return None


    def shell(cmd):
        return Popen(cmd.split(), stdout=PIPE).communicate()[0]


    def shell2(cmd, param):
        return Popen(cmd.split() + [param], stdout=PIPE).communicate()[0]


    def extractDriveFromPath(path):
        m = re.match('^(/Volumes/.+?/)', path)
        return m.group(1) if m else ''

    def volumeSerialNumber(drive):
        try:
            diskinfo = rPFS(shell2('diskutil info -plist', drive.encode('utf-8')))
            return diskinfo['VolumeUUID']
        except:
            return 'USB Drive'

    def volumeLabel(d):
        """ logical drive to label """
        d = re.sub('^/Volumes/', '', d)
        return re.sub('/$', '', d)


    def volumeDescriptor(d):
        """ logical drive to descriptor """
        label = volumeLabel(d)
        if label.startswith('Untitled'):
            label = label + ' USB Drive'
        return label


    def rootDrive():
        return expanduser("~") + '/'


    def drives():
        return [rootDrive()] + removableDrives()


    _diskData = (None, None)


    def removableDrives():
        global _diskData
        drivelist = []
        disklist = rPFS(shell('diskutil list -plist'))
        if disklist is not None and 'AllDisks' in list(disklist.keys()):
            latest = disklist['AllDisks']
            if _diskData[0] is not None and _diskData[1] is not None and _diskData[0] == latest: return _diskData[1]
            for disk in latest:
                diskinfo = rPFS(shell2('diskutil info -plist', disk.encode('utf-8')))
                if diskinfo is not None and 'BusProtocol' in list(diskinfo.keys()) and diskinfo['BusProtocol'].lower() == 'usb' \
                        and 'Internal' in list(diskinfo.keys()) and diskinfo['Internal'] == False \
                        and 'MountPoint' in list(diskinfo.keys()) and diskinfo['MountPoint'] != '' \
                        and 'FilesystemName' in list(diskinfo.keys()) \
                        and ' fat' in diskinfo['FilesystemName'].lower():
                    drivelist.append(utilities.ensureUnicode(diskinfo['MountPoint']) + '/')
            _diskData = (latest, drivelist)
        return drivelist


    _driveList = drives()


    def whatDeviceChanged():
        global _driveList
        latest = drives()
        if _driveList == latest: return []
        new = set(latest) - set(_driveList)
        old = set(_driveList) - set(latest)
        _driveList = latest
        return [('+', n) for n in new] + [('-', o) for o in old]

    def eject(drive):
        return re.search('ejected$', shell2("diskutil eject", drive)) is not None

    import wx
    macDeviceCheckingWorker = None

    def startMacDeviceCheckingThread(self, callback):
        global macDeviceCheckingWorker
        macDeviceCheckingWorker = (self, callback, MacDeviceCheckingThread(self, callback))
        macDeviceCheckingWorker[2].start()
        self.macDeviceCheckingWatchdogTimer = utilities.SafeTimer(self)
        self.Bind(wx.EVT_TIMER, onWatchdogTimer, self.macDeviceCheckingWatchdogTimer)
        self.macDeviceCheckingWatchdogTimer.Start(5000)

    def onWatchdogTimer(e):
        """
        There is a suspicion that during sleep the thread might sometimes close. This check prevents that possibility,
        however remote a probability, without doing any harm.
        """
        if not macDeviceCheckingWorker[2].isAlive():
            self = macDeviceCheckingWorker[0]
            callback = macDeviceCheckingWorker[1]
            self.macDeviceCheckingWatchdogTimer.Stop()
            self.macDeviceCheckingWatchdogTimer = None
            startMacDeviceCheckingThread(self, callback)

    class MacDeviceCheckingThread(threading.Thread):

        def __init__(self, obj, callback):
            threading.Thread.__init__(self)
            self.callback = callback
            self.obj = obj
            self.setName('MacDeviceChecking')
            self.canJoin = True

        def run(self):
            """Overrides Thread.run. Don't call this directly its called internally
            when you call Thread.start().
            """
            while not self.obj.app.timeToKillThreads.isSet():
                change = whatDeviceChanged()
                # print change
                if change != []:
                    CallAfter(self.callback, change)
                self.obj.app.timeToKillThreads.wait(1)
                try:
                    self.obj.GetName()  # terminate the thread when the calling wxPython object has been destroyed
                except PyDeadObjectError:
                    break

if (not isWindows) and (not isMac) and (not isLinux):
    def drives():
        return ['/']


    def removableDrives():
        return []


    def extractDriveFromPath(path):
        return ''
