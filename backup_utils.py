import core_studio, removabledrive
from scandir import scandir
import os, subprocess, threading, wx
import shutil

fileCopyingLock = threading.Lock()

def start_backup(obj, drive, dataDir):
    worker = FileCopyingThread(obj, drive, dataDir)
    worker.start()

def explore(dataDir):
    backupDir = os.path.join(dataDir, 'backup')
    path = os.path.normpath(backupDir)
    if os.path.isdir(path):
        if removabledrive.isWindows:
            FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
            subprocess.Popen([FILEBROWSER_PATH, path])
        elif removabledrive.isMac:
            subprocess.Popen(['open', path])
        elif removabledrive.isLinux:
            subprocess.Popen(['xdg-open', path])
    else:
        dial = wx.MessageDialog(None, 'There are no backups yet', 'Information', 
            wx.OK | wx.ICON_EXCLAMATION)
        dial.ShowModal()


def backup_memstick(drive, dataDir):
    LOGS = drive + core_studio.USB_KAFFELOGIC_DIR + os.sep + core_studio.USB_LOG_DIR
    PROFILES = drive + core_studio.USB_KAFFELOGIC_DIR + os.sep + core_studio.USB_PROFILE_DIR
    has_logs = os.path.isdir(LOGS)
    has_profiles = os.path.isdir(PROFILES)
    if has_logs or has_profiles:
        label = removabledrive.volumeLabel(drive)
        volumeSerialNum = removabledrive.volumeSerialNumber(drive)
        if label == "":
            label = "USB Drive"

        backupDir = dataDir + os.sep + 'backup'
        try:
            os.mkdir(backupDir)
        except OSError:
            pass

        suffix = '(' + volumeSerialNum + ')'
        if label.endswith(suffix):
            suffix = ''
        backupDir += os.sep + label + suffix
        try:
            os.mkdir(backupDir)
        except OSError:
            pass

        logsBackupDir = backupDir + os.sep + core_studio.USB_LOG_DIR
        try:
            os.mkdir(logsBackupDir)
        except OSError:
            pass

        profilesBackupDir = backupDir + os.sep + core_studio.USB_PROFILE_DIR
        try:
            os.mkdir(profilesBackupDir)
        except OSError:
            pass

        if has_logs:
            createBackup(LOGS, logsBackupDir)
        if has_profiles:
            createBackup(PROFILES, profilesBackupDir)

def createBackup(sourceDir, destinationDir):
    #print sourceDir, "->", destinationDir
    destinationFiles = [x.name for x in scandir(destinationDir) if x.is_file() and (x.name.lower().endswith('.kpro') or x.name.lower().endswith('.klog') )]
    for x in scandir(sourceDir):
        if x.is_file() and (x.name.lower().endswith('.kpro') or x.name.lower().endswith('.klog')):
            source = os.path.join(sourceDir, x.name)
            destination = os.path.join(destinationDir, x.name)
            if x.name in destinationFiles:
                #print x.name, "is in", destinationDir
                if not compare(source, destination):
                    # copy only if different
                    #print "copying new version", source
                    shutil.copy2(source, destination)
            else:
                #print "copying non-existing", destination
                shutil.copy2(source, destination)

def compare(fileA, fileB):
    # return true if they are equal in the first block, logs and profiles always differ in the first 3072 bytes if they are different files
    blocksize = 3072
    with open(fileA, 'rb') as A:
        buf1 = A.read(blocksize)
    with open(fileB, 'rb') as B:
        buf2 = B.read(blocksize)
    return buf1 == buf2

class FileCopyingThread(threading.Thread):

    def __init__(self, obj, drive, dataDir):
        threading.Thread.__init__(self)
        self.obj = obj
        self.drive = drive
        self.dataDir = dataDir
        self.canJoin = True
        self.setName('FileCopying')

    def run(self):
        """Overrides Thread.run. Don't call this directly its called internally
        when you call Thread.start().
        """
        if not self.obj.app.timeToKillThreads.isSet():
            with fileCopyingLock:
                backup_memstick(self.drive, self.dataDir)
