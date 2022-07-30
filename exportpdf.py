# coding:utf-8

import re, os, wx
from fpdf import FPDF, HTMLMixin
import utilities, core_studio


def exportPDF(self):
    dialog = exportPDFDialog(self)
    dialog.ShowModal()
    dialog.Destroy()

class exportPDFDialog(wx.Dialog):

    def __init__(self, parent):
        super(exportPDFDialog, self).__init__(parent)
        self.parent = parent
        self.InitUI(parent)
        self.SetTitle("Export as PDF document")

    def InitUI(self, parent):
        box = wx.BoxSizer(wx.VERTICAL)
        self.box = box
        self.tabs = ['Log'] if self.parent.fileType == "log" else []
        self.tabs += ['Roast profile curve', 'Fan profile curve', 'About this file', 'Profile settings']
        self.checkboxes = []
        for title in self.tabs:
            self.checkboxes.append(self.addCheckbox(title, box))
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, label='Save PDF')
        cancelButton = wx.Button(self, label='Cancel')
        buttons.Add(okButton, 0, wx.ALL | wx.ALIGN_RIGHT, 7)  # Mac buttons need 7-pixel borders or they overlap
        buttons.Add(cancelButton, 0, wx.ALL | wx.ALIGN_RIGHT, 7)
        box.Add(buttons, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        box.SetSizeHints(self)
        self.SetSizerAndFit(box)
        okButton.Bind(wx.EVT_BUTTON, self.onOk)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
        okButton.SetDefault()

    def addCheckbox(self, title, box):
        checkbox = wx.CheckBox(self, -1, title)
        box.Add(checkbox, 0,
                              wx.LEFT | wx.TOP | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        checkbox.SetValue(True)
        return checkbox

    def onCancel(self, e):
        self.Close()

    def onOk(self, e):
        saveFileDialog = core_studio.myFileDialog(self, "Save PDF", "", os.path.splitext(os.path.basename(self.parent.fileName))[0],
                                      "Portable Document Format (*.pdf)|*.pdf",
                                      wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        result = saveFileDialog.ShowModal()
        pdfFileName = saveFileDialog.GetPath()
        saveFileDialog.Destroy()
        if result == wx.ID_CANCEL:
            return
        pdf = PdfDoc('P', 'mm', 'A4')
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.add_font('FreeSans', '', self.parent.programPath + 'fonts/FreeSans.ttf', uni=True)
        pdf.add_font('FreeSans', 'B', self.parent.programPath + 'fonts/FreeSansBold.ttf', uni=True)
        pdf.add_font('FreeSans', 'BI', self.parent.programPath + 'fonts/FreeSansBoldOblique.ttf', uni=True)
        pdf.add_font('FreeSans', 'I', self.parent.programPath + 'fonts/FreeSansOblique.ttf', uni=True)
        pdf.set_font('FreeSans', '', 16)
        pdf.cell(0, 10, os.path.basename(self.parent.fileName), 0, 1)
        pdf.set_font('FreeSans', '', 14)
        imageCount = 0
        for page_number in range(3 if self.parent.fileType == "log" else 2):
            if self.checkboxes[page_number].GetValue():
                imageCount += 1
                where = self.parent.notebook.GetPage(page_number)
                pdf.cell(0, 10, '', 0, 1) # leave some empty space
                page_image = self.parent.page_to_image(page_number, (1200, 800))
                f_name = self.parent.options.programDataFolder + os.sep + 'temp' + str(page_number) + '.png'
                page_image.SaveFile(f_name, wx.BITMAP_TYPE_PNG)
                pdf.image(f_name, h=25.4*4)

        for page_number in list(range(3, 5)) if self.parent.fileType == "log" else list(range(2, 4)):
            if self.checkboxes[page_number].GetValue():
                if imageCount > 0:
                    pdf.add_page()
                imageCount += 1
                where = self.parent.notebook.GetPage(page_number)
                pdf.set_font('FreeSans', '', 11)
                pdf.cell(0, 10, self.tabs[page_number], 0, 1)
                html = """<font face="FreeSans" size="6"><table border="1" align="left" width="90%">
                        <thead><tr><th align="left" width="50%">Setting</th><th align="left" width="50%">Value</th></tr></thead>
                        <tbody>"""
                import copy
                orderedList = copy.deepcopy(self.parent.configurationOrderedKeys)
                orderedList = [x for x in orderedList if x in list(where.configControls.keys())]
                line_num = 0
                for key in orderedList:
                    if where.configControls[key].Shown:
                        setting = utilities.replaceUnderscoreWithSpace(key) + ':'
                        value = re.sub(r'\n','<br>', where.configControls[key].GetValue())
                        line_num += 1
                        html += self.makeTableRows(setting, value, '#FFFFFF' if line_num % 2 == 0 else '#D8D8D8')
                html += """</tbody></table></font>"""
                pdf.write_html(html)
        pdf.set_font('FreeSans', 'I', 8)
        pdf.cell(0, 10, 'Created by ' + core_studio.PROGRAM_NAME + ' v' + core_studio.PROGRAM_VERSION + ' ', 0, 1)
        pdf.set_text_color(0, 0, 255)
        pdf.set_font('FreeSans','U', 8 )
        pdf.cell(0, 0, 'kaffelogic.com', 0, 1, link='https://kaffelogic.com')
        try:
            pdf.output(pdfFileName, 'F')
        except IOError as e:
            dial = wx.MessageDialog(None, 'This file could not be saved.\n' + pdfFileName + '\n' + e.strerror + '.',
                                    'Error',
                                    wx.OK | wx.ICON_EXCLAMATION)
            dial.ShowModal()
            return
        utilities.system_open(pdfFileName)
        self.Close()

    def addPlaceHolder(self, txt):
        if txt == '':
            return '&#160;'
        return txt

    def makeTableRows(self, setting, value, bgcolor):
        """
        FPDF html tables cannot include <br> or <p>. So weird workaround...
        """
        values = value.split('<br>')
        html = '<tr bgcolor="' + bgcolor + '"><td>' + setting + '</td><td>' + self.addPlaceHolder(values[0]) + '</td></tr>'
        if len(values) > 1:
            for value in values[1:]:
                html += '<tr bgcolor="' + bgcolor + '"><td>&#160;</td><td>' + self.addPlaceHolder(value) + '</td></tr>'
        return html

class PdfDoc(FPDF, HTMLMixin):
    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # FreeSans italic 8
        self.set_font('FreeSans', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

