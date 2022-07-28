import numpy as np
import re
import wx
from wx.lib.plot import PlotCanvas, PlotGraphics, PolyLine, PolyMarker, PolyPoints
"""
class EnhancedPolyLine(PolyLine):
    def __init__(self, *args, **kw):
        super(EnhancedPolyLine, self).__init__(*args, **kw)

class EnhancedPolyMarker(PolyMarker):
    def __init__(self, *args, **kw):
        super(EnhancedPolyMarker, self).__init__(*args, **kw)
"""
class EnhancedPlotCanvas(PlotCanvas):
    def __init__(self, *args, **kw):
        super(EnhancedPlotCanvas, self).__init__(*args, **kw)

    def _drawLegend(self, dc, graphics, rhsW, topH, legendBoxWH, legendSymExt, legendTextExt):
        """
        Draws legend symbols and text.
        Doesn't display the legend for a plot line if it is empty, None, or contains '[hidden]'.
        """
        # top right hand corner of graph box is ref corner
        trhc = self.plotbox_origin + \
            (self.plotbox_size - [rhsW, topH]) * [1, -1]
        # border space between legend sym and graph box
        legendLHS = .091 * legendBoxWH[0]
        # 1.1 used as space between lines
        lineHeight = max(legendSymExt[1], legendTextExt[1]) * 1.1
        dc.SetFont(self._getFont(self._fontSizeLegend))
        row = 0
        for i in range(len(graphics)):
            o = graphics[i]
            displayText = o.getLegend()
            if displayText == '' or displayText is None or '[hidden]' in displayText: continue # no legend marker or text
            s = row * lineHeight
            if isinstance(o, PolyMarker):
                # draw marker with legend
                pnt = (trhc[0] + legendLHS + legendSymExt[0] / 2.,
                       trhc[1] + s + lineHeight / 2.)
                o.draw(dc, self.printerScale, coord=np.array([pnt]))
            elif isinstance(o, PolyLine) or isinstance(o, FilledPolyLine) or isinstance(o, FilledPolygon):
                # draw line with legend
                pnt1 = (trhc[0] + legendLHS, trhc[1] + s + lineHeight / 2.)
                pnt2 = (trhc[0] + legendLHS + legendSymExt[0],
                        trhc[1] + s + lineHeight / 2.)
                o.draw(dc, self.printerScale, coord=np.array([pnt1, pnt2]))
            else:
                raise TypeError(
                    "object is neither PolyMarker or PolyLine instance")
            # draw legend txt
            pnt = (trhc[0] + legendLHS + legendSymExt[0] + 5 * self._pointSize[0],
                   trhc[1] + s + lineHeight / 2. - legendTextExt[1] / 2.)
            dc.DrawText(displayText, pnt[0], pnt[1])
            row += 1
        dc.SetFont(self._getFont(self._fontSizeAxis))  # reset

class FilledPolyLine(PolyPoints):

    """Class to define line type and style
        - All methods except __init__ are private.
    """

    _attributes = {'colour': 'black',
                   'width': 1,
                   'style': wx.PENSTYLE_SOLID,
                   'legend': ''}

    def __init__(self, points, **attr):
        """
        Creates FilledPolyLine object

        :param `points`: sequence (array, tuple or list) of (x,y) points making up line
        :keyword `attr`: keyword attributes, default to:

         ==========================  ================================
         'colour'= 'black'           wx.Pen Colour any wx.NamedColour
         'width'= 1                  Pen width
         'style'= wx.PENSTYLE_SOLID  wx.Pen style
         'legend'= ''                Line Legend to display
         ==========================  ================================

        """
        first = (points[0][0], 0)
        last = (points[-1][0], 0)
        points.append(last)
        points.append(first)
        PolyPoints.__init__(self, points, attr)

    def draw(self, dc, printerScale, coord=None):
        colour = self.attributes['colour']
        width = self.attributes['width'] * printerScale * self._pointSize[0]
        style = self.attributes['style']
        if not isinstance(colour, wx.Colour):
            colour = wx.NamedColour(colour)
        if coord is None:
            pen = wx.Pen(colour, 0, wx.PENSTYLE_TRANSPARENT)
        else:
            pen = wx.Pen(colour, width, style)
        brush = wx.Brush(colour)
        pen.SetCap(wx.CAP_BUTT)
        dc.SetPen(pen)
        dc.SetBrush(brush)
        if coord is None:
            if len(self.scaled):  # bugfix for Mac OS X
                dc.DrawPolygon(self.scaled)
        else:
            dc.DrawLines(coord)  # draw legend line

    def getSymExtent(self, printerScale):
        """Width and Height of Marker"""
        h = self.attributes['width'] * printerScale * self._pointSize[0]
        w = 5 * h
        return (w, h)

class FilledPolygon(PolyPoints):

    """Class to define line type and style
        - All methods except __init__ are private.
    """

    _attributes = {'colour': 'black',
                   'width': 1,
                   'style': wx.PENSTYLE_SOLID,
                   'legend': ''}

    def __init__(self, points, **attr):
        """
        Creates FilledPolygon object

        :param `points`: sequence (array, tuple or list) of (x,y) points making up line
        :keyword `attr`: keyword attributes, default to:

         ==========================  ================================
         'colour'= 'black'           wx.Pen Colour any wx.NamedColour
         'width'= 1                  Pen width
         'style'= wx.PENSTYLE_SOLID  wx.Pen style
         'legend'= ''                Line Legend to display
         ==========================  ================================

        """
        PolyPoints.__init__(self, points, attr)

    def draw(self, dc, printerScale, coord=None):
        colour = self.attributes['colour']
        width = self.attributes['width'] * printerScale * self._pointSize[0]
        style = self.attributes['style']
        if not isinstance(colour, wx.Colour):
            colour = wx.NamedColour(colour)
        if coord is None:
            pen = wx.Pen(colour, 0, wx.PENSTYLE_TRANSPARENT)
        else:
            pen = wx.Pen(colour, width, style)
        brush = wx.Brush(colour)
        pen.SetCap(wx.CAP_BUTT)
        dc.SetPen(pen)
        dc.SetBrush(brush)
        if coord is None:
            if len(self.scaled):  # bugfix for Mac OS X
                dc.DrawPolygon(self.scaled)
        else:
            dc.DrawLines(coord)  # draw legend line

    def getSymExtent(self, printerScale):
        """Width and Height of Marker"""
        h = self.attributes['width'] * printerScale * self._pointSize[0]
        w = 5 * h
        return (w, h)
