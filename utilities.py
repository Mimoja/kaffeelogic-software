import sys, os, re, math, platform, wx, instances

def getProgramPath():
    BACKSLASH = r"\ "[0]  # PyCharm won't accept backslash as last character in string literal, even if it is valid Python
    if len(sys.argv) >= 1 and re.search(BACKSLASH + os.sep, sys.argv[0]) is not None:
        programPath = re.sub(BACKSLASH + os.sep + "[^" + BACKSLASH + os.sep + "]*$", "", sys.argv[0]) + os.sep
    else:
        programPath = ""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # 'running in pyinstaller bundle'
        programPath = sys._MEIPASS + os.sep
    return programPath

def makeColour(x):
    if isinstance(x, wx.Colour):
        return x
    else:
        return wx.ColourDatabase().Find(x)

def setLightness(colr, lightness):
    colr = makeColour(colr)
    asDict = {'r': colr.Red(), 'g': colr.Green(), 'b':colr.Blue(), 'a':colr.Alpha()}
    maxVal = max(colr.Get(includeAlpha=False))
    minVal = min(colr.Get(includeAlpha=False))
    midVal = None
    if maxVal == minVal:
        val = int((255.0 - maxVal) * (lightness / 255.0) + maxVal)
        return wx.Colour(val, val, val, colr.Alpha())
    maxCount = 0
    minCount = 0
    maxList = []
    minList = []
    midList = []
    for label in ['r','g','b']:
        if asDict[label] == maxVal:
            maxCount += 1
            maxList.append(label)
        elif asDict[label] == minVal:
            minCount += 1
            minList.append(label)
        else:
            midList.append(label)
            midVal = asDict[label]
    if midVal is not None:
        midRatio = float(midVal - minVal) / float(maxVal - minVal)
        base = maxVal / 255.0 * lightness
        mid = (maxVal - base) * midRatio + base
        asDict[midList[0]] = mid
        asDict[minList[0]] = base
        # print "midRatio, base, mid", midRatio, base, mid
    else:
        base = (maxVal - minVal) / 255.0 * lightness + minVal
        for label in minList:
            asDict[label] = base
    # print asDict
    return wx.Colour(asDict['r'], asDict['g'], asDict['b'], asDict['a'])

class SafeTimer(wx.Timer, instances.InstancesCollector):
    """
    Apparently in wxPython it's good practice to stop timers before exiting an app.
    Also, in python2 we can't always rely on super() to traverse all meta classes, so we explicitly call both meta class init functions.
    """
    def __init__(self, *args, **kwargs):
        instances.InstancesCollector.__init__(self)
        wx.Timer.__init__(self, *args, **kwargs)
        # print ("init SafeTimer", self)

    @staticmethod
    def stopAllTimers():
        for timer in instances.instancesOf(SafeTimer):
            timer.Stop()
            # print ("Stopping", timer)

def addToFrontOfList(item, l, limit=None):
    item = ensureUnicode(item)
    if item in l: l.remove(item)
    l.insert(0, item)
    if limit is not None:
        del l[limit:]

def addToFrontOfComparisonsList(item, comparisons):
    item.fileName = ensureUnicode(item.fileName)
    fileNameList = [c.fileName for c in comparisons]
    if item.fileName in fileNameList:
        del comparisons[fileNameList.index(item.fileName)]
    comparisons.insert(0, item)

def addTuple(a,b):
    return (a[0] + b[0], a[1] + b[1])

def encodeCtrlV(s):
    """ we use \v to indicate a line break, because the file format does not support multi-line data """
    return re.sub(r"\r\n|\r|\n", r"\\v", s)

def decodeCtrlV(s):
    return re.sub(r"\\v", r"\n", s)

def ensureUnicode(s):
    try:
        s = s.decode('utf-8')
    except UnicodeEncodeError:
        pass
    return s
    
def replaceUnderscoreWithSpace(s):
    return re.sub(r"_", r" ", s)

def replaceSpaceWithUnderscore(s):
    return re.sub(r" ", r"_", s)
    
def truncateUTF8stringTo(s, limit):
    s = str(s)
    while len(s.encode('utf-8')) > limit:
        s = s[:-1]
    return s

def trimTrailingPointZero(s):
    return re.sub(r"\.0$", "", s)

def trimWhiteSpace(s):
    return re.sub(r"^(\s|\\v)*", "", re.sub(r"(\s|\\v)*$", "", s))

def allNotNone(ls):
    for x in ls:
        if x is None: return False
    return True

def toMinSec(f, leadingZero = False, wholeSecs = True):
    try:
        f = round(float(f),5)
    except:
        return str(f)
    m, s = divmod(f, 60)
    if m < 0 and s != 0:
        m += 1
        s -= 60
    if not wholeSecs: s = f - m * 60
    negative = True if m < 0 or s < 0 else False
    m = abs(m)
    s = math.fabs(s)
    separator = ':'
    if s < 10: separator += '0'
    leadingChar = ''
    if leadingZero and m < 10: leadingChar = '0'
    return ('-' if negative else '') + leadingChar + str(int(m)) + separator + (str(int(s)) if wholeSecs else str(float(s)))

def fromMinSec(s):
    try:
        l = s.split(':')
        if len(l) ==2:
            negative = -1 if l[0][0] == '-' else 1
            mins = abs(int(l[0]))
            secs = math.fabs(float(l[1]))
            return negative * (mins * 60 + secs)
        return float(s)
    except:
        return s

def getYfromX(points, x):
    y = None
    for p in points:
        y = p[1]
        if p[0] >= x: break
    return y

def sumY(points):
    tot = 0
    for p in points:
        tot += p[1]
    return tot

def filterPointsX(points, allowed_range):
    # filters on X-range only
    return [p for p in points if p[0] < allowed_range[1] and p[0] > allowed_range[0]]


def filterPointsY(points, allowed_range):
    # filters on Y-range only
    return [p for p in points if p[1] < allowed_range[1] and p[1] > allowed_range[0]]


def shiftPointsY(points, distance):
    # filters on Y-range only
    return [(p[0], p[1] + distance) for p in points]


def maximumY(list):
    max = -99999
    for pointTuple in list:
        if pointTuple[1] > max:
            max = pointTuple[1]
    return max

def maximumYmode(lis, modeFraction):
    lis = sorted([x[1] for x in lis])
    pos = int(len(lis) * modeFraction)
    if pos < 0: pos = 0
    if pos > len(lis) - 1: pos = len(lis) - 1
    return lis[pos]
    
def maximumX(list):
    max = -99999
    for pointTuple in list:
        if pointTuple[0] > max:
            max = pointTuple[0]
    return max

def minimumY(list):
    min = 99999
    for pointTuple in list:
        if pointTuple[1] < min:
            min = pointTuple[1]
    return min

def minimumX(list):
    min = 99999
    for pointTuple in list:
        if pointTuple[0] < min:
            min = pointTuple[0]
    return min

def extremaOfAllPoints(profilePoints):
    minXval = minYval = float('inf')
    maxXval = maxYval = float('-inf')
    for p in profilePoints:
        minx = min(p.point.x, p.leftControl.x, p.rightControl.x)
        maxx = max(p.point.x, p.leftControl.x, p.rightControl.x)
        miny = min(p.point.y, p.leftControl.y, p.rightControl.y)
        maxy = max(p.point.y, p.leftControl.y, p.rightControl.y)
        if minx < minXval:
            minXval = minx
        if maxx > maxXval:
            maxXval = maxx
        if miny < minYval:
            minYval = miny
        if maxy > maxYval:
            maxYval = maxy
    return minXval, maxXval, minYval, maxYval

def extrema(tuplePoints):
    maxX = maxY = float('-inf')
    minX = minY = float('inf')
    for pointTuple in tuplePoints:
        x, y = pointTuple
        if y > maxY:
            maxY = y
        if y < minY:
            minY = y
        if x > maxX:
            maxX = x
        if x < minX:
            minX = x
    return minX, maxX, minY, maxY

def floaty(x):
    try:
        return float(x)
    except:
        return x

def floatOrNone(x):
    try:
        return float(x)
    except:
        return None

def floatOrZero(x):
    try:
        return float(x)
    except:
        return 0.0

def isFloat(x):
    return floatOrNone(x) is not None

def filterNumeric(string):
    return "".join([x for x in string if x in "0123456789."])

def cleanLineEnds(s):
    s = re.sub('\\r\\n', '\r', s)
    s = re.sub('\\n\\r', '\r', s)
    s = re.sub('\\n', '\r', s)
    return s

def clean(s):
    s = re.sub('\\t', ',', s)
    s = cleanLineEnds(s)
    s = re.sub('\\r\\r+', '\r\r', s)
    s = re.sub('\\s*$', '', s)
    return s

def replaceZeroWithBlank(x):
    if x == 0:
        return ''
    else:
        return str(x)

def replaceBlankWithZero(x):
    if x =='':
        return 0.0
    else:
        return floaty(x)

def fullPlatform():
    fullName = platform.platform()
    if platform.system() == 'Darwin':
        fullName = 'Mac OS X Version ' + platform.mac_ver()[0] + ' (' + fullName + ')'
    return fullName

import os, sys, subprocess, webbrowser
def system_open(target):
    """
    Open a file with the system viewer
    """
    if sys.platform.startswith('linux'):
        # https://github.com/pyinstaller/pyinstaller/issues/3668
        myEnv = dict(os.environ)
        lp_key = 'LD_LIBRARY_PATH'
        lp_orig = myEnv.get(lp_key + '_ORIG')
        if lp_orig is not None:
            myEnv[lp_key] = lp_orig
        else:
            lp = myEnv.get(lp_key)
            if lp is not None:
                myEnv.pop(lp_key)
        subprocess.Popen(["xdg-open", target], env=myEnv)
    else:
        webbrowser.open_new_tab('file://' + target)

def descriptionFromLevel(level):
    level = round(level, 1)
    if level >= 5: return 'dark'
    elif level >= 4:
        return 'med-dark'
    elif level >= 3:
        return 'medium'
    elif level >= 2:
        return 'med-light'
    elif level >= 1:
        return 'light'
    return 'very light'

