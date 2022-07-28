# coding:utf-8
import re
import wx
import os

import xlrd

import temperature
import utilities
import userOptions

XL_CELL_EMPTY = 0  # empty string ''
XL_CELL_TEXT = 1  # a Unicode string
XL_CELL_NUMBER = 2  # float
XL_CELL_DATE = 3  # float
XL_CELL_BOOLEAN = 4  # int; 1 means TRUE, 0 means FALSE
XL_CELL_ERROR = 5  # int representing internal Excel codes; for a text representation, refer to the supplied dictionary error_text_from_code
XL_CELL_BLANK = 6  # empty string ''. Note: this type will appear only when open_workbook(..., formatting_info=True) is used.

SHOW_THESE_COLUMNS = ['Bean', 'Inlet']


def translateEventCropsterToKaffelogic(e):
    event_translation = {
        "Color change": "colour_change",
        "First crack": "first_crack",
        "First crack end": "first_crack_end",
        "Second crack": "second_crack",
        "Second crack end": "second_crack_end",
        "Duration": "roast_end"
    }
    return event_translation[e] if e in event_translation.keys() else e


def ensure_celcius_temperature(temperature, unit):
    return ((float(temperature) - 32.0) * 5.0 / 9.0) if unit.startswith('F') else float(temperature)


def get_cell_value(cell):
    val = cell.value
    if cell.ctype == XL_CELL_DATE:
        val = xlrd.xldate.xldate_as_datetime(val, _datemode)
    return val


def sheet_to_array(s):
    array = []
    for row_number in range(s.nrows):
        row = [get_cell_value(s.cell(row_number, col_number)) for col_number in range(s.ncols)]
        array.append(row)
    return array


def general_array_to_dictionary(ar):
    """
    return values from second row, using key from first row as header row
    """
    keys = ar[0]
    vals = ar[1]
    result = {}
    for i in range(len(keys)):
        if utilities.isFloat(utilities.fromMinSec(vals[i])):
            result[keys[i]] = str(utilities.fromMinSec(vals[i]))
    return result


def add_comments_array_to_dictionary(ar, dic):
    """
    returns times in min:sec from first column, using key from third column
    """
    headers = ar[0]
    ar = ar[1:]
    for row in ar:
        if utilities.isFloat(row[0]):
            dic[row[2]] = utilities.toMinSec(row[0], wholeSecs=True)
    return dic


def extract_events(book):
    dic = add_comments_array_to_dictionary(sheet_to_array(book.sheets()[1]),
                                           general_array_to_dictionary(sheet_to_array(book.sheets()[0])))
    text = ''
    for key in dic.keys():
        event = translateEventCropsterToKaffelogic(key)
        if event != key:
            text += event + ':' + str(utilities.fromMinSec(dic[key])) + '\n'
    return text


def extract_notes(book, is_profile):
    sheet = sheet_to_array(book.sheets()[0])
    headers = sheet[0]
    information = sheet[1]
    note = ''
    for i in range(len(headers)):
        heading = headers[i]
        info = information[i]
        if i + 1 <= len(headers) - 1 and headers[i + 1].endswith(' unit'):
            note += unicode(heading) + ': ' + unicode(info) + ' ' + information[i + 1] + ', '
        elif heading != '' and info != '' and not heading.endswith(' unit'):
            note += unicode(heading) + ': ' + unicode(info) + ', '
    result = 'tasting_notes:' + utilities.encodeCtrlV(re.sub(', $', '', note)) + '\n'
    if is_profile: result += 'profile_description:' + utilities.encodeCtrlV(re.sub(', $', '', note)) + '\n'
    return result


def tidy_heading(s):
    s = re.sub(r'^Curve - ', '', s)
    s = re.sub(r'\.$', '', s)
    if s.endswith('temp') and not s.startswith('Bean'):
        prefix = '='
    else:
        prefix = ''
    if [wanted for wanted in SHOW_THESE_COLUMNS if s.startswith(wanted)] == []:
        prefix = "#" + prefix
    return utilities.replaceSpaceWithUnderscore(prefix + s)


def extract_header_array(book):
    return [tidy_heading(sheet.name) for sheet in book.sheets()[2:]]


def extract_header(book):
    return 'time\t' + '\t'.join(extract_header_array(book)) + '\n'


def extract_data(book, converter):
    data_text = ''
    heading_array = extract_header_array(book)
    data_array = [sheet_to_array(s) for s in book.sheets()[2:]]
    for row in range(1, len(data_array[0])):
        for sheet in range(len(data_array)):
            heading = heading_array[sheet]
            if heading.endswith('temp'):
                unit = extract_temperature_units(data_array[sheet][0][1])
            else:
                unit = ''
            if len(data_array[sheet]) > row:
                val = utilities.floatOrZero(data_array[sheet][row][1])
            else:
                val = 0.0
            if unit != '':
                val = temperature.makeCelsiusAndApplyEnvelope(val, unit=unit, envelopeFn=converter)
            if sheet == 0:
                row_text = str(data_array[sheet][row][0]) + '\t' + str(val)
            else:
                row_text += '\t' + str(val)
        row_text += '\n'
        data_text += row_text
    return data_text


def extract_temperature_units(s):
    if 'FAHRENHEIT' in s.upper():
        return 'F'
    else:
        return 'C'


def cropsterToKlog(cropster_book, filename, is_profile, converter):
    if cropster_book is None: return ('', '')
    general = general_array_to_dictionary(sheet_to_array(cropster_book.sheets()[0]))
    date = str(general["Date"]) if "Date" in general.keys() else ''
    klog = "log_file_name:" + filename + '\n'
    klog += extract_notes(cropster_book, is_profile)
    klog += extract_events(cropster_book)
    roast_end = str(utilities.fromMinSec(general["Duration"])) if "Duration" in general.keys() else ''
    if roast_end != '':
        klog += "roast_end:" + roast_end + '\n'
    klog += '\n' + extract_header(cropster_book)
    klog += extract_data(cropster_book, converter)
    return (klog, date)


def openAndReadCropsterXLSFileWithTimestamp(obj, fileName):
    global _datemode
    try:
        book = xlrd.open_workbook(fileName)
        _datemode = book.datemode
        with userOptions.fileCheckingLock:
            obj.fileTimeStamp = os.path.getmtime(fileName)

        return book
    except IOError as e:
        dial = wx.MessageDialog(None, 'This file could not be opened.\n' + fileName + '\n' + e.strerror + '.', 'Error',
                                wx.OK | wx.ICON_EXCLAMATION)
        dial.ShowModal()
    except xlrd.XLRDError as e:
        dial = wx.MessageDialog(None, 'This file could not be opened (not a valid XLS file)\n' + fileName, 'Error',
                                wx.OK | wx.ICON_EXCLAMATION)
        dial.ShowModal()
    return


if __name__ == '__main__':
    klog = cropsterToKlog(openAndReadCropsterXLSFileWithTimestamp('/Users/chrishilder/kaffelogic-studio/KaparaoPR-6013.klog'))
    with open('/Users/chrishilder/kaffelogic-studio/KaparaoPR-6013.klog', 'w') as output:
        output.write(klog.encode('utf8'))
