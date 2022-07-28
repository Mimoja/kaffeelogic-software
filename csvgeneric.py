# coding:utf-8
import re, wx, datetime, os, copy, json
import temperature, cropster, bezier, PathFitter, kaffelogic_studio_defaults, utilities, core_studio

ARTISAN = 'Artisan'
CROPSTER = u'Cropster'
IKAWA = u'Ikawa™'
IKAWA_DEFAULT_FAN_RPM_AT_100_PERCENT = '21000'
IKAWA_DEFAULT_FAN_STALL_PERCENT = '0'

def specialArtisanJsonEncoding(text):
    """
    Artisan double encodes the \ character when saving JSON, and then double decodes on import.
    """
    return text.replace('\\', '\\\\')


def specialArtisanJsonDecoding(text):
    """
    Artisan double encodes the \ character when saving JSON, and then double decodes on import.
    Artisan also saves unicode characters as \x99 instead of the JSON standard \u9999 so this is also addressed here.
    """
    return text.replace(r'\\x', r'\\u00').replace('\\\\', '\\')


def blankToZero(x):
    return x if x != '' else '0'


def averagePoint(alist):
    totalY = 0.0
    for p in alist:
        totalY += p[1]
    return (alist[int(len(alist) / 2)][0], totalY / len(alist))


def applyMovingMeans(alist, n):
    l = copy.deepcopy(alist)
    half = int(n / 2)
    paddedLength = len(l) + 2 * half
    while len(l) < paddedLength:
        l.insert(0, l[0])
        l.append(l[-1])
    result = []
    for i in range(len(l) - 2 * half):
        result.append(averagePoint(l[i:i + n]))
    return result


def dateUsing(date, sep):
    return re.sub(r"\.|/", sep, date)


def unquotecsv(s):
    s = re.sub(r'^"', '', s)
    s = re.sub(r'"$', '', s)
    s = re.sub(r'""', '"', s)
    return s


def disambiguate_duplicates(lis):
    for item in lis:
        if lis.count(item) > 1:
            lis[lis.index(item)] = item + '*'

def convertGumbleSegmentsToKaffelogicProfilePoints(segments, normaliser):
    """
    The PathFitter module accepts as input a list of points as a list of tuples.
    However, it outputs a bezier curve in a specific format (a list of 'Gumble' segments).
    This needs to be converted into the Kaffelogic format for a bezier curve (a list of 'ProfilePoint').
    """
    points = [bezier.ProfilePoint(seg.point.x, seg.point.y, seg.point.x + seg.handleIn.x, seg.point.y + seg.handleIn.y,
                                  seg.point.x + seg.handleOut.x, seg.point.y + seg.handleOut.y) for seg in segments]
    zeroPoint = bezier.Point(0, 0)
    normaliser.normalisePoint(zeroPoint)
    points[0].leftControl = copy.deepcopy(zeroPoint)
    points[-1].rightControl = copy.deepcopy(zeroPoint)
    return points

class NormaliseLineData():
    """
    The PathFitter module uses calculations that do not work well if x and y scales are widely different.
    This class does the scaling and re-scaling that allows the PathFitter to function correctly.
    """
    def __init__(self, points):
        """
        The points are a list of (x, y) tuples.
        """
        minX, maxX, minY, maxY = utilities.extrema(points)
        self.SCALE = 1000.0
        self.x_multiplier = self.SCALE / (maxX - minX)
        self.x_constant = minX
        self.y_multiplier = self.SCALE / (maxY - minY)
        self.y_constant = minY
        self.normalised = []
        for p in points:
            x, y = p
            x_normalised = (x - self.x_constant) * self.x_multiplier - self.SCALE / 2.0
            y_normalised = (y - self.y_constant) * self.y_multiplier - self.SCALE / 2.0
            self.normalised.append((x_normalised, y_normalised))

    def normalisedTuple(self, point):
        x, y = point
        x_normalised = (x - self.x_constant) * self.x_multiplier - self.SCALE / 2.0
        y_normalised = (y - self.y_constant) * self.y_multiplier - self.SCALE / 2.0
        return (x_normalised, y_normalised)

    def deNormalisedTuple(self, point):
        x, y = point
        x = (x + self.SCALE / 2.0) / self.x_multiplier + self.x_constant
        y = (y + self.SCALE / 2.0) / self.y_multiplier + self.y_constant
        return (x, y)

    def normalisePoint(self, point):
        point.x = (point.x - self.x_constant) * self.x_multiplier - self.SCALE / 2.0
        point.y = (point.y - self.y_constant) * self.y_multiplier - self.SCALE / 2.0

    def deNormalisePoint(self, point):
        point.x = (point.x + self.SCALE / 2.0) / self.x_multiplier + self.x_constant
        point.y = (point.y + self.SCALE / 2.0) / self.y_multiplier + self.y_constant
        if abs(point.x) < 0.000001: point.x = 0.0
        if abs(point.y) < 0.000001: point.y = 0.0

    def deNormaliseProfilePoints(self, profilePoints):
        for profilePoint in profilePoints:
            self.deNormalisePoint(profilePoint.point)
            self.deNormalisePoint(profilePoint.leftControl)
            self.deNormalisePoint(profilePoint.rightControl)

def convertLogToProfilePoints(frame, columnName, nonZeroColumn=None, avoidInitialZero=False, error=25.0,
                              ensureEndIsFlat=False):
    dropTime = frame.logData.roastEventData[frame.logData.roastEventNames.index("roast_end")][
        0] if "roast_end" in frame.logData.roastEventNames else float('inf')
    desiredPoints = []
    for i in range(len(frame.logData.ySeriesRaw[columnName])):
        if frame.logData.ySeriesRaw[columnName][i][0] >= 0.0 and \
                frame.logData.ySeriesRaw[columnName][i][0] <= dropTime and \
                (nonZeroColumn is None or frame.logData.ySeriesRaw[nonZeroColumn][i][1] > 0.0 or
                 frame.logData.ySeriesRaw[columnName][i][0] == 0.0):
            p = frame.logData.ySeriesRaw[columnName][i]
            desiredPoints.append(p)
    # Ikawa has fan at zero when time = zero, Kaffelogic must have fan running so option to use fan setting from time = 1 sec.
    if avoidInitialZero and desiredPoints[0][1] <= 0.0:
        desiredPoints[0] = (desiredPoints[0][0], desiredPoints[1][1])
    normaliser = NormaliseLineData(desiredPoints)
    normalisedPoints = normaliser.normalised
    segs = PathFitter.fitpath(normalisedPoints, error=error)
    # print "converting", len(desiredPoints), "points to", len(segs)
    n = 2
    while len(segs) > frame.emulation_mode.profile_points_edit_max:
        segs = PathFitter.fitpath(applyMovingMeans(normalisedPoints, n + 1), error=error)
        # print "smoothing", len(desiredPoints), "points to", len(segs), "n =", n
        n *= 2
    if len(segs) == 2 or ensureEndIsFlat:
        # a fan profile should not continue to drop when extrapolated, so add an extra point to avoid that
        segs.append(copy.deepcopy(segs[-1]))
        segs[-2].handleOut.x = 30
        segs[-2].handleOut.y = 0
        segs[-2].handleIn.x = -5
        segs[-2].handleIn.y = 0
        segs[-1].handleIn.x = -30
        segs[-1].handleIn.y = 0
        segs[-1].point.x += 60
    profilePoints = convertGumbleSegmentsToKaffelogicProfilePoints(segs, normaliser)
    normaliser.deNormaliseProfilePoints(profilePoints)
    return profilePoints

def removeTurningPoint(points, useSecondDerivative=True):
    """
    Search for first point where first derivative goes positive.
    If the curve is from a log it will have a well behaved second derivative, so then search for where sec derivative first goes negative. In the
    case of Ikawa the profile is made of straight lines so the second derivative cannot be relied on and can be ignored using the second parameter.
    Remove points to left of that, bring first point to 20 deg and smooth it.
    """
    bezier_points, rate_of_rise_points, second_derivative_points = bezier.generateSetOfBezierCurvePoints(points)
    if len(points) > 1 and len(bezier_points) > 1 and rate_of_rise_points[1][1] < 0.0:
        # print "curve starts downward, therefore has turning point"
        turningPointTime = None
        for p in rate_of_rise_points:
            if p[1] > 0.0:
                turningPointTime = p[0]
                break
        if turningPointTime is not None and useSecondDerivative:
            for p in second_derivative_points:
                if p[1] <= 0.0 and p[0] > turningPointTime:
                    turningPointTime = p[0]
                    break
        # print "turn at", turningPointTime
        delete_up_to = None
        for i in range(len(points)):
            if i > 0 and points[i].point.x < turningPointTime:
                delete_up_to = i + 1
        # print "delete", delete_up_to
        if delete_up_to is not None: del points[1:delete_up_to]
        points[0].point.y = 20.0
        if len(points) >= 2:
            right = bezier.controlEndPointCalculation(points[0], points[1], ratio=core_studio.CONTROL_POINT_RATIO,
                                                      start=True)
            points[0].setRightControl(right.x, right.y)
    return points


def translateKaffelogicEventSetToArtisan(event_names, event_points, offset, temperature_column_name):
    """
    Returns a set of events for the Artisan CSV header, plus a set of indexes for the JSON timeindex element
    """
    event_translation_for_header = {
        "Charge": "CHARGE",
        "Dry End": "DRYe",
        "FCs": "FCs",
        "FCe": "FCe",
        "SCs": "SCs",
        "SCe": "SCe",
        "Drop": "DROP"
    }
    event_names_translated = [translateEventKaffelogicToArtisan(name) for name in event_names]
    event_indexes = [int(round(p[0])) for p in event_points]
    CSV_header = {}
    JSON_computed_times = {}
    JSON_indexed_times = {}
    if "charge" not in [name.lower() for name in event_names_translated]:
        CSV_header["CHARGE"] = utilities.toMinSec(offset, True)
        JSON_computed_times["Charge"] = 0
        JSON_indexed_times["Charge"] = offset
    for i in range(len(event_names)):
        header_name = event_translation_for_header[event_names_translated[i]] if event_names_translated[
                                                                                     i] in event_translation_for_header.keys() else \
        event_names_translated[i]
        artisan_name = event_names_translated[i]
        adjust = -2 if header_name == "DROP" and temperature_column_name == 'temp' else 0  # make up for fact that smoothing causes the mean temp to drop earlier than true roast end, but only
        # if a native klog file, not an import
        artisan_time = event_points[i][0] + offset + adjust
        CSV_header[header_name] = utilities.toMinSec(artisan_time, True)
        JSON_computed_times[artisan_name] = event_points[i][0] + adjust
        JSON_indexed_times[artisan_name] = artisan_time
    return (CSV_header, JSON_computed_times, JSON_indexed_times)


def makeArtisanCSVHeaders(date, extras=None, CSV_header_events=None, offset=0):
    if extras is None:
        extras = []
    if CSV_header_events is None:
        CSV_header_events = {}
    header1 = "Date:{}\tUnit:{}\tCHARGE:\tTP:\tDRYe:\tFCs:\tFCe:\tSCs:\tSCe:\tDROP:\tCOOL:\tTime:".format(
        date.replace('/', '.'), temperature.getTemperatureUnit())
    for name in CSV_header_events.keys():
        header1 = header1.replace(name + ":", name + ":" + CSV_header_events[name])
    if 'CHARGE' not in CSV_header_events.keys():
        header1 = header1.replace("CHARGE:", "CHARGE:" + utilities.toMinSec(offset, True))
    header1 = header1.replace("CHARGE:00:00", "CHARGE:00:01")  # Artisan will ignore events with time value of zero
    header2 = "Time1\tTime2\tBT\tET\tEvent"
    for extra in extras:
        header2 += "\t" + extra
    return header1 + "\n" + header2 + "\n"


def translateEventKaffelogicToArtisan(e):
    event_translation = {
        "colour_change": "Dry End",
        "first_crack": "FCs",
        "first_crack_end": "FCe",
        "second_crack": "SCs",
        "second_crack_end": "SCe",
        "roast_end": "Drop"
    }
    e = utilities.replaceSpaceWithUnderscore(e)
    return event_translation[e] if e in event_translation.keys() else e


def translateEventArtisanToKaffelogic(e):
    event_translation = {
        "Dry End": "colour_change",
        "FCs": "first_crack",
        "FCe": "first_crack_end",
        "SCs": "second_crack",
        "SCe": "second_crack_end",
        "Drop": "roast_end"
    }
    return event_translation[e] if e in event_translation.keys() else e


def make_JSON_object(include_extras, notes, events, roastisodate, times, temp1, temp2, extra1, extra2):
    TIMEINDEX_CHARGE = 0
    TIMEINDEX_DRY = 1
    TIMEINDEX_FCS = 2
    TIMEINDEX_FCE = 3
    TIMEINDEX_SCS = 4
    TIMEINDEX_SCE = 5
    TIMEINDEX_DROP = 6
    TIMEINDEX_COOL = 7
    # Artisan JSON files do not have computed charge times. This is because all computed times are time2 times, that is they
    # are relative to charge time, with charge time == 0.0.
    # However, JSON timeindex entries are indexes to the time array, which is time1.
    # For this reason, the inclusion of "Charge" in the following two dictionaries is to enable correct entries in the timeindex array
    # and cannot be used to create a computed value for charge time.
    event_translation = {
        "Charge": "CHARGE_time",
        "Dry End": "DRY_time",
        "FCs": "FCs_time",
        "FCe": "FCe_time",
        "SCs": "SCs_time",
        "SCe": "SCe_time",
        "Drop": "DROP_time"
    }
    event_lookupindex = {
        "CHARGE_time": TIMEINDEX_CHARGE,
        "DRY_time": TIMEINDEX_DRY,
        "FCs_time": TIMEINDEX_FCS,
        "FCe_time": TIMEINDEX_FCE,
        "SCs_time": TIMEINDEX_SCS,
        "SCe_time": TIMEINDEX_SCE,
        "DROP_time": TIMEINDEX_DROP
    }
    template = """
{
  "mode": "C",
  "timeindex": [0, 0, 0, 0, 0, 0, 0, 0], 
  "roastisodate": "2020-01-01",
  "timex": [],
  "temp1": [],
  "temp2": [],
  "computed": {
      "DRY_time": 0,
      "FCs_time": 0,
      "FCe_time": 0,
      "SCs_time": 0,
      "SCe_time": 0,
      "DROP_time": 0
    }
}
"""
    obj = json.loads(template)
    if not notes is None:
        roasting_notes, cupping_notes = notes
        if roasting_notes != "": obj["roastingnotes"] = roasting_notes
        if cupping_notes != "": obj["cuppingnotes"] = cupping_notes
    obj["roastisodate"] = roastisodate
    obj["mode"] = temperature.getTemperatureUnit()
    obj["timex"] = times
    obj["temp1"] = temp1
    obj["temp2"] = temp2
    if include_extras:
        obj["devices"] = ["MODBUS", "+Virtual"]
        obj["extradevices"] = [25]
        obj["extraname1"] = ["Fan speed (kRPMx100)"]
        obj["extraname2"] = ["Heat (Wx10)"]
        obj["extratimex"] = [times]
        obj["extratemp1"] = [extra1]
        obj["extratemp2"] = [extra2]
    if not events is None:
        JSON_computed_times, JSON_indexed_times = events
        for name in JSON_computed_times.keys():
            if name.lower() != "charge": obj["computed"][event_translation[name]] = JSON_computed_times[name]
            event_time = JSON_indexed_times[name]
            event_time_indexes = [ti for ti in range(len(times)) if times[ti] >= event_time]
            obj["timeindex"][event_lookupindex[event_translation[name]]] = event_time_indexes[0] if len(
                event_time_indexes) > 0 else 0
    return obj


def artisanJsonToKlog(obj, filename, is_profile, envelopeFn):
    unit = obj["mode"]
    model = obj["roastertype"] if "roastertype" in obj.keys() and obj["roastertype"] != "" else "JSON file"
    date = obj["roastisodate"] if "roastisodate" in obj.keys() else ""
    description = obj["roastingnotes"] if "roastingnotes" in obj.keys() else ""
    notes = obj["cuppingnotes"] if "cuppingnotes" in obj.keys() else ""
    both = notes + '\n' + description + '\n' + "Imported from JSON file"
    date = date.split('-')
    if len(date) == 3:
        y, m, d = date
        date = d + '/' + m + '/' + y
        both += "\ndated " + date
    else:
        date = ""
    settings = "log_file_name:" + filename + "\ntasting_notes:" + utilities.encodeCtrlV(both) + "\nmodel:" + model
    if is_profile: settings += "\nprofile_description:" + utilities.encodeCtrlV(notes + '\n' + description)
    event_names = ["", "colour_change", "first_crack", "first_crack_end", "second_crack", "second_crack_end",
                   "roast_end", ""]
    event_indexes = obj["timeindex"]
    times = obj["timex"]
    offset = times[event_indexes[0]]
    temp1 = obj["temp1"]
    temp2 = obj["temp2"]

    for i in range(len(event_indexes)):
        name = event_names[i]
        index = event_indexes[i]
        timestamp = times[index] - offset
        if name != "" and index > 0:
            settings += "\n" + name + ":" + str(timestamp)
    header = 'time\tBT\t=ET'
    extra1name = obj["extraname1"][0] if "extraname1" in obj.keys() else None
    extra2name = obj["extraname2"][0] if "extraname2" in obj.keys() else None
    extra1temp = obj["extratemp1"][0] if "extratemp1" in obj.keys() else None
    extra2temp = obj["extratemp2"][0] if "extratemp2" in obj.keys() else None
    if not extra1name is None: header += '\t#' + utilities.replaceSpaceWithUnderscore(extra1name)
    if not extra2name is None: header += '\t#' + utilities.replaceSpaceWithUnderscore(extra2name)
    body = ''
    for i in range(len(times)):
        line = str(times[i] - offset) + '\t' + str(temperature.makeCelsiusAndApplyEnvelope(temp2[i], unit, 1, envelopeFn)) \
               + '\t' + str(temperature.makeCelsiusAndApplyEnvelope(temp1[i], unit, 1, envelopeFn))
        if not extra1name is None: line += '\t' + str(extra1temp[i])
        if not extra2name is None: line += '\t' + str(extra2temp[i])
        line += '\n'
        body += line
    return (settings + '\n\n' + header + '\n' + body, date, "JSON")


def artisanToKlog(artisan, filename, is_profile, envelopeFn):
    obj = None
    try:
        obj = json.loads(specialArtisanJsonDecoding(artisan))
    except:
        pass
    if obj is not None:
        return artisanJsonToKlog(obj, filename, is_profile, envelopeFn)
    artisan = artisan.replace('\r\n', '\n')
    artisan = artisan.replace('\r', '\n')
    lines = artisan.split('\n')
    lines = [l.split('\t') for l in lines]
    firstLine = [elem.split(':', 1) for elem in lines[0]]
    columnNames_art = lines[1]
    disambiguate_duplicates(columnNames_art)
    lines = lines[2:]
    lines = [x for x in lines if len(x) == len(columnNames_art)]
    header = {}
    for elem in firstLine:
        header[elem[0]] = elem[1]
    try:
        unit = header['Unit']
    except:
        unit = 'C'
    date = dateUsing(header['Date'], '/')
    dataset = {}
    for col_num in range(len(columnNames_art)):
        if columnNames_art[col_num] in ['BT', 'ET']:
            dataset[columnNames_art[col_num]] = [temperature.makeCelsiusAndApplyEnvelope(x[col_num], unit, 1, envelopeFn) for x
                                                 in lines]
        else:
            if columnNames_art[col_num] in ['Time1', 'Time2']:
                dataset[columnNames_art[col_num]] = [str(utilities.fromMinSec(x[col_num])) for x in lines]
            else:
                if columnNames_art[col_num] == "Event":
                    dataset[columnNames_art[col_num]] = [translateEventArtisanToKaffelogic(x[col_num]) for x in lines]
                else:
                    dataset[columnNames_art[col_num]] = [x[col_num] for x in lines]
    """
    Time1	Time2	        BT	ET	        Event	        Gas*30	        Extra 2	        "Gas*10""WC"	Extra 2
    time	#spot_temp	#=temp	=mean_temp	=profile	profile_ROR	=actual_ROR	#=desired_ROR	power_kW	#volts-9	#Kp	#Ki	#Kd
    """
    # assume existence of Time1, Time2, BT, ET, Event
    offset = 0
    for i in range(len(dataset['Time1'])):
        if dataset['Time1'][i] != '' and dataset['Time2'][i] != '':
            offset = float(dataset['Time2'][i]) - float(dataset['Time1'][i])
            break
    for i in range(len(dataset['Time1'])):
        if dataset['Time2'][i] == '':
            dataset['Time2'][i] = str(float(dataset['Time1'][i]) + offset)
        else:
            break

    columnNames_kaffe = columnNames_art
    columnNames_art.remove('Time1')
    columnNames_art.remove('Time2')
    columnNames_art.remove('BT')
    columnNames_art.remove('ET')
    columnNames_art.remove('Event')
    columnNames = [('#' + utilities.replaceSpaceWithUnderscore(unquotecsv(x)), x) for x in columnNames_art]
    columnNames = [('time', 'Time2'), ('BT', 'BT'), ('=ET', 'ET'), ('event', 'Event')] + columnNames
    columnHeader = '\t'.join([x[0] for x in columnNames if x[0] != 'event'])
    accessnames = [x[1] for x in columnNames]
    output = []
    settings = "log_file_name:" + filename + "\ntasting_notes:Imported CSV roast log dated " + date + "\nmodel:CSV file"
    if is_profile: settings += "\nprofile_description:"
    for i in range(len(lines)):
        if dataset['Time2'][i] != '':
            output.append('\t'.join([blankToZero(dataset[n][i]) for n in accessnames if n != 'Event']))
            if dataset['Event'][i] != '':
                # print "line#", i, dataset['Event'][i] + ':' + dataset['Time2'][i], dataset['BT'][i]
                settings += '\n' + dataset['Event'][i] + ':' + dataset['Time2'][i]
    return (settings + '\n\n' + columnHeader + '\n' + '\n'.join(output) + '\n', date, 'CSV')

class UnknownDataFormat(BaseException):
    pass

def ikawaToKlog(ikawa, filename, is_profile, converter, convert_fan, RPM_at_100_percent, fan_stall_percent):
    ikawa = ikawa.replace('\r\n', '\n')
    ikawa = ikawa.replace('\r', '\n')
    lines = ikawa.split('\n')
    lines = [re.split(r'\s*,\s*', l) for l in lines]
    columnNames_ikawa = lines[0]
    lines = lines[1:]
    zero_lines = [x for x in lines if x[0] in ['0', '0.0'] and len(x) == len(columnNames_ikawa)]
    lines = [x for x in lines if x[0] != '0' and len(x) == len(columnNames_ikawa)]
    lines = [zero_lines[-1]] + lines
    dataset = {}
    for col_num in range(len(columnNames_ikawa)):
        if columnNames_ikawa[col_num] in ['temp set', 'exaust temp', 'inlet temp', 'temp above', 'temp below', 'temp board', 'setpoint']:
            dataset[columnNames_ikawa[col_num]] = [temperature.makeCelsiusAndApplyEnvelope(x[col_num], 'C', 1, converter) for
                                                   x in lines]
        elif columnNames_ikawa[col_num] in ['fan set (%)', 'fan set'] and convert_fan:
            dataset[columnNames_ikawa[col_num]] = [(float(x[col_num]) - fan_stall_percent) * RPM_at_100_percent / (100.0 - fan_stall_percent) for x in lines]
        else:
            dataset[columnNames_ikawa[col_num]] = [x[col_num] for x in lines]
    """
    Ikawa Type A format
    time,state,temp set,exaust temp,inlet temp,fan set (%),fan speed (RPM),heater power (%)

    Ikawa Type B format
    time,fan set,setpoint,fan speed,temp above,state,heater,p,i,d,temp below,temp board,j,ror_above

    Kaffelogic format
    time,#spot_temp,#=temp,=mean_temp,=profile,profile_ROR,=actual_ROR,#=desired_ROR,power_kW,#volts-9,#Kp,#Ki,#Kd
    """

    columnNamesTypeA = [('time', 'time'),
                       ('BT', 'exaust temp'),
                       ('=profile', 'temp set'),
                       ('=inlet_temp', 'inlet temp'),
                       ('power_%', 'heater power (%)'),
                       ('fan_profile_(RPM)' if convert_fan else 'fan_profile_%', 'fan set (%)'),
                       ('#fan_actual_speed_(RPM)', 'fan speed (RPM)'),
                       ]
    columnNamesTypeB = [('time', 'time'),
                       ('BT', 'temp above'),
                       ('=profile', 'setpoint'),
                       ('=temp_below', 'temp below'),
                       ('#=temp_board', 'temp board'),
                       ('power_%', 'heater'),
                       ('fan_profile_(RPM)' if convert_fan else 'fan_profile_%', 'fan set'),
                       ('#fan_actual_speed_(RPM)', 'fan speed'),
                       ('#Kp', 'p'),
                       ('#Ki', 'i'),
                       ('#Kd', 'd'),
                       ('#j', 'j')
                       ]
    accessnamesTypeA = [x[1] for x in columnNamesTypeA]
    accessnamesTypeB = [x[1] for x in columnNamesTypeB]

    if set(accessnamesTypeA).issubset(set(columnNames_ikawa)):
        columnNames = columnNamesTypeA
    elif set(accessnamesTypeB).issubset(set(columnNames_ikawa)):
        columnNames = columnNamesTypeB
    else:
        message = "CSV format not recognised.<br />Please send <b>" + filename + "</b> to Kaffelogic support for analysis."
        raise(UnknownDataFormat(message))
    columnHeader = '\t'.join([x[0] for x in columnNames])
    accessnames = [x[1] for x in columnNames]
    output = []
    settings = "log_file_name:" + filename + "\ntasting_notes:Imported " + IKAWA + " CSV roast log\nmodel:" + IKAWA + " CSV file"
    if is_profile: settings += "\nprofile_description:"

    if convert_fan:
        percent_col = [x[0] for x in columnNames].index('fan_profile_(RPM)')
        speed_col = [x[0] for x in columnNames].index('#fan_actual_speed_(RPM)')
        percent_data = [float(dataset[accessnames[percent_col]][i]) for i in range(len(lines))]
        speed_data = [float(dataset[accessnames[speed_col]][i]) for i in range(len(lines))]
        average_percent = sum(percent_data)/len(percent_data)
        average_speed = sum(speed_data)/len(speed_data)
        for i in range(len(lines)):
            dataset[accessnames[speed_col]][i] = float(dataset[accessnames[speed_col]][i]) * average_percent / average_speed

    for i in range(len(lines)):
        output.append('\t'.join([str(dataset[n][i]) for n in accessnames]))
    return settings + '\n\n' + columnHeader + '\n' + '\n'.join(output) + '\n'


########################################################################
class importExportDialog(wx.Dialog):

    def __init__(self, parent, isImport, previousFileName='', newFileName='', CSVType=ARTISAN):
        super(importExportDialog, self).__init__(parent)
        self.previousFileName = previousFileName
        self.newFileName = newFileName
        self.description = "Import from" if isImport else "Export to"
        self.verb = "Import" if isImport else "Export"
        self.CSVType = CSVType
        self.suffixes = "XLS" if self.CSVType == CROPSTER else "CSV or JSON" if self.CSVType == ARTISAN else "CSV"
        self.InitUI(parent, isImport)
        self.SetTitle(self.description + " " + self.CSVType + " " + self.suffixes)

    def InitUI(self, parent, isImport):
        self.envelopeApplier = temperature.TemperatureEnvelopeApplier(None)
        self.parent = parent
        self.isImport = isImport
        if self.CSVType == ARTISAN:
            optionType = u"artisan"
        elif self.CSVType == CROPSTER:
            optionType = u"cropster"
        elif self.CSVType == IKAWA:
            optionType = u"ikawa"
        self.optionType = optionType
        box = wx.BoxSizer(wx.VERTICAL)
        self.box = box
        if self.CSVType != IKAWA:
            descrip = "as" if isImport else "export"
            self.radioProfile = wx.RadioButton(self, style=wx.RB_GROUP, label=descrip + " Kaffelogic profile",
                                               name="profile")
            self.radioLog = wx.RadioButton(self, label=descrip + " Kaffelogic log", name="log")
            box.Add(self.radioProfile, 0, wx.LEFT | wx.TOP | wx.ALIGN_LEFT, 10)
            box.Add(self.radioLog, 0, wx.LEFT | wx.TOP | wx.ALIGN_LEFT, 10)
            self.radioProfile.Bind(wx.EVT_RADIOBUTTON, self.onMergeBox)
            self.radioLog.Bind(wx.EVT_RADIOBUTTON, self.onMergeBox)
            # To uncheck a radio button in a group you must check another button in the same group.
            if self.parent.options.getUserOptionBoolean(self.optionType + "_import/export_as_profile", default=True):
                self.radioProfile.SetValue(True)
            else:
                self.radioLog.SetValue(True)
            if self.parent.fileType == "profile" and not isImport:
                self.radioLog.Disable()  # cannot export a log if editing a profile
                self.radioProfile.SetValue(True)

        if self.CSVType == ARTISAN and not isImport:
            formatBox = wx.BoxSizer(wx.HORIZONTAL)
            formatBox.Add(wx.StaticText(self, -1, u"File format"), 0, wx.LEFT | wx.TOP | wx.ALIGN_LEFT, 10)
            self.radioFormatCSV = wx.RadioButton(self, style=wx.RB_GROUP, label="CSV", name="CSV")
            self.radioFormatJSON = wx.RadioButton(self, label="JSON", name="JSON")
            formatBox.Add(self.radioFormatCSV, 0, wx.LEFT | wx.TOP | wx.ALIGN_LEFT, 10)
            formatBox.Add(self.radioFormatJSON, 0, wx.LEFT | wx.TOP | wx.ALIGN_LEFT, 10)
            # To uncheck a radio button in a group you must check another button in the same group.
            if self.parent.options.getUserOptionBoolean(self.optionType + "_export_as_CSV", default=True):
                self.radioFormatCSV.SetValue(True)
            else:
                self.radioFormatJSON.SetValue(True)
            box.Add(formatBox)

        if isImport:
            self.mergeBox = wx.BoxSizer(wx.VERTICAL)
            self.mergeFromFileCheckBox = wx.CheckBox(self, -1, u"Merge with " + (
                "fan profile and " if self.CSVType != IKAWA else "") + "settings from")
            self.mergeBox.Add(self.mergeFromFileCheckBox, 0,
                              wx.LEFT | wx.TOP | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
            self.mergeFromFileCheckBox.SetValue(
                self.parent.options.getUserOptionBoolean(self.optionType + "_merge_on", default=False))
            mergePath = self.parent.options.getUserOption(optionType + "_merge_template")
            self.mergeFromFileCtrl = wx.FilePickerCtrl(self, path=mergePath, message="Select profile file",
                                                       size=(500, -1),
                                                       wildcard="Kaffelogic profile files (*.kpro)|*.kpro",
                                                       style=wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST | wx.FLP_USE_TEXTCTRL)
            self.mergeBox.Add(self.mergeFromFileCtrl, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.ALIGN_LEFT, 10)
            self.mergeFromFileCtrl.SetInitialDirectory(self.parent.options.getUserOption("working_directory"))
            if core_studio.isLinux: self.mergeFromFileCtrl.GetTextCtrl().SetValue(mergePath)  # seems to be needed in Linux
            box.Add(self.mergeBox, flag=wx.TOP, border=10)

        box.AddSpacer(10)
        optionName = u"kaffelogic/" + optionType + "_envelope_temperatures"
        box.Add(temperature.widget(self, parent, self.suffixes, optionName, optionType, None, self.envelopeApplier).box)
        if self.CSVType == IKAWA:
            box.Add(wx.StaticText(self, -1, "Fan speed conversion"), 0, wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_LEFT, 10)
            self.convert_fan_speed = wx.CheckBox(self, label="Convert fan speed")
            enabled = self.parent.options.getUserOptionBoolean(optionType + "_fan_speed_conversion_on", default=False)
            self.convert_fan_speed.SetValue(enabled)
            box.Add(self.convert_fan_speed, 0, wx.LEFT | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
            RPM_100percent_box = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(self, -1, u"Kaffelogic RPM equivalent to Ikawa fan 100%")
            self.RPM_100percent = wx.TextCtrl(self, -1, self.parent.options.getUserOption("kaffelogic/ikawa_fan_100%",
                                                                                          IKAWA_DEFAULT_FAN_RPM_AT_100_PERCENT),
                                              size=(60,-1))
            RPM_100percent_box.Add(self.RPM_100percent, 0, wx.TOP | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
            RPM_100percent_box.Add(label, 0, wx.TOP | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
            box.Add(RPM_100percent_box, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_LEFT, 10)
            Ikawa_stall_percent_box = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(self, -1, u"% Ikawa fan equivalent to zero Kaffelogic RPM")
            self.Ikawa_stall_percent = wx.TextCtrl(self, -1, self.parent.options.getUserOption("ikawa_fan_stall%",
                                                                                          IKAWA_DEFAULT_FAN_STALL_PERCENT),
                                              size=(60,-1))
            Ikawa_stall_percent_box.Add(self.Ikawa_stall_percent, 0, wx.BOTTOM | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
            Ikawa_stall_percent_box.Add(label, 0, wx.BOTTOM | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
            box.Add(Ikawa_stall_percent_box, 0, wx.ALL | wx.ALIGN_LEFT, 10)
            self.RPM_100percent.SetFocus()
        if self.CSVType == ARTISAN and not isImport:
            self.checkExtras = wx.CheckBox(self, label="", name="extras")
            box.Add(self.checkExtras, 0, wx.ALL | wx.ALIGN_LEFT, 10)
            self.checkExtras.SetValue(
                self.parent.options.getUserOptionBoolean(self.optionType + "_export_extras_on", default=False))
            self.settingsadvice = wx.StaticText(self, -1,
                                                u"Extra data in a CSV file will import into Artisan better if you\nalso load settings file kaffelogic-artisan-settings.aset")
            box.Add(self.settingsadvice, 0, wx.ALL | wx.ALIGN_LEFT, 10)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        importButton = wx.Button(self, label=self.verb)
        cancelButton = wx.Button(self, label='Cancel')
        buttons.Add(importButton, 0, wx.ALL | wx.ALIGN_RIGHT, 7)  # Mac buttons need 7-pixel borders or they overlap
        buttons.Add(cancelButton, 0, wx.ALL | wx.ALIGN_RIGHT, 7)
        box.Add(buttons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.SetSizeHints(self)
        if hasattr(self, 'settingsadvice'): self.settingsadvice.Hide()
        if hasattr(self, 'checkExtras'): self.checkExtras.Bind(wx.EVT_CHECKBOX, self.onExtras)
        if hasattr(self, 'radioFormatCSV'): self.radioFormatCSV.Bind(wx.EVT_RADIOBUTTON, self.onExtras)
        if hasattr(self, 'radioFormatJSON'): self.radioFormatJSON.Bind(wx.EVT_RADIOBUTTON, self.onExtras)
        self.SetSizerAndFit(box)
        importButton.Bind(wx.EVT_BUTTON, self.onImport if isImport else self.onExport)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        importButton.SetDefault()
        self.onExtras(None)
        self.onMergeBox(None)

    def persistChoices(self):
        if hasattr(self, 'radioProfile'): self.parent.options.setUserOptionBoolean(
            self.optionType + "_import/export_as_profile", self.radioProfile.GetValue())
        if hasattr(self, 'radioFormatCSV'): self.parent.options.setUserOptionBoolean(self.optionType + "_export_as_CSV",
                                                                                     self.radioFormatCSV.GetValue())
        if hasattr(self, 'mergeFromFileCheckBox'): self.parent.options.setUserOptionBoolean(
            self.optionType + "_merge_on", self.mergeFromFileCheckBox.GetValue())
        if hasattr(self, 'checkExtras'): self.parent.options.setUserOptionBoolean(self.optionType + "_export_extras_on",
                                                                                  self.checkExtras.GetValue())
        if hasattr(self, 'RPM_100percent'): self.parent.options.setUserOption("kaffelogic/ikawa_fan_100%",
                                                                              self.RPM_100percent.GetValue())
        if hasattr(self, 'Ikawa_stall_percent'): self.parent.options.setUserOption("ikawa_fan_stall%",
                                                                              self.Ikawa_stall_percent.GetValue())

        if hasattr(self, 'convert_fan_speed'): self.parent.options.setUserOptionBoolean(self.optionType + "_fan_speed_conversion_on",
                                                                          self.convert_fan_speed.GetValue())
        self.parent.options.setUserOptionBoolean(self.optionType + "_temperature_conversion_on", self.envelopeApplier.enabled)

    def onExtras(self, event):
        if not event is None: event.Skip()
        if hasattr(self, 'checkExtras'):
            if self.checkExtras.GetValue() and self.radioFormatCSV.GetValue():
                self.settingsadvice.Show()
            else:
                self.settingsadvice.Hide()
            self.SetSizerAndFit(self.box)

    def onMergeBox(self, event):
        if not event is None: event.Skip()
        if self.isImport:
            if self.CSVType == IKAWA or self.radioProfile.GetValue():
                self.box.Show(self.mergeBox)
            else:
                self.box.Hide(self.mergeBox)
        inclusionLabel = "Include fan speed as extra data" if hasattr(self,
                                                                      'radioProfile') and self.radioProfile.GetValue() else "Include heater power and fan speed as extra data"
        if hasattr(self, 'checkExtras'): self.checkExtras.SetLabel(inclusionLabel)
        self.Layout()
        self.SetSizerAndFit(self.box)

    def importCSVAsLog(self, restoreProfileToDefault, mergeWithThisProfile=None):
        for key in kaffelogic_studio_defaults.notSavedInProfile:
            if key not in kaffelogic_studio_defaults.profileDataInLog:
                if key in self.parent.configuration.keys():
                    self.parent.configuration.pop(key)
                if key in self.parent.configurationOrderedKeys:
                    self.parent.configurationOrderedKeys.remove(key)
        self.parent.logData.reset_vars()
        if restoreProfileToDefault:
            core_studio.stringToDataObjects(kaffelogic_studio_defaults.DEFAULT_DATA, self.parent)
            self.parent.defaults = copy.deepcopy(self.parent.configuration)
            if not mergeWithThisProfile is None:
                core_studio.stringToDataObjects(mergeWithThisProfile, self.parent)
            core_studio.stringToDataObjects(self.parent.datastring, self.parent)
            self.parent.page1.profilePoints = self.parent.roastProfilePoints
            self.parent.page2.profilePoints = self.parent.fanProfilePoints
            self.parent.page1.resetHistory()
            self.parent.page2.resetHistory()
            self.parent.page3.resetHistory()
            self.parent.page4.resetHistory()
        else:
            # must retain profile points and settings, even despite calling updateLogPanels()
            core_studio.dataObjectsToString(self.parent)
            core_studio.stringToDataObjects(self.parent.datastring, self.parent)
        self.parent.fileType = "log"
        self.parent.updateLogPanels()
        self.parent.finaliseOpen()

    def getEnvelopeApplier(self):
        return self.envelopeApplier.otherToKaffelogic if self.isImport else self.envelopeApplier.kaffelogicToOther

    def getMasterColumn(self, CSVType):
        table = {
            ARTISAN: "BT",
            CROPSTER: "Bean_temp",
            IKAWA: "profile"
        }
        return table[CSVType]

    def onImport(self, e):
        is_profile = self.radioProfile.GetValue() if self.CSVType != IKAWA else True

        if self.CSVType == IKAWA:
            # Don't check if modified for Ikawa because the check has already been done.
            need_to_check = False
        else:
            if is_profile:
                # All imported profiles need checking, as they overwite current profile, and nuke current log
                need_to_check = True
            else:
                if self.parent.fileType == 'log':
                    # Imported logs need checking if they are being imported over a current log, because they will replace that log
                    need_to_check = True
                else:
                    # Imported logs don't need to check if they are being inmported over a current profile, because the profile is not overwritten
                    need_to_check = False
        if (not need_to_check) or self.parent.saveIfModified(None):
            self.parent.fileName = self.newFileName
            suffix = "XLS" if self.CSVType == CROPSTER else "CSV"  # will change over to JSON if a valid json file is detected
            if self.CSVType == ARTISAN:
                self.parent.datastring, date, suffix = artisanToKlog(core_studio.openAndReadFileWithTimestamp(self.parent, self.parent.fileName),
                                                                     self.parent.fileName, is_profile,
                                                                     self.getEnvelopeApplier())
            if self.CSVType == CROPSTER:
                self.parent.datastring, date = cropster.cropsterToKlog(
                    cropster.openAndReadCropsterXLSFileWithTimestamp(self.parent, self.parent.fileName),
                    self.parent.fileName, is_profile,
                    self.getEnvelopeApplier())
            if self.CSVType == IKAWA:
                fan_convert = utilities.floatOrZero(self.convert_fan_speed.GetValue())
                fan_convert_ratio = utilities.floatOrZero(self.RPM_100percent.GetValue())
                stall_percent = utilities.floatOrZero(self.Ikawa_stall_percent.GetValue())
                self.parent.datastring = ikawaToKlog(core_studio.openAndReadFileWithTimestamp(self.parent, self.parent.fileName),
                                                     self.parent.fileName,
                                                     True,
                                                     self.getEnvelopeApplier(),
                                                     fan_convert,
                                                     fan_convert_ratio,
                                                     stall_percent)
                date = None

            self.parent.importedSuffix = suffix
            if is_profile or self.CSVType == IKAWA:
                mergeFileName = self.mergeFromFileCtrl.GetPath()
                if not mergeFileName.lower().endswith('.kpro'):
                    mergeFileName += '.kpro'
                mergeFileData = None
                if mergeFileName == ".kpro":
                    mergeFileData = None
                else:
                    if self.mergeFromFileCheckBox.GetValue():
                        mergeFileData = core_studio.openAndReadFile(mergeFileName)
                        if mergeFileData == "":
                            mergeFileData = None
                        else:
                            self.parent.options.setUserOption(self.optionType + "_merge_template", mergeFileName)
                self.parent.configuration['profile_file_name'] = self.parent.fileName
                self.importCSVAsLog(restoreProfileToDefault=True, mergeWithThisProfile=mergeFileData)

                self.parent.configuration['emulation_mode'] = core_studio.EMULATE_KAFFELOGIC
                self.parent.emulation_mode = core_studio.EmulationMode()
                self.parent.page1.applyEmulation(self.parent)

                self.parent.page1.profilePoints = removeTurningPoint(
                    convertLogToProfilePoints(
                        self.parent,
                        self.getMasterColumn(self.CSVType),
                        nonZeroColumn='power_%' if self.CSVType == IKAWA else None,
                    ),
                    useSecondDerivative=False if self.CSVType == IKAWA else True
                )
                self.parent.roastProfilePoints = self.parent.page1.profilePoints
                self.parent.page1.selectedIndex = 0
                endpoint = self.parent.page1.profilePoints[-1].point
                for pointTuple in self.parent.logData.ySeriesScaled['Bean_temp' if self.CSVType == CROPSTER else 'BT']:
                    endTemperature = pointTuple[1]
                    if pointTuple[0] >= endpoint.x: break
                loggedEndpointTuple = (endpoint.x, endTemperature)
                recommendation = core_studio.levelFromTemperature(temperature=endpoint.y,
                                                               thresholdString=self.parent.configuration[
                                                                   'roast_levels'])
                if recommendation >= self.parent.emulation_mode.level_min_val and recommendation <= self.parent.emulation_mode.level_max_val:
                    self.parent.configuration['recommended_level'] = recommendation
                    self.parent.page1.level_floatspin.SetValue(recommendation)
                    self.parent.configuration['roast_end'] = utilities.toMinSec(loggedEndpointTuple[0], wholeSecs=False)
                    self.parent.logData.roastEventNames.append("roast_end")
                    self.parent.logData.roastEventData.append(loggedEndpointTuple)
                    core_studio.refreshGridPanel(self.parent.page3, self.parent)
                    core_studio.refreshGridPanel(self.parent.page4, self.parent)
                    self.parent.page1.phasesObject.setPhasesFromProfileData()

                self.parent.page1.level_floatspin.SetValue(self.parent.configuration['recommended_level'])
                """
                TODO: adjust to fixed position for any points that emulation mode requires, e.g. Sonofresco
                """
                self.parent.configuration['profile_short_name'] = ''
                self.parent.configuration['profile_designer'] = ''
                self.parent.configuration[
                    'profile_description'] += '\nImported from ' + self.CSVType + ' ' + suffix + ' file: ' + \
                                              self.parent.configuration['log_file_name'] + (
                                                  (' dated ' + date) if date is not None else '')
                if self.CSVType == IKAWA:
                    if fan_convert:
                        points = convertLogToProfilePoints(
                            self.parent,
                            'fan_profile_(RPM)',
                            nonZeroColumn='power_%',
                            avoidInitialZero=True,
                            ensureEndIsFlat=True,
                            error=25
                        )
                        for p in points: p.scaleY(core_studio.FAN_PROFILE_YSCALE)
                        self.parent.page2.profilePoints = points
                        self.parent.fanProfilePoints = points
                    self.parent.page2.selectedIndex = 0
                    self.parent.page1.setSpinners()
                    self.parent.page2.setSpinners()
                    self.parent.profileIsFromLogFile = True
                    self.appendProfileToDatastring()
                    self.Close()
                else:
                    wx.CallAfter(self.finaliseExtractProfile)
                    self.parent.profileIsFromLogFile = False
            else:
                # non-Ikawa import as log
                self.parent.configuration['profile_file_name'] = self.previousFileName
                self.importCSVAsLog(restoreProfileToDefault=False)
                self.parent.profileIsFromLogFile = False
                self.appendProfileToDatastring()
                self.Close()
        else:
            self.Close()

    def appendProfileToDatastring(self):
        profileText = core_studio.dataObjectsToString(self.parent)
        roastEnd = ''
        if 'roast_end' in self.parent.configuration.keys():
            roastEnd = 'roast_end:' + str(
                utilities.fromMinSec(re.sub(r'\s.*', '', self.parent.configuration['roast_end']))) + '\n'
        self.parent.datastring = roastEnd + profileText + self.parent.datastring

    def finaliseExtractProfile(self):
        self.parent.onExtractProfile(None, "Import")
        self.parent.page1.setSpinners()
        self.Close()

    def onExport(self, e):
        envelopeFn = self.getEnvelopeApplier()
        is_profile = self.radioProfile.GetValue()
        is_formatCSV = True if not hasattr(self, 'radioFormatCSV') else self.radioFormatCSV.GetValue()
        include_extras = self.checkExtras.GetValue()

        times = []
        ETpoints = []
        BTpoints = []
        fanpoints = []
        heatpoints = []

        if is_profile:
            CSV_header, JSON_computed_times, JSON_indexed_times = translateKaffelogicEventSetToArtisan(['Charge'],
                                                                                                       [(0, 0)], 1,
                                                                                                       'Charge')
            header = makeArtisanCSVHeaders(datetime.datetime.now().strftime('%d/%m/%Y'),
                                           ['Fan speed (kRPMx100)', 'Heat (Wx10)'] if include_extras else [], CSV_header,
                                           offset=1)
            temp_profile = self.parent.page1.pointsAsGraphed
            fan_profile = self.parent.page2.pointsAsGraphed
            offset = int(temp_profile[0][0] - fan_profile[0][0])

            body = '00:00\t\t' + str(envelopeFn(temp_profile[0][1])) + '\t0\t' + (
                '\t0\t0' if include_extras else '') + '\n'

            times.append(0)
            ETpoints.append(0)
            BTpoints.append(envelopeFn(temp_profile[0][1]))
            fanpoints.append(fan_profile[offset][1] / 10.0 if offset < len(fan_profile) else 0)
            heatpoints.append(0)
            for i in range(len(temp_profile)):
                time1 = utilities.toMinSec(temp_profile[i][0] + 1.0, True)
                time2 = utilities.toMinSec(temp_profile[i][0], True)
                temperature = str(envelopeFn(temp_profile[i][1]))
                fan = str(fan_profile[i + offset][1] / 10.0) if i + offset < len(fan_profile) else '0'
                body += time1 + '\t' + time2 + '\t' + temperature + '\t0\t'
                body += '\t' + fan + '\t0' if include_extras else ''
                body += '\n'

                times.append(temp_profile[i][0] + 1.0)
                ETpoints.append(0)
                BTpoints.append(envelopeFn(temp_profile[i][1]))
                fanpoints.append(fan_profile[i + offset][1] / 10.0 if i + offset < len(fan_profile) else 0)
                heatpoints.append(0)
        else:
            # must be log
            data = self.parent.logData
            BT_column_name = 'temp' if 'temp' in data.ySeriesRaw.keys() else 'BT' if 'BT' in data.ySeriesRaw.keys() else 'Bean_temp'
            BT_points = data.ySeriesRaw[BT_column_name]
            ET_points = data.ySeriesRaw['ET'] if 'ET' in data.ySeriesRaw.keys() else []
            power_points = data.ySeriesRaw[
                'power_kW'] if 'power_kW' in data.ySeriesRaw.keys() and include_extras else []
            fan_points = self.parent.page2.pointsAsGraphed if self.parent.profileIsFromLogFile and include_extras else []
            event_points = data.roastEventData
            event_names = data.roastEventNames
            # print 'event_points', event_points, 'event_names', event_names
            event_names_translated = [translateEventKaffelogicToArtisan(name) for name in event_names]
            include_ET = len(ET_points) > 0
            include_power = len(power_points) > 0
            include_fan = len(fan_points) > 0
            extras = ['Fan speed (kRPMx100)', 'Heat (Wx10)'] if include_power or include_fan else []
            all_points = sorted([p[0] for p in (BT_points + ET_points + power_points + fan_points + event_points)])
            lowestX = int(round(all_points[0]))
            highestX = int(round(all_points[-1]))
            BT_indexes = [int(round(p[0])) for p in BT_points]
            ET_indexes = [int(round(p[0])) for p in ET_points]
            power_indexes = [int(round(p[0])) for p in power_points]
            fan_indexes = [int(round(p[0])) for p in fan_points]
            event_indexes = [int(round(p[0])) for p in event_points]
            CSV_header, JSON_computed_times, JSON_indexed_times = translateKaffelogicEventSetToArtisan(
                data.roastEventNames, data.roastEventData, -lowestX, BT_column_name)
            # print 'event_indexes', event_indexes, 'event_names_translated', event_names_translated
            header = makeArtisanCSVHeaders(datetime.datetime.now().strftime('%d/%m/%Y'), extras, CSV_header, -lowestX)
            body = ''
            for i in range(1, lowestX):
                body += utilities.toMinSec(i, True) + '\t' + core_studio.toMinSec(i, True) + '\t0\t0\t' + (
                    'Charge' if i == 1 else '')
                if include_fan or include_power: body += '\t0\t0'
                body += '\n'
                times.append(utilities.floatOrZero(utilities.fromMinSec(i)))
                ETpoints.append(utilities.floatOrZero(0))
                BTpoints.append(utilities.floatOrZero(0))
                fanpoints.append(utilities.floatOrZero(0))
                heatpoints.append(utilities.floatOrZero(0))
            for i in range(lowestX, highestX + 1):
                # adjust Time1 so it comes to start at zero
                time2 = utilities.toMinSec(i, True) if i >= 0 else ''
                if lowestX < 0:
                    time1 = utilities.toMinSec(i - lowestX, True) if i - lowestX >= 0 else ''
                else:
                    time1 = time2
                BT = str(envelopeFn(BT_points[BT_indexes.index(i)][1])) if i in BT_indexes else ''
                ET = str(envelopeFn(ET_points[ET_indexes.index(i)][1])) if i in ET_indexes else '0'
                power = str(power_points[power_indexes.index(i)][1] * 100.0) if i in power_indexes else '0'
                fan = str(fan_points[fan_indexes.index(i)][1] / 10.0) if i in fan_indexes else '0'
                event = str(event_names_translated[
                                event_indexes.index(i)]) if i in event_indexes else 'Charge' if i == 0 else ''
                if BT != '':
                    body += time1 + '\t' + time2 + '\t' + BT + '\t' + ET + '\t' + event
                    if include_fan or include_power: body += '\t' + fan + '\t' + power
                    body += '\n'
                    times.append(utilities.floatOrZero(utilities.fromMinSec(time1)))
                    ETpoints.append(utilities.floatOrZero(ET))
                    BTpoints.append(utilities.floatOrZero(BT))
                    fanpoints.append(utilities.floatOrZero(fan))
                    heatpoints.append(utilities.floatOrZero(power))

        if not is_formatCSV:
            suffix = 'json'
            tasting_notes = self.parent.page3.configControls["tasting_notes"].GetValue() if not is_profile else ""
            profile_description = self.parent.page3.configControls[
                "profile_description"].GetValue() if "profile_description" in self.parent.page3.configControls.keys() else ""
            text = json.dumps(make_JSON_object(
                include_extras,
                notes=(profile_description, tasting_notes),
                events=(JSON_computed_times, JSON_indexed_times),
                roastisodate=datetime.datetime.now().strftime('%Y-%m-%d'),
                times=times,
                temp1=ETpoints,
                temp2=BTpoints,
                extra1=fanpoints,
                extra2=heatpoints
            ))
            text = specialArtisanJsonEncoding(text)
        else:
            suffix = 'csv'
            text = header + body
        saveFileDialog = core_studio.myFileDialog(self, "Save As Artisan " + suffix.upper(), "",
                                               os.path.splitext(os.path.basename(self.parent.fileName))[0],
                                               "Artisan " + suffix.upper() + " files (*." + suffix + ")|*." + suffix + "",
                                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        result = saveFileDialog.ShowModal()
        if result == wx.ID_CANCEL:
            saveFileDialog.Destroy()
            return self.Close()
        newFileName = saveFileDialog.GetPath()
        if not newFileName.lower().endswith("." + suffix):
            newFileName += "." + suffix
        saveFileDialog.Destroy()
        try:
            with open(newFileName, 'w') as output:
                output.write(text.encode('utf8'))
            self.Close()
        except IOError as e:
            dial = wx.MessageDialog(None, 'This file could not be saved.\n' + newFileName + '\n' + e.strerror + '.',
                                    'Error',
                                    wx.OK | wx.ICON_EXCLAMATION)
            dial.ShowModal()

    def onCancel(self, e):
        self.Close()

    def onClose(self, e):
        self.persistChoices()
        e.Skip()


def importGenericCSV(self, CSVType):
    # If importing a log over a profile, then no need to check if modifed because the profile will not be overwritten.
    # However, we don't know whether we are importing a log or a profile yet, except for Ikawa import.
    # If importing Ikawa both profile and log are imported, so check now for modified. Otherwise check later.
    if CSVType != IKAWA or self.saveIfModified(None):
        if CSVType == ARTISAN:
            suffixes = "CSV or JSON"
            wildcard = "Artisan files (*.csv, *.json)|*.csv;*.json"
        elif CSVType == CROPSTER:
            suffixes = "XLS"
            wildcard = "Cropster Excel files (*.xls)|*.xls"
        elif CSVType == IKAWA:
            suffixes = "CSV"
            wildcard = "Ikawa CSV files (*.csv)|*.csv"
        openFileDialog = core_studio.myFileDialog(self, "Open " + CSVType + " " + suffixes, "", "",
                                               wildcard,
                                               wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        result = openFileDialog.ShowModal()
        if result == wx.ID_CANCEL:
            return
        previousFileName = self.fileName
        newFileName = openFileDialog.GetPath()
        openFileDialog.Destroy()
        dialog = importExportDialog(self, True, previousFileName, newFileName, CSVType=CSVType)
        dialog.ShowModal()
        dialog.Destroy()


def importArtisan(self, event):
    importGenericCSV(self, ARTISAN)


def importCropster(self, event):
    importGenericCSV(self, CROPSTER)


def importIkawa(self, event):
    importGenericCSV(self, IKAWA)


def exportGenericCSV(self, CSVType):
    dialog = importExportDialog(self, False, CSVType=CSVType)
    dialog.ShowModal()
    dialog.Destroy()


def exportArtisan(self, event):
    exportGenericCSV(self, ARTISAN)


if __name__ == '__main__':
    core_studio = __import__('Kaffelogic Studio')

    with open('costa_rica.csv', 'r') as infile:
        datastring = infile.read().decode('utf-8')
    # print artisanToKlog(datastring)
    # print makeArtisanHeaders("3/4/1965", ['one', 'two'], ["Drop"], ["100"])
