# coding:utf-8



import numpy

"""
This software requires wxPython v 3.0.2.0
"""

import wx
import wx.aui
import wx.html
from plot_enhancements import EnhancedPlotCanvas as PlotCanvas
from wx.lib.plot import PlotGraphics, PolyLine, PolyMarker
from plot_enhancements import FilledPolyLine, FilledPolygon

import wx.lib.agw.floatspin as FS
import wx.lib.scrolledpanel
import webbrowser
import threading

import datetime, os, errno, operator

from utilities import *
from bezier import *
from kaffelogic_studio_defaults import *
from removabledrive import *
import temperature
import sonofresco
import csvgeneric
import phases
import fileproperties
import calculator
import dialogs
import viewmemstick
import exportpdf
import backup_utils
import tools
import logpanel

from HtmlPopupTransientWindow import *
from  global_strings import *
import userOptions

if isWindows: import WndProcHookMixinCtypes
if isLinux: import time as py_time

USB_KAFFELOGIC_DIR = 'kaffelogic'
USB_LOG_DIR = 'roast-logs'
USB_PROFILE_DIR = 'roast-profiles'
USB_FIRMWARE_DIR = 'firmware'
DEFAULT_PROFILE = 'K-logic classic'
TIP_FILE = 'kaffelogic_studio_tips.txt'
HINT_FILE = 'kaffelogic_studio_hints.txt'
DOWNLOADS_URL = 'https://kaffelogic.com/downloads'
DOCUMENTATION_URL = 'https://kaffelogic.com/manuals'
COMMUNITY_URL = 'https://kaffelogic.com/community'
SUPPORT_URL = 'https://kaffelogic.com/support'
SOFTWARE_RELEASE_NOTES_URL = 'https://kaffelogic.com/downloads/Release%20Notes%20-%20Kaffelogic%20Studio.txt'
FIRMWARE_RELEASE_NOTES_URL = 'https://kaffelogic.com/downloads/Release%20notes%20Nano7%20Firmware.txt'
FIRMWARE_RELEASE_FOLDER = 'https://kaffelogic.com/downloads'
CORE_PROFILES_ZIP_URL = 'https://kaffelogic.com/downloads/resources/kaffelogic.zip'

MASTER_COLUMNS = ['mean_temp', 'BT', 'Bean_temp']
MASTER_COLUMN_OFFSETS = {'mean_temp': 3.5, 'BT': 0,
                         'Bean_temp': 0}  # used when picking roast end temperature, pick back in time to get the middle of the last good moving mean cycle

EMULATE_KAFFELOGIC = 0
EMULATE_SONOFRESCO = 1

CONTROL_POINT_RATIO = 0.3
ROAST_ABSOLUTE_MAX = 20 * 60  # 20 mins is absolute max time the roast cycle will run
MAX_POWER_AVAILABLE = 1400
MAX_FAN_RPM = 18000
MIN_FAN_RPM = 8000
MAX_VALID_ROAST_TEMPERATURE = 300

DEBUG_LOG = False

STANDARD_X_AXIS = (0, 720)
STANDARD_Y_AXIS = (0, 250)
DERIVATIVE_ALLOWED_YRANGE = (-100, 300)
FAN_PROFILE_YSCALE = 0.1
SCALE_MODE_THRESHOLD = 0.995
AVOID_INFINITE_GRADIENT_THRESHOLD = 0.1  # force control points to be this far away from profile points (on x axis), to avoid infinite gradients
LAST_CONTROL_POINT_THRESHOLD = 5  # force final control point to be this far away from final profile points (on x axis), to avoid messy extrapolation
GRID_COLOUR = wx.Colour(220, 220, 220)
FIXED_SCALE_COLUMNS = {"profile_ROR": 1, "actual_ROR": 1, "desired_ROR": 1, "spot_temp": 1}
ROR_MULTIPLIER_APPLIES_TO = ["profile_ROR", "actual_ROR", "desired_ROR"]
ROR_SMOOTHING_APPLIES_TO = "actual_ROR"

TM = '™'
REFRESH_CHAR = '↻' if not isWindows else 'ѻ'
ARROW_KEYS = [wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_UP, wx.WXK_DOWN]

"""
version 4.4.1
    - new feature: Fahrenheit

version 4.3.5
	- new feature: zone and corners can be made visible on log and profile tabs, and in comparisions 
	- improvement: new file format supported for Ikawa CSV file import 
	- improvement: improved workflow for Ikawa CSV file import
	- new feature: splash screen while loading

version 4.3.2
    - new feature: fan speed can be made visible on log and profile tabs
    - new feature: roast events now visible when comparing logs
    - improvement: legend and check boxes improved labelling and workflow

version 4.3.1
    - new feature: compare files can show all log lines, according to options setting

version 4.3.0
    - improvement: restore default window when otherwise restored window would be off screen
    - bugfix: Cropster Import feature: cope with incomplete gas comments sheet in Cropster file, identify and import Cropster roast end

version 4.2.11.2
    - bugfix: issue with error message when displaying hover text

version 4.2.11.1
    - improved thread management (no effect except faster app shutdown)

version 4.2.11
    - new feature: automatic memory stick backups of profiles and logs
    - new feature: save and load temperature conversion envelopes as files
    - make units clearer for AUC calculator by adding a multiplication sign between deg and min
    - support back2back count in log files
    - indicate firmware version 7.5.0
    - minor layout fix to Linux version, some widgets were slightly too narrow for their contents
    - minor improvement to removable drive detection in Windows, no functional change under Windows 10

version 4.2.9
    - new menu option: new app window

version 4.2.8
    - indicate schema version 1.7 when using power profiling in zone 3

version 4.2.7
    - fix bug in fan profile tab when clicking on the curve

version 4.2.6
    - improvement: enhance Help menu with extra links to Documentation and Community
    - improvement: display phase data in information labels when viewing logs

version 4.2.5
    - bugfix: allow short name to consist of digits only
    - bugfix: fix bug where open log, followed by open profile, followed by edit options, gave error. Same error happened if options changed in a different window followed by edit options.
    - improvement: display phase data in information labels when editing a roast profile
    - improvement: enhance missing roast levels message to make it clear that expert level or above is needed
    - improvement: validate that times are in min:sec format (no longer accept plain seconds)
    - improvement: validate that zone ends come after zone starts

version 4.2.4
	- bugfix: display hovers correctly for preferences data in log files
	- improvement: better message when saying that firmware update is recommended

version 4.2.3
    - use hidden Sonofresco file on Mac
    - tweak Sonofresco validation criteria for rate of rise

version 4.2.2
	- new feature: export PDF

version 4.2.1
    - improvement: better error handling and layout of core profile download tab
    - improvement: display recommended roast end as actual threshold line, so 'end by ratio' becomes visible
    - improvement: add a new 'expert' difficulty level to make it easier to avoid touching the true engineer settings
    - improvement: add phases panel to 'Cpature and save image' tool
    - improvement: control the second derivative line with an option instead of difficulty
    - improvement: recognise FAT16 memory stick as well as FAT32 (Windows and Mac) 

version 4.2.0
    - new feature: core profiles tab added to the view memstick tool

version 4.1.3
    - bugfix: Fix obscure division by zero error in AUC calculator
    - improvement: increase width of text boxes in time calculator
    - improvement: Linux only, increase width of text boxes in phases panel for Ubuntu 20
    - bugfix: Linux only, Fix memstick icon not showing in toolbar for Ubuntu 20
    - improvement: getting firmware file list made more resilient to unexpected removal of memstick
    - bugfix: Import feature was failing in some cases, now made more resilient
    - bugfix: Mac only, paste temperature conversion envelope was broken

version 4.1.2
    - improvement: watchdog implemented for Mac detection of memory stick, improves reliability
    - bugfix: error message if Internet not available on program launch

version 4.1.1
    - bugfix: saving recommended level
    - bugfix: incorrect text display for level 1.0

version 4.1.0
    - addition of a third zone
    - support for power profiling
    - supports schema version 1.6 and firmware version 7.4.5
    - Sonofresco import now looks at correct default location
    - better dialog behaviour on Mac (some dialogs were needing to be explicitly closed)
    - improved display of safe to remove message on Mac
    - improved restore window to size on opening on Mac
    - schema versions now handled automatically, no ability for user to set them
    - compare files now allows comparisons to be added one at a time
    - fix bug in DTR display in Sonofresco mode
    - fix bug in hover text formatting if long word and multiple files compared
    - improved management of files and options when more than one instance is open (Windows and Linux)
    - fix bug when only one profile point
    - add level descriptions to recommended level

version 4.0.7
    - check for firmware updates as part of check for updates
    - time shift when importing and exporting Sonofresco profiles - adjust by 15 secs to allow for strange Sonofresco ADR behaviour
    - implement user can set Sonofresco file location
    - improved recognition of memory stick (don't recognise unless it is USB and FAT32, avoids annoying recognition of SD Cards, Removable Hard Drives, etc)
    - improve handling of unnamed memory stick under Linux
    - use urllib3 for Internet connections (hope to avoid some problems accessing Internet on Mac)
    - further improvement to UI for arrow keys

version 4.0.6
    - improved system for disabling type-ahead when using arrow keys for profile editing, now works cross platform

version 4.0.5
    - manage standard axes better to avoid showing too much cool down on long cooling
    - disable type-ahead when using arrow keys for profile editing - use Atl key for fast moving when using arrow keys for profile editing
    - fix Cropster import bug where blank event data was causing errors
    - preserve event data when refreshing log data on options change
    - add preferences to support extended cooling

version 4.0.4
    - fix bug where editing options sometimes generates an error if currently editing a profile after previously viewing a log
    - edit hint text (hovers) for corners to line up with the advice in Roaster's Companion

version 4.0.3
    - fix Artisan invalid JSON unicode encoding issue
    - change title of extract menu to "Import" when importing
    - ensure that empty and broken log lines are tolerated
    - update menu when changing tab to give validation message
    - minor edit to text on the time calculator buttons
    - log now properly supports log data scaling of 0.1 and smaller (rarely encountered)
    - change text of capture image menu item
    - update enable status of all log lines when leaving edit options dialog
    - fix JSON export time issues, some times were out by typically several seconds, and CSV date issues
    - support USB drives with no volume name on MacOS (refactor drive detection)

version 4.0.2
    - implement Artisan JSON import/export
    - implement Cropster import
    - implement area under the curve tool
    - implement multi-file compares
    - allow setting of size when capturing image
    - minor improvements:
        - keep save button active if undo all edits after saving
        - correctly support RoR multiplier for old style log files
        - disable transform menu item when transform is not available in settings tab
        - improve behaviour of import/export dialogs
        - improve Sonofresco export validation messages
version 4.0.1
    - suppress windows error log file
    - minor improvements to import Artisan and Ikawa
version 4.0.0
    - name change from 'Kaffelogic Profile Management Studio' to 'Kaffelogic Studio'
    - improvement:
	- handling of default folder improved on Mac and Linux, eliminating use of CWD altogether
    - minor text edits
version 3.3.6
    - bugfix: refactor changing directory to root on Mac to support new Catalina conventions
    - tidy up some underscores in labels
    - improve roast end detection in import Ikawa
    - improve klog saving after import Ikawa
version 3.3.5
    - bugfix: unicode encoding further resilience in Mac version
version 3.3.4
    - bugfix: unicode encoding of user volume name in Mac version
    - bugfix: display 'K-logic classic' as as short name when profile does not have a 'profile_short_name' element (very obscure edge case)
    - improve handling of hidden files in view memstick
version 3.3.3
    - new option: legend font size
    - improvement to position of data labels
    - RoR multiplier applied to profile as well as log
version 3.3.2
    - new options: RoR multiplier (log only), RoR smoothing
version 3.3.1
    - sanity check control points so they can't cause infinite gradients
    - report OSX versions correctly
    - bugfix: allow temperature conversion envelope to contain only one point
    - bugfix: always reset selection to first point on new file
    - improve smoothing of first and last points in unusual cases
    - improve setting of axes in profile editing tab
    - fix up calculation of recommended endpoint in cases where profile approaches flat or negative slope
    - implement unusable levels recommendation when validating profiles
    - implement fan speed validation when validating profiles
    - allow user to disable automatic check for updates
    - implement Ikawa CSV import
    - implement auto removal of turning point when importing a profile from CSV

version 3.3.0.2
    - throttle zoom with timer instead of clock
version 3.3.0.1
    - when giving message if updated, say 'rolled back' if version number has gone down
    - new user option for disabling zoom on mouse wheel
    - include platform in about and error dialogs
    - limit zooming by mouse wheel to 5 wheel events per second
    - refactor to use utilities.py
version 3.3.0
    - check for software updates
    - check for and download firmware updates
    - enhancement (Mac only): improve the method for detecting removable drive changes to avoid freezing the GUI
version 3.2.4
    - fix bug that prevents entering new colour change and first crack data into a log where no times were marked during the roast 
version 3.2.3
    - allow user to edit and save first crack and colour change values in log file
    - add ability to view logs as well as profiles with view memory stick button
    - fix scale for RoR and temperature so that they are always the same value (1.0) when graphing a log
version 3.2.2
    - new option: default colour change and first crack temperatures, to be used when there is no data in the profile file
    - enhancement: allow merge to import about this tab, colour change and first crack data, allow zones and corners to be merged separate from other settings
    - bug fix: prevent short name from being blank in schema version 1.4
    - enhancement: advise user if long file name will be truncated when loading into roaster
    - enhancement: colour change, first crack, and recommended level changes can now use undo/redo
    - new feature: properties menu item allows converting between profile schema versions
version 3.2.1
    - new feature: calculate and display roast phases for the log, allow them to be extracted to the profile
    - new feature: merge profile (tools menu) allows merging just one curve from a profile e.g. fan curve, into the current edit session
    - new feature: time calculator (tools menu) 
    - improvement: store phases data in the profile file (profile schema version 1.5.1 - updated firmware not required)
    - deprecated feature: development time calculator has been removed
version 3.2.0
    - new feature: calculate and display roast phases for the profile curve
    - new feature: recent files list to allow quickly re-opening files
    - improvement: fully support unicode in file names
    - improvement: remember the last used folder between sessions
    - improvement: user now has option to put the USB button at the bottom or the top of the screen
    - improvement: USB drives are now better handled if starting Studio with more than one removable drive already connected
    - improvement: window size is restored on re-opening the app
version 3.1.4
    - new feature: use temperature envelope for importing and exporting
    - new feature: compare default
    - new feature: view source
    - move Transform into Draw menu
    - improve removable drive handling
    - detect empty files
version 3.1.3
    - enhanced compare feature (now includes profile settings)
    - add 'compare to default' feature
    - important fix to temperature conversion routines
    - add event temperature entry to import/export Sonofrasco
    - improvement to behaviour of 'Save a copy to USB' button
    - allow decimal point to end number in roast levels string
    - fix minor bug in line width display updating
version 3.1.2
    - new feature: compare
version 3.1.1
    - new feature: providing recommendations to assist setting preheat power and min rate of rise correctly
    - bugfix when saving using the removable drive button and an extracted profile
    - removed accelerator table which was giving Linux troubles
version 3.1.0
    - new feature: display of roast events recorded in the log: colour change, first crack start/end, second crack start/end, roast end
    - new feature: import/export Artisan CSV
    - new feature: 'Smooth all' command in Draw menu
    - if a profile point is moved on top of another point they are merged into one point
    - yellow controls cannot now be dragged to create 'impossible' curves
    - 'Smooth point' now works for first and last points of the curve
    - first profile point cannot be moved away from t=0 secs
    - development time calculator now uses actual times recorded in the log
    - display graph labels without underscores
    - expand the standard log x-axis if the data goes off the right edge
    - restrict the profile x-axis so that it does not show data in negative time
    - expand the fan profile x-axis to match the temperature profile x-axis
    - transform dialog to use RPM label instead of Temperature label if transforming the fan profile curve
    - alert user to short name on save as
    - reject top 0.5% of data when calculating scale for a log line

version 3.0.0
    - add capture screenshot feature
    - only show second derivative curve in engineer mode
    - option to alter line thickness
    - slight change to improve consistency of colours
    - give user reassuring message after they have updated the software
    - help menu has tips and support page links
    - tips appear at program launch under user control via options dialog
    - help hints appear when mouse over about/settings labels
    - three difficulty levels implemented which allow fewer items displayed in about/settings tabs reducing clutter
    - display labels without underscores
    - remove trailing decimal point/zero from settings that are actually integer
    - limit length of designer name to match firmware limit
version 2.3.7
    - skip hidden files when showing all profiles on the memory stick (Mac computers create hidden files that were causing error messages)
    - support the appearance of calibration data in log files, this supports firmware changes in v 7.3.5
    - save file dialog now uses file name, not full path name (this was especially irritating on the Mac)
    - display first crack in log view
    - allow copy and paste from error message dialog
    - allow short name to be blank, in which case the file name will be used for display on the roaster, this is made possible by firmware changes in v 7.3.5 and profile schema version 1.5
    - handle incorrect UTF-8 encoding in a file gracefully

version 2.3.6.1
    - fix issue when saving profiles on Linux caused by file dialog not enforcing file extension requirements
version 2.3.6
    - limit values for ROR and 2nd derivative to avoid insanely large Y scales
    - reorganise menus adding a tools menu to make the menu contents more intuitive
    - add a new tool: development time calculator
    - show mins and secs for times in the about and setting tabs (previously they were just seconds)
    - unicode support in notes and descriptions, unicode filtered out in short name
    - Linux version built on Ubuntu
version 2.3.5
    - add red square marker at recommended end point, and extend graph beyond the last profile point to cover full range of levels
    - add red lines to grid indicating recommended end point
    - support native_schema_version in log files
    - refuse to open future versioned profile files
version 2.3.4
    - major bugfix: bug preventing use of about and settings tab due to changes in captureHistory function paramaters
version 2.3.3
    - use minutes and secs throughout on graphs (about and profile settings still uses seconds)
    - time scale increments and grid lines are now aligned with whole minutes in a sane fashion
    - dragging a control point off the edge of the graph now doesn't 'go all over the place'
    - entering coordinates via number entry, spin up or down, or arrow keys are now properly stored in the undo history
version 2.3.2
    - bugfix for case insensitive checking for duplicate Sonofresco profile names
version 2.3.1
    - add check for conflicting profile short names
    - add view memory stick dialog
    - bugfixes for opening files and closing the app, extracting Sonofresco
version 2.3.0
    - implement Sonofresco™ mode
    - treat preferences separately from profile
    - validation of profile data (rudimentary)
    - set default buttons on dialogs
    - recognise heater hours and motor hours in the log file
    - improve removable drive handling
    - switch to left-most tab on opening a file
    - only show control points for the selected point
    - minor bugfixes
version 2.2.3
    - fix bug to allow log files generated by manual mode, i.e. no embedded profile
version 2.2.2
    - save tasting notes when 'Save As...' for a log file, save changes when extracting profile by 'Save As...'
version 2.2.1
    - remove unnecessary flashing when dragging or entering data
    - fix y-scale so matching data lines share a common scale
version 2.2.0
    - implement new transform feature
version 2.1.0
    - use the more basic theme for the notebook widget on Windows to keep removable drive info always on top
    - refactor removable drive management to allow for Mac
    - always hide the 'safe to remove' message after actual removal of a device
version 2.0.0
    - support Mac
    - improve the theme for the notebook widget
    - tweaks to accelerator keys to make Mac/Win more consistent
    - remove a bug in the undo code for grid panels
version 1.3.12
    - add toolbar
    - fix more undo bugs (minor)
    - support incidental data in log file (lines starting with '!')
version 1.3.11
    - fix bug with undo when loading a profile
version 1.3.10
    - display coordinates when clicking on log and profile graph
    - zoom in and out on log and profile graph
    - fix a bug on loading a second log file
    - change the chart coordinates for the fan profile so dragging control points behaves more sanely
    - make profiles read-only when viewing a log
TO DO
panning
enable shift key constraining a control point to stay in line
enable control key constraining control points to rotate
"""

FAN_POINTS_EDIT_MAX = 15
FAN_POINTS_EDIT_MIN = 1
FAN_POINTS_SAVE_MIN = 3


class EmulationMode():
    def __init__(self):
        # Kaffelogic defaults
        self.description = ""
        self.canExportSonofresco_fn = None
        self.level_min_val = 0.1
        self.level_max_val = 5.9
        self.level_increment = 0.1
        self.level_decimal_places = 1
        self.levels_count = 7
        self.levels_pattern = r"\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*,\s*\d+(\.\d*)?\s*$"
        self.levels_min_separation = 1
        self.levels_min_temperature = 150
        self.levels_max_temperature = 242.5

        self.profile_points_edit_max = 15
        self.profile_points_edit_min = 1
        self.profile_points_save_min = 3
        self.profile_points_only_insert_after_index = 0
        self.profile_locked_points = []
        self.profile_points_timelock_last = False
        self.profile_min_time_interval = 1.0
        self.profile_custom_verify_fn = None

class BaseDataObject():
    def __init__(self):
        if hasattr(wx.App.Get(), 'frame'):
            self.frame = wx.App.Get().frame
            self.temperature_unit = self.frame.options.getUserOption("temperature_unit", default='C')
        else:
            self.frame = self
        self.fileName = ""
        self.configuration = {}
        self.configurationOrderedKeys = []
        self.roastProfilePoints = []
        self.fanProfilePoints = []
        self.comparisons = None
        self.compareDefault = False
        self.fileType = "profile"
        self.removableDriveButton = None
        self.saveToRemovableDriveIsApproved = False
        stringToDataObjects(DEFAULT_DATA, self)
        self.defaults = copy.deepcopy(self.configuration)
        self.wasSavedWithHistory = False
        self.emulation_mode = EmulationMode()

def calculateZoomedAxes(canvas, scalefactor, centre=None, pan_to_centre=False, expand_y=False):
    xLo = canvas.GetXCurrentRange()[0]
    xHi = canvas.GetXCurrentRange()[1]
    yLo = canvas.GetYCurrentRange()[0]
    yHi = canvas.GetYCurrentRange()[1]
    if centre is None:
        xCentre = (xLo + xHi) / 2.0
        yCentre = (yLo + yHi) / 2.0
    else:
        xCentre = centre[0]
        yCentre = centre[1]
        if pan_to_centre:
            adjustX = (xLo + xHi) / 2.0 - centre[0]
            adjustY = (yLo + yHi) / 2.0 - centre[1]
            xLo -= adjustX
            xHi -= adjustX
            yLo -= adjustY
            yHi -= adjustY
    if expand_y:
        return (
            ((xLo - xCentre) + xCentre, (xHi - xCentre) + xCentre),
            ((yLo - yCentre) * scalefactor + yCentre, (yHi - yCentre) * scalefactor + yCentre)
        )
    else:
        return (
            ((xLo - xCentre) * scalefactor + xCentre, (xHi - xCentre) * scalefactor + xCentre),
            ((yLo - yCentre) * scalefactor + yCentre, (yHi - yCentre) * scalefactor + yCentre)
        )

def splitProfileFromLog(string):
    """
    returns tuple (profile, log)
    also picks up any incidentals from the log and appends them to the profile
    """
    data = clean(string).split('\r\r')
    if len(data) > 0:
        profile = data[0]
    else:
        profile = ''
    if len(data) == 1:
        log = ''
    else:
        log = '\r'.join(data[1:])
    # pick up any incidentals from the log and append them to the profile
    lines = log.split('\r')
    log = []
    for line in lines:
        if len(line) > 0 and line[0] == '!':
            profile += '\r' + line[1:]
        else:
            log.append(line)
    return (profile, '\r'.join(log))


def temperatureFromLevel(levelString, thresholdString):
    try:
        thresholds = thresholdString.split(',')
        thresholds = [float(t) for t in thresholds]
    except:
        return None
    try:
        level = float(levelString)
    except:
        return None
    (ratio, index) = modf(level)
    index = trunc(index)
    if index == len(thresholds) - 1:
        return thresholds[index]
    if index < 0 or index > len(thresholds) - 1:
        return None
    interval = thresholds[index + 1] - thresholds[index]
    return thresholds[index] + ratio * interval


def levelFromTemperature(temperature, thresholdString):
    try:
        thresholds = thresholdString.split(',')
        thresholds = [float(t) for t in thresholds]
    except:
        return None
    if temperature >= thresholds[-1]:
        return float("inf")
    if temperature < thresholds[0]:
        return 0.0
    for i in range(len(thresholds) - 1):
        if temperature <= thresholds[i + 1]:
            lower = thresholds[i]
            upper = thresholds[i + 1]
            break
    threshold_range = upper - lower
    threshold_temp = temperature - lower
    if len(thresholds) < 10:
        return i + float(int(threshold_temp / threshold_range * 10)) / 10
    else:
        return i + int(round(threshold_temp / threshold_range))


class LogData:
    def __init__(self, frame):
        self.frame = frame
        self.reset_vars()

    def reset_vars(self):
        self.ySeriesRaw = {}
        self.ySeriesScaled = {}
        self.yScaleFactors = {}
        self.yMaxima = {}
        self.yMinima = {}
        self.legends = {}
        self.colours = {}
        self.enabled = {}
        self.autoScale = {}
        self.isTemperature = {}
        self.isDelta = {}
        self.xAxis = ''
        self.columnHeadings = []
        self.roastEventNames = []
        self.roastEventData = []
        self.masterColumn = ''
        self.hasFanProfile = False
        self.colourList = [
            ('grey', wx.SOLID),
            ('purple', wx.SOLID),
            ('red', wx.SOLID),
            ('blue', wx.SOLID),
            ('green', wx.SOLID),
            ('orange', wx.SOLID),
            ('yellow', wx.SOLID),
            ('black', wx.SOLID),
            ('red', wx.LONG_DASH),
            ('blue', wx.LONG_DASH),
            ('green', wx.LONG_DASH),
            ('purple', wx.LONG_DASH),
            ('grey', wx.LONG_DASH),
            ('orange', wx.LONG_DASH),
            ('yellow', wx.LONG_DASH),
            ('black', wx.LONG_DASH)]
        # light green is #90EE90 or wx.Colour(144, 238, 144) which is not listed at https://wxpython.org/Phoenix/docs/html/wx.ColourDatabase.html#wx-colourdatabase
        self.eventStyles = {
            "colour_change": {"colour": "firebrick", "marker": "triangle_down", "size": 1.5 * self.frame.markerSize,
                              "fillstyle": wx.SOLID},
            "first_crack": {"colour": "green", "marker": "triangle_down", "size": 1.5 * self.frame.markerSize,
                            "fillstyle": wx.SOLID},
            "first_crack_end": {"colour": wx.Colour(144, 238, 144), "marker": "triangle_down",
                                "size": 1.5 * self.frame.markerSize, "fillstyle": wx.SOLID},
            "second_crack": {"colour": "black", "marker": "triangle_down", "size": 1.5 * self.frame.markerSize,
                             "fillstyle": wx.SOLID},
            "second_crack_end": {"colour": "grey", "marker": "triangle_down", "size": 1.5 * self.frame.markerSize,
                                 "fillstyle": wx.SOLID},
            "roast_end": {"colour": "red", "marker": "square", "size": 0.3 * self.frame.markerSize,
                          "fillstyle": wx.SOLID}
        }

    def legendToColour(self, legend, eventStyles):
        legend = utilities.replaceSpaceWithUnderscore(legend)
        if legend in EVENT_NAMES:
            return eventStyles[legend]["colour"]
        else:
            if legend in list(self.colours.keys()):
                return self.colours[legend]
            else:
                return 'grey'

    def legendToColumnName(self, legend):
        legend = utilities.replaceSpaceWithUnderscore(legend)
        for columnName in list(self.legends.keys()):
            if legend == utilities.replaceSpaceWithUnderscore(self.legends[columnName]):
                return columnName
        return legend


def calculateYScaleFactor(maximumValue, minimumValue):
    if maximumValue <= 0:
        return calculatePositiveScaleFactor(abs(minimumValue))
    else:
        return calculatePositiveScaleFactor(abs(maximumValue))


def calculatePositiveScaleFactor(maximumValue):
    if temperature.getTemperatureUnit() == 'F':
        scale = 2
    else:
        scale = 1
    if maximumValue < 2.5 * scale:
        return 100 * scale
    else:
        if maximumValue < 10 * scale:
            return 100 * scale
        else:
            if maximumValue < 25 * scale:
                return 10 * scale
            else:
                if maximumValue > 3000 * scale:
                    return 0.01 *scale
                else:
                    if maximumValue > 300 * scale:
                        return 0.1 * scale
                    else:
                        return scale


def scaled(list, yScale):
    result = []
    for pointTuple in list:
        result.append((pointTuple[0], pointTuple[1] * yScale))
    return result


def stringToLogData(string, frame):
    """
    time	#@spot_temp	#=@temp	=@mean_temp	=@profile	&profile_ROR	=&actual_ROR	#=&desired_ROR	power_kW	#volts-9	#Kp	#Ki	#Kd
    """
    DEFAULT_LOG_TEMPERATURE_COLS = ['spot_temp', 'temp', 'mean_temp', 'profile']
    DEFAULT_LOG_DELTA_COLS = ['profile_ROR', 'actual_ROR', 'desired_ROR']

    logData = LogData(frame)
    lines = string.split('\r')
    # If first line is offsets, initialise the offsets array and treat the second line as the column heading names.
    offsets = lines[0].split(',')
    if offsets[0] == 'offsets':
        lines = lines[1:]
    else:
        offsets = None
    header = lines[0] if len(lines) > 0 else ''
    temperaturesAreIndicated = re.search(r'(^|\t)(#|=)?(@|&)', header) is not None # temperatures were not labelled with @ and & in earlier firmware versions
    columnHeadings = header.split(',')
    logData.xAxis = columnHeadings[0]
    logData.columnHeadings = []
    # If first character is # then the column of data is initially hidden.
    # If first character is = then scale used will be the scale calculated for the previous column, otherwise auto calc.
    # If first character is @ then it is treated as a temperature column and converted to Fahrenheit if appropriate
    # If first character is & then it is treated as a relative temperature (delta) column and converted to Fahrenheit if appropriate

    for rawCol in columnHeadings[1:]:
        if rawCol[0] == '#':
            col = rawCol[1:]
            enabled = False
        else:
            col = rawCol
            enabled = True

        if col[0] == '=':
            col = col[1:]
            autoScale = False
        else:
            autoScale = True

        if col[0] == '@':
            col = col[1:]
            isTemperature = True
        else:
            isTemperature = False

        if col[0] == '&':
            col = col[1:]
            isDelta = True
            isTemperature = True
        else:
            isDelta = False

        if not temperaturesAreIndicated:
            isTemperature = col in DEFAULT_LOG_TEMPERATURE_COLS + DEFAULT_LOG_DELTA_COLS
            isDelta = col in DEFAULT_LOG_DELTA_COLS

        if col in MASTER_COLUMNS:
            logData.masterColumn = col
            isTemperature = True
            isDelta = False
            autoScale = True
        logData.enabled[col] = enabled
        logData.autoScale[col] = autoScale
        logData.isTemperature[col] = isTemperature
        logData.isDelta[col] = isDelta
        logData.ySeriesRaw[col] = []
        logData.columnHeadings.append(col)
    columnHeadings = [columnHeadings[0]] + logData.columnHeadings
    lines = lines[1:]
    lastTime = float("-inf")
    for line_num in range(len(lines)):
        line = lines[line_num]
        numbers = line.split(',')
        thisTime = floatOrZero(numbers[0])
        if len(numbers) >= len(columnHeadings) and thisTime > lastTime:
            lastTime = thisTime
            for i in range(1, len(columnHeadings)):
                if offsets is None or len(offsets) != len(columnHeadings):
                    thisoffset = 0
                else:
                    thisoffset = floatOrZero(offsets[i])
                thisvalue = floatOrZero(numbers[i])
                thiskey = columnHeadings[i]
                if logData.isTemperature[thiskey]:
                    thisvalue = temperature.convertCelciusToSpecifiedUnit(thisvalue, delta=logData.isDelta[thiskey])
                logData.ySeriesRaw[columnHeadings[i]].append((thisTime + thisoffset, thisvalue))
    currentScaleFactor = 1
    for i in range(1, len(columnHeadings)):
        if len(logData.ySeriesRaw[columnHeadings[i]]) > 0:
            maximum = maximumYmode(logData.ySeriesRaw[columnHeadings[i]], SCALE_MODE_THRESHOLD)
            logData.yMaxima[columnHeadings[i]] = maximum
            minimum = minimumY(logData.ySeriesRaw[columnHeadings[i]])
            logData.yMinima[columnHeadings[i]] = minimum
            if logData.autoScale[columnHeadings[i]]:
                if (maximum == 0 and minimum == 0):
                    scaleFactor = 1
                    currentScaleFactor = 1
                    # override any scale repeat setting on the next column
                    if i + 1 < len(columnHeadings):
                        logData.autoScale[columnHeadings[i + 1]] = True
                else:
                    if columnHeadings[i] in list(FIXED_SCALE_COLUMNS.keys()):
                        multiplier = int(frame.options.getUserOption("ror_multiplier")) if columnHeadings[
                                                                                               i] in ROR_MULTIPLIER_APPLIES_TO else 1
                        scaleFactor = FIXED_SCALE_COLUMNS[columnHeadings[i]] * multiplier
                    elif columnHeadings[i] in MASTER_COLUMNS:
                        scaleFactor = 1
                    else:
                        scaleFactor = calculateYScaleFactor(maximum, minimum)
                    currentScaleFactor = scaleFactor
            else:
                scaleFactor = currentScaleFactor
            logData.yScaleFactors[columnHeadings[i]] = scaleFactor
            logData.ySeriesScaled[columnHeadings[i]] = scaled(logData.ySeriesRaw[columnHeadings[i]], scaleFactor)
            logData.legends[columnHeadings[i]] = addScaleFactorToLegendText(columnHeadings[i], scaleFactor)
            if columnHeadings[i] == ROR_SMOOTHING_APPLIES_TO:
                logData.ySeriesScaled[columnHeadings[i]] = csvgeneric.applyMovingMeans(
                    logData.ySeriesScaled[columnHeadings[i]], int(frame.options.getUserOption("ror_smoothing")))
    return logData


def addScaleFactorToLegendText(text, scaleFactor):
    if scaleFactor == 1:
        return replaceUnderscoreWithSpace(text)
    elif scaleFactor > 1:
        return replaceUnderscoreWithSpace(text + ' × ' + str(int(scaleFactor)))
    else:
        return replaceUnderscoreWithSpace(text + ' ÷ ' + str(int(1.0 / scaleFactor)))


def addZoneStartEnd(self, legendText):
    # print 'addZoneStartEnd', legendText
    legendText = replaceUnderscoreWithSpace(legendText)
    zoneIndex = re.findall(r"\d+", legendText)
    if len(zoneIndex) == 0:
        return legendText
    zone_selector = 'zone' if legendText.startswith("Zone") else 'corner'
    zone_selector += str(zoneIndex[0]) + '_'
    zone_start_str = self.frame.page4.configControls[zone_selector + 'time_start'].GetValue()
    zone_end_str = self.frame.page4.configControls[zone_selector + 'time_end'].GetValue()
    return legendText + '\n' + zone_start_str + ' to ' + zone_end_str


def removeScaleFactorFromLegendAndData(frame, legendText, dataValue, scale=None):
    legendText = replaceUnderscoreWithSpace(legendText)
    parts = legendText.split(':')
    legendText = parts[0]
    legend = legendText.split(' × ')
    if len(legend) == 2:
        legendText = legend[0]
        scale = float(legend[1])
        dataValue = dataValue / scale
    elif legendText in ['fan speed', 'Fan speed']:
        if scale == 'fit':
            dataValue = int(round(convertFanRPMfromFitTemperatureScale(frame, dataValue) / FAN_PROFILE_YSCALE, -1))
    if len(parts) == 2:
        legendText += ':' + parts[1]
    return {"legend": legendText, "value": dataValue}


def compareProfileSchemaVersionsOf(a, b):
    """
    -1 means a<b
    0 meand a==b
    1 means a > b
    only the first two levels of the version numbers are compared, so 1.3.1 is compared as if it were 1.3
    """
    versionA = re.findall(r"(^|\n)(profile_schema_version:)(.*?)(\r|\n|$)", a)
    versionB = re.findall(r"(^|\n)(profile_schema_version:)(.*?)(\r|\n|$)", b)
    versionAstring = versionA[0][2] if len(versionA) > 0 else ''
    versionBstring = versionB[0][2] if len(versionB) > 0 else ''
    return (compareProfileSchemaVersions(versionAstring, versionBstring), versionAstring, versionBstring)


def compareProfileSchemaVersions(versionAstring, versionBstring):
    return compareVersions(versionAstring, versionBstring, depth=2)


def compareVersions(versionAstring, versionBstring, depth=None):
    """
    return  A < B -1
            A = B 0
            A > B 1
    """
    if versionAstring is None and versionBstring is None: return 0
    if versionAstring is None: return -1
    if versionBstring is None: return 1
    versionA = versionAstring.split('.') if versionAstring != '' else []
    versionB = versionBstring.split('.') if versionBstring != '' else []
    maxLen = max(len(versionA), len(versionB), 1)
    while len(versionA) < maxLen: versionA.append('0')
    while len(versionB) < maxLen: versionB.append('0')
    for i in range(len(versionA) if depth is None else depth):
        try:
            if int(versionA[i]) < int(versionB[i]): return -1
            if int(versionA[i]) > int(versionB[i]): return 1
        except:
            return 0
    return 0


def extractVersionFromNotes(notes):
    version = re.sub(r"^.*?\sVersion", "", notes, 1, re.I | re.S).strip()
    version = re.sub(r"(\s).*$", "", version, 1, re.S).strip()
    return version


def stringToDataObjects(string, frame):
    """
    Puts the profile data into frame.configuration, frame.configurationOrderedKeys, frame.roastProfilePoints, frame.fanProfilePoints.
    Puts the log data into frame.logData.
    Only updates data that is present in the string, if data is missing it is not updated so default data will remain.
    Note this doesn't put the profile points into the page itself, i.e it doesn't do e.g. page1.profilePoints = frame.roastProfilePoints,
    and it doesn't put configuration data into the grid panels either.
    """
    profile, log = splitProfileFromLog(
        string)  # also picks up any incidentals from the log and appends them to the profile
    frame.logData = stringToLogData(log, frame.frame if hasattr(frame, 'frame') else frame)
    for line in profile.split('\r'):
        elements = line.split(':')
        if len(elements) > 2:
            elements = [elements[0], ':'.join(elements[1:])]
        if len(elements) == 2:
            key, value = elements
            key = replaceSpaceWithUnderscore(key)
            if key == 'roast_profile' or key == 'fan_profile':
                numbers = value.split(",")
                if len(numbers) % 6 == 0:
                    if key == 'roast_profile':
                        frame.roastProfilePoints = []
                        while len(numbers) // 6 > 0:
                            frame.roastProfilePoints.append(
                                temperature.convertCelciusProfilePointToSpecifiedUnit(
                                    ProfilePoint(floaty(numbers[0]), floaty(numbers[1]), floaty(numbers[2]),
                                             floaty(numbers[3]), floaty(numbers[4]), floaty(numbers[5])),
                                    to_unit=frame.temperature_unit)
                            )
                            numbers = numbers[6:]
                    if key == 'fan_profile':
                        frame.fanProfilePoints = []
                        frame.logData.hasFanProfile = True
                        while len(numbers) // 6 > 0:
                            frame.fanProfilePoints.append(ProfilePoint(
                                floaty(numbers[0]),
                                floaty(numbers[1]) * FAN_PROFILE_YSCALE,
                                floaty(numbers[2]),
                                floaty(numbers[3]) * FAN_PROFILE_YSCALE,
                                floaty(numbers[4]),
                                floaty(numbers[5]) * FAN_PROFILE_YSCALE))
                            numbers = numbers[6:]
            else:
                # print key, ":", value
                if key in EVENT_NAMES:
                    # add to events
                    temperature_taken_from_time = int(float(value))
                    if key == 'roast_end':
                        temperature_taken_from_time -= MASTER_COLUMN_OFFSETS[frame.logData.masterColumn]
                    points = [point for point in frame.logData.ySeriesRaw[frame.logData.masterColumn] if
                              point[0] >= temperature_taken_from_time]
                    if len(points) > 0:
                        point = points[0]
                        """
                        TODO: interpolate...
                        """
                        time = float(value)
                        thisTemperature = point[1]
                        # print "inserting", key, ':', utilities.toMinSec(time), ", ", thisTemperature, 'from', frame.logData.masterColumn
                        if key in frame.logData.roastEventNames:
                            loc = frame.logData.roastEventNames.index(key)
                            frame.logData.roastEventNames.pop(loc)
                            frame.logData.roastEventData.pop(loc)
                        frame.logData.roastEventData.append((time, thisTemperature))
                        frame.logData.roastEventNames.append(key)
                        frame.configuration[key] = toMinSec(value, wholeSecs=False)

                elif key == 'roast_levels':
                    frame.configuration[key] = temperature.convertCelciusListToSpecifiedUnit(value,
                                                                                             to_unit=frame.temperature_unit)
                elif key in timeInMinSec:
                    frame.configuration[key] = toMinSec(value, wholeSecs=False)
                elif key in temperatureParameters:
                    frame.configuration[key] = temperature.convertCelciusToSpecifiedUnit(value,
                                                                                         to_unit=frame.temperature_unit,
                                                                                         keepZero=key in keepZeroParameters)
                elif key in temperatureDeltas:
                    frame.configuration[key] = temperature.convertCelciusToSpecifiedUnit(value,
                                                                                         to_unit=frame.temperature_unit,
                                                                                         delta=True
                                                                                         )
                else:
                    frame.configuration[key] = floaty(value)
                if key not in frame.configurationOrderedKeys:
                    frame.configurationOrderedKeys.append(key)
    convertAllZonesBoostCelciusToSpecifiedUnit(frame.configuration, to_unit=frame.temperature_unit)
    frame.roastProfilePoints[0].leftControl = Point(0, 0)
    frame.roastProfilePoints[len(frame.roastProfilePoints) - 1].rightControl = Point(0, 0)
    calculateControlPoints(frame.roastProfilePoints, CONTROL_POINT_RATIO)
    frame.fanProfilePoints[0].leftControl = Point(0, 0)
    frame.fanProfilePoints[len(frame.fanProfilePoints) - 1].rightControl = Point(0, 0)
    calculateControlPoints(frame.fanProfilePoints, CONTROL_POINT_RATIO)


def stringToKeyValues(fileName, string, wanted):
    """
    Used only by viewmemstick which supplies the wanted list of keys.
    This wanted list never includes temperatures, so we do not perform any
    temperature conversions here.
    """
    result = {'profile_file_name': os.path.basename(fileName)}
    profile, log = splitProfileFromLog(string)  # also picks up any incidentals and adds them to the profile
    for line in profile.split('\r'):
        elements = line.split(':')
        if len(elements) > 2:
            elements = [elements[0], ':'.join(elements[1:])]
        if len(elements) == 2:
            key, value = elements
            value = utilities.trimWhiteSpace(value)
            key = replaceSpaceWithUnderscore(key)
            if key in wanted:
                result[key] = toMinSec(value, wholeSecs=True) if key in timeInMinSec else value
    return result


def dataObjectsToString(frame):
    schemaVersion = fileproperties.updateSchemaVersion(frame)
    page3_list = list(frame.page3.configControls.keys())
    page4_list = list(frame.page4.configControls.keys())
    orderedList = copy.deepcopy(frame.configurationOrderedKeys)
    fileproperties.filterOutUnsupportedSettings(orderedList, schemaVersion)  # filter known future keys
    known = set(list(frame.defaults.keys()) + profileDataInLog + logFileName + notSavedInProfile)
    orderedList = [x for x in orderedList if x in known]

    for key in page3_list:
        # print frame.page3.configControls[key].GetValue()
        frame.configuration[key] = encodeCtrlV(frame.page3.configControls[key].GetValue())
    for key in page4_list:
        # print frame.page4.configControls[key].GetValue()
        frame.configuration[key] = encodeCtrlV(frame.page4.configControls[key].GetValue())
    frame.configuration['recommended_level'] = frame.page1.level_floatspin.GetValue()
    frame.configuration['expect_colrchange'] = replaceBlankWithZero(frame.page1.phasesObject.getColourChange())
    frame.configuration['expect_fc'] = replaceBlankWithZero(frame.page1.phasesObject.getFirstCrack())
    result = ''
    for key in orderedList:
        if (key in page3_list + page4_list + notOnTabs) and (not key in logFileName + notSavedInProfile):
            if key in timeInMinSec:
                result += key + ':' + str(fromMinSec(frame.configuration[key])) + '\n'
            elif key == 'roast_levels':
                result += key + ':' + temperature.convertSpecifiedUnitListToCelcius(frame.configuration[key],
                                                                                             rounding=None) + '\n'
            elif key in temperatureParameters:
                result += key + ':' + str(temperature.convertSpecifiedUnitToCelcius(
                                            frame.configuration[key],
                                            rounding=None,
                                            keepZero=key in keepZeroParameters
                                      ))+ '\n'
            elif key in temperatureDeltas:
                result += key + ':' + str(temperature.convertSpecifiedUnitToCelcius(
                                            frame.configuration[key],
                                            rounding=None,
                                            delta=True
                                        )) + '\n'
            elif key in zoneBoosts:
                result += key + ':' + convertZoneBoostSpecifiedUnitToCelcius(frame.configuration, key, rounding=None) + '\n'
            else:
                result += key + ':' + str(frame.configuration[key]) + '\n'

    result += 'profile_modified:' + datetime.datetime.now().strftime('%d/%m/%Y %I:%M:%S%p') + '\n'
    result += profilePointsToString("roast_profile", temperature.convertSpecifiedUnitProfileToCelcius(frame.page1.profilePoints, rounding=None))
    result += profilePointsToString("fan_profile", frame.page2.profilePoints, FAN_PROFILE_YSCALE)
    return result

def convertAllZonesBoostCelciusToSpecifiedUnit(configuration, to_unit):
    for key in zoneBoosts:
        value = configuration[key]
        index = re.findall(r'\d+', key)[0]
        Kp_key = 'zone' + index + '_multiplier_Kp'
        Kd_key = 'zone' + index + '_multiplier_Kd'
        if float(configuration[Kp_key]) == 0 and float(configuration[Kd_key]) == 0:
            # power profile zone, so no conversion
            return
        else:
            # boost or gain scheduling zone, so convert to F if appropriate
            configuration[key] = temperature.convertCelciusToSpecifiedUnit(value,
                                                                                 to_unit=to_unit,
                                                                                 delta=True
                                                                                 )

def convertZoneBoostSpecifiedUnitToCelcius(configuration, key, rounding=None):
    value = configuration[key]
    index = re.findall(r'\d+', key)[0]
    Kp_key = 'zone' + index + '_multiplier_Kp'
    Kd_key = 'zone' + index + '_multiplier_Kd'
    if float(configuration[Kp_key]) == 0 and float(configuration[Kd_key]) == 0:
        # power profile zone, so no conversion
        return str(value)
    else:
        # boost or gain scheduling zone, so convert to F if appropriate
        return str(temperature.convertSpecifiedUnitToCelcius(
            value,
            rounding=None,
            delta=True
        ))

def openAndReadFileWithTimestamp(obj, fileName):
    """
    obj must have a time stamp
    """
    with userOptions.fileCheckingLock:
        obj.fileTimeStamp = None
    datastring = openAndReadFile(fileName)
    with userOptions.fileCheckingLock:
        obj.fileTimeStamp = os.path.getmtime(fileName)
    return datastring


def openAndReadFile(fileName):
    datastring = ""
    try:
        with open(fileName, 'r') as infile:
            datastring = infile.read()
    except IOError as e:
        dial = wx.MessageDialog(None, 'This file could not be opened.\n' + fileName + '\n' + e.strerror + '.', 'Error',
                                wx.OK | wx.ICON_EXCLAMATION)
        dial.ShowModal()
    except UnicodeDecodeError as e:
        dial = wx.MessageDialog(None, 'This file could not be opened (Unicode UTF-8 decode error)\n' + fileName,
                                'Error',
                                wx.OK | wx.ICON_EXCLAMATION)
        dial.ShowModal()
    return datastring

def extractShortName(fileName, shortName):
    if shortName != "" and shortName is not None:
        return shortName
    return os.path.splitext(os.path.basename(fileName))[0][:15]

def getProfileFilesInDir(d, suffix, sort=False):
    if not os.path.exists(d):
        return None
    fileList = [d + os.sep + x for x in os.listdir(str(d)) if
                x.endswith('.' + suffix) and not file_is_hidden(d + os.sep + x)]
    if sort:
        fileList.sort()
    return fileList


def extractVersionFromFirmwareFilename(fname, modelNumber):
    ver = re.sub('^' + modelNumber + '-', '', fname)
    ver = re.sub('.bin', '', ver)
    return ver


def getFirmwareFilesInDir(d, modelNumber, sort=True):
    fileList = []
    for x in (os.listdir(str(d)) if os.path.exists(d) else []):
        if re.match(modelNumber + r'-\d+(\.\d+)*\.bin$', x, re.I) and not file_is_hidden(d + os.sep + x):
            fileList.append(extractVersionFromFirmwareFilename(x, modelNumber))
    if sort:
        fileList.sort(cmp=compareVersions, reverse=True)
    return fileList


def getFirmwareVersionFromDrive(drive):
    if drive is not None:
        d = drive + USB_KAFFELOGIC_DIR + os.sep + USB_FIRMWARE_DIR
        if os.path.exists(d):
            files = getFirmwareFilesInDir(d, MODEL_NUMBER)
            existingVersion = files[0] if len(files) > 0 else None
        else:
            existingVersion = None
    else:
        existingVersion = None
    return existingVersion


def file_is_hidden(p):
    if isWindows:
        attribute = win32api.GetFileAttributes(p)
        return attribute & (win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
    else:
        return os.path.basename(p).startswith('.')  # linux-osx


def dirToKeyValuesArray(d, keys, suffix, sort=False):
    files = getProfileFilesInDir(d, suffix, sort)
    if files is None:
        return None
    return [stringToKeyValues(f, openAndReadFile(f), keys) for f in files]


def drawZones(self, bezier_points, useConfig=False, fileName='', lightness=0):
    ZONE_DISPLAY_ALPHA = 150  # out of 255, where 255 is opaque
    ZONE_WIDTH = 12 # display zones this many deg C above and below profile line
    zoneWidthScale = 2 if self.frame.temperature_unit == 'F' else 1
    zoneLines = []
    for z in range(NUMBER_OF_ZONES):
        zone_selector = 'zone' + str(z + 1) + '_'
        if useConfig:
            zone_start = utilities.fromMinSec(self.configuration[zone_selector + 'time_start'])
            zone_end = utilities.fromMinSec(self.configuration[zone_selector + 'time_end'])
            zone_multiplier_Kp = utilities.floatOrZero(self.configuration[zone_selector + 'multiplier_Kp'])
            zone_multiplier_Kd = utilities.floatOrZero(self.configuration[zone_selector + 'multiplier_Kd'])
            zone_boost = utilities.floatOrZero(self.configuration[zone_selector + 'boost'])
        else:
            zone_start = utilities.fromMinSec(self.frame.page4.configControls[zone_selector + 'time_start'].GetValue())
            zone_end = utilities.fromMinSec(self.frame.page4.configControls[zone_selector + 'time_end'].GetValue())
            zone_multiplier_Kp = utilities.floatOrZero(
                self.frame.page4.configControls[zone_selector + 'multiplier_Kp'].GetValue())
            zone_multiplier_Kd = utilities.floatOrZero(
                self.frame.page4.configControls[zone_selector + 'multiplier_Kd'].GetValue())
            zone_boost = utilities.floatOrZero(self.frame.page4.configControls[zone_selector + 'boost'].GetValue())
        if zone_end > 0 and zone_end > zone_start and not (
                zone_multiplier_Kp == 1 and zone_multiplier_Kd == 1 and zone_boost == 0):
            legend = 'Zone ' + str(z + 1) + ' '
            if zone_multiplier_Kp == 0 and zone_multiplier_Kd == 0:
                zone_colour = wx.Colour(0, 0, z, ZONE_DISPLAY_ALPHA)
                legend += 'power '
                if zone_boost >= 0:
                    legend += '+'
                legend += str(zone_boost) + '%'
            elif zone_multiplier_Kp == 1 and zone_multiplier_Kd == 1:
                zone_colour = wx.Colour(60, 120, 60 + z * 10, ZONE_DISPLAY_ALPHA)
                legend += 'boost '
                if zone_boost >= 0:
                    legend += '+'
                legend += str(zone_boost)
            else:
                zone_colour = wx.Colour(120, 60, 60 + z * 10, ZONE_DISPLAY_ALPHA)
                legend += 'gain scheduling'
            legend += ('' if fileName == '' else ' : ') + fileName
            zone_affected_points = utilities.filterPointsX(bezier_points, (zone_start, zone_end))
            displayPoints = utilities.shiftPointsY(zone_affected_points,
                                                   (ZONE_WIDTH - z) * zoneWidthScale) + (utilities.shiftPointsY(
                zone_affected_points, (-ZONE_WIDTH + z) * zoneWidthScale))[::-1]
            zoneLines.append(FilledPolygon(displayPoints,
                                           legend=legend,
                                           colour=utilities.setLightness(zone_colour, lightness),
                                           style=wx.SOLID,
                                           width=self.frame.lineWidth))
    for c in range(NUMBER_OF_CORNERS):
        legend = 'Corner ' + str(c + 1) + '' if fileName == '' else ': ' + fileName
        zone_selector = 'corner' + str(c + 1) + '_'
        if useConfig:
            zone_start = utilities.fromMinSec(self.configuration[zone_selector + 'time_start'])
            zone_end = utilities.fromMinSec(self.configuration[zone_selector + 'time_end'])
        else:
            zone_start = utilities.fromMinSec(self.frame.page4.configControls[zone_selector + 'time_start'].GetValue())
            zone_end = utilities.fromMinSec(self.frame.page4.configControls[zone_selector + 'time_end'].GetValue())
        zone_colour = wx.Colour(255, 255, 0, ZONE_DISPLAY_ALPHA)
        zone_affected_points = utilities.filterPointsX(bezier_points, (zone_start, zone_end))
        displayPoints = utilities.shiftPointsY(zone_affected_points,
                                               (ZONE_WIDTH - 4 - c) * zoneWidthScale) + (utilities.shiftPointsY(
            zone_affected_points, (-ZONE_WIDTH + 4 + c) * zoneWidthScale))[::-1]
        if zone_end > 0 and zone_end > zone_start:
            zoneLines.append(FilledPolygon(displayPoints,
                                           legend=legend,
                                           colour=utilities.setLightness(zone_colour, lightness),
                                           style=wx.SOLID,
                                           width=self.frame.lineWidth))
    return zoneLines


def drawComparisons(self, title):
    COMPARISON_EXTRA_COLS = []
    if self.frame.comparisons is not None:
        comparisonLines = []
        colourThreshold = 2 if self.frame.comparisons[-1].fileName == "Default" else 1
        logColourValue = 155 if len(self.frame.comparisons) <= colourThreshold else 88
        profileColourValue = 188 if len(self.frame.comparisons) <= colourThreshold else 96
        logColourStep = (200 - logColourValue) // len(self.frame.comparisons)
        profileColourStep = (200 - profileColourValue) // len(self.frame.comparisons)
        columns_to_show = self.frame.options.getUserOption("compare_columns",
                                                           userOptions.COMPARE_COLUMN_DEFAULTS).split(',')
        for comparison in self.frame.comparisons:
            profileName, logName = self.frame.getComparisonFileNames(comparison)
            bezierLineMode = (int(round(float(comparison.configuration["emulation_mode"]))) == EMULATE_KAFFELOGIC) or \
                             (title == 'Fan Profile Curve')
            if 'zones' in columns_to_show and (title != 'Fan Profile Curve'):
                comparisonLines += drawZones(
                    comparison,
                    calculatePointsFromProfile(self.frame, comparison.roastProfilePoints, bezierLineMode),
                    useConfig=True,
                    fileName=profileName,
                    lightness=logColourValue
                )
            i = 0
            for col in comparison.logData.columnHeadings:
                comparison.logData.colours[col] = comparison.logData.colourList[i][0]
                i += 1
            if comparison.logData.masterColumn != '' and (title != 'Fan Profile Curve'):
                for col in columns_to_show:
                    if col == 'mean_temp':
                        col = comparison.logData.masterColumn
                    if col in comparison.logData.columnHeadings and col != 'profile':
                        comparisonPoints = [p for p in comparison.logData.ySeriesScaled[col] if p[0] >= 0.0]
                        thisColour = comparison.logData.legendToColour(col, comparison.logData.eventStyles)
                        legend = addScaleFactorToLegendText(col, comparison.logData.yScaleFactors[col])
                        comparisonLines.append(PolyLine(comparisonPoints, legend=legend + ': ' + logName,
                                                        colour=utilities.setLightness(thisColour, logColourValue),
                                                        style=wx.SOLID, width=self.frame.lineWidth))
            if title != 'Fan Profile Curve':
                fanScale = 'fit'
                fanScaleText = ''
                fanStyle = wx.PENSTYLE_LONG_DASH
                comparisonPoints = calculatePointsFromProfile(self.frame, comparison.roastProfilePoints, bezierLineMode)
                if 'profile' in columns_to_show:
                    comparisonLines.append(PolyLine(comparisonPoints, legend='profile: ' + profileName,
                                                    colour=utilities.setLightness(wx.Colour(0, 0, 255),
                                                                                  profileColourValue), style=wx.SOLID,
                                                    width=self.frame.lineWidth))
            else:
                fanScale = None
                fanScaleText = ''
                fanStyle = wx.PENSTYLE_SOLID
            comparisonPoints = calculatePointsFromProfile(self.frame, comparison.fanProfilePoints, True, fanScale)
            if 'fan_speed' in columns_to_show or title == 'Fan Profile Curve':
                comparisonLines.append(
                    PolyLine(comparisonPoints, legend='fan speed' + fanScaleText + ': ' + profileName,
                             colour=utilities.setLightness(wx.Colour(0, 0, 255), profileColourValue), style=fanStyle,
                             width=self.frame.lineWidth))

            styles = comparison.logData.eventStyles
            if 'events' in columns_to_show and title != 'Fan Profile Curve':
                for i in range(len(comparison.logData.roastEventNames)):
                    name = comparison.logData.roastEventNames[i]
                    comparisonLines.append(
                        PolyMarker([comparison.logData.roastEventData[i]],
                                   legend=utilities.replaceUnderscoreWithSpace(name) + ': ' + logName,
                                   colour=utilities.setLightness(styles[name]["colour"], logColourValue),
                                   marker=styles[name]["marker"], size=styles[name]["size"],
                                   fillstyle=styles[name]["fillstyle"]))

            logColourValue += logColourStep
            profileColourValue += profileColourStep
        return comparisonLines
    else:
        return []


def calculatePointsFromProfile(frame, backgroundProfile, bezierLineMode, scale=None, temperature_unit=None):
    if scale == 'fit' and not hasattr(frame, 'page2'): return []
    comparisonPoints = []
    for i in range(len(backgroundProfile) - 1):
        a = backgroundProfile[i].point
        b = backgroundProfile[i].rightControl
        c = backgroundProfile[i + 1].leftControl
        d = backgroundProfile[i + 1].point
        if b.x == 0 and b.y == 0:
            b = a
        if c.x == 0 and c.y == 0:
            c = d
        for time in range(int(round(a.x)), int(round(d.x))):
            if bezierLineMode:
                p = bezierPointFromX(time, a, b, c, d)
            else:
                p = Point()
                p.x = time
                p.gradient = (d.y - a.y) / (d.x - a.x)
                p.y = a.y + (p.x - a.x) * p.gradient
                p.second_div = 0
            comparisonPoints.append((p.x, convertFanRPMtoFitTemperatureScale(frame, p.y) if scale == 'fit' else p.y))
    return comparisonPoints


def updateProfilePointsOnTab(where, newPoints):
    where.profilePoints = newPoints
    if where.title.startswith('Fan'):
        where.frame.fanProfilePoints = where.profilePoints
    else:
        where.frame.roastProfilePoints = where.profilePoints

def convertFanRPMtoFitTemperatureScale(frame, rpm):
    rpm_max, rpm_min = frame.page2.unzoomedYaxis
    rpm_max_fit_to, rpm_min_fit_to = frame.page1.unzoomedYaxis

    m = float(rpm_max_fit_to - rpm_min_fit_to) / float(rpm_max - rpm_min)
    c = rpm_min_fit_to - m * rpm_min
    return rpm * m + c

def convertFanRPMfromFitTemperatureScale(frame, temperature):
    rpm_max, rpm_min = frame.page2.unzoomedYaxis
    rpm_max_fit_to, rpm_min_fit_to = frame.page1.unzoomedYaxis

    m = float(rpm_max_fit_to - rpm_min_fit_to) / float(rpm_max - rpm_min)
    c = rpm_min_fit_to - m * rpm_min
    return (temperature - c) / m

def drawProfile(self, title, yAxis, profilePoints, selectedIndex, selectedType, showRateOfRise,
                levelString=None, thresholdString=None, closest_point=None, emulationMode=EMULATE_KAFFELOGIC,
                showGrid=False):
    comparisonLines = drawComparisons(self, title)
    bezierLineMode = (emulationMode == EMULATE_KAFFELOGIC) or (title == 'Fan Profile Curve')
    profile_points = []
    bezier_points = []
    control_points = []
    rate_of_rise_points = []
    fanScale = 'fit'
    fanScaleText = ''
    fanStyle = wx.PENSTYLE_LONG_DASH
    fan_speed_points = calculatePointsFromProfile(self.frame, self.frame.fanProfilePoints, True, scale=fanScale, temperature_unit=self.frame.temperature_unit)
    fan_speed_line = PolyLine(fan_speed_points, legend='Fan speed' + fanScaleText, colour='blue', style=fanStyle,
                              width=self.frame.lineWidth)
    second_derivative_points = []
    recommended_temperature = temperatureFromLevel(levelString, thresholdString)
    if recommended_temperature is None:
        recommended_temperature = float("-inf")

    highest_temperature = temperatureFromLevel(self.frame.emulation_mode.level_max_val, thresholdString)
    self.recommended_endpoint = None
    self.highest_endpoint = None
    p = profilePoints[0].point  # in case only one profile point, p needs to be set
    p.gradient = 1
    p.second_div = 0
    for i in range(len(profilePoints) - 1):
        ## print roast_profile[i].toTuple()
        profile_points.append(profilePoints[i].point.toTuple())
        a = profilePoints[i].point
        b = profilePoints[i].rightControl
        c = profilePoints[i + 1].leftControl
        d = profilePoints[i + 1].point
        if b.x == 0 and b.y == 0:
            b = a
        else:
            if i == selectedIndex:
                control_points.append(b.toTuple())
        if c.x == 0 and c.y == 0:
            c = d
        else:
            if i + 1 == selectedIndex:
                control_points.append(c.toTuple())
        low_temperature = min(a.y, d.y) 
        high_temperature = max(a.y, d.y)
        if recommended_temperature > low_temperature and recommended_temperature <= high_temperature and self.recommended_endpoint is None:
            if bezierLineMode:
                # recommended_endpoint found before last profile point
                self.recommended_endpoint = bezierPointFromY(recommended_temperature, a, b, c, d).toTuple()
            else:
                p = Point()
                p.y = recommended_temperature
                p.gradient = (d.y - a.y) / (d.x - a.x)
                p.x = a.x + (p.y - a.y) / p.gradient
                self.recommended_endpoint = p.toTuple()
        if highest_temperature > low_temperature and highest_temperature <= high_temperature and self.highest_endpoint is None:
            if bezierLineMode:
                self.highest_endpoint = bezierPointFromY(highest_temperature, a, b, c, d).toTuple()
            else:
                p = Point()
                p.y = highest_temperature
                p.gradient = (d.y - a.y) / (d.x - a.x)
                p.x = a.x + (p.y - a.y) / p.gradient
                self.highest_endpoint = p.toTuple()
        """
        print "a=", a.toTuple()
        print "b=", b.toTuple()
        print "c=", c.toTuple()
        print "d=", d.toTuple()
        """

        for time in range(int(round(a.x)), int(round(d.x))):
            if bezierLineMode:
                p = bezierPointFromX(time, a, b, c, d)
            else:
                p = Point()
                p.x = time
                p.gradient = (d.y - a.y) / (d.x - a.x)
                p.y = a.y + (p.x - a.x) * p.gradient
                p.second_div = 0

            bezier_points.append(p.toTuple())
            # print "appending point", p
            rate_of_rise_points.append((p.x, p.gradient * 60))
            second_derivative_points.append((p.x, p.second_div * 60 * 60))
    profile_last_point = p if (not bezierLineMode) or (len(profilePoints) < 2) else bezierPointFromX(d.x, a, b, c, d)
    if self.highest_endpoint is None and highest_temperature > profilePoints[-1].point.y and abs(
            profile_last_point.gradient) > 0.001:
        # if highest temperature is over the end of the profile, we extrapolate the profile
        self.highest_endpoint = Point(
            profile_last_point.x + (highest_temperature - profile_last_point.y) / profile_last_point.gradient,
            highest_temperature).toTuple()
        if (self.highest_endpoint[0] > ROAST_ABSOLUTE_MAX) or p.gradient <= 0:
            self.highest_endpoint = (ROAST_ABSOLUTE_MAX, highest_temperature)
    if self.recommended_endpoint is None and recommended_temperature > profilePoints[
        -1].point.y and profile_last_point.gradient > 0.001:
        # i.e. recommended temperature is over the end of the profile, in the extrapolated zone, or maybe beyond the extrapolated zone
        self.recommended_endpoint = Point(
            profile_last_point.x + (recommended_temperature - profile_last_point.y) / profile_last_point.gradient,
            recommended_temperature).toTuple()
        if (self.recommended_endpoint[0] > self.highest_endpoint[0]):
            self.recommended_endpoint = None
    if title == 'Fan Profile Curve':
        # we will use the highest endpoint from the temperature profile curve
        temperature_end = self.frame.page1.pointsAsGraphed[-1]
        if int(round(profile_last_point.x)) < int(round(temperature_end[0])):
            self.highest_endpoint = temperature_end
    if self.highest_endpoint is not None:
        time = profile_last_point.x
        temp = profile_last_point.y
        grad = profile_last_point.gradient
        while temp < self.highest_endpoint[1] and time <= ROAST_ABSOLUTE_MAX:
            time += 1.0
            temp = profile_last_point.y + (time - profile_last_point.x) * grad
            p = Point()
            p.x = time
            p.y = temp
            p.gradient = grad
            p.second_div = 0
            bezier_points.append(p.toTuple())
            rate_of_rise_points.append((p.x, p.gradient * 60))
            second_derivative_points.append((p.x, p.second_div * 60 * 60))

    if recommended_temperature is not None:
        level_extent = bezier_points[-1][0] if self.recommended_endpoint is None else self.recommended_endpoint[0]
        roastEndByTimeRatio = float(self.frame.page4.configControls["roast_end_by_time_ratio"].GetValue())
        # The roast end criteria is calculated by the following C code...
        #   profilePoint.y * time_ratio + actualTemperature * (1 - time_ratio) >= endTemperature;
        #
        # actualTemperature = T
        # time_ratio = R
        # time = t
        # profilePoint.y = bezierCalculate(t).y
        # endTemperature = Tend = recommended_temperature
        #
        # Algebra:
        #   bezierCalculate(t).y * R + T * (1 - R) = Tend
        #   T * (1 - R) = Tend - bezierCalculate(t).y * R
        #   T = (-bezierCalculate(t).y * R + Tend) / (1 - R)
        if self.recommended_endpoint is None:
            recommended_level_points = [(profilePoints[0].point.x, recommended_temperature),
                                        (level_extent, recommended_temperature)]
        else:
            if abs(1 - roastEndByTimeRatio) < 0.01:
                recommended_level_points = [(level_extent, 250.0), (level_extent, 0.0)]
            else:
                recommended_level_points = []
                for p in bezier_points:
                    T = (-p[1] * roastEndByTimeRatio + recommended_temperature) / (1 - roastEndByTimeRatio)
                    recommended_level_points.append((p[0], T))
        recommended_level_line = PolyLine(recommended_level_points, legend='Threshold line',
                                          colour=wx.Colour(255, 148, 148), style=wx.DOT, width=self.frame.lineWidth)
    profile_points.append(profilePoints[len(profilePoints) - 1].point.toTuple())
    profile_markers = PolyMarker(profile_points, legend='Points', colour='blue',
                                 marker='circle', size=self.frame.markerSize)
    selection = []
    if selectedType == 'point':
        selection.append(profilePoints[selectedIndex].point.toTuple())
    if selectedType == 'leftControl':
        selection.append(profilePoints[selectedIndex].leftControl.toTuple())
    if selectedType == 'rightControl':
        selection.append(profilePoints[selectedIndex].rightControl.toTuple())
    control_markers = PolyMarker(control_points, legend='Controls[hidden]', colour='yellow',
                                 marker='circle', size=self.frame.markerSize)
    selected_markers = PolyMarker(selection, legend='Selection[hidden]', colour='black',
                                  marker='circle', size=1.75 * self.frame.markerSize, fillstyle=wx.TRANSPARENT)
    if self.recommended_endpoint is not None:
        endpoint_markers = PolyMarker([self.recommended_endpoint], legend='Recommended level', colour='red',
                                      marker='square', size=self.frame.markerSize)

    control_line_points = []
    if profilePoints[selectedIndex].leftControl.toTuple() != (0.0, 0.0):
        control_line_points.append(profilePoints[selectedIndex].leftControl.toTuple())
    control_line_points.append(profilePoints[selectedIndex].point.toTuple())
    if profilePoints[selectedIndex].rightControl.toTuple() != (0.0, 0.0):
        control_line_points.append(profilePoints[selectedIndex].rightControl.toTuple())
    if len(control_line_points) <= 1:
        control_line_points = []
    control_lines = PolyLine(control_line_points, legend='Control lines[hidden]', colour='black', style=wx.LONG_DASH,
                             width=self.frame.lineWidth)

    zoneLines = drawZones(self, bezier_points) if title == 'Roast Profile Curve' and hasattr(self,
                                                                                             'showZones') and self.showZones else []

    self.pointsAsGraphed = bezier_points
    self.gradientsAsGraphed = rate_of_rise_points
    self.secdivsAsGraphed = second_derivative_points
    RoR_scale = float(self.frame.options.getUserOption("ror_multiplier"))
    self.gradientsAsGraphedScaled = scaled(rate_of_rise_points, RoR_scale)
    self.secdivsAsGraphedScaled = scaled(second_derivative_points, RoR_scale)
    phases_lines = []
    if hasattr(self, 'phasesObject') and hasattr(self, 'togglePhases') and self.togglePhases.IsChecked():
        self.phasesObject.recalculateProfilePhases()
        cc = floatOrNone(fromMinSec(self.phasesObject.phasesControls["colour_change_Time"].GetValue()))
        fc = floatOrNone(fromMinSec(self.phasesObject.phasesControls["first_crack_Time"].GetValue()))
        top_y = 300 if self.frame.temperature_unit == 'C' else 500
        if cc is not None and cc != 0.0:
            phases_lines.append(
                PolyLine([(cc, 0), (cc, top_y)], legend='Expected colour change', colour=wx.Colour(245, 225, 65),
                         width=self.frame.lineWidth))
        if fc is not None and fc != 0.0:
            phases_lines.append(
                PolyLine([(fc, 0), (fc, top_y)], legend='Expected first crack', colour=wx.Colour(255, 185, 65),
                         width=self.frame.lineWidth))
    bezier_line = PolyLine(bezier_points, legend='Profile', colour='blue', width=self.frame.lineWidth) if len(
        bezier_points) > 1 else None
    rate_of_rise_line = PolyLine(utilities.filterPointsY(self.gradientsAsGraphedScaled, temperature.convertCelciusPointToSpecifiedUnit(DERIVATIVE_ALLOWED_YRANGE, self.frame.temperature_unit)),
                                 legend=addScaleFactorToLegendText(temperature.insertTemperatureUnit('Rate of rise °/min',
                                                                self.frame.temperature_unit), RoR_scale),
                                 colour='green', width=self.frame.lineWidth)
    second_derivative_line = PolyLine(utilities.filterPointsY(self.secdivsAsGraphed, temperature.convertCelciusPointToSpecifiedUnit(DERIVATIVE_ALLOWED_YRANGE, self.frame.temperature_unit)),
                                      legend=addScaleFactorToLegendText(temperature.insertTemperatureUnit('Second derivative °/min/min',
                                                                self.frame.temperature_unit),
                                                                        RoR_scale), colour='purple',
                                      width=self.frame.lineWidth)
    linesToGraph = []
    linesToGraph += zoneLines
    linesToGraph += [bezier_line] if len(bezier_points) > 1 else []
    linesToGraph += phases_lines
    if recommended_temperature is not None and (showGrid or self.recommended_endpoint is None):
        linesToGraph.append(recommended_level_line)
    if bezierLineMode: linesToGraph += [control_lines]
    linesToGraph += [profile_markers]
    if bezierLineMode: linesToGraph += [control_markers]
    if self.recommended_endpoint is not None:
        linesToGraph += [endpoint_markers]
    linesToGraph += [selected_markers]
    if closest_point is not None and self.showSelectionCross:
        linesToGraph.append(PolyMarker([closest_point.toTuple()], legend='Selection cross[hidden]', colour="gray",
                                       marker='cross', size=1.5 * self.frame.markerSize, fillstyle=wx.TRANSPARENT))

    self.rates = []
    if title == 'Roast Profile Curve' and showRateOfRise:
        self.rates = [rate_of_rise_line]
        if bezierLineMode and self.frame.options.getUserOption("show_second_derivative") == "yes":
            self.rates = [rate_of_rise_line, second_derivative_line]
        linesToGraph = (self.rates if len(bezier_points) > 1 else []) + linesToGraph

    if title == 'Roast Profile Curve' and hasattr(self, 'showFanSpeed') and self.showFanSpeed:
        linesToGraph = [fan_speed_line] + linesToGraph

    if self.frame.comparisons is not None:
        linesToGraph += comparisonLines

    if yAxis == 'temperature':
        yAxis = temperature.insertTemperatureUnit('temperature (°)', self.frame.temperature_unit)
    if yAxis == 'speed':
        yAxis = 'speed (RPM x 10)'
    return PlotGraphics(linesToGraph, title, "time (min:sec)", yAxis)


########################################################################
def loadCurrentLogAsFirstCompare(self, clearOtherCompares):
    backObj = BaseDataObject()
    backObj.fileName = self.fileName
    dataList = clean(self.datastring).split('\r\r')
    try:
        logText = dataList[1]
    except:
        return
    backObj.datastring = dataObjectsToString(self) + '\r\r' + logText
    self.comparisons = [backObj] + ([] if self.comparisons is None or clearOtherCompares else self.comparisons)
    self.loadComparisons()


class extractProfileDialog(wx.Dialog):

    def __init__(self, parent, title="Extract"):
        super(extractProfileDialog, self).__init__(parent)
        self.parent = parent
        self.SetTitle(title + " profile from log")
        self.result = "cancel"
        self.modified = False
        self.useLogAsComparison = False
        self.clearOtherCompares = False
        self.box = wx.BoxSizer(wx.VERTICAL)
        grid = wx.FlexGridSizer(cols=5, vgap=5, hgap=5)

        label = wx.StaticText(self, -1, "Copy logged data to expected/recommended values if required")
        self.box.Add(label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)

        self.controls = {}
        colour_change = self.parent.logPanel.phasesObject.getColourChange()
        first_crack = self.parent.logPanel.phasesObject.getFirstCrack()
        roast_level = self.parent.page3.configControls[
            'roasting_level'].GetValue() if 'roasting_level' in list(self.parent.page3.configControls.keys()) else ''

        self.addRow(grid, "colour change", colour_change, self.parent.page1.phasesObject.getColourChange())
        self.addRow(grid, "first crack", first_crack, self.parent.page1.phasesObject.getFirstCrack())
        self.addRow(grid, "level", roast_level, str(self.parent.page1.level_floatspin.GetValue()), True)

        self.background = wx.CheckBox(self, label='Use log as background compare file')
        self.background.SetValue(self.parent.options.getUserOptionBoolean("use_log_as_compare_on_extract", False))
        self.clearOthers = wx.CheckBox(self, label='Clear other compare files')
        self.clearOthers.SetValue(self.parent.options.getUserOptionBoolean("clear_compare_on_extract", False))

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        applyButton = wx.Button(self, label=title)
        cancelButton = wx.Button(self, label='Cancel')
        buttons.Add(applyButton, 1, wx.ALL, 7)  # Mac buttons need 7-pixel borders or they overlap
        buttons.Add(cancelButton, 1, wx.ALL, 7)
        self.box.Add(grid, 0, wx.ALL, 10)

        checkboxes = wx.BoxSizer(wx.VERTICAL)
        checkboxes.Add(self.background, 0, wx.ALL | wx.ALIGN_LEFT, 10)
        checkboxes.Add(self.clearOthers, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_LEFT, 10)
        self.box.Add(checkboxes, 0, wx.ALL | wx.ALIGN_CENTRE, 0)
        self.box.Add(buttons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        self.box.SetSizeHints(self)
        self.SetSizer(self.box)
        applyButton.Bind(wx.EVT_BUTTON, self.onApply)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
        self.Bind(wx.EVT_BUTTON, self.onCopyButton)

        applyButton.SetDefault()
        if not isLinux: self.Raise()

    def addRow(self, grid, eventName, loggedValue, expectedValue, isRecommended=False):
        leftDescriptor = "Logged"
        rightDescriptor = "Recommended" if isRecommended else "Expected"
        label = wx.StaticText(self, -1, leftDescriptor + " " + eventName)
        grid.Add(label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        logged = wx.TextCtrl(self, -1, loggedValue, size=(60, -1))
        self.controls["source_" + eventName] = logged
        grid.Add(logged, 0, wx.EXPAND)
        grid.Add(wx.Button(self, label='»', size=(20, -1), name=eventName))
        expected = wx.TextCtrl(self, -1, expectedValue, size=(60, -1))
        expected.Bind(wx.EVT_TEXT, self.onModify)
        self.controls["destination_" + eventName] = expected
        grid.Add(expected, 0, wx.EXPAND)
        label = wx.StaticText(self, -1, rightDescriptor + " " + eventName)
        grid.Add(label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)

    def onModify(self, event):
        self.modified = True

    def onCopyButton(self, event):
        name = event.EventObject.GetName()
        source = self.controls["source_" + name]
        destination = self.controls["destination_" + name]
        destination.SetValue(temperature.removeTemperatureUnit(source.GetValue()))

    def onApply(self, e):
        self.result = "ok"
        if self.modified:
            self.parent.page1.phasesObject.setColourChange(self.controls["destination_colour change"].GetValue())
            self.parent.page1.phasesObject.setFirstCrack(self.controls["destination_first crack"].GetValue())
            level = floatOrNone(self.controls["destination_level"].GetValue())
            if level is not None: self.parent.page1.level_floatspin.SetValue(level)
        self.useLogAsComparison = self.background.GetValue()
        self.parent.options.setUserOptionBoolean("use_log_as_compare_on_extract", self.useLogAsComparison)
        self.clearOtherCompares = self.clearOthers.GetValue()
        self.parent.options.setUserOptionBoolean("clear_compare_on_extract", self.clearOtherCompares)
        self.Close()

    def onCancel(self, e):
        self.modified = False
        self.Close()


########################################################################
class mergeDialog(wx.Dialog):
    HINT_TEXT = "Merge into the current profile from\n"

    def __init__(self, parent):
        super(mergeDialog, self).__init__(parent)
        self.parent = parent
        self.SetTitle("Merge into the current profile")
        box = wx.BoxSizer(wx.VERTICAL)
        optionsBox = wx.BoxSizer(wx.VERTICAL)

        hintText = wx.StaticText(self, -1, self.HINT_TEXT + self.parent.mergeFrom.fileName)
        hintText.Wrap(250)
        box.Add(hintText, 0, wx.ALL | wx.ALIGN_CENTRE, 10)

        self.profileCurve = wx.CheckBox(self, label="Roast profile curve")
        self.phases = wx.CheckBox(self, label="Expected colour change, expected first crack, and recommended level")
        self.fanCurve = wx.CheckBox(self, label="Fan profile curve")
        self.description = wx.CheckBox(self, label="Short name, designer, and description")
        self.zones = wx.CheckBox(self, label="Zone and corner settings")
        self.settings = wx.CheckBox(self, label="All other profile settings")
        optionsBox.Add(self.profileCurve, 0, wx.ALL | wx.ALIGN_LEFT, 2)
        optionsBox.Add(self.phases, 0, wx.ALL | wx.ALIGN_LEFT, 2)
        optionsBox.Add(self.fanCurve, 0, wx.ALL | wx.ALIGN_LEFT, 2)
        optionsBox.Add(self.description, 0, wx.ALL | wx.ALIGN_LEFT, 2)
        optionsBox.Add(self.zones, 0, wx.ALL | wx.ALIGN_LEFT, 2)
        optionsBox.Add(self.settings, 0, wx.ALL | wx.ALIGN_LEFT, 2)
        box.Add(optionsBox, 0, wx.ALL | wx.ALIGN_CENTRE, 8)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        mergeButton = wx.Button(self, label='Merge')
        cancelButton = wx.Button(self, label='Cancel')
        buttons.Add(mergeButton, 1, wx.ALL, 7)  # Mac buttons need 7-pixel borders or they overlap
        buttons.Add(cancelButton, 1, wx.ALL, 7)
        box.Add(buttons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.SetSizeHints(self)
        self.SetSizer(box)
        mergeButton.Bind(wx.EVT_BUTTON, self.onMerge)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
        mergeButton.SetDefault()
        if not isLinux: self.Raise()

    def onMerge(self, e):
        wx.App.Get().doRaise()
        if (not self.profileCurve.IsChecked()) and \
                (not self.fanCurve.IsChecked()) and \
                (not self.phases.IsChecked()) and \
                (not self.description.IsChecked()) and \
                (not self.zones.IsChecked()) and \
                (not self.settings.IsChecked()):
            return
        # Put the relevant profile data into frame.configuration, frame.configurationOrderedKeys, frame.roastProfilePoints, frame.fanProfilePoints.
        self.parent.loadExtraDataObject(self.parent.mergeFrom)
        self.updated = None
        if self.profileCurve.IsChecked():
            self.parent.captureHistory(self.parent.page1, 'merge', True)  # , isBulkChange=self.phases.IsChecked())
            self.parent.roastProfilePoints = copy.deepcopy(self.parent.mergeFrom.roastProfilePoints)
            self.parent.page1.profilePoints = self.parent.roastProfilePoints
            self.parent.emulation_mode = self.parent.mergeFrom.emulation_mode
            self.parent.configuration["emulation_mode"] = self.parent.mergeFrom.configuration["emulation_mode"]
            self.parent.modified(True)
            self.parent.page1.setSpinners()
            self.updated = 0
        if self.phases.IsChecked():
            self.parent.captureHistory(self.parent.page1, 'capture', calledFromTextChange=True,
                                       isBulkChange=self.profileCurve.IsChecked())
            self.pageMerge(settingGroups['phases'], self.parent.page1, 0)
        if self.fanCurve.IsChecked():
            self.parent.captureHistory(self.parent.page2, 'merge', True)
            self.parent.fanProfilePoints = copy.deepcopy(self.parent.mergeFrom.fanProfilePoints)
            self.parent.page2.profilePoints = self.parent.fanProfilePoints
            self.parent.modified(True)
            self.parent.page2.setSpinners()
            self.updated = 1
        if self.description.IsChecked():
            desiredSettings = list(self.parent.page3.configControls.keys())  # we know it is a profile, so grab all of the config settings from page3
            self.pageMerge(desiredSettings, self.parent.page3, 2)
        desiredSettings = []
        if self.zones.IsChecked():
            desiredSettings += settingGroups['zones']
        if self.settings.IsChecked():
            desiredSettings += [k for k in self.parent.configurationOrderedKeys if
                                k not in ['profile_schema_version'] + settingGroups['phases'] + settingGroups['zones']]
        self.pageMerge(desiredSettings, self.parent.page4, 3)
        if self.updated is not None:
            self.parent.notebook.SetSelection(self.updated)
        self.Close()

    def pageMerge(self, desiredSettings, page, pageIndex):
        if len(desiredSettings) > 0:
            settingsKeys = page.configList
            for key in settingsKeys:
                if (key in desiredSettings) and (key in list(page.configControls.keys())):
                    control = page.configControls[key]
                    new = self.parent.mergeFrom.configuration[key]
                    old = floaty(control.GetValue())
                    # print key, old, '==>', new
                    if new != old:
                        control.SetFocus()
                        isBulkChange = True
                        if key == settingsKeys[-1]:
                            isBulkChange = False
                        self.parent.focus(page, control, isBulkChange=isBulkChange)
                        control.ChangeValue(str(new))
                        self.parent.txtChange(page, control, isBulkChange=isBulkChange)  # captures it in history
            self.updated = pageIndex

    def onCancel(self, e):
        self.Close()


def displayUpdateStatus(self, data, errorMessage, onlyAlertIfUpdateAvailable, flag=None):
    if flag is not None and not flag.is_set(): return
    try:
        p = self
        while not p.IsTopLevel():
            p = p.GetParent()
    except wx.PyDeadObjectError:
        p = None
    softCheckBoxIndex = None
    firmCheckBoxIndex = None
    if errorMessage is not None or data is None:
        htmlList = viewmemstick.UNABLE_TO_CONNECT_MESSAGE.replace('[[errorMessage]]', errorMessage)
        checkBoxTextList = None
        if onlyAlertIfUpdateAvailable:
            return
    else:
        softVersion = extractVersionFromNotes(data[0])
        softStatus = compareVersions(softVersion, PROGRAM_VERSION)
        firmVersion = extractVersionFromNotes(data[1])
        frame = wx.App.Get().frame
        highest = frame.options.getUserOption("highest_firmware_version_seen")
        firmStatus = compareVersions(firmVersion, highest) if not (highest == '' and onlyAlertIfUpdateAvailable) else 0
        if onlyAlertIfUpdateAvailable and frame.options.getUserOption("no_alert_for_this_version") == softVersion:
            softStatus = 0
        if onlyAlertIfUpdateAvailable and frame.options.getUserOption("no_alert_for_this_firmware") == firmVersion:
            firmStatus = 0
        if onlyAlertIfUpdateAvailable and (softStatus != 1) and (firmStatus != 1): return
        htmlList = []
        checkBoxTextList = []
        if softStatus == 1 or not onlyAlertIfUpdateAvailable:
            html = "<h2>" + PROGRAM_NAME + "</h2>"
            if softStatus == 0:
                softMessage = "Your current version is up to date."
            elif softStatus == -1:
                softMessage = "You are ahead of the latest official release. Thank you for being a beta tester."
            elif softStatus == 1:
                softMessage = "There is an update available. Please visit <a href='" + DOWNLOADS_URL + "'>the " + PROGRAM_SHORTNAME + " download page</a> to download and install the latest version."
            html += '<p>Latest release is ' + PROGRAM_SHORTNAME + ' ' + softVersion + '</p><p>You are using ' + PROGRAM_SHORTNAME + \
                    ' ' + PROGRAM_VERSION + '</p><p>' + softMessage + '</p>'
            htmlList.append(html)
            checkBoxTextList.append(
                "Don't show this again for the current release, " + PROGRAM_SHORTNAME + " version " + softVersion)
            softCheckBoxIndex = 0
        if firmStatus == 1 or not onlyAlertIfUpdateAvailable:
            html = "<h2>Firmware</h2>"
            if firmStatus == 0:
                firmMessage = "It looks like you have successfully downloaded the update."
            elif firmStatus == -1:
                firmMessage = "It looks like you have downloaded firmware that is ahead of the latest official release: you have downloaded version " + \
                              frame.options.getUserOption(
                                  "highest_firmware_version_seen") + ". Thank you for being a beta tester."
            elif firmStatus == 1:
                firmMessage = "It looks like you haven't downloaded the latest version yet. (" + PROGRAM_NAME + " hasn't detected the update file on your memory stick.)"
            html += '<p>The latest firmware available is ' + firmVersion + '</p>'
            html += '''<p>Firmware updates need to be downloaded and saved on a USB memory stick. They are installed on the roaster from the memory stick.</p>
                    For more information put a memory stick in your computer, close this dialog and use the menu to select <i>Tools, View memory stick, Firmware</i>.'''
            html += '<p>' + firmMessage + '</p>'
            htmlList.append(html)
            checkBoxTextList.append("Don't show this again for the current firmware release, version " + firmVersion)
            firmCheckBoxIndex = 0 if softCheckBoxIndex is None else 1
    dialog = dialogs.enhancedMessageDialog(p)
    dialog.init(htmlList, 'Update Status',
                checkBox=[False, False] if (onlyAlertIfUpdateAvailable and errorMessage is None) else None,
                checkBoxText=checkBoxTextList, wideFormat=False, exitOnLinkClick=True)
    dialog.ShowModal()
    if softCheckBoxIndex is not None and dialog.getCheckBox(softCheckBoxIndex):
        frame.options.setUserOption("no_alert_for_this_version", softVersion)
    if firmCheckBoxIndex is not None and dialog.getCheckBox(firmCheckBoxIndex):
        frame.options.setUserOption("no_alert_for_this_firmware", firmVersion)
    dialog.Destroy()
    if flag is not None:
        flag.clear()


########################################################################
def saveWorkingDirectories(filename):
    wx.App.Get().frame.options.setUserOption("working_directory", os.path.dirname(filename))
    if not extractDriveFromPath(filename) in removableDrives():
        wx.App.Get().frame.options.setUserOption("nonremovable_working_directory", os.path.dirname(filename))
        # print "setting option with", os.path.dirname(self.GetPath())


class myFileDialog(wx.FileDialog):
    def __init__(self, parent, message, defaultDir, defaultFile, wildcard, style):
        working_directory = defaultDir if defaultDir != '' else wx.App.Get().frame.options.getUserOption("working_directory",
                                                                                            default=rootDrive())
        if not os.path.isdir(working_directory):
            working_directory = wx.App.Get().frame.options.getUserOption("nonremovable_working_directory", default=rootDrive())
            if not os.path.isdir(working_directory):
                working_directory = rootDrive()
        # print "working_directory", repr(working_directory), 'defaultDir', repr(defaultDir)
        wx.FileDialog.__init__(self, parent, message, defaultDir=working_directory, defaultFile=defaultFile,
                               wildcard=wildcard, style=style)

    def ShowModal(self):
        result = wx.FileDialog.ShowModal(self)
        filename = self.GetPath()
        if result != wx.ID_CANCEL:
            saveWorkingDirectories(filename)
        return result


########################################################################

def refreshGridPanel(panel, app):
    for item in panel.configList:
        if item in list(panel.configControls.keys()):
            if item in list(app.configuration.keys()):
                panel.configControls[item].ChangeValue(decodeCtrlV(str(app.configuration[item])))
            else:
                panel.configControls[item].ChangeValue('')
    panel.Layout()
    app.Layout()


class HistoryConfigEntry:
    def __init__(self, control, isFocusEvent, isBulkChange=False, applyLinuxFix=False):
        self.entryType = 'config'
        self.isFocusEvent = isFocusEvent
        self.bulkChange = isBulkChange
        self.key = control.GetName()
        self.value = str(control.GetValue())
        if hasattr(control, 'GetInsertionPoint'):
            self.cursorPos = control.GetInsertionPoint() + (1 if applyLinuxFix and isLinux else 0)
        else:
            self.cursorPos = 0

    def toDisplay(self):
        print(self.key + ": " + self.value + " @" + str(self.cursorPos))
        if hasattr(self, "restoreCursorPos"): print("restore to " + str(self.restoreCursorPos))
        if hasattr(self, "isFocusEvent"): print("isFocusEvent " + str(self.isFocusEvent))


class HistoryNullConfigEntry:
    def __init__(self):
        self.entryType = 'config'
        self.isFocusEvent = True
        self.bulkChange = False
        self.key = ""
        self.value = ""
        self.cursorPos = 0


########################################################################
class GridPanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, frame, configList):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)
        self.frame = frame
        self.parent = parent
        self.SetupScrolling()
        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.grid = None
        self.initConfigList(frame, configList)
        self.hover = None
        self.addGrid(frame)
        self.SetSizerAndFit(self.mainSizer)
        self.resetHistory()

    def initConfigList(self, frame, configList):
        # Data that is not recognised because the log/profile has data elements in it that are not part of the schema is unknown.
        # Unknowns always go on page3 for consistency.
        known = set(list(frame.defaults.keys()) + profileDataInLog + logFileName + notSavedInProfile)
        unknown = [x for x in list(frame.configuration.keys()) if x not in known]
        if configList == "others":
            # We are populating page4, exclude the unknowns
            keys = frame.configurationOrderedKeys
            unwanted = set(
                aboutThisFileParameters + logFileName + notSavedInProfile + ['recommended_level', 'expect_fc',
                                                                             'expect_colrchange',
                                                                             'emulation_mode'] + unknown)
            configList = [x for x in keys if x not in unwanted]
            self.configList = copy.deepcopy(configList)
        else:
            # We are populating page3, include the unknowns
            self.configList = copy.deepcopy(configList + unknown)

    def resetHistory(self):
        # The history array must contain one entry, so we make sure it does, and also make sure that it is the first enabled control on the tab.
        self.history = [HistoryConfigEntry(self.configControls[self.configList[0]], isFocusEvent=True)]
        for control in self.configList:
            if control in list(self.configControls.keys()) and self.configControls[control].IsEnabled():
                self.history = [HistoryConfigEntry(self.configControls[control], isFocusEvent=True)]
                break
        # self.history = [HistoryConfigEntry(self.configControls[self.configList[0]])]
        self.historyIndex = 0
        self.historyCanUndo = False
        self.captureFocusEvents = True

    def addGrid(self, frame):
        shown = self.IsShown()
        self.Show(False)
        if not self.grid is None:
            self.grid.Clear(True)
            self.mainSizer.Remove(self.grid)
            self.grid = None
        if not self.hover is None:
            self.hover.Destroy()
            self.hover = None
        self.grid = wx.GridBagSizer(0, 3)
        self.grid.SetEmptyCellSize((0, 0))
        self.configControls = {}
        self.configLabels = {}
        self.itemCount = 0
        for item in self.configList:
            self.addItem(frame, item, False)
        self.mainSizer.Add(self.grid, 1, wx.ALL | wx.EXPAND, 5)
        frame.Layout()
        self.SetupScrolling()
        self.SendSizeEvent()
        self.hover = HtmlPopup(self, wx.NO_BORDER, "placeholder", "#c0c0c0", size=(500, 800), position=(0, 0))
        self.hover.Hide()
        self.focusObject = None
        if shown:
            self.Show(True)
        self.refreshDiffStatusAll(frame)

    def difficulty_name_to_integer(self, difficulty_text):
        return 4 if difficulty_text == "engineer" else 3 if difficulty_text == "expert" else 2 if difficulty_text == "advanced" else 1

    def applyDifficulties(self):
        """
        Difficulties are defined for each config setting in kaffelogic_studio_hints.txt
        """
        if isWindows: self.Freeze()
        difficulty_text = self.frame.options.getUserOption("difficulty")
        difficulty_level = self.difficulty_name_to_integer(difficulty_text)
        for item in self.configList:
            if item in list(self.configLabels.keys()) and item in list(self.configControls.keys()):
                item_difficulty = self.difficulty_name_to_integer(
                    self.frame.hints[item]["difficulty"]) if item in list(self.frame.hints.keys()) else 4
                diff = self.frame.FindWindowByName(item + '_diff')
                if item_difficulty <= difficulty_level:
                    if diff is not None: diff.Show()
                    self.configLabels[item].Show()
                    self.configControls[item].Show()
                else:
                    if diff is not None: diff.Hide()
                    self.configLabels[item].Hide()
                    self.configControls[item].Hide()
        if not self.grid.IsColGrowable(1): self.grid.AddGrowableCol(1, 1)
        x = self.GetSize()
        self.grid.Fit(self)
        self.SetSize(x)
        self.hover.Hide()
        where = self.frame.notebook.GetPage(self.frame.notebook.GetSelection())
        if isWindows: self.Thaw()
        if hasattr(where, 'reDraw'): where.reDraw()

    def formatEventDataByKey(self, frame, key):
        if key in frame.logData.roastEventNames:
            thisTemperature = ' ' + str(
                round(frame.logData.roastEventData[frame.logData.roastEventNames.index(key)][1], 1)) + temperature.insertTemperatureUnit('°')
            return toMinSec(float(fromMinSec(frame.configuration[key]))) + thisTemperature

    def setDiffStatusByKey(self, frame, key, disabling=False):
        diff = frame.FindWindowByName(key + '_diff')
        if disabling:
            diff.SetLabel('')
        else:
            if diff is not None:
                diff.SetLabel('↭' if frame.comparisonDiffByKey(key) is not None else '')
                return diff

    def refreshDiffStatusAll(self, frame):
        for key in list(self.configControls.keys()):
            self.setDiffStatusByKey(frame, key)

    def clearDiffStatusAll(self, frame):
        for key in list(self.configControls.keys()):
            self.setDiffStatusByKey(frame, key, disabling=True)

    def addItem(self, frame, item, is_expanding):
        if frame.fileType == "log" and item in notFoundInLog:
            return
        if frame.fileType == "log" and item in optionalInLog and (
                item not in list(frame.configuration.keys()) or frame.configuration[item] in [None, '']):
            return
        if is_expanding:
            self.grid.SetRows(self.grid.GetRows() + 1)
        if not item in list(frame.configuration.keys()):
            frame.configuration[item] = ''
            frame.configurationOrderedKeys.append(item)
        if item == 'profile_short_name':
            frame.configuration[item] = str(frame.configuration[item])[:15]
        if item == 'profile_designer':
            frame.configuration[item] = truncateUTF8stringTo(frame.configuration[item],
                                                             31)  # unicode is allowed in a designer name, but only 31 bytes of utf-8 encoded text

        label = wx.StaticText(self, -1, replaceUnderscoreWithSpace(item))
        labelSizer = wx.BoxSizer(wx.HORIZONTAL)
        labelSizer.Add(label)
        diff_label = wx.StaticText(self, -1, '', size=(20, -1),
                                   style=wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_BOTTOM | wx.ST_NO_AUTORESIZE,
                                   name=item + '_diff')
        diff_label.SetFont(diff_label.GetFont().Scale(1))
        labelSizer.Add(diff_label)
        if item == 'tasting_notes' or item == 'profile_description':
            self.grid.Add(labelSizer, pos=(self.itemCount, 0), flag=wx.ALIGN_RIGHT | wx.TOP, border=4)
            txt = wx.TextCtrl(self, -1, decodeCtrlV(str(frame.configuration[item])), size=(-1, 200),
                              style=wx.TE_MULTILINE, name=item)
        else:
            self.grid.Add(labelSizer, pos=(self.itemCount, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
            if item in frame.logData.roastEventNames:
                contents = self.formatEventDataByKey(frame, item)
            else:
                contents = trimTrailingPointZero(decodeCtrlV(str(frame.configuration[item])))
            txt = wx.TextCtrl(self, -1, contents, name=item)
        if item == 'profile_short_name':
            txt.SetMaxLength(15)
        if item == 'profile_designer':
            txt.SetMaxLength(31)
        self.configLabels[item] = label
        self.configControls[item] = txt
        # print txt.GetName()
        self.grid.Add(txt, pos=(self.itemCount, 1), flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=1)
        if not self.grid.IsColGrowable(1): self.grid.AddGrowableCol(1, 1)
        self.itemCount += 1
        if (frame.fileType == "log" and item != 'tasting_notes') or item in readOnly:
            txt.Disable()
        txt.Bind(wx.EVT_TEXT, self.onTxtChange)
        txt.Bind(wx.EVT_SET_FOCUS, self.onFocus)
        txt.Bind(wx.EVT_ENTER_WINDOW, self.onMouseEnter)
        if isLinux:
            label.Bind(wx.EVT_MOTION, on_info_hover)  # it seems EVT_ENTER doesn't fire for StaticText controls in Linux
        else:
            label.Bind(wx.EVT_ENTER_WINDOW, on_info_hover)

    def onTxtChange(self, event):
        # print event.EventObject.GetName() + ": " + event.EventObject.GetValue()
        self.frame.txtChange(self, event.EventObject,
                             applyLinuxFix=True)  # known issue for Linux insertion point in EVT_TEXT handler
        """
        While doing this, I noticed that GetInsertionPoint() doesn't
        work on Linux in an EVT_TEXT handler. it returns a value
        that is 1 less than it should be. In a EVT_KEY_DOWN handler
        on the other hand, it does return the correct value.
        https://trac.wxwidgets.org/ticket/10051
        """

        """
            for x in self.history:
                x.toDisplay()
            print "---------------"
        """

    def onFocus(self, event):
        self.frame.focus(self, event.EventObject)
        on_info_unhover(event)
        event.Skip()

    def onMouseEnter(self, event):
        on_info_unhover(event)
        event.Skip()

    ########################################################################


class myPlotCanvas(PlotCanvas):
    def __init__(self, *args, **kwargs):
        PlotCanvas.__init__(self, *args, **kwargs)

    def _xticks(self, *args):
        ticks = PlotCanvas._xticks(self, *args)
        if len(ticks) >= 2:
            default_first = ticks[0][0]
            default_last = ticks[-1][0]
            default_step = ticks[1][0] - ticks[0][0]
            max_ticks = len(ticks) * 2.5
        else:
            return ticks
        first = default_first
        last = default_last
        step = default_step
        good_steps = [1, 2, 5, 10, 15, 30, 60, 120, 180, 240, 300]
        for n in good_steps:
            step = n
            if n * max_ticks >= last - first:
                break
        first = (first // step) * step
        if first < 0:
            first += step
        last = (last // step) * step
        return [(time, toMinSec(time)) for time in range(int(first), int(last) + step, step)]


def initialiseDisplaySelectedText(self, labelText):
    displaySelectedText = wx.StaticText(self.canvas,
                                        id=wx.ID_ANY,
                                        label=labelText)
    positionDisplaySelectedText(self, displaySelectedText)
    return displaySelectedText


def positionDisplaySelectedText(self, displaySelectedText):
    posX, posY = addTuple(self.canvas.PositionUserToScreen(self.closest_point.toTuple()), (0, 7.5))
    sizeX, sizeY = displaySelectedText.GetSize()
    plotRight, plotBottom = self.canvas.PositionUserToScreen(
        (self.canvas.GetXCurrentRange()[1], self.canvas.GetYCurrentRange()[0]))
    if posX + sizeX > plotRight:
        posX -= sizeX
    if posY + sizeY > plotBottom:
        posY -= sizeY + 7.5
    displaySelectedText.SetPosition((posX, posY))


def destroySelectedText(self):
    if self.displaySelectedText is not None:
        self.displaySelectedText.Destroy()
    self.closest_point = None
    self.closest_distance = None
    self.closest_legend = None
    self.displaySelectedText = None


class myFloatSpinWithChangeValue(FS.FloatSpin):
    def __init__(self, *args, **kwargs):
        FS.FloatSpin.__init__(self, *args, **kwargs)
        self.__name = kwargs['name']
        self._textctrl.SetName(self.__name)
        self._spinbutton.SetName(self.__name)

    def GetName(self):
        return self.__name

    def ChangeValue(self, val):
        self._textctrl.ChangeValue(str(val))
        self.SyncSpinToText(send_event=False)


class myFloatSpin(FS.FloatSpin):
    def __init__(self, *args, **kwargs):
        self._leading = 0
        self._suffix = ''
        FS.FloatSpin.__init__(self, *args, **kwargs)

    def SetValue(self, *args):
        FS.FloatSpin.SetValue(self, *args)
        self._textctrl.SetValue(self._textctrl.GetValue().rjust(self._leading, '0') + self._suffix)

    def SyncSpinToText(self, *args):
        self._textctrl.SetValue(self._textctrl.GetValue().replace(self._suffix, ''))
        FS.FloatSpin.SyncSpinToText(self, *args)

    def SetLeading(self, lead):
        digits = self.GetDigits()
        if digits:
            lead += digits + 1
        self._leading = lead

    def SetSuffix(self, suffix):
        self._suffix = suffix


########################################################################
class ProfilePanel(wx.Panel):
    def __init__(self, parent, frame, title, yAxis):
        wx.Panel.__init__(self, parent)

        self.frame = frame
        self.title = title
        self.yAxis = yAxis
        self.closest_point = None
        self.closest_distance = None
        self.closest_legend = None
        self.displaySelectedText = None
        self.showSelectionCross = True
        self.configControls = {}
        self.configList = []
        self.captureFocusEvents = True
        self.focusObject = None

        # variables for managing arrow keys
        self.arrowkeyTimer = SafeTimer()
        self.arrowkeyTimer.Bind(wx.EVT_TIMER, self.onArrowkeyTimer)
        self.arrowkeyRepeatCount = 0
        self.arrowkeyCurrent = None
        self.arrowkeyIsAlt = False
        self.arrowkeyWentDownAt = None

        # initialise zooming variables
        self.zoomScale = 1
        self.expandY = False
        self.unzoomedYaxis = None
        self.zoomXAxis = None
        self.zoomYAxis = None

        if title == 'Roast Profile Curve':
            self.profilePoints = frame.roastProfilePoints
        if title == 'Fan Profile Curve':
            self.profilePoints = frame.fanProfilePoints
        self.pointsAsGraphed = None
        self.selectedIndex = 0
        self.selectedType = 'point'
        self.currentOperation = None
        self.resetHistory()
        self.isCloseEnoughToDrag = False
        self.wasCloseEnoughToDrag = False
        self.showRateOfRise = False
        self.lockAxes = False

        # create some sizers
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.chartSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.checkSizer = wx.BoxSizer(wx.HORIZONTAL)
        innerCheckSizer = wx.BoxSizer(wx.HORIZONTAL)

        # create the widgets

        # canvas
        self.canvas = myPlotCanvas(self)
        self.canvas.canvas.Bind(wx.EVT_LEFT_DOWN, self.onClick)
        self.canvas.canvas.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
        self.canvas.canvas.Bind(wx.EVT_MOTION, self.onMotion)
        self.canvas.canvas.Bind(wx.EVT_LEAVE_WINDOW, self.onLeaveWindow)
        self.canvas.canvas.Bind(wx.EVT_KEY_DOWN, self.onKeyDownEvent)
        self.canvas.canvas.Bind(wx.EVT_KEY_UP, self.onKeyUpEvent)
        self.canvas.canvas.SetWindowStyleFlag(wx.WANTS_CHARS)

        self.canvas.enableHiRes = True
        self.canvas.enableAntiAliasing = True
        #self.canvas.gridPen = wx.Pen(GRID_COLOUR, 1, wx.PENSTYLE_DOT)

        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_NORMAL, wx.WXK_INSERT, frame.INSERTPOINT_ID),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, frame.DELETEPOINT_ID),
            (wx.ACCEL_NORMAL, wx.WXK_BACK, frame.DELETEPOINT_ID),
            (wx.ACCEL_CTRL | wx.ACCEL_ALT, ord('='), frame.EXPANDYIN_ID)
        ])
        self.canvas.SetAcceleratorTable(accel_tbl)

        # float spins
        x_label = wx.StaticText(self, -1, "time = ")
        if title == 'Fan Profile Curve':
            MAX = MAX_FAN_RPM * FAN_PROFILE_YSCALE
            INCREMENT = 10 * FAN_PROFILE_YSCALE
            DIGITS = 0
        else:
            MAX = temperature.convertCelciusToSpecifiedUnit(MAX_VALID_ROAST_TEMPERATURE, self.frame.temperature_unit)
            INCREMENT = 0.1
            DIGITS = 1
        extra = 60 if isLinux and 'gtk3' in wx.PlatformInfo else 0
        self.x_min_floatspin = myFloatSpin(self, -1, min_val=-1.0, max_val=20, increment=1.0, name='x_min',
                                           size=(50 + extra, -1))
        self.x_min_floatspin.SetFormat("%f")
        self.x_min_floatspin.SetDigits(0)
        self.x_min_floatspin.SetLeading(2)
        self.x_min_floatspin.SetSuffix(':')
        self.x_sec_floatspin = myFloatSpin(self, -1, min_val=-0.1, max_val=60, increment=0.1, name='x_sec',
                                           size=(60 + extra, -1))
        self.x_sec_floatspin.SetFormat("%f")
        self.x_sec_floatspin.SetDigits(1)
        self.x_sec_floatspin.SetLeading(2)
        y_label = wx.StaticText(self, -1, yAxis + " = ")
        self.y_floatspin = FS.FloatSpin(self, -1, min_val=0.0, max_val=MAX, increment=INCREMENT, name='y',
                                        size=(80 + extra, -1))
        self.y_floatspin.SetFormat("%f")
        self.y_floatspin.SetDigits(DIGITS)
        if title != 'Fan Profile Curve':
            level_label = wx.StaticText(self, -1, "Recommended level = ")
            self.level_temperature = wx.StaticText(self, -1, "")
            self.level_description = wx.StaticText(self, -1, "")
            self.level_floatspin = myFloatSpinWithChangeValue(self, -1, name='recommended_level', size=(50 + extra, -1))
            self.configControls['recommended_level'] = self.level_floatspin
            self.level_floatspin._spinbutton.Bind(wx.EVT_LEFT_DOWN, self.onLevelFloatSpinClick)
            self.level_floatspin._textctrl.Bind(wx.EVT_CHAR, self.onLevelFloatSpinClick)
            self.configList.append('recommended_level')
            self.level_floatspin.SetFormat("%f")
            self.applyEmulation(frame)
        self.Bind(FS.EVT_FLOATSPIN, self.onFloatSpin)

        # layout the widgets
        if frame.options.getUserOption("phases-panel-position") != "left":
            self.chartSizer.Add(self.canvas, 1, wx.EXPAND)
        if title != 'Fan Profile Curve':
            self.phasesObject = phases.PhasesPanel()
            self.phasesPanel = self.phasesObject.initPanel(self, self.chartSizer)
            self.configControls['expect_colrchange'] = self.phasesObject.getColourChangeControl()
            self.configList.append('expect_colrchange')
            self.configControls['expect_fc'] = self.phasesObject.getFirstCrackControl()
            self.configList.append('expect_fc')
            self.toggleRoR = self.makeCheckBox("ROR", self.onToggleRoR, default=False)
            self.toggleFanSpeed = self.makeCheckBox("Fan", self.onToggleFanSpeed, default=False)
            self.toggleZones = self.makeCheckBox("Zones", self.onToggleZones, default=False)
            self.togglePhases = self.makeCheckBox("Phases", self.onTogglePhases, default=False)
        if frame.options.getUserOption("phases-panel-position") == "left":
            self.chartSizer.Add(self.canvas, 1, wx.EXPAND)
        toggleGrid = self.makeCheckBox("Grid", self.onToggleGrid, default=False)
        toggleLegend = self.makeCheckBox("Legend", self.onToggleLegend, default=False)
        self.checkSizer.Add(x_label, 0, wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 5)
        self.checkSizer.Add(self.x_min_floatspin, 0, wx.RIGHT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 5)
        self.checkSizer.Add(self.x_sec_floatspin, 0, wx.RIGHT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 5)
        self.checkSizer.Add(y_label, 0, wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 5)
        self.checkSizer.Add(self.y_floatspin, 0, wx.RIGHT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 5)
        if title != 'Fan Profile Curve':
            innerCheckSizer.Add(self.toggleRoR, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            innerCheckSizer.Add(self.toggleFanSpeed, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            innerCheckSizer.Add(self.toggleZones, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            innerCheckSizer.Add(self.togglePhases, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        innerCheckSizer.Add(toggleGrid, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        innerCheckSizer.Add(toggleLegend, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.checkSizer.Add(innerCheckSizer, 0, wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 1 if isWindows else 0)
        if title != 'Fan Profile Curve':
            self.checkSizer.Add(level_label, 0, wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 5)
            self.checkSizer.Add(self.level_floatspin, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            self.level_floatspin.SetValue(self.frame.configuration['recommended_level'])
            self.phasesObject.setPhasesFromProfileData()  # will set modified flag
            self.frame.modified(False)
            self.checkSizer.Add(self.level_temperature, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            self.checkSizer.Add(self.level_description, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.mainSizer.Add(self.chartSizer, 1, wx.EXPAND)
        self.mainSizer.Add(self.checkSizer)
        self.SetSizerAndFit(self.mainSizer)
        self.setSpinners()
        self.canvas.SetFocus()

    def applyEmulation(self, frame):
        self.level_floatspin.SetDigits(frame.emulation_mode.level_decimal_places)
        self.level_floatspin.SetIncrement(frame.emulation_mode.level_increment)
        self.level_floatspin.SetRange(frame.emulation_mode.level_min_val - 0.00001,
                                      frame.emulation_mode.level_max_val + 0.00001)

    def resetHistory(self):
        self.history = [HistoryPointsEntry(self.profilePoints, self.selectedIndex, self.selectedType)]
        self.historyIndex = 0
        self.historyCanUndo = False

    def reDraw(self):
        self.canvas.fontSizeLegend = self.frame.legendFontSize
        if self.zoomScale == 1 and not self.expandY:
            xAxis = None
            yAxis = None
        else:
            xAxis = self.zoomXAxis
            yAxis = self.zoomYAxis
        if self.lockAxes:
            xAxis = self.xAxisWhenMouseWentDown
            yAxis = self.yAxisWhenMouseWentDown
        thresholdString = self.frame.page4.configControls["roast_levels"].GetValue()
        if hasattr(self, 'level_floatspin'):
            if not validate_levels(self.frame, thresholdString): return
            levelString = self.level_floatspin.GetValue()
            self.level_temperature.SetLabel(
                str(round(temperatureFromLevel(levelString, thresholdString), 1)) +
                temperature.insertTemperatureUnit('°', self.frame.temperature_unit))
            self.level_description.SetLabel(descriptionFromLevel(levelString))
            if self.frame.configuration['emulation_mode'] == EMULATE_SONOFRESCO:
                self.level_description.Hide()
            else:
                self.level_description.Show()
        else:
            levelString = None
        for i in [1, 2]:
            thisProfile = drawProfile(self,
                                      self.title,
                                      self.yAxis,
                                      self.profilePoints,
                                      self.selectedIndex,
                                      self.selectedType,
                                      self.showRateOfRise,
                                      levelString,
                                      thresholdString,
                                      self.closest_point,
                                      int(round(float(self.frame.configuration["emulation_mode"]))),
                                      self.canvas.enableGrid)
            minX, maxX, minY, maxY = extremaOfAllPoints(self.profilePoints)
            # print 'minX, maxX, minY, maxY', minX, maxX, minY, maxY
            maxXgraphed = ceil(self.pointsAsGraphed[-1][0]) + 30.0
            maxY = ceil(max(maximumY(self.pointsAsGraphed), maxY) / 50.0) * 50.0
            if self.recommended_endpoint is not None:
                endpointX = ceil((self.recommended_endpoint[0] + 60.0) / 240.0) * 240.0
                if endpointX > maxXgraphed:
                    maxX = max(maxXgraphed, maxX)
                else:
                    maxX = max(endpointX, maxX)
            else:
                maxX = max(maxXgraphed, maxX)
            if len(self.rates) > 0:
                minY = min(minimumY(self.gradientsAsGraphedScaled), minY)
            if len(self.rates) > 1:
                minY = min(minimumY(self.secdivsAsGraphedScaled), minY)
            minY = max(minY, temperature.convertCelciusToSpecifiedUnit(DERIVATIVE_ALLOWED_YRANGE[0], self.frame.temperature_unit))
            max_xAxis = (minX, maxX)
            max_yAxis = (minY, maxY) #  None if self.title == 'Fan Profile Curve' else (minY, maxY) #TODO
            self.canvas.Draw(thisProfile,
                             xAxis=xAxis if xAxis is not None else max_xAxis,
                             yAxis=yAxis if yAxis is not None else max_yAxis)
        if self.zoomScale == 1 and not self.expandY:
            self.unzoomedYaxis = (self.canvas.GetYCurrentRange()[0], self.canvas.GetYCurrentRange()[1])
        self.zoomXAxis = (self.canvas.GetXCurrentRange()[0], self.canvas.GetXCurrentRange()[1])  # must be a tuple
        self.zoomYAxis = (self.canvas.GetYCurrentRange()[0], self.canvas.GetYCurrentRange()[1])
        if self.displaySelectedText is not None:
            self.displaySelectedText.Destroy()
            self.displaySelectedText = None
        if self.closest_point is not None or self.closest_legend == 'Recommended_level':
            if self.title == 'Fan Profile Curve':
                yScale = FAN_PROFILE_YSCALE
                yValue = int(round(self.closest_point.y / yScale, -1))
                scale = None
            else:
                yScale = 1
                yValue = round(self.closest_point.y / yScale, 1)
                scale = 'fit'
            if self.closest_legend.startswith("Zone") or self.closest_legend.startswith("Corner"):
                thisLabel = addZoneStartEnd(self, self.closest_legend)
            else:
                displayData = removeScaleFactorFromLegendAndData(self.frame, self.closest_legend, yValue, scale)
                thisLabel = displayData["legend"] + "\n" + str(displayData["value"]) + " at " + toMinSec(
                    int(self.closest_point.x))
                if hasattr(self, 'phasesObject') and displayData["legend"] in ['Profile', 'Recommended level']:
                    thisLabel += self.phasesObject.displayPhaseData(nowTime=self.closest_point.x,
                                                                    nowTemperature=float(displayData["value"]))
            self.displaySelectedText = initialiseDisplaySelectedText(self, thisLabel)

    def disableOrEnableLevelSpinner(self):
        if hasattr(self, 'level_floatspin'):
            if self.frame.fileType == "log":
                self.level_floatspin.Disable()
            else:
                self.level_floatspin.Enable()

    def disableSpinners(self):
        self.x_min_floatspin.Disable()
        self.x_sec_floatspin.Disable()
        self.y_floatspin.Disable()
        self.disableOrEnableLevelSpinner()

    def enableSpinners(self, lockTime=False):
        if lockTime:
            self.x_min_floatspin.Disable()
            self.x_sec_floatspin.Disable()
        else:
            self.x_min_floatspin.Enable()
            self.x_sec_floatspin.Enable()
        self.y_floatspin.Enable()
        self.disableOrEnableLevelSpinner()

    def setTimeSpinners(self, time):
        mins, secs = divmod(time, 60)
        self.x_min_floatspin.SetValue(mins)
        self.x_sec_floatspin.SetValue(secs)

    def setSpinners(self):
        focussed = wx.Window.FindFocus()
        selectedpoint = self.profilePoints[self.selectedIndex]
        if self.selectedType == 'point':
            self.setTimeSpinners(selectedpoint.point.x)
            self.y_floatspin.SetValue(selectedpoint.point.y)
        if self.selectedType == 'leftControl':
            self.setTimeSpinners(selectedpoint.leftControl.x)
            self.y_floatspin.SetValue(selectedpoint.leftControl.y)
        if self.selectedType == 'rightControl':
            self.setTimeSpinners(selectedpoint.rightControl.x)
            self.y_floatspin.SetValue(selectedpoint.rightControl.y)
        if self.frame.fileType == "log" or (
                self.selectedIndex in self.frame.emulation_mode.profile_locked_points
                and self.title == 'Roast Profile Curve'
                and self.selectedType == 'point'
        ):
            self.disableSpinners()
        else:
            self.enableSpinners(self.selectedType == 'point' and (
                    (
                            self.frame.emulation_mode.profile_points_timelock_last
                            and self.selectedIndex == len(self.profilePoints) - 1
                            and self.title == 'Roast Profile Curve'
                    )
                    or self.selectedIndex == 0
            ))
        self.reDraw()
        if focussed is not None: wx.CallAfter(focussed.SetFocus)

    def makeCheckBox(self, label, handler, default=False):
        check = wx.CheckBox(self, label=label)
        self.frame.checkBoxControls[self.title + "_" + label] = check
        check.SetValue(self.frame.options.getUserOptionBoolean(self.title + "_" + label, default=default))
        handler(check)
        check.Bind(wx.EVT_CHECKBOX, handler)
        return check

    def onTogglePhases(self, event):
        if event.IsChecked():
            self.phasesPanel.Show()
            self.chartSizer.Layout()
        else:
            self.phasesPanel.Hide()
            self.chartSizer.Layout()
        self.reDraw()

    def onToggleRoR(self, event):
        self.showRateOfRise = event.IsChecked()
        # print self.displaySelectedText, self.closest_legend[:4]
        if self.displaySelectedText is not None and self.closest_legend[:4] in ["Rate", "Seco"]:
            self.killDisplaySelectedText()
        self.reDraw()

    def onToggleFanSpeed(self, event):
        self.showFanSpeed = event.IsChecked()
        # print self.displaySelectedText, self.closest_legend[:4]
        if self.displaySelectedText is not None and self.closest_legend == "Fan speed":
            self.killDisplaySelectedText()
        self.reDraw()

    def onToggleZones(self, event):
        self.showZones = event.IsChecked()
        # print self.displaySelectedText, self.closest_legend[:4]
        if self.displaySelectedText is not None and self.closest_legend == "Zones":
            self.killDisplaySelectedText()
        self.reDraw()

    def killDisplaySelectedText(self):
        self.displaySelectedText.Destroy()
        self.displaySelectedText = None
        self.closest_point = None
        self.closest_legend = None

    def onToggleGrid(self, event):
        self.canvas.SetEnableGrid(event.IsChecked())
        # if self.closest_point != None and not self.wasCloseEnoughToDrag:
        self.reDraw()

    def onToggleLegend(self, event):
        self.canvas.SetEnableLegend(event.IsChecked())
        if self.closest_point is not None and not self.wasCloseEnoughToDrag:
            self.reDraw()

    def onKeyDownEvent(self, event):
        keycode = event.GetKeyCode()
        if keycode not in ARROW_KEYS:
            event.Skip()
            return
        if self.arrowkeyCurrent != keycode:
            self.arrowkeyCurrent = keycode
            self.arrowkeyWentDownAt = copy.copy(self.profilePoints[self.selectedIndex])
            self.arrowkeyIsAlt = wx.GetKeyState(wx.WXK_ALT)
            self.arrowkeyTimer.Start(200)
            self.arrowkeyRepeatCount = 0

    def onKeyUpEvent(self, event):
        keycode = event.GetKeyCode()
        if keycode not in ARROW_KEYS:
            event.Skip()
            return
        self.arrowkeyTimer.Stop()
        wx.CallAfter(self.arrowKeyFinish)

    def onArrowkeyTimer(self, event):
        if self.arrowkeyCurrent is not None and wx.GetKeyState(self.arrowkeyCurrent):
            self.arrowkeyRepeatCount += 1
            wx.CallAfter(self.arrowKeyUpdate)
        else:
            self.arrowkeyTimer.Stop()
            wx.CallAfter(self.arrowKeyFinish)

    def arrowKeyFinish(self):
        if self.arrowkeyRepeatCount == 0:
            self.arrowkeyRepeatCount = 1
            self.handleArrowKey()
        self.arrowkeyCurrent = None
        self.arrowkeyWentDownAt = None
        self.arrowkeyIsAlt = False
        self.arrowkeyRepeatCount = 0

    def arrowKeyUpdate(self):
        if self.arrowkeyTimer.IsRunning() and self.arrowkeyCurrent is not None and wx.GetKeyState(self.arrowkeyCurrent):
            self.handleArrowKey()
        else:
            return

    def handleArrowKey(self):
        count = self.arrowkeyRepeatCount
        if count > 1:
            if count <= 5:
                return
            count -= 5
        if self.title == 'Fan Profile Curve' and (
                self.arrowkeyCurrent == wx.WXK_UP or self.arrowkeyCurrent == wx.WXK_DOWN):
            multiplier = 1
        else:
            multiplier = 0.1
        if self.arrowkeyIsAlt:
            multiplier *= 10
        if self.arrowkeyCurrent == wx.WXK_LEFT:
            self.deltaX = -count * multiplier
            self.deltaY = 0
        elif self.arrowkeyCurrent == wx.WXK_RIGHT:
            self.deltaX = count * multiplier
            self.deltaY = 0
        elif self.arrowkeyCurrent == wx.WXK_DOWN:
            self.deltaY = -count * multiplier
            self.deltaX = 0
        elif self.arrowkeyCurrent == wx.WXK_UP:
            self.deltaY = count * multiplier
            self.deltaX = 0
        else:
            return
        deltaX = self.deltaX
        deltaY = self.deltaY
        if self.frame.fileType == "log" or (deltaX == 0 and deltaY == 0) or self.arrowkeyWentDownAt is None:
            return
        destroySelectedText(self)
        self.frame.modified(True)
        self.frame.captureHistory(self, 'arrow')
        if deltaX != 0 and self.x_min_floatspin.IsEnabled():
            if self.selectedType == 'point':
                self.profilePoints[self.selectedIndex].point.x = self.arrowkeyWentDownAt.point.x + deltaX
                if self.profilePoints[self.selectedIndex].leftControl.toTuple() != (0.0, 0.0):
                    self.profilePoints[
                        self.selectedIndex].leftControl.x = self.arrowkeyWentDownAt.leftControl.x + deltaX
                if self.profilePoints[self.selectedIndex].rightControl.toTuple() != (0.0, 0.0):
                    self.profilePoints[
                        self.selectedIndex].rightControl.x = self.arrowkeyWentDownAt.rightControl.x + deltaX
            if self.selectedType == 'leftControl':
                self.profilePoints[self.selectedIndex].leftControl.x = self.arrowkeyWentDownAt.leftControl.x + deltaX
            if self.selectedType == 'rightControl':
                self.profilePoints[self.selectedIndex].rightControl.x = self.arrowkeyWentDownAt.rightControl.x + deltaX
        if deltaY != 0 and self.y_floatspin.IsEnabled():
            if self.selectedType == 'point':
                self.profilePoints[self.selectedIndex].point.y = self.arrowkeyWentDownAt.point.y + deltaY
                if self.profilePoints[self.selectedIndex].leftControl.toTuple() != (0.0, 0.0):
                    self.profilePoints[
                        self.selectedIndex].leftControl.y = self.arrowkeyWentDownAt.leftControl.y + deltaY
                if self.profilePoints[self.selectedIndex].rightControl.toTuple() != (0.0, 0.0):
                    self.profilePoints[
                        self.selectedIndex].rightControl.y = self.arrowkeyWentDownAt.rightControl.y + deltaY
            if self.selectedType == 'leftControl':
                self.profilePoints[self.selectedIndex].leftControl.y = self.arrowkeyWentDownAt.leftControl.y + deltaY
            if self.selectedType == 'rightControl':
                self.profilePoints[self.selectedIndex].rightControl.y = self.arrowkeyWentDownAt.rightControl.y + deltaY
        self.killDuplicates()
        self.balance()
        self.setSpinners()

    def killDuplicates(self):
        """
        remove the second point of any pair of points that are too close together
        """
        PROXIMITY_THRESHOLD = 5
        for i in range(len(self.profilePoints) - 1):
            if i < len(self.profilePoints) - 1 and distanceBetweenTwoPoints(self.profilePoints[i].point,
                                                                            self.profilePoints[
                                                                                i + 1].point) < PROXIMITY_THRESHOLD:
                self.profilePoints.pop(i + 1)
                if self.selectedIndex > i:
                    self.selectedIndex -= 1
                if self.selectedIndex >= len(self.profilePoints) - 1:
                    self.selectedIndex = len(self.profilePoints) - 1
                calculateControlPoints(self.profilePoints, CONTROL_POINT_RATIO)
                self.frame.onSmoothPoint(None, False)
                self.setSpinners()

    def onLevelFloatSpinClick(self, event):
        if self.captureFocusEvents:
            self.frame.captureHistory(self, 'capture', calledFromTextChange=True)
            self.frame.focus(self, self.level_floatspin)
        event.Skip()

    def onFloatSpin(self, event):
        floatspin = event.GetEventObject()
        floatspinName = floatspin.GetName()
        value = floatspin.GetValue()
        mins = self.x_min_floatspin.GetValue()
        secs = self.x_sec_floatspin.GetValue()
        if secs > 59.9:
            if mins < 20:
                mins += 1
                self.x_min_floatspin.SetValue(mins)
                secs = 0
                self.x_sec_floatspin.SetValue(secs)
            else:
                secs = 59.9
                self.x_sec_floatspin.SetValue(secs)
        if secs < 0:
            if mins > -1:
                mins -= 1
                self.x_min_floatspin.SetValue(mins)
                secs = 59.9
                self.x_sec_floatspin.SetValue(secs)
            else:
                secs = 0
                self.x_sec_floatspin.SetValue(secs)
        time = mins * 60 + secs
        self.frame.modified(True)
        if floatspinName == 'recommended_level':
            self.frame.captureHistory(self, 'capture', calledFromTextChange=True)
            self.frame.txtChange(self, self.level_floatspin,
                                 applyLinuxFix=True)  # known issue for Linux insertion point in EVT_TEXT handler
            self.captureFocusEvents = False
            self.canvas.SetFocus()
            self.captureFocusEvents = True
            destroySelectedText(self)
            self.reDraw()
        else:
            destroySelectedText(self)
            self.frame.captureHistory(self, 'spinner')
            if floatspinName[0] == 'x':
                value = time
                if self.selectedType == 'point':
                    delta = value - self.profilePoints[self.selectedIndex].point.x
                    self.profilePoints[self.selectedIndex].point.x += delta
                    if self.profilePoints[self.selectedIndex].leftControl.toTuple() != (0.0, 0.0):
                        self.profilePoints[self.selectedIndex].leftControl.x += delta
                    if self.profilePoints[self.selectedIndex].rightControl.toTuple() != (0.0, 0.0):
                        self.profilePoints[self.selectedIndex].rightControl.x += delta
                if self.selectedType == 'leftControl':
                    self.profilePoints[self.selectedIndex].leftControl.x = value
                if self.selectedType == 'rightControl':
                    self.profilePoints[self.selectedIndex].rightControl.x = value
            if floatspinName == 'y':
                if self.selectedType == 'point':
                    delta = value - self.profilePoints[self.selectedIndex].point.y
                    self.profilePoints[self.selectedIndex].point.y += delta
                    if self.profilePoints[self.selectedIndex].leftControl.toTuple() != (0.0, 0.0):
                        self.profilePoints[self.selectedIndex].leftControl.y += delta
                    if self.profilePoints[self.selectedIndex].rightControl.toTuple() != (0.0, 0.0):
                        self.profilePoints[self.selectedIndex].rightControl.y += delta
                if self.selectedType == 'leftControl':
                    self.profilePoints[self.selectedIndex].leftControl.y = value
                if self.selectedType == 'rightControl':
                    self.profilePoints[self.selectedIndex].rightControl.y = value
            self.killDuplicates()
            self.balance()

    def swapContolPoints(self):
        if self.selectedType == 'leftControl':
            self.selectedType = 'rightControl'
        else:
            if self.selectedType == 'rightControl':
                self.selectedType = 'leftControl'
        a = self.profilePoints[self.selectedIndex].rightControl
        self.profilePoints[self.selectedIndex].rightControl = self.profilePoints[self.selectedIndex].leftControl
        self.profilePoints[self.selectedIndex].leftControl = a

    def balance(self):
        if self.selectedType == 'leftControl':
            if self.profilePoints[self.selectedIndex].rightControl.toTuple() != (0.0, 0.0):
                rightControlYDelta = abs(self.profilePoints[self.selectedIndex].point.y - self.profilePoints[
                    self.selectedIndex].rightControl.y)
                if rightControlYDelta > 0.0:
                    ratio = abs(self.profilePoints[self.selectedIndex].point.y - self.profilePoints[
                        self.selectedIndex].leftControl.y) / rightControlYDelta
                else:
                    ratio = 1.0
                if ratio > 1.0:
                    threshold = AVOID_INFINITE_GRADIENT_THRESHOLD * ratio
                else:
                    threshold = AVOID_INFINITE_GRADIENT_THRESHOLD
                if abs(self.profilePoints[self.selectedIndex].point.x - self.profilePoints[
                    self.selectedIndex].leftControl.x) < threshold:
                    self.profilePoints[self.selectedIndex].leftControl.x = self.profilePoints[
                                                                               self.selectedIndex].point.x - threshold
                b = balanceControlPoint(self.profilePoints[self.selectedIndex], False)
                self.profilePoints[self.selectedIndex].setRightControl(b.x, b.y)
                if self.profilePoints[self.selectedIndex].point.x < self.profilePoints[
                    self.selectedIndex].leftControl.x:
                    self.swapContolPoints()
            else:
                if self.profilePoints[self.selectedIndex].leftControl.toTuple() != (0.0, 0.0):
                    # we are dealing with the end point, which has a left control point, but no right control point
                    if self.profilePoints[self.selectedIndex].point.x - LAST_CONTROL_POINT_THRESHOLD < \
                            self.profilePoints[self.selectedIndex].leftControl.x:
                        self.profilePoints[self.selectedIndex].leftControl.x = self.profilePoints[
                                                                                   self.selectedIndex].point.x - LAST_CONTROL_POINT_THRESHOLD
        else:
            if self.selectedType == 'rightControl':
                if self.profilePoints[self.selectedIndex].leftControl.toTuple() != (0.0, 0.0):
                    leftControlYDelta = abs(self.profilePoints[self.selectedIndex].point.y - self.profilePoints[
                        self.selectedIndex].leftControl.y)
                    if leftControlYDelta > 0.0:
                        ratio = abs(self.profilePoints[self.selectedIndex].point.y - self.profilePoints[
                            self.selectedIndex].rightControl.y) / leftControlYDelta
                    else:
                        ratio = 1.0
                    if ratio > 1.0:
                        threshold = AVOID_INFINITE_GRADIENT_THRESHOLD * ratio
                    else:
                        threshold = AVOID_INFINITE_GRADIENT_THRESHOLD
                    if abs(self.profilePoints[self.selectedIndex].point.x - self.profilePoints[
                        self.selectedIndex].rightControl.x) < threshold:
                        self.profilePoints[self.selectedIndex].rightControl.x = self.profilePoints[
                                                                                    self.selectedIndex].point.x + threshold
                    b = balanceControlPoint(self.profilePoints[self.selectedIndex], True)
                    self.profilePoints[self.selectedIndex].setLeftControl(b.x, b.y)
                    if self.profilePoints[self.selectedIndex].point.x > self.profilePoints[
                        self.selectedIndex].rightControl.x:
                        self.swapContolPoints()
                else:
                    if self.profilePoints[self.selectedIndex].rightControl.toTuple() != (0.0, 0.0):
                        # we are dealing with the first point, which has a right control point, but no left control point
                        if self.profilePoints[self.selectedIndex].point.x + AVOID_INFINITE_GRADIENT_THRESHOLD > \
                                self.profilePoints[self.selectedIndex].rightControl.x:
                            self.profilePoints[self.selectedIndex].rightControl.x = self.profilePoints[
                                                                                        self.selectedIndex].point.x + AVOID_INFINITE_GRADIENT_THRESHOLD
        self.reDraw()

    def onClick(self, event):
        self.canvas.SetFocus()
        PROXIMITY_THRESHOLD = 5
        # GetClosestPoints returns list with [curveNumber, legend, index of closest point, pointXY, scaledXY, distance]
        self.mouseWentDownAt = self.canvas.PositionScreenToUser(event.GetPosition())
        self.xAxisWhenMouseWentDown = (self.canvas.GetXCurrentRange()[0], self.canvas.GetXCurrentRange()[1])
        self.yAxisWhenMouseWentDown = (self.canvas.GetYCurrentRange()[0], self.canvas.GetYCurrentRange()[1])
        self.lockAxes = True
        data = self.canvas.GetClosestPoints(self.mouseWentDownAt)
        self.closest_point = None
        self.closest_distance = None
        self.closest_legend = None
        self.showSelectionCross = True
        distanceControl = float('inf')
        for curve in data:
            legend = curve[1]
            distance = curve[5]
            closest = Point(curve[3][0], curve[3][1])
            # print legend, distance, closest.toTuple()
            if legend == 'Points':
                closestPoint = closest
                distancePoint = distance
            if legend == 'Controls[hidden]':
                closestControl = closest
                distanceControl = distance
            if '[hidden]' not in legend and legend not in ['Points']:
                thisdistance = distanceBetweenTwoPoints(pointFromTuple(self.mouseWentDownAt), closest)
                if legend[:4] == 'Reco':
                    thisdistance *= 0.3333  # give priority to recommended_level
                if self.closest_distance is None or thisdistance < self.closest_distance:
                    self.closest_distance = thisdistance
                    self.closest_point = closest
                    self.closest_legend = replaceSpaceWithUnderscore(legend)

        self.mouseIsAt = self.mouseWentDownAt
        if distancePoint > distanceControl:
            closest = closestControl
        else:
            closest = closestPoint
        self.pointStartedAt = closest
        self.isCloseEnoughToDrag = distanceBetweenTwoPoints(pointFromTuple(self.mouseWentDownAt),
                                                            closest) <= PROXIMITY_THRESHOLD
        self.wasCloseEnoughToDrag = self.isCloseEnoughToDrag
        if self.isCloseEnoughToDrag:
            if distancePoint > distanceControl:
                thisSelectedType = 'control'
                closest = closestControl
            else:
                thisSelectedType = 'point'
                closest = closestPoint
            for i in range(len(self.profilePoints)):
                testpoint = self.profilePoints[i]
                if thisSelectedType == 'point':
                    if testpoint.point.x == closestPoint.x and testpoint.point.y == closestPoint.y:
                        # print "selected", point.toTuple()

                        # captureHistory calls ToolBar.Realize() which in turn triggers
                        # a resize event which repositions the displaySelected Text control
                        # before it has been updated, so get rid of it now...
                        if self.displaySelectedText is not None:
                            self.displaySelectedText.Destroy()
                            self.displaySelectedText = None
                        self.frame.captureHistory(self, 'click')
                        self.selectedIndex = i
                        self.selectedType = 'point'
                        self.showSelectionCross = False
                        # no need to call setSpinners() because onLeftUp will do it for us
                else:
                    if testpoint.leftControl.x == closestControl.x and testpoint.leftControl.y == closestControl.y:
                        # print "selected", point.leftControlToTuple()
                        self.frame.captureHistory(self, 'click')
                        self.selectedIndex = i
                        self.selectedType = 'leftControl'
                        self.closest_point = None
                        self.closest_distance = None
                        self.closest_legend = None
                        self.setSpinners()
                    if testpoint.rightControl.x == closestControl.x and testpoint.rightControl.y == closestControl.y:
                        # print "selected", point.rightControlToTuple()
                        self.frame.captureHistory(self, 'click')
                        self.selectedIndex = i
                        self.selectedType = 'rightControl'
                        self.closest_point = None
                        self.closest_distance = None
                        self.closest_legend = None
                        self.setSpinners()
        else:
            if self.closest_distance > PROXIMITY_THRESHOLD or self.isCloseEnoughToDrag:
                # check if we are on one of the level lines
                if (
                        self.recommended_endpoint is not None and
                        self.canvas.enableGrid and abs(
                    self.mouseIsAt[0] - self.recommended_endpoint[0]) < PROXIMITY_THRESHOLD
                ):
                    self.closest_point = Point(self.recommended_endpoint[0], self.recommended_endpoint[1])
                    self.closest_distance = 0
                    self.closest_legend = 'Recommended_level'
                else:
                    self.closest_point = None
                    self.closest_distance = None
                    self.closest_legend = None

            # print self.closest_point, self.closest_distance, self.closest_legend
            self.reDraw()

    def onLeftUp(self, event):
        self.lockAxes = False
        self.updateDuringDrag(event)
        self.killDuplicates()
        self.isCloseEnoughToDrag = False

    def updateDuringDrag(self, event):
        if self.frame.fileType == "log" or (
                self.selectedIndex in self.frame.emulation_mode.profile_locked_points and self.title == 'Roast Profile Curve'):
            return
        DRAG_MINIMUM_MOVE_THRESHOLD = 3
        if self.isCloseEnoughToDrag:
            self.mouseIsAt = self.canvas.PositionScreenToUser(event.GetPosition())
            if distanceBetweenTwoPoints(pointFromTuple(self.mouseWentDownAt),
                                        pointFromTuple(self.mouseIsAt)) < DRAG_MINIMUM_MOVE_THRESHOLD:
                self.mouseIsAt = self.pointStartedAt.toTuple()
            else:
                self.frame.modified(True)
            if self.selectedType == 'point':
                if (
                        self.frame.emulation_mode.profile_points_timelock_last
                        and self.selectedIndex == len(self.profilePoints) - 1
                        and self.title == 'Roast Profile Curve'
                ) or self.selectedIndex == 0:
                    self.mouseIsAt = (self.profilePoints[self.selectedIndex].point.x, self.mouseIsAt[1])
                deltaX = self.mouseIsAt[0] - self.profilePoints[self.selectedIndex].point.x
                deltaY = self.mouseIsAt[1] - self.profilePoints[self.selectedIndex].point.y
                self.profilePoints[self.selectedIndex].setXY(self.mouseIsAt[0], self.mouseIsAt[1])
                if self.profilePoints[self.selectedIndex].leftControl.toTuple() != (0.0, 0.0):
                    self.profilePoints[self.selectedIndex].leftControl.x += deltaX
                    self.profilePoints[self.selectedIndex].leftControl.y += deltaY
                if self.profilePoints[self.selectedIndex].rightControl.toTuple() != (0.0, 0.0):
                    self.profilePoints[self.selectedIndex].rightControl.x += deltaX
                    self.profilePoints[self.selectedIndex].rightControl.y += deltaY
            if self.selectedType == 'leftControl':
                self.profilePoints[self.selectedIndex].setLeftControl(self.mouseIsAt[0], self.mouseIsAt[1])
                self.balance()
            else:
                if self.selectedType == 'rightControl':
                    self.profilePoints[self.selectedIndex].setRightControl(self.mouseIsAt[0], self.mouseIsAt[1])
                    self.balance()
            self.setSpinners()

    def onMotion(self, event):
        if self.isCloseEnoughToDrag:
            self.updateDuringDrag(event)

    def onLeaveWindow(self, event):
        pass


########################################################################
class noClass():
    pass


w = WndProcHookMixinCtypes.WndProcHookMixin if isWindows else noClass


class MyGraph(wx.Frame, w, BaseDataObject):
    def __init__(self, app):
        self.app = app
        if isWindows:
            WndProcHookMixinCtypes.WndProcHookMixin.__init__(self)

        self.options = userOptions.UserOptions(self)
        maxi = self.options.getUserOptionBoolean("window-maximized", default=False)
        style=wx.DEFAULT_FRAME_STYLE
        if maxi:
            style |= wx.MAXIMIZE
        pos, size = userOptions.getPosSizeFromOptions(self.options)
        wx.Frame.__init__(self, None, wx.ID_ANY, PROGRAM_NAME, pos,
                          size=size, style=style)
        if not DEBUG_MACEVENTS: sys.excepthook = MyExceptionHook

        self.programPath = utilities.getProgramPath()

        if isWindows or isLinux:
            icon = wx.Icon()
            icon.CopyFromBitmap(wx.Bitmap(self.programPath + r"favicon.ico", wx.BITMAP_TYPE_ANY))
            self.SetIcon(icon)

        
        self.lineWidth = int(self.options.getUserOption("linewidth"))
        self.legendFontSize = int(self.options.getUserOption("legend_font_size"))

        self.markerSize = 1
        # Call userOptions.restoreSizeFromOptions only after the window has Layout
        self.fileTimeStamp = None

        tb = wx.ToolBar(self, -1)
        self.ToolBar = tb
        menuImages = {
            "new": wx.Bitmap(self.programPath + r"toolbar/new-file.png", wx.BITMAP_TYPE_ANY),
            "load": wx.Bitmap(self.programPath + r"toolbar/open-file.png", wx.BITMAP_TYPE_ANY),
            "save": wx.Bitmap(self.programPath + r"toolbar/disk.png", wx.BITMAP_TYPE_ANY),
            "pdf_icon": wx.Bitmap(self.programPath + r"toolbar/pdf_icon.png", wx.BITMAP_TYPE_ANY),
            "undo": wx.Bitmap(self.programPath + r"toolbar/edit-undo.png", wx.BITMAP_TYPE_ANY),
            "redo": wx.Bitmap(self.programPath + r"toolbar/edit-redo.png", wx.BITMAP_TYPE_ANY),
            "smooth": wx.Bitmap(self.programPath + r"toolbar/smooth.png", wx.BITMAP_TYPE_ANY),
            "zoomreset": wx.Bitmap(self.programPath + r"toolbar/zoom-fit.png", wx.BITMAP_TYPE_ANY),
            "zoomin": wx.Bitmap(self.programPath + r"toolbar/zoom-in.png", wx.BITMAP_TYPE_ANY),
            "zoomout": wx.Bitmap(self.programPath + r"toolbar/zoom-out.png", wx.BITMAP_TYPE_ANY),
            "camera": wx.Bitmap(self.programPath + r"toolbar/camera.png", wx.BITMAP_TYPE_ANY),
            "viewmemstick": wx.Bitmap(self.programPath + r"toolbar/memstick.png", wx.BITMAP_TYPE_ANY),
            "viewmemstick_disabled": wx.Bitmap(self.programPath + r"toolbar/memstick-disabled.png", wx.BITMAP_TYPE_ANY)
        }
        if isWindows:
            toolImages = menuImages
        else:
            toolImages = {
                "new": wx.Bitmap(self.programPath + r"toolbar/new-file24x24.png", wx.BITMAP_TYPE_ANY),
                "load": wx.Bitmap(self.programPath + r"toolbar/open-file24x24.png", wx.BITMAP_TYPE_ANY),
                "save": wx.Bitmap(self.programPath + r"toolbar/disk24x24.png", wx.BITMAP_TYPE_ANY),
                "pdf_icon": wx.Bitmap(self.programPath + r"toolbar/pdf_icon24x24.png", wx.BITMAP_TYPE_ANY),
                "undo": wx.Bitmap(self.programPath + r"toolbar/edit-undo24x24.png", wx.BITMAP_TYPE_ANY),
                "redo": wx.Bitmap(self.programPath + r"toolbar/edit-redo24x24.png", wx.BITMAP_TYPE_ANY),
                "smooth": wx.Bitmap(self.programPath + r"toolbar/smooth24x24.png", wx.BITMAP_TYPE_ANY),
                "zoomreset": wx.Bitmap(self.programPath + r"toolbar/zoom-fit24x24.png", wx.BITMAP_TYPE_ANY),
                "zoomin": wx.Bitmap(self.programPath + r"toolbar/zoom-in24x24.png", wx.BITMAP_TYPE_ANY),
                "zoomout": wx.Bitmap(self.programPath + r"toolbar/zoom-out24x24.png", wx.BITMAP_TYPE_ANY),
                "camera": wx.Bitmap(self.programPath + r"toolbar/camera24x24.png", wx.BITMAP_TYPE_ANY),
                "viewmemstick": wx.Bitmap(self.programPath + r"toolbar/memstick24x24.png", wx.BITMAP_TYPE_ANY),
                "viewmemstick_disabled": wx.Bitmap(self.programPath + r"toolbar/memstick-disabled24x24.png",
                                                   wx.BITMAP_TYPE_ANY)
            }
        # Tools carry their own IDs, that allows us to know we are dealing with a tool using hasattr(tool, 'id').
        self.NEW_TOOL_ID = wx.NewId()
        self.LOAD_TOOL_ID = wx.NewId()
        self.SAVE_FILE_TOOL_ID = wx.NewId()
        self.UNDO_TOOL_ID = wx.NewId()
        self.REDO_TOOL_ID = wx.NewId()
        self.SMOOTH_TOOL_ID = wx.NewId()
        self.ZOOMRESET_TOOL_ID = wx.NewId()
        self.ZOOMIN_TOOL_ID = wx.NewId()
        self.ZOOMOUT_TOOL_ID = wx.NewId()
        self.VIEWMEMSTICK_TOOL_ID = wx.NewId()
        newtool = tb.AddTool(self.NEW_TOOL_ID, '', toolImages["new"], shortHelp='New')
        newtool.id = self.NEW_TOOL_ID
        loadtool = tb.AddTool(self.LOAD_TOOL_ID, '', toolImages["load"], shortHelp='Open')
        loadtool.id = self.LOAD_TOOL_ID
        self.savetool = tb.AddTool(self.SAVE_FILE_TOOL_ID, '', toolImages["save"], shortHelp='Save')
        self.savetool.id = self.SAVE_FILE_TOOL_ID
        tb.AddSeparator()
        self.undotool = tb.AddTool(self.UNDO_TOOL_ID, '', toolImages["undo"], shortHelp='Undo')
        self.undotool.id = self.UNDO_TOOL_ID
        self.redotool = tb.AddTool(self.REDO_TOOL_ID, '', toolImages["redo"], shortHelp='Redo')
        self.redotool.id = self.REDO_TOOL_ID
        self.smoothtool = tb.AddTool(self.SMOOTH_TOOL_ID, '', toolImages["smooth"], shortHelp='Smooth point')
        self.smoothtool.id = self.SMOOTH_TOOL_ID
        self.zoomresettool = tb.AddTool(self.ZOOMRESET_TOOL_ID, '', toolImages["zoomreset"], shortHelp='Zoom all')
        self.zoomresettool.id = self.ZOOMRESET_TOOL_ID
        self.zoomintool = tb.AddTool(self.ZOOMIN_TOOL_ID, '', toolImages["zoomin"], shortHelp='Zoom in')
        self.zoomintool.id = self.ZOOMIN_TOOL_ID
        self.zoomouttool = tb.AddTool(self.ZOOMOUT_TOOL_ID, '', toolImages["zoomout"], shortHelp='Zoom out')
        self.zoomouttool.id = self.ZOOMOUT_TOOL_ID
        tb.AddSeparator()
        self.viewmemsticktool = tb.AddTool(self.VIEWMEMSTICK_TOOL_ID, '', toolImages["viewmemstick"],
                                           toolImages["viewmemstick_disabled"], shortHelp='View memory stick')
        self.viewmemsticktool.id = self.VIEWMEMSTICK_TOOL_ID
        tb.Realize()

        menubar = wx.MenuBar()
        self.fileMenu = wx.Menu()
        LOAD_FILE_ID = wx.NewId()
        self.RECENT_FILE_ID = wx.NewId()
        NEW_FILE_ID = wx.NewId()
        EXTRACT_PROFILE_ID = wx.NewId()
        SAVE_FILE_ID = wx.NewId()
        SAVE_AS_FILE_ID = wx.NewId()
        FILE_PROPERTIES_ID = wx.NewId()
        IMPORT_SONOFRESCO_ID = wx.NewId()
        EXPORT_SONOFRESCO_ID = wx.NewId()
        IMPORT_ARTISAN_ID = wx.NewId()
        IMPORT_CROPSTER_ID = wx.NewId()
        EXPORT_ARTISAN_ID = wx.NewId()
        IMPORT_IKAWA_ID = wx.NewId()
        EXPORT_PDF_ID = wx.NewId()
        NEW_APP_WINDOW_ID = wx.NewId()
        REDO_ID = wx.NewId()
        UNDO_ID = wx.NewId()
        self.INSERTPOINT_ID = wx.NewId()
        self.DELETEPOINT_ID = wx.NewId()
        SMOOTHPOINT_ID = wx.NewId()
        SMOOTHALL_ID = wx.NewId()
        CALCULATE_ID = wx.NewId()
        TRANSFORM_ID = wx.NewId()
        AREAUNDERCURVE_ID = wx.NewId()
        COMPARE_ID = wx.NewId()
        COMPAREDEFAULT_ID = wx.NewId()
        CLEAR_COMPARE_ID = wx.NewId()
        self.MERGE_ID = wx.NewId()
        EXPLORE_BACKUPS_ID = wx.NewId()
        self.VIEWSOURCE_ID = wx.NewId()
        CAPTUREIMAGE_ID = wx.NewId()
        ZOOMIN_ID = wx.NewId()
        ZOOMOUT_ID = wx.NewId()
        self.EXPANDYIN_ID = wx.NewId()
        EXPANDYOUT_ID = wx.NewId()
        ZOOMRESET_ID = wx.NewId()
        VIEWMEMSTICK_ID = wx.NewId()
        DIFFICULTYBASIC_ID = wx.NewId()
        DIFFICULTYADVANCED_ID = wx.NewId()
        DIFFICULTYEXPERT_ID = wx.NewId()
        DIFFICULTYENGINEER_ID = wx.NewId()
        EDITGENERALOPTIONS_ID = wx.NewId()
        EDITCOMPAREOPTIONS_ID = wx.NewId()
        DOCUMENTATION_ID = wx.NewId()
        COMMUNITY_ID = wx.NewId()
        SUPPORT_ID = wx.NewId()
        TIPSASHELP_ID = wx.NewId()

        newitem = wx.MenuItem(self.fileMenu, NEW_FILE_ID, '&New\tCtrl+N', 'New profile')
        newitem.SetBitmap(menuImages["new"])
        self.fileMenu.Append(newitem)
        loaditem = wx.MenuItem(self.fileMenu, LOAD_FILE_ID, '&Open ...\tCtrl+O', 'Open a file')
        loaditem.SetBitmap(menuImages["load"])
        self.fileMenu.Append(loaditem)

        self.recentFileMenu = wx.Menu()
        self.fileMenu.Append(self.RECENT_FILE_ID, 'Recent &files', self.recentFileMenu)
        self.fileMenu.Enable(self.RECENT_FILE_ID, False)

        self.saveitem = wx.MenuItem(self.fileMenu, SAVE_FILE_ID, '&Save\tCtrl+S', 'Save file')
        self.saveitem.SetBitmap(menuImages["save"])
        self.fileMenu.Append(self.saveitem)
        saveAsitem = self.fileMenu.Append(SAVE_AS_FILE_ID, 'Save &as ...\tCtrl+Shift+S', 'Save as file')
        filePropertiesitem = self.fileMenu.Append(FILE_PROPERTIES_ID, '&Properties ...', 'File properties')
        self.fileMenu.Append(wx.MenuItem(self.fileMenu, wx.ID_SEPARATOR))
        self.extractitem = self.fileMenu.Append(EXTRACT_PROFILE_ID, 'Ext&ract profile from log\tCtrl+R',
                                                'Extract profile from log')

        importMenu = wx.Menu()
        exportMenu = wx.Menu()
        self.importartisanitem = importMenu.Append(IMPORT_ARTISAN_ID, '&Artisan ...', 'Import Artisan file')
        self.importcropsteritem = importMenu.Append(IMPORT_CROPSTER_ID, '&Cropster ...', 'Import Cropster file')
        self.importikawaitem = importMenu.Append(IMPORT_IKAWA_ID, '&Ikawa ...', 'Import Ikawa file')
        self.importsonofrescoitem = importMenu.Append(IMPORT_SONOFRESCO_ID, '&Sonofresco ...',
                                                      'Import Sonofresco profile')
        self.exportartisanitem = exportMenu.Append(EXPORT_ARTISAN_ID, '&Artisan ...', 'Export Artisan file')
        self.exportsonofrescoitem = exportMenu.Append(EXPORT_SONOFRESCO_ID, '&Sonofresco ...',
                                                      'Export Sonofresco profile')
        self.exportpdfitem = wx.MenuItem(exportMenu, EXPORT_PDF_ID, '&PDF ...\tCtrl-P', 'Export PDF document')
        self.exportpdfitem.SetBitmap(menuImages["pdf_icon"])
        exportMenu.Append(self.exportpdfitem)
        self.fileMenu.Append(wx.NewId(), '&Import', importMenu)
        self.fileMenu.Append(wx.NewId(), '&Export', exportMenu)

        self.fileMenu.Append(wx.MenuItem(self.fileMenu, wx.ID_SEPARATOR))
        self.newappwindowitem = self.fileMenu.Append(NEW_APP_WINDOW_ID, 'New app &window\tCtrl+W', 'New app window')

        self.fileMenu.Append(wx.MenuItem(self.fileMenu, wx.ID_SEPARATOR))
        quititem = self.fileMenu.Append(wx.ID_EXIT, '&Quit\tCtrl+Q', 'Quit application')
        menubar.Append(self.fileMenu, '&File')

        editMenu = wx.Menu()
        self.undoItem = wx.MenuItem(editMenu, UNDO_ID, '&Undo\tCtrl+Z')
        self.undoItem.SetBitmap(menuImages["undo"])
        editMenu.Append(self.undoItem)
        self.redoItem = wx.MenuItem(editMenu, REDO_ID, '&Redo\tCtrl+Y')
        self.redoItem.SetBitmap(menuImages["redo"])
        editMenu.Append(self.redoItem)
        menubar.Append(editMenu, '&Edit')

        drawMenu = wx.Menu()
        if isMac:
            delchar = 'back'
            inschar = 'Ctrl+I'
        else:
            delchar = 'Del'
            inschar = 'Ins'
        insertPointItem = drawMenu.Append(self.INSERTPOINT_ID, '&Insert point\t' + inschar, 'Insert point to the right')
        deletePointItem = drawMenu.Append(self.DELETEPOINT_ID, '&Delete point\t' + delchar, 'Delete selected point')
        drawMenu.Append(wx.MenuItem(drawMenu, wx.ID_SEPARATOR))
        smoothPointItem = wx.MenuItem(drawMenu, SMOOTHPOINT_ID, '&Smooth point\tCtrl+/', 'Smooth selected point')
        smoothPointItem.SetBitmap(wx.Bitmap(self.programPath + r"toolbar/smooth.png", wx.BITMAP_TYPE_ANY))
        drawMenu.Append(smoothPointItem)
        smoothAllItem = drawMenu.Append(SMOOTHALL_ID, 'Smooth &all\tAlt+Ctrl+/', 'Smooth all points')
        menubar.Append(drawMenu, '&Draw')

        viewMenu = wx.Menu()
        zoomInItem = wx.MenuItem(viewMenu, ZOOMIN_ID, 'Zoom &in\tCtrl++')
        zoomInItem.SetBitmap(menuImages["zoomin"])
        viewMenu.Append(zoomInItem)
        zoomOutItem = wx.MenuItem(viewMenu, ZOOMOUT_ID, 'Zoom &out\tCtrl+-')
        zoomOutItem.SetBitmap(menuImages["zoomout"])
        viewMenu.Append(zoomOutItem)
        expandYInItem = viewMenu.Append(self.EXPANDYIN_ID, 'E&xpand Y in\tAlt+Ctrl++')
        expandYOutItem = viewMenu.Append(EXPANDYOUT_ID, 'Expand Y ou&t\tAlt+Ctrl+-')
        zoomResetItem = wx.MenuItem(viewMenu, ZOOMRESET_ID, 'Zoom a&ll\tCtrl+L')
        zoomResetItem.SetBitmap(menuImages["zoomreset"])
        viewMenu.Append(zoomResetItem)
        menubar.Append(viewMenu, '&View')

        toolsMenu = wx.Menu()
        self.viewMemstickItem = wx.MenuItem(toolsMenu, VIEWMEMSTICK_ID, 'View &memory stick ...\tCtrl+M')
        self.viewMemstickItem.SetBitmap(menuImages["viewmemstick"])
        toolsMenu.Append(self.viewMemstickItem)
        toolsMenu.Append(wx.MenuItem(toolsMenu, wx.ID_SEPARATOR))
        self.compareDefaultItem = toolsMenu.Append(COMPAREDEFAULT_ID, '&Compare default', 'Compare default',
                                                   kind=wx.ITEM_CHECK)
        self.compareItem = toolsMenu.Append(COMPARE_ID, 'Compare &files...\tCtrl+F',
                                            'Compare files')  # , kind=wx.ITEM_CHECK)
        self.clearCompareItem = toolsMenu.Append(CLEAR_COMPARE_ID, 'Clea&r compare', 'Clear compare')
        toolsMenu.Append(wx.MenuItem(toolsMenu, wx.ID_SEPARATOR))
        self.transformItem = toolsMenu.Append(TRANSFORM_ID, '&Transform profile ...\tCtrl+T', 'Transform profile')
        self.mergeItem = toolsMenu.Append(self.MERGE_ID, 'M&erge profile ...\tCtrl+E', 'Merge profile')
        toolsMenu.Append(wx.MenuItem(toolsMenu, wx.ID_SEPARATOR))
        self.areaUnderCurveItem = toolsMenu.Append(AREAUNDERCURVE_ID, '&Area under curve ...\tCtrl+U',
                                                   'Area under curve')
        self.calculateitem = toolsMenu.Append(CALCULATE_ID, 'Time calc&ulator ...\tAlt+Ctrl+U', 'Time calculator')
        toolsMenu.Append(wx.MenuItem(toolsMenu, wx.ID_SEPARATOR))
        self.captureImageItem = wx.MenuItem(toolsMenu, CAPTUREIMAGE_ID, 'Capture and save &image ...')
        self.captureImageItem.SetBitmap(menuImages["camera"])
        toolsMenu.Append(self.captureImageItem)
        self.viewSourceItem = wx.MenuItem(None, self.VIEWSOURCE_ID, 'View &source ...', 'View source')
        self.exploreBackupsItem = toolsMenu.Append(EXPLORE_BACKUPS_ID, 'E&xplore memory stick backups ...',
                                                   'Explore memory stick backups')
        menubar.Append(toolsMenu, '&Tools')
        self.toolsMenu = toolsMenu

        optionsMenu = wx.Menu()
        menubar.Append(optionsMenu, '&Options')

        difficultyMenu = wx.Menu()
        self.difficultyBasicItem = difficultyMenu.Append(DIFFICULTYBASIC_ID, 'Basic', 'Basic', kind=wx.ITEM_RADIO)
        self.difficultyAdvancedItem = difficultyMenu.Append(DIFFICULTYADVANCED_ID, 'Advanced', 'Advanced',
                                                            kind=wx.ITEM_RADIO)
        self.difficultyExpertItem = difficultyMenu.Append(DIFFICULTYEXPERT_ID, 'Expert', 'Expert', kind=wx.ITEM_RADIO)
        self.difficultyEngineerItem = difficultyMenu.Append(DIFFICULTYENGINEER_ID, 'Engineer', 'Engineer',
                                                            kind=wx.ITEM_RADIO)
        optionsMenu.Append(wx.NewId(), 'Difficulty', difficultyMenu)
        self.editGeneralOptionsItem = optionsMenu.Append(EDITGENERALOPTIONS_ID, '&General options ...',
                                                         'General options')
        self.editCompareOptionsItem = optionsMenu.Append(EDITCOMPAREOPTIONS_ID, '&Compare options ...',
                                                         'Compare options')

        helpMenu = wx.Menu()
        tipsashelpitem = helpMenu.Append(TIPSASHELP_ID, 'Tips...')
        documentationitem = helpMenu.Append(DOCUMENTATION_ID, 'Documentation ...')
        communityitem = helpMenu.Append(COMMUNITY_ID, 'Community forum ...')
        supportitem = helpMenu.Append(SUPPORT_ID, 'Support ...')
        aboutitem = helpMenu.Append(wx.ID_ABOUT, '&About ...')
        menubar.Append(helpMenu, '&Help')
        self.SetMenuBar(menubar)

        self.menuDisabling = {
            "log": [insertPointItem, deletePointItem, smoothPointItem, smoothAllItem, self.transformItem,
                    self.smoothtool],
            "grid": [zoomInItem, zoomOutItem, expandYInItem, expandYOutItem, zoomResetItem, self.captureImageItem,
                     self.zoomresettool, self.zoomintool, self.zoomouttool],
            "sonofresco": [smoothPointItem, smoothAllItem, self.smoothtool]}

        self.Bind(wx.EVT_MENU, self.onNewProfile, newitem, id=NEW_FILE_ID)
        self.Bind(wx.EVT_TOOL, self.onNewProfile, newtool)
        self.Bind(wx.EVT_MENU, self.onExtractProfile, self.extractitem, id=NEW_FILE_ID)
        self.Bind(wx.EVT_MENU, self.onCalculate, self.calculateitem)
        self.Bind(wx.EVT_MENU, self.onSave, self.saveitem, id=SAVE_FILE_ID)
        self.Bind(wx.EVT_TOOL, self.onSave, self.savetool)
        self.Bind(wx.EVT_MENU, self.onSaveAs, saveAsitem, id=SAVE_AS_FILE_ID)
        self.Bind(wx.EVT_MENU, self.onFileProperties, filePropertiesitem, id=FILE_PROPERTIES_ID)
        self.Bind(wx.EVT_MENU, self.onImportSonofresco, self.importsonofrescoitem, id=IMPORT_SONOFRESCO_ID)
        self.Bind(wx.EVT_MENU, self.onExportSonofresco, self.exportsonofrescoitem, id=EXPORT_SONOFRESCO_ID)
        self.Bind(wx.EVT_MENU, self.onImportArtisan, self.importartisanitem, id=IMPORT_ARTISAN_ID)
        self.Bind(wx.EVT_MENU, self.onImportCropster, self.importcropsteritem, id=IMPORT_CROPSTER_ID)
        self.Bind(wx.EVT_MENU, self.onExportArtisan, self.exportartisanitem, id=EXPORT_ARTISAN_ID)
        self.Bind(wx.EVT_MENU, self.onImportIkawa, self.importikawaitem, id=IMPORT_IKAWA_ID)
        self.Bind(wx.EVT_MENU, self.onExportPDF, self.exportpdfitem, id=EXPORT_PDF_ID)
        self.Bind(wx.EVT_MENU, self.onNewAppWindow, self.newappwindowitem, id=NEW_APP_WINDOW_ID)
        self.Bind(wx.EVT_MENU, self.onOpen, loaditem, id=LOAD_FILE_ID)
        self.Bind(wx.EVT_TOOL, self.onOpen, loadtool)
        self.Bind(wx.EVT_MENU, self.onQuit, quititem, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.onUndo, self.undoItem)
        self.Bind(wx.EVT_TOOL, self.onUndo, self.undotool)
        self.Bind(wx.EVT_MENU, self.onRedo, self.redoItem)
        self.Bind(wx.EVT_TOOL, self.onRedo, self.redotool)
        self.Bind(wx.EVT_MENU, self.onInsert, insertPointItem)
        self.Bind(wx.EVT_MENU, self.onDelete, deletePointItem)
        self.Bind(wx.EVT_MENU, self.onSmoothPoint, smoothPointItem)
        self.Bind(wx.EVT_MENU, self.onSmoothAll, smoothAllItem)
        self.Bind(wx.EVT_TOOL, self.onSmoothPoint, self.smoothtool)
        self.Bind(wx.EVT_MENU, self.onCompare, self.compareItem)
        self.Bind(wx.EVT_MENU, self.onCompareDefault, self.compareDefaultItem)
        self.Bind(wx.EVT_MENU, self.onClearCompare, self.clearCompareItem)
        self.Bind(wx.EVT_MENU, self.onMerge, self.mergeItem)
        self.Bind(wx.EVT_MENU, self.onTransform, self.transformItem)
        self.Bind(wx.EVT_MENU, self.onAreaUnderCurve, self.areaUnderCurveItem)
        self.Bind(wx.EVT_MENU, self.onCaptureImage, self.captureImageItem)
        self.Bind(wx.EVT_MENU, self.onExploreBackups, self.exploreBackupsItem)
        self.Bind(wx.EVT_MENU, self.onZoomIn, zoomInItem)
        self.Bind(wx.EVT_MENU, self.onZoomOut, zoomOutItem)
        self.Bind(wx.EVT_MENU, self.onExpandYIn, expandYInItem)
        self.Bind(wx.EVT_MENU, self.onExpandYOut, expandYOutItem)
        self.Bind(wx.EVT_MENU, self.onZoomReset, zoomResetItem)
        self.Bind(wx.EVT_MENU, self.onViewMemstick, self.viewMemstickItem)
        self.Bind(wx.EVT_TOOL, self.onZoomReset, self.zoomresettool)
        self.Bind(wx.EVT_TOOL, self.onZoomIn, self.zoomintool)
        self.Bind(wx.EVT_TOOL, self.onZoomOut, self.zoomouttool)
        self.Bind(wx.EVT_TOOL, self.onViewMemstick, self.viewmemsticktool)
        self.Bind(wx.EVT_MENU, self.onDifficultyBasic, self.difficultyBasicItem)
        self.Bind(wx.EVT_MENU, self.onDifficultyAdvanced, self.difficultyAdvancedItem)
        self.Bind(wx.EVT_MENU, self.onDifficultyExpert, self.difficultyExpertItem)
        self.Bind(wx.EVT_MENU, self.onDifficultyEngineer, self.difficultyEngineerItem)
        self.Bind(wx.EVT_MENU, self.onEditGeneralOptions, self.editGeneralOptionsItem)
        self.Bind(wx.EVT_MENU, self.onEditCompareOptions, self.editCompareOptionsItem)
        self.Bind(wx.EVT_MENU, self.onTipsAsHelp, tipsashelpitem)
        self.Bind(wx.EVT_MENU, self.onDocumentation, documentationitem)
        self.Bind(wx.EVT_MENU, self.onCommunity, communityitem)
        self.Bind(wx.EVT_MENU, self.onSupport, supportitem)
        self.Bind(wx.EVT_MENU, self.onAboutBox, aboutitem)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_SIZE, self.onResize)
        self.setupMouseWheel()

        self.temperature_unit = self.options.getUserOption("temperature_unit", default='C')
        BaseDataObject.__init__(self)
        self.modified(False)

        self.panel = wx.Panel(self, wx.ID_ANY)

        self.removableDriveButton = None
        self.clearCompareItem.Enable(False)
        # self.compareItem.Check(False)
        self.compareDefaultItem.Check(False)
        self.viewMemstickItem.Enable(False)
        self.ToolBar.EnableTool(self.VIEWMEMSTICK_TOOL_ID, False)

        self.lastCurrentWorkingDirectory = None
        self.importedSuffix = None
        if isWindows:
            self.notebook = wx.Notebook(self.panel)
        else:
            self.notebook = wx.aui.AuiNotebook(self.panel, style=wx.aui.AUI_NB_TOP)

        self.checkBoxControls = {}
        self.page3 = GridPanel(self.notebook, self, aboutThisFileParameters)
        self.page4 = GridPanel(self.notebook, self, "others")
        self.page1 = ProfilePanel(self.notebook, self, "Roast Profile Curve", "temperature")
        self.page2 = ProfilePanel(self.notebook, self, "Fan Profile Curve", "speed")
        self.notebook.AddPage(self.page1, "Roast profile curve")
        self.notebook.AddPage(self.page2, "Fan profile curve")
        self.notebook.AddPage(self.page3, "About this file")
        self.notebook.AddPage(self.page4, "Profile settings")
        fileproperties.updateSchemaVersion(self)
        self.notebook.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.onNotebookChange)
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onNotebookChange)
        sizer = wx.BoxSizer()
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.panel.SetSizerAndFit(sizer)
        self.panel.Layout()
        self.safeToRemoveText = wx.StaticText(self.panel, id=wx.ID_ANY, label="Safe to remove", pos=(0, 0))
        self.safeToRemoveText.SetBackgroundColour((255, 255, 255))
        self.safeToRemoveText.Hide()

        self.currentRemovableDrive = None
        self.savedToUSB = False
        self.searchForRemovableDrives(preferKaffelogic=True)
        self.refreshRemovableDriveInfo()
        if self.options.getUserOption("automatic_check_for_updates") == "yes":
            updatesWorker = viewmemstick.GetURL_Thread(self, displayUpdateStatus,
                                                       [SOFTWARE_RELEASE_NOTES_URL, FIRMWARE_RELEASE_NOTES_URL],
                                                       extra=True)
            updatesWorker.start()
        self.recentFileList = userOptions.textToListOfStrings(self.options.getUserOption("recentfiles"))
        self.buildRecentFileMenu()
        self.updateMenu()
        self.hints = self.loadHints(self.temperature_unit)
        self.updateDifficulty()
        self.recommendationsAlreadyGiven = []
        wx.CallAfter(userOptions.messageIfUpdated, self)
        self.TipOfTheDay = wx.adv.CreateFileTipProvider(self.programPath + TIP_FILE,
                                                    int(self.options.getUserOption("tipnumber")) - 1)
        wx.CallAfter(userOptions.handleTips, self, self.TipOfTheDay)
        if DEBUG_LOG:
            self.addLogPage()
        if len(argv) >= 2:
            if DEBUG_MACEVENTS:
                wx.CallLater(1000, wx.MessageBox, "dropped file open " + argv[1])
            self.fileName = argv[1]
            wx.CallAfter(self.openFileAndSetWorkingDirectory)
        self.wheelTimer = SafeTimer(self)
        self.Bind(wx.EVT_TIMER, self.onWheelTimer, self.wheelTimer)
        self.externallyModifiedDialogInstance = None

        self.Layout()
        if maxi:
            self.Maximize()
        elif isMac:
            self.SetPosition(pos)
            self.SetSize(size)

        # set these up after all objects have been initialised, and any file that is going to be opened has been opened
        wx.CallAfter(userOptions.startFileCheckingThread, self, self.options, self.options.refreshOptionsFull,
                     self.externallyChanged)
        wx.CallAfter(self.setUpDeviceChecking)

    def updateWithNewTemperatureUnit(self):
        max = temperature.convertCelciusToSpecifiedUnit(MAX_VALID_ROAST_TEMPERATURE)
        self.page1.y_floatspin.SetRange(self.page1.y_floatspin.GetMin(), max)
        self.hints = self.loadHints(self.temperature_unit)

    def cleanFileName(self):
        # some mail programs (Thunderbird) will append .txt to the file name, but still try to open them with Kaffelogic Studio
        fileNameCleaned = re.sub(r"\.klog(-\d+)?\.txt$", r".klog", self.fileName, count=1, flags=re.IGNORECASE)
        fileNameCleaned = re.sub(r"\.kpro(-\d+)?\.txt$", r".kpro", fileNameCleaned, count=1,
                                 flags=re.IGNORECASE)
        if fileNameCleaned != self.fileName:
            self.fileName = fileNameCleaned
            self.modified(True)
            self.setProgramTitle()

    def setUpDeviceChecking(self):
        if isWindows:
            self.addMsgHandler(win32con.WM_DEVICECHANGE, self.onWindowsDeviceChange)
            self.hookWndProc()

        elif isMac:
            startMacDeviceCheckingThread(self=self, callback=self.onMacDeviceChange)

        elif isLinux:
            observer.Bind(pyudev.wx.EVT_DEVICE_EVENT, self.onLinuxDeviceChange)
            monitor.start()

    def setupMouseWheel(self, enableZoom=True):
        if enableZoom and self.options.getUserOption("zoom_on_mouse_wheel") == "yes":
            self.Bind(wx.EVT_MOUSEWHEEL, self.onWheel)
        else:
            self.Unbind(wx.EVT_MOUSEWHEEL)

    def buildRecentFileMenu(self):
        for m in self.recentFileMenu.GetMenuItems():
            self.recentFileMenu.DestroyItem(m)
        for f in self.recentFileList:
            ID = wx.NewId()
            x = self.recentFileMenu.Append(ID, f, f)
            self.Bind(wx.EVT_MENU, self.onRecentFile, x, id=ID)
        self.fileMenu.Enable(self.RECENT_FILE_ID, self.recentFileList != [])
        self.options.setUserOption("recentfiles", userOptions.listOfStringsToText(self.recentFileList))

    def openFileAndSetWorkingDirectory(self):
        self.openFile()
        self.cleanFileName()
        saveWorkingDirectories(self.fileName)

    def substituteTemperaturesInHints(self, hint_text, temperature_unit):
        temperatures = re.findall(r'\[\[DEG=(\d+\.?\d*)\]\]', hint_text)
        for t in temperatures:
            pattern = r'\[\[DEG=' + t + '\]\]'
            converted = utilities.trimTrailingPointZero(str(temperature.convertCelciusToSpecifiedUnit(float(t), temperature_unit)))
            hint_text = re.sub(pattern, converted, hint_text)
        return hint_text

    def loadHints(self, temperature_unit):
        data = self.substituteTemperaturesInHints(temperature.insertTemperatureUnit(openAndReadFile(self.programPath + HINT_FILE), temperature_unit), temperature_unit)
        hints = {}
        entry = []
        lines = data.splitlines()
        lines.append('')
        for line in lines:
            line = line.strip()
            if len(line) == 0 and len(entry) > 0:
                hints[entry[0].strip()] = {"key": entry[0].strip(), "difficulty": "", "unit": "", "text": ""}
                try:
                    hints[entry[0]]["key"] = entry[0].strip()
                except:
                    pass
                try:
                    hints[entry[0]]["difficulty"] = entry[1].strip()
                except:
                    pass
                try:
                    hints[entry[0]]["unit"] = entry[2]
                except:
                    pass
                try:
                    hints[entry[0]]["text"] = " ".join(entry[3:])
                except:
                    pass
                entry = []
            else:
                entry.append(line)
        return hints

    def updateDifficulty(self):
        self.page3.applyDifficulties()
        self.page4.applyDifficulties()
        if self.options.getUserOption("difficulty") == "basic":
            self.difficultyBasicItem.Check(True)
        else:
            if self.options.getUserOption("difficulty") == "advanced":
                self.difficultyAdvancedItem.Check(True)
            else:
                if self.options.getUserOption("difficulty") == "expert":
                    self.difficultyExpertItem.Check(True)
                else:
                    if self.options.getUserOption("difficulty") == "engineer":
                        self.difficultyEngineerItem.Check(True)
        self.updateMenu()

    def onDifficultyBasic(self, event):
        self.options.setUserOption("difficulty", "basic")
        self.updateDifficulty()

    def onDifficultyAdvanced(self, event):
        self.options.setUserOption("difficulty", "advanced")
        self.updateDifficulty()

    def onDifficultyExpert(self, event):
        self.options.setUserOption("difficulty", "expert")
        self.updateDifficulty()

    def onDifficultyEngineer(self, event):
        self.options.setUserOption("difficulty", "engineer")
        self.updateDifficulty()

    def onEditGeneralOptions(self, event):
        self.options.editGeneralOptions(self)

    def onEditCompareOptions(self, event):
        self.options.editCompareOptions(self)

    def onExploreBackups(self, event):
        backup_utils.explore(self.options.programDataFolder)

    def onNotebookChange(self, evt=None):
        if evt is not None:
            evt.Skip()
        self.updateMenu()
        where = self.notebook.GetPage(self.notebook.GetSelection())
        if hasattr(where, 'reDraw'):
            wx.CallAfter(where.reDraw)
        else:
            where.hover.Hide()

    def setNotebookPageSelection(self, i):
        self.notebook.SetSelection(i)
        self.updateMenu()

    def updateMenu(self):
        where = self.notebook.GetPage(self.notebook.GetSelection())
        title = self.notebook.GetPageText(self.notebook.GetSelection()).lower()
        for item in self.menuDisabling["log"]:
            toEnable = hasattr(where, 'canvas') and self.fileType != "log"
            if hasattr(item, 'id'):
                self.ToolBar.EnableTool(item.id, toEnable)
            else:
                item.Enable(toEnable)
        for item in self.menuDisabling["grid"]:
            toEnable = hasattr(where, 'canvas')
            if hasattr(item, 'id'):
                self.ToolBar.EnableTool(item.id, toEnable)
            else:
                item.Enable(toEnable)
        for item in self.menuDisabling["sonofresco"]:
            toEnable = hasattr(where, 'canvas') and self.fileType != "log" and not (self.configuration[
                                                                                        'emulation_mode'] == EMULATE_SONOFRESCO and where.title == 'Roast Profile Curve')
            if hasattr(item, 'id'):
                self.ToolBar.EnableTool(item.id, toEnable)
            else:
                item.Enable(toEnable)
        if self.options.getUserOption("difficulty") == "engineer":
            if self.viewSourceItem.GetMenu() is None:
                self.toolsMenu.Append(self.viewSourceItem)
                self.Bind(wx.EVT_MENU, self.onViewSource, self.viewSourceItem)
            self.viewSourceItem.Enable(
                hasattr(self, 'datastring') and self.datastring is not None and self.datastring != '')
        else:
            if self.viewSourceItem.GetMenu() is not None:
                self.toolsMenu.RemoveItem(self.viewSourceItem)
        self.extractitem.Enable(self.fileType == "log")
        self.mergeItem.Enable(self.fileType == "profile")
        self.areaUnderCurveItem.Enable(title in ['roast profile curve', 'log'])
        if self.notebook.GetPageText(self.notebook.GetSelection()).endswith('settings') and self.fileType != "log":
            self.transformItem.Enable(True)  # special case for transform zones and corners
        self.exportsonofrescoitem.Enable(self.emulation_mode.canExportSonofresco_fn(
            self) if self.emulation_mode.canExportSonofresco_fn is not None else False)
        self.setUndoRedo()
        self.raiseRemovableDriveButtons()

    def modified(self, isChanged, disableRemovableDriveButton=False):
        self._modified = isChanged
        if isChanged and not disableRemovableDriveButton:
            self.savedToUSB = False
        if self.removableDriveButton is not None:
            self.removableDriveButton.Enable((not disableRemovableDriveButton) and (isChanged or not self.savedToUSB))
        if not isChanged:
            self.wasSavedWithHistory = self.thereIsSomeHistory()
        self.saveitem.Enable(isChanged)
        self.ToolBar.EnableTool(self.savetool.id, isChanged)
        self.ToolBar.Realize()
        self.OSXSetModified(isChanged)

    def onCaptureImage(self, event):
        where_index = self.notebook.GetSelection()
        where = self.notebook.GetPage(where_index)
        if hasattr(where, 'canvas'):
            dialog = tools.captureImageDialog(self)
            dialog.ShowModal()
            result = dialog.result
            dialog.Destroy()
            if result == wx.ID_CANCEL: return
            wildcard = "Portable Network Graphics (*.png)|*.png"
            if not isMac: # Mac doesn't support multiple extensions for save type
                wildcard += "|JPEG  (*.jpg,*.jpe,*.jpeg)|*.jpg;*.jpe;*.jpeg"
            saveFileDialog = myFileDialog(self, "Save Image As", "",
                                          os.path.splitext(os.path.basename(self.fileName))[0],
                                          wildcard,
                                          wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            result = saveFileDialog.ShowModal()
            captureFileName, ext = os.path.splitext(saveFileDialog.GetPath())
            ext = ext.lower()
            if ext == '':
                ext = ['.png', '.jpg'][saveFileDialog.GetFilterIndex()]
            if not ext in ['.png', '.jpg', '.jpeg', '.jpe']:
                ext = '.png'
            extensions = {'.png': wx.BITMAP_TYPE_PNG, '.jpg': wx.BITMAP_TYPE_JPEG, '.jpe': wx.BITMAP_TYPE_JPEG,
                          '.jpeg': wx.BITMAP_TYPE_JPEG}
            saveFileDialog.Destroy()
            if result != wx.ID_CANCEL:
                canvas = self.page_to_image(where_index)
                if not isMac:
                    wx.CallAfter(self.saveCanvas, canvas, captureFileName + ext, extensions[ext])
                else:
                    # avoid weird Mac bug by callafter direct to SaveFile
                    wx.CallAfter(canvas.SaveFile, captureFileName + ext, extensions[ext])

    def saveCanvas(self, canvas, fileName, extension):
        try:
            canvas.SaveFile(fileName, extension)
        except IOError as e:
            dial = wx.MessageDialog(None, 'This file could not be saved.\n' + fileName + '\n' + e.strerror + '.',
                                    'Error',
                                    wx.OK | wx.ICON_EXCLAMATION)
            dial.ShowModal()

    def page_to_image(self, where_index, size=None):
        where = self.notebook.GetPage(where_index)
        notebookPage = self.notebook.GetSelection()
        storeAppSize = self.GetSize()
        storeAppPos = self.GetPosition()
        storeSize = where.canvas.GetSize()
        storeFontSizes = (
            where.canvas.GetFontSizeAxis(),
            where.canvas.GetFontSizeTitle()
        )
        storeLegendFontSize = self.legendFontSize
        storeLineWidth = self.lineWidth
        storeMarkerSize = self.markerSize
        storeFullscreen = self.fullscreenWasActive
        if size is None:
            data = self.options.getUserOption("capture_image_size").split(',')
            width = int(data[0])
            height = int(data[1])
        else:
            width, height = size
        fontScale = 1.0 if width <= 1000 else width / 1000.0
        where.canvas.SetFontSizeAxis(storeFontSizes[0] * fontScale)
        where.canvas.SetFontSizeTitle(storeFontSizes[1] * fontScale)
        self.legendFontSize = storeLegendFontSize * fontScale
        self.lineWidth = storeLineWidth * fontScale
        self.markerSize = storeMarkerSize * fontScale
        if where.displaySelectedText is not None:
            textSize = where.displaySelectedText.GetSize()
            textSize = (textSize[0] * fontScale, textSize[1] * fontScale)
            font = where.displaySelectedText.GetFont()
            font.SetPointSize(font.GetPointSize() * fontScale)
        if hasattr(where, 'phasesPanel'):
            self.notebook.SetSelection(where_index)
            self.fullscreenWasActive = True  # supress fullscreen dialog
            self.SetSize(wx.GetDisplaySize())
            self.SetPosition((0, 0))
            wx.Yield()
            phases = self.window_to_bitmap(where.phasesPanel).ConvertToImage()
        where.canvas.SetSize((width, height))
        where.reDraw()
        if where.displaySelectedText is not None:
            where.displaySelectedText.SetFont(font)
            where.displaySelectedText.SetLabel(where.displaySelectedText.GetLabel())
            if isLinux:
                where.displaySelectedText.SetSize(textSize)  # we have to work to get it to resize
            positionDisplaySelectedText(where, where.displaySelectedText)
            x, y = where.displaySelectedText.GetPosition()
            # Native Windows statictext control has white background.
            # Native X statictext control has transparent background.
            # So they get treated differently here.
            self.draw_text_on_bitmap(where.displaySelectedText.GetLabel(), font, x, y, where.canvas._Buffer,
                                     clear=textSize if isWindows else None)
        canvas = where.canvas._Buffer.ConvertToImage()
        if hasattr(where, 'phasesObject') and hasattr(where, 'togglePhases') \
                and where.togglePhases.IsChecked():
            w, h = where.phasesPanel.GetSize()
            if self.options.getUserOption("phases-panel-position") != "left":
                phaseX = canvas.GetWidth()
                canvasX = 0
            else:
                phaseX = 0
                canvasX = w
            canvas.Resize(size=(canvas.GetWidth() + w, canvas.GetHeight()), pos=(canvasX, 0), r=255, g=255, b=255)
            canvas.Paste(phases, phaseX, 5)
        self.SetSize(storeAppSize)
        self.SetPosition(storeAppPos)
        self.fullscreenWasActive = storeFullscreen
        self.notebook.SetSelection(notebookPage)
        self.Refresh()
        self.legendFontSize = storeLegendFontSize
        self.lineWidth = storeLineWidth
        self.markerSize = storeMarkerSize
        where.canvas.SetSize(storeSize)
        where.canvas.SetFontSizeAxis(storeFontSizes[0])
        where.canvas.SetFontSizeTitle(storeFontSizes[1])
        where.reDraw()
        return canvas

    def window_to_bitmap(self, window):
        width, height = window.GetSize()
        """
        There is a problem on Windows, because the alpha channel doesn't blit correctly, so make it 
        unnecessary by using wx.OR and a black background. There is a problem on Linux
        because the whole bitmap doesn't always get blitted, so make it look ok with a white background.
        """
        if isWindows:
            operation = wx.OR
            r = g = b = 0
        else:
            operation = wx.COPY
            r = g = b = 255
        bitmap = wx.EmptyBitmapRGBA(width, height, red=r, green=g, blue=b, alpha=255)
        wdc = wx.WindowDC(window)
        mdc = wx.MemoryDC()
        mdc.SelectObject(bitmap)
        mdc.Blit(0, 0, width, height, wdc, 0, 0, operation)
        mdc.SelectObject(wx.NullBitmap)
        return bitmap

    def draw_text_on_bitmap(self, text, font, x, y, bitmap, clear=None):
        dc = wx.MemoryDC()
        dc.SelectObject(bitmap)
        if clear is not None:
            w, h = clear
            gc = wx.GraphicsContext.Create(dc)
            gc.SetFont(font, 'Black')
            gc.SetPen(wx.Pen(wx.Colour(255, 255, 255, 255)))
            gc.SetBrush(wx.Brush(wx.Colour(255, 255, 255, 255)))
            gc.DrawRectangle(x - 2, y - 2, w + 4, h + 4)
            gc.DrawText(text, x, y)  # doesn't cope with new lines on Mac, but ok with them on Windows
            gc.SetBrush(wx.NullBrush)
            gc.SetPen(wx.NullPen)
        else:
            dc.SetFont(font)
            dc.DrawText(text, x, y)  # copes with new lines on Mac, but doesn't cope with alpha properly on Windows
        dc.SelectObject(wx.NullBitmap)

    def onViewSource(self, event):
        if hasattr(self, 'datastring') and self.datastring is not None and self.datastring != '':
            dialog = dialogs.enhancedMessageDialog(self)
            dialog.init('<pre>' + decodeCtrlV(self.datastring).replace('\n', '<br>') + '</pre>', 'Source',
                        wideFormat=True)
            dialog.ShowModal()
            dialog.Destroy()

    def onAreaUnderCurve(self, event):
        dialog = tools.areaUnderCurveDialog(self)
        dialog.ShowModal()
        dialog.Destroy()

    def onTransform(self, event):
        dialog = tools.transformDialog(self)
        dialog.ShowModal()
        dialog.Destroy()

    def onCalculate(self, event):
        dialog = calculator.calculateDialog(self)
        dialog.ShowModal()
        dialog.Destroy()

    def onFileProperties(self, event):
        dialog = fileproperties.propertiesDialog(self)
        dialog.ShowModal()
        dialog.Destroy()

    def onImportSonofresco(self, event):
        if self.saveIfModified(event):
            dialog = sonofresco.importDialog(self)
            dialog.ShowModal()
            dialog.Destroy()

    def onExportSonofresco(self, event):
        dialog = sonofresco.exportDialog(self)
        dialog.ShowModal()
        dialog.Destroy()

    def onImportArtisan(self, event):
        csvgeneric.importArtisan(self, event)

    def onImportCropster(self, event):
        csvgeneric.importCropster(self, event)

    def onExportArtisan(self, event):
        csvgeneric.exportArtisan(self, event)

    def onImportIkawa(self, event):
        csvgeneric.importIkawa(self, event)

    def onExportPDF(self, event):
        exportpdf.exportPDF(self)

    def onExpandYIn(self, event):
        self.onZoomIn(event, expand_y=True)

    def onExpandYOut(self, event):
        self.onZoomIn(event, expand_y=True, expand_direction_in=False)

    def onZoomIn(self, event, expand_y=False, expand_direction_in=True):
        where = self.notebook.GetPage(self.notebook.GetSelection())
        if hasattr(where, 'canvas'):
            if hasattr(where, 'closest_point') and where.closest_point is not None:
                centre = where.closest_point.toTuple()
                pan_to_centre = True
            else:
                if hasattr(where, 'selectedIndex') and where.wasCloseEnoughToDrag:
                    centre = where.profilePoints[where.selectedIndex].point.toTuple()
                    if where.selectedType == 'leftControl':
                        centre = where.profilePoints[where.selectedIndex].leftControl.toTuple()
                    if where.selectedType == 'rightControl':
                        centre = where.profilePoints[where.selectedIndex].rightControl.toTuple()
                    pan_to_centre = True
                else:
                    centre = where.canvas.PositionScreenToUser(where.canvas.ScreenToClient(wx.GetMousePosition()))
                    pan_to_centre = False
            self.zoom(where, True, centre, pan_to_centre, expand_y, expand_direction_in)

    def onZoomOut(self, event):
        where = self.notebook.GetPage(self.notebook.GetSelection())
        if hasattr(where, 'canvas'):
            self.zoom(where, False)

    def zoom(self, where, directionIn, centre=None, pan_to_centre=False, expand_y=False, expandDirectionIn=True):
        wx.App.Get().doRaise()
        if expand_y:
            where.expandY = True
            if expandDirectionIn:
                axes = calculateZoomedAxes(where.canvas, 0.5, centre, pan_to_centre, True)
            else:
                axes = calculateZoomedAxes(where.canvas, 2.0, centre, pan_to_centre, True)
        else:
            if directionIn:
                where.zoomScale *= sqrt(2)
                axes = calculateZoomedAxes(where.canvas, 1 / sqrt(2), centre, pan_to_centre)
            else:
                where.zoomScale /= sqrt(2)
                axes = calculateZoomedAxes(where.canvas, sqrt(2), centre)
        if where.zoomScale < 1:
            where.zoomScale = 1
            where.expandY = False
        where.zoomXAxis = axes[0]
        where.zoomYAxis = axes[1]
        where.reDraw()

    def onWheelTimer(self, event):
        self.setupMouseWheel(True)

    def onWheel(self, event):
        self.setupMouseWheel(False)
        self.wheelTimer.Start(200, wx.TIMER_ONE_SHOT)
        shift = wx.GetKeyState(wx.WXK_SHIFT)
        where = self.notebook.GetPage(self.notebook.GetSelection())
        if hasattr(where, 'canvas'):
            amount = event.GetWheelRotation()
            # Dividing by the negative delta results in the proper direction for scrolling,
            # at least on win32 and Gentoo.
            delta = event.GetWheelDelta()
            if delta != 0:
                if amount / delta > 0:
                    # centre = where.canvas.PositionScreenToUser(where.canvas.ScreenToClient(wx.GetMousePosition()))
                    # self.zoom(where, directionIn=True, centre=centre)
                    if shift:
                        self.onExpandYIn(event)
                    else:
                        self.onZoomIn(event)
                else:
                    # self.zoom(where, directionIn=False)
                    if shift:
                        self.onExpandYOut(event)
                    else:
                        self.onZoomOut(event)
        else:
            event.Skip()

    def onZoomReset(self, event):
        wx.App.Get().doRaise()
        where = self.notebook.GetPage(self.notebook.GetSelection())
        if hasattr(where, 'canvas'):
            where.expandY = False
            where.zoomScale = 1
            where.reDraw()

    def onWindowsDeviceChange(self, wParam, lParam):
        """
        Windows
        """
        self.registerDeviceChange(whatDeviceChanged(wParam, lParam))
        return True  # does not disable autorun even if you return False, so the explorer window will open regardless

    def onLinuxDeviceChange(self, dev):
        """
        Linux
        """
        if dev.device.device_type == 'partition':
            py_time.sleep(1)
            self.registerDeviceChange(whatDeviceChanged())

    def onMacDeviceChange(self, change):
        """
        Mac
        """
        self.registerDeviceChange(change)

    def registerDeviceChange(self, changes):
        for change in changes:
            direction, drive = change
            if direction == '+':
                if self.currentRemovableDrive is None or self.currentRemovableDrive != drive:
                    self.saveToRemovableDriveIsApproved = False
                    self.currentRemovableDrive = drive
                    self.options.setUserOption("last_removable_drive_added", drive)
                    self.updateHighestFirmwareFromDrive()
                    backup_utils.start_backup(self, self.currentRemovableDrive, self.options.programDataFolder)
                    self.refreshRemovableDriveInfo()
            else:
                wx.CallLater(2000, self.safeToRemoveText.Hide)
                if self.currentRemovableDrive is not None and self.currentRemovableDrive == drive:
                    if extractDriveFromPath(self.fileName) in removableDrives():
                        self.currentRemovableDrive = extractDriveFromPath(self.fileName)
                    else:
                        self.searchForRemovableDrives(preferKaffelogic=True)
                    self.refreshRemovableDriveInfo()

    def onEjectButton(self, e):
        if self.currentRemovableDrive is None:
            return

        result = eject(self.currentRemovableDrive)
        if result == True:
            self.searchForRemovableDrives(preferKaffelogic=True)
            self.safeToRemoveText.Show()
            self.refreshRemovableDriveInfo()
        else:
            wx.MessageBox(
                "It is not safe to remove " + volumeDescriptor(self.currentRemovableDrive) + " at the moment.",
                volumeDescriptor(self.currentRemovableDrive), wx.OK)

    def updateHighestFirmwareFromDrive(self):
        version_on_drive = getFirmwareVersionFromDrive(self.currentRemovableDrive)
        highest = self.options.getUserOption("highest_firmware_version_seen")
        firmStatus = compareVersions(version_on_drive, highest)
        if firmStatus == 1:
            self.options.setUserOption("highest_firmware_version_seen", version_on_drive)

    def searchForRemovableDrives(self, preferKaffelogic=False):
        driveList = removableDrives()
        old = self.currentRemovableDrive
        if len(driveList) > 0:
            if preferKaffelogic:
                mostPreferred = self.options.getUserOption("last_removable_drive_added")
                if mostPreferred in driveList:
                    self.currentRemovableDrive = mostPreferred
                else:
                    kaffelogics = [d for d in driveList if os.path.isdir(d + USB_KAFFELOGIC_DIR)]
                    if len(kaffelogics) > 0:
                        self.currentRemovableDrive = kaffelogics[-1]
                    else:
                        self.currentRemovableDrive = driveList[-1]
            else:
                self.currentRemovableDrive = driveList[0]
            self.updateHighestFirmwareFromDrive()
            backup_utils.start_backup(self, self.currentRemovableDrive, self.options.programDataFolder)
        else:
            self.currentRemovableDrive = None
        if self.currentRemovableDrive != old:
            self.saveToRemovableDriveIsApproved = False

    def raiseRemovableDriveButtons(self):
        if self.removableDriveButton is not None:
            self.safeToRemoveText.Raise()
            self.removableDriveButton.Raise()
            self.ejectButton.Raise()

    def positionRemovableDriveButtons(self):
        if self.removableDriveButton is not None:
            if self.options.getUserOption("usb-button-position", default="bottom") == "bottom":
                x = self.GetSize()[0] - self.removableDriveButton.GetSize()[0] - self.ejectButton.GetSize()[0] - 20
                y = self.page1.GetPosition()[1] + self.page1.level_floatspin.GetPosition()[1] - (2 if isWindows else 0)
                self.removableDriveButton.SetPosition((x, y))
                x = self.GetSize()[0] - self.safeToRemoveText.GetSize()[0] - self.ejectButton.GetSize()[0] - 20
                self.safeToRemoveText.SetPosition((x, y))
                x = self.GetSize()[0] - self.ejectButton.GetSize()[0] - 20
                self.ejectButton.SetPosition((x, y))
            else:
                x = self.GetSize()[0] - self.removableDriveButton.GetSize()[0] - self.ejectButton.GetSize()[0] - 20
                y = 0
                self.removableDriveButton.SetPosition((x, y))
                x = self.GetSize()[0] - self.safeToRemoveText.GetSize()[0] - self.ejectButton.GetSize()[0] - 20
                self.safeToRemoveText.SetPosition((x, y))
                x = self.GetSize()[0] - self.ejectButton.GetSize()[0] - 20
                self.ejectButton.SetPosition((x, y))
            self.raiseRemovableDriveButtons()

    def onResize(self, e):
        where = None
        try:
            where = self.notebook.GetPage(self.notebook.GetSelection())
        except:
            pass
        if where is not None and hasattr(where, 'displaySelectedText') and where.displaySelectedText is not None:
            positionDisplaySelectedText(where, where.displaySelectedText)
        wx.CallAfter(self.positionRemovableDriveButtons)
        if e is not None:
            e.Skip()

    def txtChange(self, page, control, isBulkChange=False, applyLinuxFix=False):
        self.captureHistory(page, 'text', item=control, isBulkChange=isBulkChange, applyLinuxFix=applyLinuxFix)
        self.modified(True)
        if self.comparisons is not None:
            for k, val in page.configControls.items():
                if val is control:
                    key = k
                    break
            if hasattr(page, 'setDiffStatusByKey'): page.setDiffStatusByKey(self, key)

    def focus(self, page, control, isBulkChange=False):
        if page.captureFocusEvents: self.captureHistory(page, 'focus', item=control, isFocusEvent=True,
                                                        isBulkChange=isBulkChange)
        page.focusObject = control

    def setFromHistoryItem(self, where, historyItem):
        where.captureFocusEvents = False
        if historyItem.entryType == 'config':
            if isinstance(where.configControls[historyItem.key], FS.FloatSpin):
                if hasattr(where, 'canvas'): where.canvas.SetFocus()
            else:
                where.configControls[historyItem.key].SetFocus()
            where.configControls[historyItem.key].ChangeValue(historyItem.value)
            if hasattr(where.configControls[historyItem.key], 'SetInsertionPoint'):
                if hasattr(historyItem, 'restoreCursorPos'):
                    where.configControls[historyItem.key].SetInsertionPoint(historyItem.restoreCursorPos)
                else:
                    where.configControls[historyItem.key].SetInsertionPoint(historyItem.cursorPos)
            if hasattr(where, 'setDiffStatusByKey'): where.setDiffStatusByKey(self, historyItem.key)
            if hasattr(where, 'reDraw'): where.reDraw()
        else:
            updateProfilePointsOnTab(where, copy.deepcopy(historyItem.profilePoints))
            where.selectedIndex = historyItem.selectedIndex
            where.selectedType = historyItem.selectedType
            where.setSpinners()
            where.currentOperation = 'history'
            if where.historyIndex == 0 or isinstance(wx.Window.FindFocus(), wx.TextCtrl):
                where.canvas.SetFocus()
        self.modified(True)
        where.captureFocusEvents = True

    def lastItemOfSameType(self, where, index, entryType):
        for i in range(index, -1, -1):
            if where.history[i].entryType == entryType:
                return where.history[i]
        return None

    def captureHistory(self, where, operation, alwaysCapture=False, item=None, isFocusEvent=False, isBulkChange=False,
                       applyLinuxFix=False, calledFromTextChange=False):
        # print 'capture', operation, 'isFocusEvent=', isFocusEvent
        if operation in ['text', 'focus']:
            if isFocusEvent:
                newItem = HistoryConfigEntry(item, isFocusEvent, isBulkChange=isBulkChange, applyLinuxFix=applyLinuxFix)
                where.history.insert(where.historyIndex + 1, newItem)
                where.historyIndex += 1
            else:
                where.history = where.history[:where.historyIndex + 1]
                lastItem = self.lastItemOfSameType(where, where.historyIndex,
                                                   'config')  # where.history[where.historyIndex]
                newItem = HistoryConfigEntry(item, isFocusEvent, isBulkChange=isBulkChange, applyLinuxFix=applyLinuxFix)
                if lastItem is not None:
                    lastItem.restoreCursorPos = len(lastItem.value) - len(newItem.value) + newItem.cursorPos
                where.history.append(newItem)
                where.historyIndex += 1
                where.historyCanUndo = True
        else:
            lastItem = self.lastItemOfSameType(where, where.historyIndex, 'points')  # where.history[where.historyIndex]
            if (alwaysCapture \
                or where.history[where.historyIndex].entryType == 'config' and not calledFromTextChange \
                or (hasattr(where, 'profilePoints') and lastItem.profilePoints[lastItem.selectedIndex].toTuple() !=
                    where.profilePoints[where.selectedIndex].toTuple()) \
                or (hasattr(where, 'currentOperation') and where.currentOperation in ['transform', 'merge'])) \
                    and ((hasattr(where, 'currentOperation') and where.currentOperation not in ['spinner', 'arrow']) \
                         or operation not in ['spinner', 'arrow']):
                where.history = where.history[:where.historyIndex + 1]
                where.history.append(HistoryPointsEntry(where.profilePoints, where.selectedIndex, where.selectedType,
                                                        isBulkChange=isBulkChange))
                where.historyIndex += 1
            where.historyCanUndo = True
        self.setUndoRedo()
        where.currentOperation = operation

    def onUndo(self, e):
        where = self.notebook.GetPage(self.notebook.GetSelection())
        if hasattr(where, 'history'):
            where.captureFocusEvents = False
            if where.history[where.historyIndex].entryType == 'points' and where.historyIndex == len(where.history) - 1:
                self.captureHistory(where, 'capture')
            if where.historyIndex > 0:
                where.historyIndex -= 1
            startingAtFocus = hasattr(where.history[where.historyIndex], 'isFocusEvent') and where.history[
                where.historyIndex].isFocusEvent
            while where.historyIndex > 0 and ((hasattr(where.history[where.historyIndex], 'isFocusEvent') \
                                               and where.history[where.historyIndex].isFocusEvent) or where.history[
                                                  where.historyIndex].bulkChange):
                self.setFromHistoryItem(where, where.history[where.historyIndex])
                where.historyIndex -= 1
            self.setFromHistoryItem(where, where.history[where.historyIndex])

            if where.historyIndex > 0 \
                    and where.history[where.historyIndex].entryType == 'points' \
                    and where.history[where.historyIndex - 1].entryType == 'config' \
                    and where.history[where.historyIndex - 1].isFocusEvent is False:
                self.onUndo(e)

            if where.historyIndex == 0:
                where.historyCanUndo = False
            self.setUndoRedo()
            where.historyTransition = False
            if (not self.thereIsSomeHistory()) and (not self.wasSavedWithHistory):
                self._modified = False
                self.OSXSetModified(False)
                self.saveitem.Enable(False)
                self.ToolBar.EnableTool(self.savetool.id, False)
                self.ToolBar.Realize()
                if self.currentRemovableDrive is not None and extractDriveFromPath(
                        self.fileName) == self.currentRemovableDrive:
                    self.removableDriveButton.Enable(False)
                where.captureFocusEvents = True

    def thereIsSomeHistory(self):
        try:
            return self.page1.historyCanUndo or self.page2.historyCanUndo or self.page3.historyCanUndo or self.page4.historyCanUndo or \
                   (self.fileType == "log" and self.logPanel.historyCanUndo)
        except:
            return False

    def setUndoRedo(self):
        selection = self.notebook.GetSelection()
        if selection != -1:
            where = self.notebook.GetPage(selection)
            if hasattr(where, 'history'):
                index = where.historyIndex
                while index > 0 and hasattr(where.history[index], 'isFocusEvent') and where.history[index].isFocusEvent:
                    index -= 1
                canUndo = index > 0 or (where.historyCanUndo and not hasattr(where.history[index], 'isFocusEvent'))
                self.undoItem.Enable(canUndo)
                self.ToolBar.EnableTool(self.undotool.id, canUndo)
                where.historyCanUndo = canUndo
                index = where.historyIndex + 1
                while index < len(where.history) and hasattr(where.history[index], 'isFocusEvent') and where.history[
                    index].isFocusEvent:
                    index += 1
                canRedo = len(where.history) > 0 and index < len(where.history)
            else:
                self.undoItem.Enable(False)
                self.ToolBar.EnableTool(self.undotool.id, False)
                canRedo = False
            self.redoItem.Enable(canRedo)
            self.ToolBar.EnableTool(self.redotool.id, canRedo)
            self.ToolBar.Realize()
            # ToolBar.Realize() will cause a resize, and therefore call the onResize handler
            """
            for i in range(len(where.history)):
                where.history[i].toDisplay()
                if i == where.historyIndex:
                    print "INDEX>>>>>>>>>>>>>>>>>>"
            """

    def onRedo(self, e):
        where = self.notebook.GetPage(self.notebook.GetSelection())
        if hasattr(where, 'history'):
            while True:
                if where.historyIndex < len(where.history) - 1:
                    where.historyIndex += 1
                    self.setFromHistoryItem(where, where.history[where.historyIndex])
                    if where.historyIndex == len(where.history) - 1 \
                            or (
                            (
                                    not (
                                            hasattr(where.history[where.historyIndex], 'isFocusEvent') \
                                            and where.history[where.historyIndex].isFocusEvent
                                    )
                            )
                            and
                            (
                                    not where.history[where.historyIndex].bulkChange
                            )
                    ): break
                else:
                    break
                # print "multiple redo on item", where.historyIndex, where.history[where.historyIndex].entryType
            if where.historyIndex > 0 \
                    and where.historyIndex < len(where.history) - 1 \
                    and where.history[where.historyIndex].entryType == 'points' \
                    and where.history[where.historyIndex - 1].entryType == 'config' \
                    and where.history[where.historyIndex - 1].isFocusEvent is False:
                self.onRedo(e)
            where.historyCanUndo = True
            self.setUndoRedo()

    def onDelete(self, e):
        where = self.notebook.GetPage(self.notebook.GetSelection())
        if self.fileType == "log" or (len(
                where.profilePoints) <= self.emulation_mode.profile_points_edit_min and where.title == 'Roast Profile Curve') \
                or (len(where.profilePoints) <= FAN_POINTS_EDIT_MIN and where.title != 'Roast Profile Curve'):
            return
        wx.App.Get().doRaise()
        if hasattr(where, 'profilePoints'):
            if (where.selectedType == 'point' and
                    where.selectedIndex > 0 and
                    (
                            where.selectedIndex not in self.emulation_mode.profile_locked_points or where.title != 'Roast Profile Curve') and
                    (not (self.emulation_mode.profile_points_timelock_last and where.selectedIndex == len(
                        where.profilePoints) - 1) or where.title != 'Roast Profile Curve')):
                self.captureHistory(where, 'delete', True)
                where.profilePoints.pop(where.selectedIndex)
                self.modified(True)
                if where.selectedIndex >= len(where.profilePoints) - 1:
                    where.selectedIndex = len(where.profilePoints) - 1
                calculateControlPoints(where.profilePoints, CONTROL_POINT_RATIO)
                where.setSpinners()

    def onInsert(self, e):
        where = self.notebook.GetPage(self.notebook.GetSelection())
        if self.fileType == "log" or (len(
                where.profilePoints) >= self.emulation_mode.profile_points_edit_max and where.title == 'Roast Profile Curve') \
                or (len(where.profilePoints) >= FAN_POINTS_EDIT_MAX and where.title != 'Roast Profile Curve'):
            return
        wx.App.Get().doRaise()
        if hasattr(where, 'profilePoints'):
            insert_forward = True
            if where.selectedIndex + 1 >= len(where.profilePoints):
                rightX, rightY = where.profilePoints[where.selectedIndex].toTuple()[:2]
                leftX, leftY = where.profilePoints[where.selectedIndex - 1].toTuple()[:2]
                if self.emulation_mode.profile_points_timelock_last and where.title == 'Roast Profile Curve':
                    insert_forward = False
                    newX = (leftX + rightX) / 2
                    newY = (leftY + rightY) / 2
                else:
                    newX = rightX + (rightX - leftX) / 2
                    newY = rightY + (rightY - leftY) / 2
            else:
                if where.selectedIndex < self.emulation_mode.profile_points_only_insert_after_index:
                    where.selectedIndex = self.emulation_mode.profile_points_only_insert_after_index
                rightX, rightY = where.profilePoints[where.selectedIndex + 1].toTuple()[:2]
                leftX, leftY = where.profilePoints[where.selectedIndex].toTuple()[:2]
                newX = (leftX + rightX) / 2
                newY = (leftY + rightY) / 2
            if leftX == rightX and leftY == rightY:
                newX = leftX + 60
            if leftY == rightY:
                newY = leftY + 10
            newP = ProfilePoint(newX, newY)
            self.captureHistory(where, 'insert', True)
            if insert_forward:
                where.profilePoints.insert(where.selectedIndex + 1, newP)
                where.selectedIndex += 1
            else:
                where.profilePoints.insert(where.selectedIndex, newP)
            self.modified(True)
            calculateControlPoints(where.profilePoints, CONTROL_POINT_RATIO)
            where.selectedType = 'point'
            where.setSpinners()

    def onSmoothAll(self, e, menuAction=True):
        if self.fileType == "log":
            return
        where = self.notebook.GetPage(self.notebook.GetSelection())
        if hasattr(where, 'profilePoints') and len(where.profilePoints) >= 3:
            if menuAction: self.captureHistory(where, 'smoothpoint', True)
            index = where.selectedIndex
            for where.selectedIndex in range(len(where.profilePoints)):
                self.onSmoothPoint(e, menuAction=False)
            where.selectedIndex = index
            if menuAction: where.setSpinners()

    def onSmoothPoint(self, e, menuAction=True):
        if self.fileType == "log":
            return
        wx.App.Get().doRaise()
        where = self.notebook.GetPage(self.notebook.GetSelection())
        if hasattr(where, 'profilePoints') and len(where.profilePoints) >= 3:
            if menuAction: self.captureHistory(where, 'smoothpoint', True)
            if where.selectedIndex > 0 and where.selectedIndex < len(where.profilePoints) - 1:
                A = where.profilePoints[where.selectedIndex - 1].point
                B = where.profilePoints[where.selectedIndex].point
                C = where.profilePoints[where.selectedIndex + 1].point
                left = controlPointCalculation(A, B, C, ratio=CONTROL_POINT_RATIO, left=True)
                right = controlPointCalculation(A, B, C, ratio=CONTROL_POINT_RATIO, left=False)
                where.profilePoints[where.selectedIndex].setLeftControl(left.x, left.y)
                where.profilePoints[where.selectedIndex].setRightControl(right.x, right.y)
            else:
                if where.selectedIndex == 0:
                    right = controlEndPointCalculation(where.profilePoints[0], where.profilePoints[1],
                                                       ratio=CONTROL_POINT_RATIO, start=True)
                    where.profilePoints[0].setRightControl(right.x, right.y)
                else:
                    if where.selectedIndex == len(where.profilePoints) - 1:
                        left = controlEndPointCalculation(where.profilePoints[-2], where.profilePoints[-1],
                                                          ratio=CONTROL_POINT_RATIO, start=False)
                        where.profilePoints[-1].setLeftControl(left.x, left.y)
            self.modified(True)
            if menuAction: where.setSpinners()

    def removeLogPage(self):
        if self.notebook.GetPageText(0) == "Log":
            self.persistCheckBoxData()
            for key in list(self.checkBoxControls.keys()):
                if key.startswith("Log_"):
                    self.checkBoxControls.pop(key)
            self.notebook.DeletePage(0)
            self.logPanel = None

    def addLogPage(self):
        if isWindows: self.Freeze()
        self.removeLogPage()
        self.logPanel = logpanel.LogPanel(self.notebook, self)
        self.notebook.InsertPage(0, self.logPanel, "Log", select=True)
        if isWindows: self.Thaw()

    def onAboutBox(self, e):
        about = tools.aboutDialog(self)
        about.ShowModal()
        about.Destroy()

    def onTipsAsHelp(self, e):
        wx.CallAfter(userOptions.handleTips, self, self.TipOfTheDay, asHelp=True)

    def onSupport(self, e):
        webbrowser.open(SUPPORT_URL, new=2)

    def onDocumentation(self, e):
        webbrowser.open(DOCUMENTATION_URL, new=2)

    def onCommunity(self, e):
        webbrowser.open(COMMUNITY_URL, new=2)

    def onViewMemstick(self, e):
        dia = viewmemstick.showMemstickDialog(self)
        dia.ShowModal()
        dia.Destroy()

    def onQuit(self, e):
        self.Close()

    def updateLogPanels(self):
        known = set(list(self.defaults.keys()) + profileDataInLog + logFileName + notSavedInProfile)
        unknown = [x for x in list(self.configuration.keys()) if x not in known]
        if self.fileType == "profile":
            for unwanted in logFileName + notSavedInProfile + unknown:
                if unwanted in self.page3.configList:
                    self.page3.configList.remove(unwanted)
            for wanted in notFoundInLog:
                if wanted not in self.page3.configList:
                    self.page3.configList.append(wanted)
            for wanted in unknown:
                if wanted not in self.page3.configList:
                    self.page3.configList.append(wanted)
            self.page1.enableSpinners()
            self.page2.enableSpinners()
            self.page3.addGrid(self)
            self.page4.addGrid(self)
            self.removeLogPage()
        else:  # file type must be log
            # remove items from page3, to ensure they are added in the desired order
            for notwanted in logFileName + aboutThisFileParameters + notSavedInProfile + unknown:
                if notwanted in self.page3.configList:
                    self.page3.configList.remove(notwanted)
            for wanted in logFileName + aboutThisFileParameters + notSavedInProfile:
                if wanted not in self.page3.configList:
                    self.page3.configList.append(wanted)
            for notwanted in notFoundInLog:
                if notwanted in self.page3.configList:
                    self.page3.configList.remove(notwanted)
            for wanted in unknown:
                if wanted not in self.page3.configList:
                    self.page3.configList.append(wanted)

            self.page1.disableSpinners()
            self.page2.disableSpinners()
            self.page3.addGrid(self)
            self.page4.addGrid(self)
            self.addLogPage()
        self.updateDifficulty()
        fileproperties.updateSchemaVersion(self)

    def openDroppedFile(self, filename):
        # Mac only, and also open from view memstick dialog
        try:
            wx.App.Get().doRaise()
        except:
            return  # no app so open would fail
        if self.saveIfModified(None):
            self.fileName = filename
            self.openFileAndSetWorkingDirectory()
            return True
        return False

    def externallyChanged(self):
        with userOptions.fileCheckingLock:
            self.fileTimeStamp = os.path.getmtime(self.fileName)
        if self.externallyModifiedDialogInstance is None and self.importedSuffix is None:
            # Only log (.klog) and profile (.kpro) get change notifications, imported files do not get the notification.
            self.externallyModifiedDialogInstance = dialogs.externallyModifiedDialog(self.panel, self._modified)
            self.externallyModifiedDialogInstance.ShowModal()
            answer = self.externallyModifiedDialogInstance.result
            self.externallyModifiedDialogInstance.Destroy()
            self.externallyModifiedDialogInstance = None
            if answer == 'update':
                self.openFile()

    def onClearCompare(self, event):
        self.comparisons = None
        self.clearCompareItem.Enable(False)
        self.loadComparisons()

    def loadExtraDataObject(self, dataObject, overrideEmulationMode=None):
        dataObject.configuration = {}
        dataObject.configurationOrderedKeys = []
        dataObject.logData.reset_vars()
        dataObject.temperature_unit = temperature.getTemperatureUnit()
        stringToDataObjects(DEFAULT_DATA, dataObject)
        dataObject.defaults = copy.deepcopy(dataObject.configuration)
        stringToDataObjects(dataObject.datastring, dataObject)
        if overrideEmulationMode == EMULATE_SONOFRESCO or dataObject.configuration[
            'emulation_mode'] == EMULATE_SONOFRESCO:
            dataObject.configuration = {}
            dataObject.configurationOrderedKeys = []
            stringToDataObjects(SONOFRESCO_DEFAULT_DATA, dataObject)
            # Sonofresco default data doesn't have profile points, they need to be imported with the current temperature conversion values
            dataObject.defaults = copy.deepcopy(dataObject.configuration)
            if dataObject.datastring == "":
                stringToDataObjects(sonofresco.getSonofrescoDefaultAsKaffelogic(), dataObject)
            else:
                stringToDataObjects(dataObject.datastring, dataObject)

    def loadComparisons(self, overrideEmulationMode=None):
        if self.comparisons is not None:
            for c in self.comparisons:
                self.loadExtraDataObject(c, overrideEmulationMode)
        if self.compareDefault:
            if self.comparisons is None or len(self.comparisons) == 0:
                self.comparisons = [BaseDataObject()]
                self.comparisons[-1].fileName = "Default"
                self.comparisons[-1].datastring = ""
            else:
                if self.comparisons[-1].fileName != "Default":
                    self.comparisons.append(BaseDataObject())
                    self.comparisons[-1].fileName = "Default"
                    self.comparisons[-1].datastring = ""
        else:
            if self.comparisons is not None and len(self.comparisons) > 0 and self.comparisons[
                -1].fileName == "Default":
                self.comparisons = self.comparisons[:-1]
        if self.comparisons is not None and len(self.comparisons) == 0:
            self.comparisons = None
        self.clearCompareItem.Enable(self.comparisons is not None and self.comparisons[0].fileName != "Default")
        self.page3.refreshDiffStatusAll(self)
        self.page4.refreshDiffStatusAll(self)
        where = self.notebook.GetPage(self.notebook.GetSelection())
        fanProfile = self.page2
        if not where is fanProfile:
            fanProfile.reDraw()
        if hasattr(where, 'reDraw'):
            where.reDraw()

    def onCompareDefault(self, event):
        if self.compareDefault:
            self.compareDefault = False
            self.compareDefaultItem.Check(False)
        else:
            self.compareDefault = True
            self.compareDefaultItem.Check(True)
        self.loadComparisons()

    def onCompare(self, event):
        openFileDialog = myFileDialog(self, "Compare with ...", "", "",
                                      "Kaffelogic files (*.kpro, *.klog)|*.kpro;*.klog",
                                      wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        result = openFileDialog.ShowModal()
        if result == wx.ID_CANCEL:
            return
        fileNames = openFileDialog.GetPaths()
        openFileDialog.Destroy()
        if self.comparisons is None: self.comparisons = []
        for f in fileNames:
            c = BaseDataObject()
            c.fileName = f
            c.datastring = openAndReadFile(f)
            if c.datastring != "":
                comparison, version_default, version_opening = compareProfileSchemaVersionsOf(DEFAULT_DATA,
                                                                                              c.datastring)
                if comparison < 0:
                    """
                    Best practice is to use CallAfter to have MessageBox displayed in main GUI thread. Seems to be more crucial on the Mac.
                    """
                    wx.CallAfter(wx.MessageBox, os.path.basename(
                        f) + " uses a more recent profile schema version (v" + version_opening + ") than that supported " +
                                 "by this version of " + PROGRAM_NAME + " (v" + version_default + ").\n\n" +
                                 "This file cannot be opened.\n\n" +
                                 "Please download and install the latest version of " + PROGRAM_NAME + " so that you can open this file.",
                                 "Warning", wx.OK)
                else:
                    utilities.addToFrontOfComparisonsList(c, self.comparisons)
        if self.comparisons == []: self.comparisons = None
        self.loadComparisons()

    def onMerge(self, event):
        if self.fileType == "log":
            return
        openFileDialog = myFileDialog(self, "Merge from  ...", "", "",
                                      "Kaffelogic files (*.kpro, *.klog)|*.kpro;*.klog",
                                      wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        result = openFileDialog.ShowModal()
        if result == wx.ID_CANCEL:
            return
        self.mergeFrom = BaseDataObject()
        self.mergeFrom.fileName = openFileDialog.GetPath()
        openFileDialog.Destroy()
        self.mergeFrom.datastring = openAndReadFile(self.mergeFrom.fileName)
        if self.mergeFrom.datastring != "":
            comparison, version_default, version_opening = compareProfileSchemaVersionsOf(DEFAULT_DATA,
                                                                                          self.mergeFrom.datastring)
            if comparison < 0:
                """
                Best practice is to use CallAfter to have MessageBox displayed in main GUI thread. Seems to be more crucial on the Mac.
                """
                wx.CallAfter(wx.MessageBox,
                             "The file you are opening uses a more recent profile schema version (v" + version_opening + ") than that supported " +
                             "by this version of " + PROGRAM_NAME + " (v" + version_default + ").\n\n" +
                             "This file cannot be opened.\n\n" +
                             "Please download and install the latest version of " + PROGRAM_NAME + " so that you can open this file.",
                             "Warning", wx.OK)
                self.mergeFrom = None
        else:
            self.mergeFrom = None
        dialog = mergeDialog(self)
        dialog.ShowModal()
        dialog.Destroy()

    def onRecentFile(self, event):
        fName = event.EventObject.FindItemById(event.GetId()).GetLabel()
        if os.path.isfile(fName):
            if self.saveIfModified(event):
                self.fileName = fName
                self.openFileAndSetWorkingDirectory()
        else:
            wx.MessageBox(fName + "\ncan no longer be found.", "File not found", wx.OK)

    def onOpen(self, event):
        if self.saveIfModified(event):
            openFileDialog = myFileDialog(self, "Open", "", "",
                                          "Kaffelogic files (*.kpro, *.klog)|*.kpro;*.klog",
                                          wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
            result = openFileDialog.ShowModal()
            if result == wx.ID_CANCEL:
                return
            self.fileName = openFileDialog.GetPath()
            openFileDialog.Destroy()
            self.openFile()

    def openFile(self):
        with userOptions.fileCheckingLock:
            self.fileTimeStamp = None
        self.datastring = openAndReadFile(self.fileName)
        if self.datastring != "":
            comparison, version_default, version_opening = compareProfileSchemaVersionsOf(DEFAULT_DATA, self.datastring)
            if comparison < 0:
                """
                Best practice is to use CallAfter to have MessageBox displayed in main GUI thread. Seems to be more crucial on the Mac.
                """
                wx.CallAfter(wx.MessageBox,
                             "The file you are opening uses a more recent profile schema version (v" + version_opening + ") than that supported " +
                             "by this version of " + PROGRAM_NAME + " (v" + version_default + ").\n\n" +
                             "This file cannot be opened and the default profile will be opened instead.\n\n" +
                             "Please download and install the latest version of " + PROGRAM_NAME + " so that you can open this file.",
                             "Warning", wx.OK)
                self.fileName = ""
                self.openFromString(self, DEFAULT_DATA, "")
            else:
                self.openFromString(self, DEFAULT_DATA, self.datastring)
                with userOptions.fileCheckingLock:
                    self.fileTimeStamp = os.path.getmtime(self.fileName)
        else:
            wx.CallAfter(wx.MessageBox,
                         self.fileName + " is an empty file and cannot be opened. The default profile will be opened instead.",
                         "Warning", wx.OK)
            self.fileName = ""
            self.openFromString(self, DEFAULT_DATA, "")

    def openFromString(self, frame, default, data):
        self.importedSuffix = None
        destroySelectedText(self.page1)
        destroySelectedText(self.page2)
        self.page1.closest_point = None
        self.page1.closest_distance = None
        self.page1.closest_legend = None
        self.page1.displaySelectedText = None
        self.page2.closest_point = None
        self.page2.closest_distance = None
        self.page2.closest_legend = None
        self.page2.displaySelectedText = None
        self.page1.selectedIndex = 0
        self.page2.selectedIndex = 0
        self.configuration = {}
        self.configurationOrderedKeys = []
        self.logData.reset_vars()
        self.profileIsFromLogFile = True  # always true unless custom import e.g. import Artisan CSV as log
        stringToDataObjects(default, self)
        self.defaults = copy.deepcopy(self.configuration)
        stringToDataObjects(data, self)
        if self.configuration['emulation_mode'] == EMULATE_SONOFRESCO:
            self.configuration = {}
            self.configurationOrderedKeys = []
            stringToDataObjects(SONOFRESCO_DEFAULT_DATA, self)
            self.defaults = copy.deepcopy(self.configuration)
            stringToDataObjects(data, self)
        if self.logData.xAxis == '':
            self.fileType = "profile"
        else:
            self.fileType = "log"
        if self.fileName.lower().endswith('.klog') and self.fileType == "profile":
            self.fileName = ''
        self.page3.initConfigList(self, aboutThisFileParameters)
        self.page3.addGrid(self)
        refreshGridPanel(self.page3, self)
        self.page4.initConfigList(self, "others")
        self.page4.addGrid(self)
        refreshGridPanel(self.page4, self)
        self.page1.profilePoints = self.roastProfilePoints
        self.page1.level_floatspin.SetValue(self.configuration['recommended_level'])
        self.page1.phasesObject.setPhasesFromProfileData()
        self.emulation_mode = EmulationMode()
        if self.configuration['emulation_mode'] == EMULATE_SONOFRESCO:
            sonofresco.setLimits(self, self.emulation_mode)
            if self.fileType == "log":
                self.emulation_mode.canExportSonofresco_fn = None
        self.page1.applyEmulation(frame)
        self.page2.profilePoints = self.fanProfilePoints
        self.updateLogPanels()
        self.page1.selectedType = 'point'
        self.page2.selectedType = 'point'
        self.page1.expandY = False
        self.page1.zoomScale = 1
        self.page2.expandY = False
        self.page2.zoomScale = 1
        # self.page1.reDraw()
        # self.page2.reDraw() done by setSpinners
        self.page1.resetHistory()
        self.page2.resetHistory()
        self.page3.resetHistory()
        self.page4.resetHistory()
        self.page1.setSpinners()
        self.page2.setSpinners()
        self.page1.canvas.SetFocus()
        self.finaliseOpen()

    def setProgramTitle(self):
        if isWindows:
            if self.fileName == "":
                self.SetTitle(PROGRAM_NAME + self.emulation_mode.description)
            else:
                self.SetTitle(self.fileName + ' - ' + PROGRAM_NAME + self.emulation_mode.description)
        else:
            self.SetTitle(self.fileName + self.emulation_mode.description)
        if self.fileName != "" and self.importedSuffix is None:
            utilities.addToFrontOfList(self.fileName, self.recentFileList, limit=20)
        self.buildRecentFileMenu()

    def finaliseOpen(self):
        self.setProgramTitle()
        self.savedToUSB = False
        self.refreshRemovableDriveInfo()
        if self.currentRemovableDrive is not None and extractDriveFromPath(self.fileName) == self.currentRemovableDrive:
            self.saveToRemovableDriveIsApproved = True
            self.savedToUSB = True
        self.modified(False)
        self.app.doRaise()
        self.notebook.SetSelection(0)
        if isMac:
            wx.CallLater(100, self.notebook.SetSelection, 0)  # workaround for Mac bug
        self.page1.phasesObject.enableEventEditing()

    def onNewAppWindow(self, event):
        if isWindows:
            cmd = 'start "" "' + self.programPath + PROGRAM_NAME + '"'
        elif isMac:
            cmd = "open -n '/Applications/" + PROGRAM_NAME + ".app'"
        elif isLinux:
            cmd = "'/opt/kaffelogic-studio/" + PROGRAM_NAME + "' & disown"
        else:
            cmd = ""
        os.system(cmd)

    def onNewProfile(self, event):
        if self.saveIfModified(event):
            self.fileName = ""
            self.openFromString(self, DEFAULT_DATA, "")
            self.datastring = ""
            self.updateMenu()

    def ensureFolderExists(self, folder):
        try:
            os.makedirs(folder)
        except OSError as e:
            if e.errno != errno.EEXIST:
                dial = wx.MessageDialog(None, 'The kaffelogic folder could not be created\non ' + volumeDescriptor(
                    self.currentRemovableDrive) + '\n' + e.strerror + '.', 'Error',
                                        wx.OK | wx.ICON_EXCLAMATION)
                dial.ShowModal()
                return False
        return True

    def checkShortNameConflictOk(self, fileName):
        """ returns True if there is no conflict, False if there is a conflict """
        actualShortName = self.page3.configControls["profile_short_name"].GetValue().strip()
        currentShortName = extractShortName(fileName, actualShortName)
        if self.currentRemovableDrive is not None and extractDriveFromPath(fileName) == self.currentRemovableDrive and \
                os.path.dirname(fileName) == self.currentRemovableDrive + USB_KAFFELOGIC_DIR + os.sep + USB_PROFILE_DIR:
            profiles = dirToKeyValuesArray(os.path.dirname(fileName),
                                           ['profile_short_name', 'profile_designer', 'profile_description',
                                            'profile_modified'], 'kpro')
            profiles.append(
                {'profile_file_name': DEFAULT_PROFILE, 'profile_short_name': DEFAULT_PROFILE, 'profile_designer': '',
                 'profile_description': '', 'profile_modified': ''})
            otherShortNames = [extractShortName(pro['profile_file_name'], pro['profile_short_name'].strip()) for pro in
                               profiles if 'profile_short_name' in list(pro.keys()) and \
                               os.path.basename(fileName) != pro['profile_file_name']]
            if currentShortName in otherShortNames:
                conflictedProfiles = [pro for pro in profiles if 'profile_short_name' in list(pro.keys()) and \
                                      currentShortName == extractShortName(pro['profile_file_name'],
                                                                           pro['profile_short_name'].strip()) and \
                                      os.path.basename(fileName) != pro['profile_file_name']]
                conflicted = conflictedProfiles[0]
                message = "The display name '" + currentShortName + "' is used for the "
                message += "default profile" if conflicted['profile_file_name'] == DEFAULT_PROFILE else (
                            "file " + os.path.basename(conflicted['profile_file_name']))
                message += ".\n\nPlease use a different "
                message += "file name" if actualShortName == '' else "short name"
                message += ".\n\nDisplay names are used when loading profiles on the Nano 7 and need to be distinct."
                self.setNotebookPageSelection(2)
                self.page3.configControls["profile_short_name"].SetFocus()
                dial = wx.MessageDialog(None, message, 'Error',
                                        wx.OK | wx.ICON_EXCLAMATION)
                dial.ShowModal()
                return False
        return True

    def appendUserEnteredDataToLogData(self):
        newstring = re.sub(r"(^|\r|\r\n)tasting_notes:.*?($|\r\n|\r)", r"\1", cleanLineEnds(self.datastring))
        newstring = re.sub(r"\r", r"\n", newstring)
        newstring = "tasting_notes:" + encodeCtrlV(
            self.page3.configControls["tasting_notes"].GetValue()) + "\n" + newstring
        newstring = re.sub(r"\n$", "", newstring) + "\n"  # force file to end with line end

        original_colour_change = floatOrNone(fromMinSec(
            self.configuration["colour_change"] if "colour_change" in list(self.configuration.keys()) else ""))
        original_first_crack = floatOrNone(
            fromMinSec(self.configuration["first_crack"] if "first_crack" in list(self.configuration.keys()) else ""))
        original_roast_end = floatOrNone(
            fromMinSec(self.configuration["roast_end"] if "roast_end" in list(self.configuration.keys()) else ""))
        new_colour_change = self.logPanel.phasesObject.getColourChangeTime()
        new_first_crack = self.logPanel.phasesObject.getFirstCrackTime()
        new_roast_end = self.logPanel.phasesObject.getRoastEndTime()

        extras = ""
        if new_colour_change is not None:
            if original_colour_change is None or int(original_colour_change) != int(new_colour_change):
                extras += "!colour_change:" + str(new_colour_change) + "\n"
        if new_first_crack is not None:
            if original_first_crack is None or int(original_first_crack) != int(new_first_crack):
                extras += "!first_crack:" + str(new_first_crack) + "\n"
        if new_roast_end is not None:
            if original_roast_end is None or int(original_roast_end) != int(new_roast_end):
                extras += "!roast_end:" + str(new_roast_end) + "\n"
        return newstring + extras

    def onSave(self, event, specifiedFileName=None, fromMenu=True):
        if fromMenu:
            self.recommendationsAlreadyGiven = []
        if not self.validation(): return 'cancel'
        if specifiedFileName is None:  # which will be true if fired from the menu, but not true if called for other places in the code and a file name is specified
            if self.fileName != "":
                if self.currentRemovableDrive is not None and extractDriveFromPath(
                        self.fileName) == self.currentRemovableDrive:
                    if not self.checkRemovableDriveFilenameApproved(self.fileName):
                        return 'cancel'
            fileName = self.fileName
        else:
            fileName = specifiedFileName
        if fileName == "" or self.importedSuffix is not None:
            return self.onSaveAs(event, fromMenu=False)
        else:
            if self.fileType == "log":
                newstring = self.appendUserEnteredDataToLogData()
            else:
                newstring = dataObjectsToString(self)
                if not self.checkShortNameConflictOk(fileName):
                    return 'cancel'
            try:
                with userOptions.fileCheckingLock:
                    with open(fileName, 'w') as output:
                        self.fileTimeStamp = None  # prevent firing a detected change between writing and closing
                        output.write(newstring.encode('utf8'))
                    self.fileTimeStamp = os.path.getmtime(fileName)
                self.datastring = newstring
                self.modified(False)
                if self.currentRemovableDrive is not None and self.currentRemovableDrive == extractDriveFromPath(
                        fileName):
                    self.removableDriveButton.Disable()
                    backup_utils.start_backup(self, self.currentRemovableDrive, self.options.programDataFolder)
            except IOError as e:
                dial = wx.MessageDialog(None, 'This file could not be saved.\n' + fileName + '\n' + e.strerror + '.',
                                        'Error',
                                        wx.OK | wx.ICON_EXCLAMATION)
                dial.ShowModal()
                return 'cancel'
            self.setProgramTitle()

    def saveIfModified(self, event):
        if self._modified:
            dia = dialogs.saveIfModifiedDialog(self.panel)
            dia.ShowModal()
            if dia.result == 'discard':
                dia.Destroy()
                return True
            if dia.result == 'save':
                dia.Destroy()
                if self.onSave(event, fromMenu=False) == 'cancel':
                    return False
                else:
                    return True
            dia.Destroy()
            return False
        else:  # not modified
            return True

    def checkRemovableDriveFilenameApproved(self, filename):
        if (not self.saveToRemovableDriveIsApproved) and os.path.exists(filename):
            dial = wx.MessageDialog(None, 'The file ' + os.path.basename(filename) + ' exists on ' + volumeDescriptor(
                self.currentRemovableDrive) +
                                    '.\nDo you want to replace it?', 'File exists',
                                    wx.CANCEL | wx.OK | wx.ICON_QUESTION)
            if dial.ShowModal() == wx.ID_CANCEL:
                return False
        return True

    def refreshRemovableDriveInfo(self):
        if len(self.fileName) > 0 and self.importedSuffix is None and self.currentRemovableDrive is not None and \
                extractDriveFromPath(self.fileName) != self.currentRemovableDrive:
            copyMessage = " a copy"
        else:
            copyMessage = ""
        if self.currentRemovableDrive is None:
            self.viewMemstickItem.Enable(False)
            self.ToolBar.EnableTool(self.VIEWMEMSTICK_TOOL_ID, False)
            if self.removableDriveButton is not None:
                self.removableDriveButton.Destroy()
                self.ejectButton.Destroy()
                self.removableDriveButton = None
        else:
            # print "Save" + copyMessage + " to " + volumeDescriptor(self.currentRemovableDrive)
            newLabel = "Save" + copyMessage + " to " + volumeDescriptor(self.currentRemovableDrive)
            if self.removableDriveButton is not None:
                if self.removableDriveButton.GetLabel() == newLabel:
                    return
                self.removableDriveButton.Destroy()
                self.ejectButton.Destroy()
            self.removableDriveButton = wx.Button(self.panel, label=newLabel, pos=(0, 0))
            self.viewMemstickItem.Enable(True)
            self.ToolBar.EnableTool(self.VIEWMEMSTICK_TOOL_ID, True)
            self.ejectButton = wx.BitmapButton(self.panel, id=wx.ID_ANY,
                                               bitmap=wx.Bitmap(self.programPath + "media-eject.bmp",
                                                                wx.BITMAP_TYPE_BMP), pos=(0, 0), style=wx.BU_BOTTOM)
            self.removableDriveButton.Bind(wx.EVT_BUTTON, self.onSaveRemovableDriveButton)
            self.ejectButton.Bind(wx.EVT_BUTTON, self.onEjectButton)
            self.safeToRemoveText.Hide()
            self.onResize(None)

    def onSaveRemovableDriveButton(self, e):
        if self.currentRemovableDrive is None:
            return
        if len(self.fileName) > 0 and self.currentRemovableDrive is not None and \
                extractDriveFromPath(
                    self.fileName) == self.currentRemovableDrive and self.importedSuffix is None:  # removable drive state (file was opened from removable drive)
            self.onSave(e)
            self.savedToUSB = True
        else:
            if self.fileType == "profile":
                folder = self.currentRemovableDrive + USB_KAFFELOGIC_DIR + os.sep + USB_PROFILE_DIR + os.sep
            else:
                folder = self.currentRemovableDrive + USB_KAFFELOGIC_DIR + os.sep + USB_LOG_DIR + os.sep
            if self.ensureFolderExists(folder):
                if self.fileName == "" or self.importedSuffix is not None:  # new state (file has never been saved, even though it might have a name)
                    if self.onSaveAs(e, folder) == 'cancel':
                        return
                    self.savedToUSB = True
                else:  # non-removable drive state (file was opened from internal drive)
                    temporaryFileName = folder + os.path.basename(self.fileName)
                    if not self.checkRemovableDriveFilenameApproved(temporaryFileName):
                        return
                    self.saveToRemovableDriveIsApproved = True
                    temporaryModified = self._modified
                    self.onSave(e, temporaryFileName)
                    self.savedToUSB = True
                    self.modified(temporaryModified, disableRemovableDriveButton=True)

    def persistCheckBoxData(self):
        for key in list(self.checkBoxControls.keys()):
            self.options.setUserOption(key, str(self.checkBoxControls[key].GetValue()))
        if hasattr(self, 'logOptionsControls'):
            allLogOptions = []
            enabledLogOptions = []
            for cntrl in self.logOptionsControls:
                try:
                    allLogOptions.append(cntrl.GetLabel())
                except wx.PyDeadObjectError as e:
                    # After extracting a profile from a log, the controls are all dead objects
                    return
                if cntrl.GetValue():
                    enabledLogOptions.append(cntrl.GetLabel())
            self.options.setUserOption('allLogOptions', ','.join(allLogOptions))
            self.options.setUserOption('enabledLogOptions', ','.join(enabledLogOptions))

    def onClose(self, event):
        self.app.doRaise()
        if event.CanVeto() and not self.saveIfModified(event):
            event.Veto()
            return
        self.persistCheckBoxData()
        userOptions.saveSizeToOptions(self, self.options)
        self.killTimers()
        wx.App.Get().killThreads()
        # self.Destroy()
        event.Skip()
        # the default event handler calls Destroy()

    def killTimers(self):
        utilities.SafeTimer.stopAllTimers()

    def onExtractProfile(self, event, title="Extract"):
        if self.fileType == "profile":
            return
        wx.App.Get().doRaise()
        if self.saveIfModified(event):

            dia = extractProfileDialog(self, title)
            dia.ShowModal()
            modifiedInDialog = dia.modified
            useLogAsComparison = dia.useLogAsComparison
            clearOtherCompares = dia.clearOtherCompares
            if dia.result == 'cancel':
                dia.Destroy()
                return
            dia.Destroy()
            wx.CallAfter(self.finishExtractProfile, modifiedInDialog, useLogAsComparison, clearOtherCompares)

    def finishExtractProfile(self, modifiedInDialog, useLogAsComparison, clearOtherCompares):
        if useLogAsComparison:
            loadCurrentLogAsFirstCompare(self, clearOtherCompares)
        self.fileType = "profile"
        profileFileName = os.path.basename(self.configuration['profile_file_name'])
        self.updateLogPanels()
        self.page1.phasesObject.enableEventEditing()
        self.page3.selectedType = 'point'
        self.page4.selectedType = 'point'
        self.page3.selectedIndex = 0
        self.page4.selectedIndex = 0
        self.page3.resetHistory()
        self.page4.resetHistory()
        self.fileName = profileFileName
        self.importedSuffix = profileFileName.split('.')[-1]
        self.setProgramTitle()
        if self.configuration['emulation_mode'] == EMULATE_SONOFRESCO:
            sonofresco.setLimits(self, self.emulation_mode)
        self.savedToUSB = False
        self.modified(modifiedInDialog)
        self.refreshRemovableDriveInfo()
        self.updateMenu()

    def shortNameAdvice(self, canCancel=True):
        # self.shortName must be initialised before calling this function
        if self.shortName != "" and self.fileType == "profile":
            self.setNotebookPageSelection(2)
            return wx.MessageBox("This profile will load into the roaster as '" + self.shortName +
                                 "'.\n\nEdit the profile short name to change this.",
                                 "FYI", (wx.OK | wx.CANCEL) if canCancel else wx.OK)
        return wx.OK

    def fileNameAdvice(self, fileName, shortName, canCancel=True):
        if shortName != "" or self.fileType != "profile":
            return wx.OK
        loadName = extractShortName(fileName, shortName)
        if loadName != os.path.splitext(os.path.basename(fileName))[0]:
            self.setNotebookPageSelection(2)
            return wx.MessageBox("This profile will load into the roaster as '" + loadName +
                                 "'.\n\nEnter a profile short name to change this.",
                                 "FYI", (wx.OK | wx.CANCEL) if canCancel else wx.OK)
        return wx.OK

    def onSaveAs(self, event, folder="", fromMenu=True):
        if fromMenu:
            self.recommendationsAlreadyGiven = []
        if not self.validation():
            return 'cancel'
        self.shortName = self.page3.configControls["profile_short_name"].GetValue().strip()
        result = self.shortNameAdvice()
        if result == wx.CANCEL:
            return 'cancel'
        if self.importedSuffix is None:
            currentFileName = self.fileName
        else:
            currentFileName = re.sub(r"\." + self.importedSuffix + "$", "", self.fileName, flags=re.I)
        if self.fileType == "profile":
            # must save as a profile, no option to save as a log

            saveFileDialog = myFileDialog(self, "Save As", folder,
                                          os.path.splitext(os.path.basename(currentFileName))[0],
                                          "Kaffelogic profile files (*.kpro)|*.kpro",
                                          wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        else:
            # can save a log as a profile, same as extract profile
            saveFileDialog = myFileDialog(self, "Save As", folder,
                                          os.path.splitext(os.path.basename(currentFileName))[0],
                                          "Kaffelogic logs (*.klog)|*.klog|Kaffelogic profiles (*.kpro)|*.kpro",
                                          wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        result = saveFileDialog.ShowModal()
        if result == wx.ID_CANCEL:
            return 'cancel'
        newFileName = saveFileDialog.GetPath()
        saveFileDialog.Destroy()
        if newFileName != "":
            extract_profile = False
            extension = newFileName.split('.')[-1]
            if self.fileType == "log" and not extension.lower() in ["kpro", "klog"]:
                newFileName += ".klog"
                extension = "klog"
            if self.fileType == "profile" and extension.lower() != "kpro":
                newFileName += ".kpro"
                extension = "kpro"
            original_fileType = self.fileType
            if extension.lower() == "kpro":
                if self.fileType == "log":
                    extract_profile = True
                    if not self.saveIfModified(event):
                        return 'cancel'
                if not self.checkShortNameConflictOk(newFileName):
                    return 'cancel'
                if self.fileNameAdvice(newFileName, self.shortName, canCancel=True) == wx.CANCEL:
                    return 'cancel'
                self.fileType = "profile"
            else:
                self.fileType = "log"
            self.fileName = newFileName
            if self.currentRemovableDrive is not None and extractDriveFromPath(
                    self.fileName) == self.currentRemovableDrive:
                self.saveToRemovableDriveIsApproved = True
            self.importedSuffix = None
            self.onSave(event, fromMenu=False)
            if extract_profile:
                self.updateLogPanels()
                self.page3.resetHistory()
                self.page4.resetHistory()
                self.updateMenu()
                self.shortNameAdvice(False)
            self.refreshRemovableDriveInfo()

    def getComparisonFileNames(self, comparison):
        if comparison is None: return None
        logName = os.path.basename(comparison.fileName)
        profileName = logName
        if "profile_short_name" in list(comparison.configuration.keys()):
            if comparison.configuration["profile_short_name"] != '':
                profileName = comparison.configuration["profile_short_name"]
            else:
                if "profile_file_name" in list(comparison.configuration.keys()):
                    profileName = os.path.basename(comparison.configuration["profile_file_name"])
        return (profileName, logName)

    def comparisonDiffByKey(self, key):
        if self.comparisons is None: return None
        current_raw = None
        if key in list(self.page3.configControls.keys()):
            current_raw = str(self.page3.configControls[key].GetValue())
        if key in list(self.page4.configControls.keys()):
            current_raw = str(self.page4.configControls[key].GetValue())
        if current_raw is None: return None
        current_raw = utilities.trimWhiteSpace(current_raw)
        current = floaty(fromMinSec(current_raw))
        results = []
        atLeastOneDifference = False
        for comparison in self.comparisons:
            if key in list(comparison.configuration.keys()):
                compare_raw = trimTrailingPointZero(
                    utilities.trimWhiteSpace(decodeCtrlV(str(comparison.configuration[key]))))
                if key in comparison.logData.roastEventNames:
                    compare_raw = self.page3.formatEventDataByKey(comparison, key)
                compare = floaty(fromMinSec(compare_raw))
                if current != compare:
                    atLeastOneDifference = True
                profileName, logName = self.getComparisonFileNames(comparison)
                if key in notSavedInProfile:
                    compareFile = logName
                else:
                    compareFile = profileName
                diff = (compare_raw, compareFile)
                if not diff in results: results.append(diff)
        if not atLeastOneDifference: return None
        return {'value': current_raw, 'diffs': results}

    def appendRecommendations(self, key, html):
        recommend = "<p>The value recommended for the current profile is <b>[[recommend]]</b>, although you may want to experiment with nearby values to get even better results."
        if hasattr(self, key + '_recommended_calc'):
            value = getattr(self, key + '_recommended_calc')()[0]
            html += recommend.replace('[[recommend]]',
                                      value)  # we rely on the first element returned in the tuple to be a string version of the value
        diff = self.comparisonDiffByKey(key)
        if diff:
            current = diff['value']
            differences = diff['diffs']
            compares = [x[0] for x in differences]
            bgcolor = '#AAAAAA'
            longest_word = max([len(x) for x in re.split(r'\s', current + ' ' + ' '.join(compares))])
            MAX_WORD = 40  # if longest  word is longer than this then switch format of table
            template_row1 = "<p><table border='0' cellspacing='2' cellpadding='5'><tr><td valign='top' BGCOLOR='" + bgcolor + \
                            "'>This file</td><td valign='top' BGCOLOR='" + bgcolor + "'>[[current]]</td></tr>" \
                if longest_word < MAX_WORD else \
                "<p><table border='0' cellspacing='2' cellpadding='5'><tr><td valign='top' BGCOLOR='" + bgcolor + \
                "'>This file</td></tr><tr><td valign='top' BGCOLOR='" + bgcolor + "'>" + \
                "[[current]]</td></tr>"
            template_add_row = "<tr><td valign='top' BGCOLOR='" + bgcolor + "'>" + \
                               "[[fileName]]</td><td valign='top' BGCOLOR='" + bgcolor + "'>" + \
                               "[[compare]]</td></tr>" \
                if longest_word < MAX_WORD else \
                "<tr><td valign='top' BGCOLOR='" + bgcolor + "'>[[fileName]]</td></tr><tr><td valign='top' BGCOLOR='" + bgcolor + "'>" + \
                "[[compare]]</td></tr>"
            row1 = template_row1.replace('[[current]]', "blank" if current == "" else current.replace('\n', '<br>'))
            add_rows = []
            for d in differences:
                compare, fileName = d
                row = template_add_row.replace('[[fileName]]', fileName).replace('[[compare]]',
                                                                                 "blank" if compare == "" else compare.replace(
                                                                                     '\n', '<br>'))
                add_rows.append(row)
            html += row1 + ''.join(add_rows) + "</table>"
        return html

    def preheat_power_recommended_calc(self):
        temp_profile = self.page1.pointsAsGraphed
        fan_profile = self.page2.pointsAsGraphed
        temperature_at_0 = temp_profile[0][1]
        for i in range(len(temp_profile)):
            if temp_profile[i][0] >= 60.0:
                temperature_at_60 = temp_profile[i][1]
                break
        for i in range(len(fan_profile)):
            if fan_profile[i][0] >= 60.0:
                fan_at_60 = fan_profile[i][1]
                break
        expected_preheat_power = temperature.convertSpecifiedUnitToCelcius(temperature_at_60 - temperature_at_0, delta=True, rounding=None) * 12.0 * (fan_at_60 / 1470.0)
        expected_preheat_power_str = str(int(round(expected_preheat_power / 10.0) * 10))
        preheat_power_str = self.page4.configControls['preheat_power'].GetValue()
        try:
            preheat_power = float(preheat_power_str)
            ratio = preheat_power / expected_preheat_power
        except:
            preheat_power = 0
            ratio = 1.0
        return (
            expected_preheat_power_str,
            expected_preheat_power,
            preheat_power_str,
            preheat_power,
            ratio,
            temperature_at_0,
            temperature_at_60,
            fan_at_60
        )

    def unusable_levels_validation(self):
        """
        Unusable levels recommendation
        """
        if 'unusable_levels' in self.recommendationsAlreadyGiven or (
                self.fileName != '' and self.options.getUserOption(
            'supress_recommendation_unusable_levels') == os.path.basename(self.fileName)
        ):
            return True

        max_temperature = round(maximumY(self.page1.pointsAsGraphed), 1)
        max_level = levelFromTemperature(max_temperature, self.page4.configControls["roast_levels"].GetValue())
        max_level_desired = self.emulation_mode.level_max_val
        if max_level >= max_level_desired:
            return True
        else:
            message = "<h3>Some roast levels are not defined</h3>"
            message += "<p>The maximum temperature of the current profile is " + str(
                int(round(max_temperature, 0))) + \
                       temperature.insertTemperatureUnit("°, equivalent to level ") + \
                       str(max_level) + ".</p>"
            message += "This means that roasts between level <b>" + str(max_level) + "</b> and <b>" + str(
                max_level_desired) + "</b> will not terminate at a predictable time. They may run for up to " + str(
                int(ROAST_ABSOLUTE_MAX / 60)) + " mins and then time out.</p>"
            message += "<p>This is acceptable if you do not intend using this profile for roasts above level " + str(
                max_level) + ". "
            message += "In that case it is best to mention in the profile description that the profile is not intended for levels above " + str(
                max_level) + ".</p>"
            message += "<p>If you are designing this profile for general use "
            message += "you may wish to ensure that all roast levels are defined. Either reduce the temperatures for the roast levels "
            message += "(on the 'Profile settings' tab at Expert or Engineer difficulty level) "
            message += "to match appropriate points on the profile curve, or increase the slope of the profile curve towards the end of the roast.</p>"

        dialog = dialogs.enhancedMessageDialog(self)
        if self.fileName == '' or self.importedSuffix is not None:
            checkBox = None
            checkBoxText = ''
        else:
            checkBox = False
            checkBoxText = "don't show this recommendation again for " + os.path.basename(self.fileName)
        middleButtonText = None
        dialog.init(message, "Recommendation", "Save anyway", True, middleButtonText=middleButtonText,
                    checkBox=checkBox, checkBoxText=checkBoxText)
        dialog.ShowModal()
        result = dialog.result
        checked = dialog.getCheckBox()
        dialog.Destroy()
        if result in [wx.ID_OK, wx.ID_APPLY]:
            if checked:
                self.options.setUserOption('supress_recommendation_unusable_levels', os.path.basename(self.fileName))
            self.recommendationsAlreadyGiven.append('unusable_levels')
            return True
        return False

    def preheat_power_validation(self):
        """
        Preheat power validation recommendation
        """
        if 'preheat_power' in self.recommendationsAlreadyGiven or (
                self.fileName != '' and self.options.getUserOption(
            'supress_recommendation_preheat_power') == os.path.basename(self.fileName)
        ):
            return True
        expected_preheat_power_str, \
        expected_preheat_power, \
        preheat_power_str, \
        preheat_power, \
        ratio, \
        temperature_at_0, \
        temperature_at_60, \
        fan_at_60 = self.preheat_power_recommended_calc()
        unrealistic = expected_preheat_power > MAX_POWER_AVAILABLE or preheat_power > MAX_POWER_AVAILABLE
        reality_statement = "The " + MODEL_NAME + " is capable of delivering a maximum power of about " + str(
            MAX_POWER_AVAILABLE) + \
                            " watts (depending on supply voltage)."
        if expected_preheat_power > MAX_POWER_AVAILABLE:
            reality_statement += ' <font color="red">This means your profile curve is unrealistically steep.</font> '
        if preheat_power > MAX_POWER_AVAILABLE:
            reality_statement += ' <font color="red">This means your preheat power setting is unrealistic.</font> '
        reality_statement += "It is better to allow for some variation in supply voltage, and use a profile curve with a recommended preheat power of less than 1200&nbsp;watts."

        warn = ratio > 1.25 or ratio < 0.85
        severe = ratio > 1.5 or ratio < 0.7
        if not warn: return True
        severe_message = ''
        if severe:
            if ratio > 1.0:
                severe_message = "Heat too fast"
            else:
                severe_message = "Heat too slow"
        message = "Preheat power is currently set at <b>" + preheat_power_str + "</b>&nbsp;watts. " + \
                  "The recommended setting for this profile curve is <b>" + expected_preheat_power_str + "</b>&nbsp;watts." + \
                  (("</p><p>" + reality_statement) if unrealistic else '') + \
                  "<hr><b>Explanation</b></p><p>" + \
                  "Preheat power governs the roast for the first 30 to 60&nbsp;seconds. After that the PID control system has enough data to " + \
                  "take over and start following the profile curve. This means if you want the roast to follow the curve from the very start " + \
                  "you need to adjust the preheat power to match the initial slope of the curve.</p>" + \
                  "<p>The current setting of " + preheat_power_str + " is " + (
                      "almost certainly" if severe else "probably") + \
                  " too " + ("high" if ratio > 1.0 else "low") + " for this curve." + \
                  (" It also makes it likely that you will get '" + severe_message + "' errors. " if severe else '') + \
                  "<p>The recommended preheat power setting of " + expected_preheat_power_str + "&nbsp;watts is based on a temperature rise of " + str(
            int(temperature_at_60 - temperature_at_0)) + \
                  temperature.insertTemperatureUnit("° during the first minute with a typical load of 120g and a fan speed of ") + str(
            int(round(fan_at_60) * 10)) + \
                  "&nbsp;RPM. " + \
                  ("You may need to collect logs and fine tune " + \
                   "for smaller load sizes or for high precision curve following." if expected_preheat_power <= MAX_POWER_AVAILABLE else "") + \
                  "</p>"""
        dialog = dialogs.enhancedMessageDialog(self)
        if self.fileName == '' or self.importedSuffix is not None:
            checkBox = None
            checkBoxText = ''
        else:
            checkBox = False
            checkBoxText = "don't show this recommendation again for " + os.path.basename(self.fileName)
        middleButtonText = "Apply recommendation" if (not unrealistic) or (
                    expected_preheat_power < MAX_POWER_AVAILABLE) else None
        dialog.init(message, "Recommendation", "Save anyway", True, middleButtonText=middleButtonText,
                    checkBox=checkBox, checkBoxText=checkBoxText)
        dialog.ShowModal()
        result = dialog.result
        checked = dialog.getCheckBox()
        dialog.Destroy()
        if result == wx.ID_APPLY:
            control = self.page4.configControls['preheat_power']
            control.SetValue(expected_preheat_power_str)
            self.modified(True)
            self.captureHistory(self.page4, 'focus', item=control, isFocusEvent=True)
            self.page4.focusObject = control
            self.captureHistory(self.page4, 'text', item=control)
        if result in [wx.ID_OK, wx.ID_APPLY]:
            if checked:
                self.options.setUserOption('supress_recommendation_preheat_power', os.path.basename(self.fileName))
            self.recommendationsAlreadyGiven.append('preheat_power')
            return True
        return False

    def roast_min_desired_rate_of_rise_recommended_calc(self):
        self.REJOIN_DIFFERENTIAL = 1.0  # recommend the setting is below the minumum curve slope by this amount
        profile_gradients = self.page1.gradientsAsGraphed
        min_profile_curve_gradient_point = sorted(profile_gradients, key=operator.itemgetter(1, 0))[0]
        min_profile_curve_gradient = min_profile_curve_gradient_point[1]
        roast_min_desired_rate_of_rise_str = self.page4.configControls['roast_min_desired_rate_of_rise'].GetValue()
        try:
            roast_min_desired_rate_of_rise = float(roast_min_desired_rate_of_rise_str)
        except:
            roast_min_desired_rate_of_rise = 0
        recommended = min_profile_curve_gradient - temperature.convertCelciusToSpecifiedUnit(self.REJOIN_DIFFERENTIAL, rounding=None, delta=True)
        if recommended < 0.0:
            lowest_acceptable = recommended - 0.05
        else:
            lowest_acceptable = 0.0
        recommended_str = str(round(recommended, 1))
        lowest_acceptable_str = str(round(lowest_acceptable, 1))
        return (
            recommended_str,
            recommended,
            lowest_acceptable_str,
            lowest_acceptable,
            roast_min_desired_rate_of_rise_str,
            roast_min_desired_rate_of_rise,
            min_profile_curve_gradient,
            min_profile_curve_gradient_point
        )

    def roast_min_desired_rate_of_rise_validation(self):
        """
        Roast min desired rate of rise validation recommendation
        """
        if 'roast_min_desired_rate_of_rise' in self.recommendationsAlreadyGiven or (
                self.fileName != '' and self.options.getUserOption(
                'supress_recommendation_min_rate_of_rise') == os.path.basename(self.fileName)):
            return True
        recommended_str, \
        recommended, \
        lowest_acceptable_str, \
        lowest_acceptable, \
        roast_min_desired_rate_of_rise_str, \
        roast_min_desired_rate_of_rise, \
        min_profile_curve_gradient, \
        min_profile_curve_gradient_point = self.roast_min_desired_rate_of_rise_recommended_calc()
        small_amount = temperature.convertCelciusToSpecifiedUnit(0.05, rounding=None, delta=True)
        if roast_min_desired_rate_of_rise <= recommended + small_amount and roast_min_desired_rate_of_rise >= lowest_acceptable:
            return True
        message = "<i>Roast min desired rate of rise</i> is currently set at <b>" + roast_min_desired_rate_of_rise_str + \
                  temperature.insertTemperatureUnit("</b>°/min. ") + \
                  "The recommended setting for this profile curve is " + "<b>" + recommended_str + "</b>."
        if min_profile_curve_gradient < -small_amount:
            message += "</p><p>The profile curve has negative rate of rise in some places. This is not usually desirable. " + \
                       '<font color="red">Further editing of the roast profile curve is recommended.</font>'
        message += "<hr><b>Explanation:</b></p><p>"
        if min_profile_curve_gradient >= -small_amount and roast_min_desired_rate_of_rise > min_profile_curve_gradient:  # A1
            message += "The current setting is steeper than the profile curve in some places. In those places the roast will not follow the curve, " + \
                       "instead it will follow the roast min desired rate of rise setting. The profile curve goes as low as " + \
                       str(round(min_profile_curve_gradient, 1)) + temperature.insertTemperatureUnit("°/min at time ") + \
                       toMinSec(min_profile_curve_gradient_point[0]) + ".</p>" + \
                       "<p>We recommend lowering the <i>roast min desired rate of rise</i> setting to " + recommended_str + " or lower.</p>"
        if min_profile_curve_gradient >= -small_amount and roast_min_desired_rate_of_rise <= min_profile_curve_gradient \
                and roast_min_desired_rate_of_rise > min_profile_curve_gradient - temperature.convertCelciusToSpecifiedUnit(self.REJOIN_DIFFERENTIAL + 0.05, rounding=None, delta=True):  # A2 B2
            message += "The current setting is close to the profile curve rate of rise in some places. In those places the roast may not follow the curve, " + \
                       "instead minor fluctuations may cause it to drift above the curve. The profile curve goes as low as " + \
                       str(round(min_profile_curve_gradient, 1)) + temperature.insertTemperatureUnit("°/min at time ") + \
                       toMinSec(min_profile_curve_gradient_point[0]) + ".</p>" + \
                       "<p>We recommend lowering the <i>roast min desired rate of rise</i> setting to " + recommended_str + " or lower.</p>"
        if min_profile_curve_gradient >= temperature.convertCelciusToSpecifiedUnit(self.REJOIN_DIFFERENTIAL, rounding=None, delta=True) and roast_min_desired_rate_of_rise < lowest_acceptable:  # A4
            message += "<p>A negative setting may permit the rate of rise to be negative when the control system is trying to get the roast back on the profile curve, " + \
                       "something that is not usually desirable. " + \
                       "The profile curve rate of rise does not go below " + \
                       str(round(min_profile_curve_gradient,
                                 1)) + temperature.insertTemperatureUnit("°/min so a negative setting is unlikely to be necessary.</p>") + \
                       "<p>We recommend increasing the <i>roast min desired rate of rise</i> setting to between zero and " + recommended_str + ".</p>"
        if min_profile_curve_gradient >= -small_amount and roast_min_desired_rate_of_rise > lowest_acceptable and \
                roast_min_desired_rate_of_rise < min_profile_curve_gradient - self.REJOIN_DIFFERENTIAL and min_profile_curve_gradient < self.REJOIN_DIFFERENTIAL:  # B1 B2 B3
            message += "<p>The profile curve rate of rise goes as low as " + \
                       str(round(min_profile_curve_gradient, 1)) + temperature.insertTemperatureUnit("°/min at time ") + \
                       toMinSec(min_profile_curve_gradient_point[0]) + ".</p>" + \
                       "<p>A setting of zero or lower may be necessary to allow the system to follow such a flat curve.</p>"
        if min_profile_curve_gradient >= -small_amount and \
                min_profile_curve_gradient < temperature.convertCelciusToSpecifiedUnit(self.REJOIN_DIFFERENTIAL, rounding=None, delta=True) and \
                roast_min_desired_rate_of_rise < lowest_acceptable:  # B4
            message += "<p>If the setting is too low it may permit the rate of rise to be unduly negative when the control system is trying to get the roast back on the profile curve, " + \
                       "something that is not usually desirable. " + \
                       "The profile curve rate of rise does not go below " + \
                       str(round(min_profile_curve_gradient,
                                 1)) + temperature.insertTemperatureUnit("°/min so such a low setting is unlikely to be necessary.</p>") + \
                       "<p>We recommend increasing the <i>roast min desired rate of rise</i> setting to " + recommended_str + ".</p>"
        if min_profile_curve_gradient < -small_amount and roast_min_desired_rate_of_rise > min_profile_curve_gradient:  # C1
            message += "<p>The profile curve rate of rise goes as low as " + \
                       str(round(min_profile_curve_gradient, 1)) + temperature.insertTemperatureUnit("°/min at time ") + \
                       toMinSec(min_profile_curve_gradient_point[0]) + ".</p>" + \
                       "<p>The roast will not follow the curve where the <i>roast min desired rate of rise</i> setting exceeds the " + \
                       "slope of the profile curve.</p>"
        if min_profile_curve_gradient < -small_amount and roast_min_desired_rate_of_rise <= min_profile_curve_gradient:  # C2 C3
            message += "<p>The profile curve rate of rise goes as low as " + \
                       str(round(min_profile_curve_gradient, 1)) + temperature.insertTemperatureUnit("°/min at time ") + \
                       toMinSec(min_profile_curve_gradient_point[0]) + ".</p>"
        dialog = dialogs.enhancedMessageDialog(self)
        if self.fileName == '' or self.importedSuffix is not None:
            checkBox = None
            checkBoxText = ''
        else:
            checkBox = False
            checkBoxText = "don't show this recommendation again for " + os.path.basename(self.fileName)
        middleButtonText = "Apply recommendation" if recommended_str is not None else None
        dialog.init(message, "Recommendation", "Save anyway", True, middleButtonText=middleButtonText,
                    checkBox=checkBox, checkBoxText=checkBoxText)
        dialog.ShowModal()
        result = dialog.result
        checked = dialog.getCheckBox()
        dialog.Destroy()
        if result == wx.ID_APPLY:
            control = self.page4.configControls['roast_min_desired_rate_of_rise']
            control.SetValue(recommended_str)
            self.modified(True)
            self.captureHistory(self.page4, 'focus', item=control, isFocusEvent=True)
            self.page4.focusObject = control
            self.captureHistory(self.page4, 'text', item=control)
        if result in [wx.ID_OK, wx.ID_APPLY]:
            if checked:
                self.options.setUserOption('supress_recommendation_min_rate_of_rise', os.path.basename(self.fileName))
            self.recommendationsAlreadyGiven.append('roast_min_desired_rate_of_rise')
            return True
        return False

    def validate_individual_Points(self, page, page_select, points, min_time_interval, curve_name):
        for i in range(len(points) - 1):
            difference = round(points[i + 1].point.x, 1) - round(points[i].point.x, 1)
            if difference < min_time_interval:
                self.setNotebookPageSelection(page_select)
                page.selectedIndex = i
                page.selectedType = 'point'
                page.setSpinners()
                page.reDraw()
                if difference < 0:
                    wx.MessageBox("The " + curve_name + " curve must not turn back on itself.",
                                  "Warning", wx.OK)
                else:
                    wx.MessageBox("All " + curve_name + " points must be separated by a minimum of " + str(
                        self.emulation_mode.profile_min_time_interval) + " seconds.",
                                  "Warning", wx.OK)
                return False

        for i in range(len(points)):
            leftDiff = points[i].point.x - points[i].leftControl.x + 0.01
            rightDiff = points[i].rightControl.x - points[i].point.x + 0.01
            message = False
            if points[i].leftControl.toTuple() != (0.0, 0.0) and leftDiff < (
            LAST_CONTROL_POINT_THRESHOLD if i == len(points) - 1 else AVOID_INFINITE_GRADIENT_THRESHOLD):
                message = True
                page.selectedType = 'leftControl'
                # print 'left invalid', leftDiff, 'with left control x =', points[i].leftControl.x, 'and point x =', points[i].point.x, leftDiff < AVOID_INFINITE_GRADIENT_THRESHOLD
            if points[i].rightControl.toTuple() != (0.0, 0.0) and rightDiff < AVOID_INFINITE_GRADIENT_THRESHOLD:
                message = True
                page.selectedType = 'rightControl'
                # print 'right invalid', rightDiff, 'with right control x =', points[i].rightControl.x, 'and point x =', points[i].point.x, rightDiff < AVOID_INFINITE_GRADIENT_THRESHOLD
            if message:
                self.setNotebookPageSelection(page_select)
                page.selectedIndex = i
                page.setSpinners()
                page.reDraw()
                wx.MessageBox(
                    "The selected yellow control point needs to be moved further away from its " + curve_name + " point, or use smooth point tool.",
                    "Warning", wx.OK)
                return False
        return True

    def validate_zones(self):
        for zone in range(1, NUMBER_OF_ZONES + 1):
            start = 'zone' + str(zone) + '_time_start'
            end = 'zone' + str(zone) + '_time_end'
            start_string = self.page4.configControls[start].GetValue()
            end_string = self.page4.configControls[end].GetValue()
            try:
                start_time = float(fromMinSec(start_string))
                end_time = float(fromMinSec(end_string))
            except:
                return True  # will fail validation later on, so it passes here
            if end_time < start_time:
                self.setNotebookPageSelection(3)
                self.page4.configControls[end].SetFocus()
                wx.MessageBox("'" + end + "' must be after '" + start + "'",
                              "Warning", wx.OK)
                return False
        return True

    def validation(self, exporting=False):
        if self.fileType == "log": return True
        if not self.preheat_power_validation(): return False
        if not self.roast_min_desired_rate_of_rise_validation(): return False

        for config in self.page4.configList:
            if config not in nonNumericData:
                if config in timeInMinSec:
                    invalid_time = False
                    time_string = self.page4.configControls[config].GetValue()
                    try:
                        float(fromMinSec(time_string))
                    except:
                        invalid_time = True
                    if ':' not in time_string:
                        invalid_time = True
                    if invalid_time:
                        self.setNotebookPageSelection(3)
                        self.page4.configControls[config].SetFocus()
                        wx.MessageBox("'" + config + "' must be min:sec",
                                      "Warning", wx.OK)
                        return False
                else:
                    try:
                        float(self.page4.configControls[config].GetValue())
                    except:
                        self.setNotebookPageSelection(3)
                        self.page4.configControls[config].SetFocus()
                        wx.MessageBox("'" + config + "' must be a number.",
                                      "Warning", wx.OK)
                        return False

        for config in list(self.page1.configControls.keys()):
            val = self.page1.configControls[config].GetValue()
            if val != '':
                try:
                    float(val)
                except:
                    self.setNotebookPageSelection(0)
                    self.page1.configControls[config].SetFocus()
                    wx.MessageBox("'" + self.page1.configControls[config].GetName() + "' must be a number.",
                                  "Warning", wx.OK)
                    return False

        val = float(self.page4.configControls['roast_end_by_time_ratio'].GetValue())
        if val < 0.0 or val > 1.0:
            self.setNotebookPageSelection(3)
            self.page4.configControls['roast_end_by_time_ratio'].SetFocus()
            wx.MessageBox("'roast end by time ratio' must be between 0.0 and 1.0.",
                          "Warning", wx.OK)
            return False

        if not self.validate_zones(): return False
        if not validate_levels(self, self.page4.configControls["roast_levels"].GetValue()): return False
        if not self.unusable_levels_validation(): return False

        points = self.page2.profilePoints
        if len(points) < FAN_POINTS_SAVE_MIN:
            self.setNotebookPageSelection(1)
            wx.MessageBox("The fan curve must contain a minimum of " + str(FAN_POINTS_SAVE_MIN) + " points.",
                          "Warning", wx.OK)
            return False

        max_fan_speed = maximumY(self.page2.pointsAsGraphed) / FAN_PROFILE_YSCALE
        min_fan_speed = minimumY(self.page2.pointsAsGraphed) / FAN_PROFILE_YSCALE
        if max_fan_speed > MAX_FAN_RPM:
            self.setNotebookPageSelection(1)
            wx.MessageBox("The fan curve goes up to " + str(int(
                max_fan_speed)) + " RPM. That's more than the top speed of the fan motor which cannot go over " + str(
                MAX_FAN_RPM) + " RPM.",
                          "Warning", wx.OK)
            return False
        if min_fan_speed < MIN_FAN_RPM:
            self.setNotebookPageSelection(1)
            wx.MessageBox("The fan curve goes down to " + str(int(
                min_fan_speed)) + " RPM. That's way too slow for bean circulation. It must always be at least " + str(
                MIN_FAN_RPM) + " RPM.",
                          "Warning", wx.OK)
            return False

        points = self.page1.profilePoints
        if len(points) < self.emulation_mode.profile_points_save_min:
            self.setNotebookPageSelection(0)
            wx.MessageBox("The profile curve must contain a minimum of " + str(
                self.emulation_mode.profile_points_save_min) + " points.",
                          "Warning", wx.OK)
            return False

        if not self.validate_individual_Points(self.page1, 0, self.page1.profilePoints,
                                               self.emulation_mode.profile_min_time_interval, "profile"): return False
        if not self.validate_individual_Points(self.page2, 1, self.page2.profilePoints, 1.0,
                                               "fan profile"): return False

        if exporting:
            # Custom verification should apply only when exporting - in Kaffelogic profiles anything goes.
            if self.emulation_mode.profile_custom_verify_fn is not None:
                if self.emulation_mode.profile_custom_verify_fn(self, self.page1.profilePoints) == False:
                    return False

        else:
            designerName = self.page3.configControls["profile_designer"].GetValue()
            if len(str(designerName).encode('utf-8')) > 31:
                designerName = truncateUTF8stringTo(designerName, 31)
                wx.MessageBox("Profile designer name has been shortened to fit. It will be saved as " + designerName,
                              "Warning", wx.OK)
                self.page3.configControls["profile_designer"].SetValue(designerName)
                # information only so do not return a value here

            shortName = self.page3.configControls["profile_short_name"].GetValue().strip()
            if shortName.encode('ascii', 'ignore') != shortName:
                self.setNotebookPageSelection(2)
                self.page3.configControls["profile_short_name"].SetFocus()
                wx.MessageBox("Short name may not contain " + ''.join([c for c in shortName if
                                                                       c not in shortName.encode('ascii',
                                                                                                 'ignore')]) + ". (Please use ASCII only.)",
                              "Warning", wx.OK)
                return False

        return True


# ----------------------------------------------------------------------
def validate_levels(self, levels):
    if self.fileType == "log": return True
    if re.search(self.emulation_mode.levels_pattern, levels) is None:
        self.setNotebookPageSelection(3)
        self.page4.configControls["roast_levels"].SetFocus()
        wx.MessageBox(
            "Roast levels must be a set of " + str(self.emulation_mode.levels_count) + " numbers, separated by commas.",
            "Warning", wx.OK)
        return False
    levels = [float(L) for L in levels.split(",")]
    for i in range(len(levels) - 1):
        if levels[i] > levels[i + 1]:
            self.setNotebookPageSelection(3)
            self.page4.configControls["roast_levels"].SetFocus()
            wx.MessageBox("Roast levels must be increasing temperatures.",
                          "Warning", wx.OK)
            return False
        min_sep = temperature.convertCelciusToSpecifiedUnit(self.emulation_mode.levels_min_separation,
                                                    self.temperature_unit, delta=True)
        if levels[i + 1] - levels[i] < min_sep:
            self.setNotebookPageSelection(3)
            self.page4.configControls["roast_levels"].SetFocus()
            wx.MessageBox("Roast levels must be separated by a minimum of " + str(
                min_sep) + temperature.insertTemperatureUnit("°."),
                          "Warning", wx.OK)
            return False
    min_temp = temperature.convertCelciusToSpecifiedUnit(self.emulation_mode.levels_min_temperature, self.temperature_unit)
    max_temp = temperature.convertCelciusToSpecifiedUnit(self.emulation_mode.levels_max_temperature, self.temperature_unit)
    if levels[0] < min_temp:
        self.setNotebookPageSelection(3)
        self.page4.configControls["roast_levels"].SetFocus()
        wx.MessageBox(
            "Roast levels must all be higher than " + str(min_temp) +
            temperature.insertTemperatureUnit("°."),
            "Warning", wx.OK)
        return False
    if levels[-1] > max_temp:
        self.setNotebookPageSelection(3)
        self.page4.configControls["roast_levels"].SetFocus()
        wx.MessageBox(
            "Roast levels must all be lower than " + str(max_temp) +
            temperature.insertTemperatureUnit("°."),
            "Warning", wx.OK)
        return False
    return True


# ----------------------------------------------------------------------
wxExcepthook = sys.excepthook
import traceback


def MyExceptionHook(etype, value, trace):
    """
    Handler for all unhandled exceptions.

    :param `etype`: the exception type (`SyntaxError`, `ZeroDivisionError`, etc...);
    :type `etype`: `Exception`
    :param string `value`: the exception error message;
    :param string `trace`: the traceback header, if any (otherwise, it prints the
     standard Python header: ``Traceback (most recent call last)``.
    """
    tmp = [str(etype), str(value), "<br>".join(traceback.format_exception(etype, value, trace))]
    exception = "<b>An error has occurred</b><br><br>" + "<br>".join(
        tmp) + "<br><br>" + "(Version " + PROGRAM_VERSION + " on " + fullPlatform() + ")<br><br><i>Please advise support@kaffelogic.com</i>"
    message = dialogs.enhancedMessageDialog(wx.App.Get().frame)
    message.init(exception, "Please advise support@kaffelogic.com")
    message.ShowModal()
    message.Destroy()
    wxExcepthook(etype, value, trace)


