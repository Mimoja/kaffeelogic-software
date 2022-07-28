from __future__ import division
from math import *
import copy, sys


class Point:
    def __init__(self, x=0, y=0):
        self.setXY(x, y)
        self.gradient = None

    def __str__(self):
        return '%G,%G' % (self.x, self.y)

    def __repr__(self):
        return 'Point(%r, %r)' % (self.x, self.y)

    def setXY(self, x, y):
        self.x = x
        self.y = y

    def toTuple(self):
        return (self.x, self.y)

    def scale(self, scaleFactor):
        return Point(self.x * scaleFactor, self.y * scaleFactor)

    def yScale(self, scaleFactor):
        return Point(self.x, self.y * scaleFactor)


def pointFromTuple(p):
    return Point(p[0], p[1])


def swapXY(p):
    return Point(p.y, p.x)


class ProfilePoint:
    def __init__(self, x=0, y=0, leftControlX=0, leftControlY=0, rightControlX=0, rightControlY=0):
        self.point = Point(x, y)
        self.leftControl = Point(leftControlX, leftControlY)
        self.rightControl = Point(rightControlX, rightControlY)

    def __str__(self):
        return '((%G,%G), (%G,%G), (%G,%G))' % (
            self.point.x, self.point.y, self.leftControl.x, self.leftControl.y, self.rightControl.x,
            self.rightControl.y)

    def __repr__(self):
        return 'ProfilePoint(%r, %r, %r, %r, %r, %r)' % (
            self.point.x, self.point.y, self.leftControl.x, self.leftControl.y, self.rightControl.x,
            self.rightControl.y)

    def setXY(self, x, y):
        self.point.setXY(x, y)

    def setLeftControl(self, x, y):
        self.leftControl.setXY(x, y)

    def setRightControl(self, x, y):
        self.rightControl.setXY(x, y)

    def toTuple(self):
        return (
            self.point.x, self.point.y, self.leftControl.x, self.leftControl.y, self.rightControl.x,
            self.rightControl.y)

    def _transform(self, x, m, c):
        return x * m + c

    def transform(self, m_x, c_x, m_y, c_y):
        self.point.x = self._transform(self.point.x, m_x, c_x)
        self.point.y = self._transform(self.point.y, m_y, c_y)
        if self.leftControl.toTuple() != (0.0, 0.0):
            self.leftControl.x = self._transform(self.leftControl.x, m_x, c_x)
            self.leftControl.y = self._transform(self.leftControl.y, m_y, c_y)
        if self.rightControl.toTuple() != (0.0, 0.0):
            self.rightControl.x = self._transform(self.rightControl.x, m_x, c_x)
            self.rightControl.y = self._transform(self.rightControl.y, m_y, c_y)

    def scaleY(self, scale_factor):
        self.transform(1.0, 0.0, scale_factor, 0.0)

def profilePointsToString(name, data, yScale=1.0):
    result = name + ":"
    for p in data:
        result += ","
        result += str(p.point.x) + ","
        result += str(p.point.y / yScale) + ","
        result += str(p.leftControl.x) + ","
        result += str(p.leftControl.y / yScale) + ","
        result += str(p.rightControl.x) + ","
        result += str(p.rightControl.y / yScale)
    return result.replace(":,", ":") + "\n"


class HistoryPointsEntry:
    def __init__(self, profilePoints, selectedIndex, selectedType, isBulkChange=False):
        self.entryType = 'points'
        self.bulkChange = isBulkChange
        self.profilePoints = copy.deepcopy(profilePoints)
        self.selectedIndex = selectedIndex
        self.selectedType = selectedType

    def toDisplay(self):
        for i in range(len(self.profilePoints)):
            if i == self.selectedIndex:
                print "Selected", self.selectedType, i,
            print self.profilePoints[i].toTuple()


def bezierPointFromX(x, a, b, c, d):
    t = bezierCalculate_tGiven_x(x, a, b, c, d)
    return bezierCalculation(t, a, b, c, d)


def bezierPointFromY(y, a, b, c, d):
    t = bezierCalculate_tGiven_x(y, swapXY(a), swapXY(b), swapXY(c), swapXY(d))
    return bezierCalculation(t, a, b, c, d)


def bezierCalculate_tGiven_x(x, a, b, c, d):
    """
    This calculation assumes that the Bezier curve meets the following criteria:
        1. a.x < d.x
        2. control points b and c lie within the rectangle defined by points a and d.

    The profile MUST be checked to ensure that these criteria are met.
    A more general function would be needed to support a general Bezier curve, however the
    constraints on a coffee roasting profile are such that this simpler approach is sufficient.
    BUT BEWARE if using this outside of those constraints!!!
    """
    lowGuess = 0.0
    highGuess = 1.0
    if (x == a.x):
        return 0.0
    if (x == d.x):
        return 1.0
    C1 = (d.x - (3.0 * c.x) + (3.0 * b.x) - a.x)
    C2 = ((3.0 * c.x) - (6.0 * b.x) + (3.0 * a.x))
    C3 = ((3.0 * b.x) - (3.0 * a.x))
    C4 = (a.x)

    MAX_ITERATIONS = 32  # 16 on the 8-bit machine!!
    THRESHOLD = 0.000001
    for i in range(0, MAX_ITERATIONS):
        currentGuess = (lowGuess + highGuess) / 2.0
        t2 = currentGuess * currentGuess
        t3 = t2 * currentGuess
        currentResult = C1 * t3 + C2 * t2 + C3 * currentGuess + C4
        if (abs(currentResult - x) < THRESHOLD):
            return currentGuess
        else:
            if (currentResult < x):
                lowGuess = currentGuess
            else:
                highGuess = currentGuess
    return currentGuess


def bezierCalculation(t, a, b, c, d):
    """
    a is the start point, b is the control for a,
    d is the end point, c is the control for d
    """
    C1x = (d.x - (3.0 * c.x) + (3.0 * b.x) - a.x)
    C2x = ((3.0 * c.x) - (6.0 * b.x) + (3.0 * a.x))
    C3x = ((3.0 * b.x) - (3.0 * a.x))
    C4x = (a.x)
    C1y = (d.y - (3.0 * c.y) + (3.0 * b.y) - a.y)
    C2y = ((3.0 * c.y) - (6.0 * b.y) + (3.0 * a.y))
    C3y = ((3.0 * b.y) - (3.0 * a.y))
    C4y = (a.y)
    if C3x == 0.0:
        C3x += 0.000001
    # it's now easy to calculate the point, using those coefficients:
    bezier = Point()
    bezier.x = (C1x * t * t * t + C2x * t * t + C3x * t + C4x)
    bezier.y = (C1y * t * t * t + C2y * t * t + C3y * t + C4y)
    dx_by_dt = ((3.0 * C1x * t * t) + (2.0 * C2x * t) + C3x)
    dy_by_dt = ((3.0 * C1y * t * t) + (2.0 * C2y * t) + C3y)
    bezier.gradient = dy_by_dt / dx_by_dt
    d_by_dt_of_gradient = (
                                  6.0 * C1y * C2x * t * t + 6.0 * C1y * C3x * t - 6.0 * C2y * C1x * t * t + 2.0 * C2y * C3x - 6.0 * C3y * C1x * t - 2.0 * C3y * C2x) / \
                          sqr(t * (3 * C1x * t + 2 * C2x) + C3x)
    if d_by_dt_of_gradient == 0:
        bezier.second_div = 0
    else:
        if dx_by_dt == 0:
            bezier.second_div = 99999999
        else:
            bezier.second_div = d_by_dt_of_gradient / dx_by_dt
    return bezier


def distanceBetweenTwoPoints(A, B):
    return sqrt(sqr(A.x - B.x) + sqr(A.y - B.y))


def distanceBetweenTwoPointsScaled(A, B, xScale=1, yScale=1):
    return sqrt(sqr(xScale * (A.x - B.x)) + sqr(yScale * (A.y - B.y)))


def sqr(x):
    return x * x


def gradientOfTwoPoints(A, B):
    if B.x - A.x == 0.0:
        return sys.float_info.max
    else:
        return ((B.y - A.y) / (B.x - A.x))


def midpointCalculation(A, B):
    mid = Point()
    mid.x = (A.x + B.x) / 2
    mid.y = (A.y + B.y) / 2
    return mid


def angleBisectorGradient(A, B, C):
    AB = distanceBetweenTwoPoints(A, B)
    if AB == 0.0:
        distanceRatio = 0.0
    else:
        distanceRatio = distanceBetweenTwoPoints(B, C) / distanceBetweenTwoPoints(A, B)
    Cprime = Point()
    Cprime.x = (B.x - ((B.x - A.x) * distanceRatio))
    Cprime.y = (B.y - ((B.y - A.y) * distanceRatio))
    mid = midpointCalculation(C, Cprime)
    if mid.x == B.x and mid.y == B.y:
        dividend = gradientOfTwoPoints(A, C)
        if dividend != 0.0:
            return -1 / dividend
        else:
            return float("inf")
    else:
        return gradientOfTwoPoints(mid, B)


def angleFromThreePoints(A, B, C):
    return atan2(C.y - B.y, C.x - B.x) - atan2(A.y - B.y, A.x - B.x)


def sign(x):
    if x > 0.0:
        return 1
    elif x < 0.0:
        return -1
    else:
        return 0


def pointOnLineCalculation(origin, m, distance, left):
    xOffset = sqrt(sqr(distance) / (1 + sqr(m)))
    yOffset = xOffset * m
    if (left):
        xOffset *= -1.0
        yOffset *= -1.0
    result = Point()
    result.x = origin.x + xOffset
    result.y = origin.y + yOffset
    return result


def balanceControlPoint(profilePoint, left):
    if (left):
        """
        We have moved the right control point, and are balancing the left control point
        """
        return pointOnLineCalculation(profilePoint.point,
                                      gradientOfTwoPoints(profilePoint.point, profilePoint.rightControl),
                                      distanceBetweenTwoPoints(profilePoint.point, profilePoint.leftControl),
                                      True if profilePoint.rightControl.x > profilePoint.point.x else False)
    else:
        """
        We have moved the left control point, and are balancing the right control point
        """
        return pointOnLineCalculation(profilePoint.point,
                                      gradientOfTwoPoints(profilePoint.leftControl, profilePoint.point),
                                      distanceBetweenTwoPoints(profilePoint.point, profilePoint.rightControl),
                                      False if profilePoint.leftControl.x < profilePoint.point.x else True)


def controlPointCalculation(A, B, C, ratio, left):
    """
        There are two possible control points for B,
        one on the left for the segment AB, and one
        on the right for segment BC.
        """
    if (left):
        distance = distanceBetweenTwoPoints(A, B)
    else:
        distance = distanceBetweenTwoPoints(B, C)
    gradient = angleBisectorGradient(A, B, C)
    if gradient == 0.0:
        if left:
            return A
        else:
            return B
    else:
        return pointOnLineCalculation(B, -1 / gradient, distance * ratio, left)


"""
def controlEndPointCalculation(A, B, C, ratio, start):
        ""
        Calculates the single control point for an endpoint.
        If the endpoint is the start endpoint, then it is A, and B and C are points [1] and [2] respectively.
        If the endpoint is the end endpoint, then it is C, and A and B are points [-3] and [-2] respectively.
        ""
        if (start):
                distance = distanceBetweenTwoPoints(A, B)
        else:
                distance = distanceBetweenTwoPoints(B, C)
        gradient = angleBisectorGradient(A, B, C)
        if gradient == 0.0:
            if start:
                return A
            else:
                return C
        if start:
            Bcontrol = pointOnLineCalculation(B, -1 / gradient, distance * ratio, True)
            gradient = tan(angleFromThreePoints(Bcontrol, B, A) + atan2(B.y - A.y, B.x - A.x))
            if sign(B.y - A.y) != sign(gradient):
                gradient = (B.y - A.y) / (B.x - A.x)
            return pointOnLineCalculation(A, gradient, distance * ratio, False)
        else:
            Bcontrol = pointOnLineCalculation(B, -1 / gradient, distance * ratio, False)
            gradient = tan(angleFromThreePoints(Bcontrol, B, C) + atan2(C.y - B.y, C.x - B.x))
            if sign(C.y - B.y) != sign(gradient):
                gradient = (C.y - B.y) / (C.x - B.x)
            return pointOnLineCalculation(C, gradient, distance * ratio, True)
"""


def controlEndPointCalculation(A, B, ratio, start):
    """
    A and B are profile points, if start==True then A is the first point, B is the second, else A is the second to last point and B is the last point
    """
    a = A.point
    b = A.rightControl
    c = B.leftControl
    d = B.point
    distance = distanceBetweenTwoPoints(a, d) * ratio
    if start:  # first profile point
        if c.x < a.x:
            gradient = gradientOfTwoPoints(a, d)
        else:
            gradient = gradientOfTwoPoints(a, c)
        return pointOnLineCalculation(origin=a, m=gradient, distance=distance, left=False)
    else:  # last profile point
        if b.x > d.x:
            gradient = gradientOfTwoPoints(a, d)
        else:
            gradient = gradientOfTwoPoints(b, d)
        return pointOnLineCalculation(origin=d, m=gradient, distance=distance, left=True)


def calculateControlPoints(data, ratio):
    if len(data) >= 3:
        for i in range(1, len(data) - 1):
            A = data[i - 1].point
            B = data[i].point
            C = data[i + 1].point
            left = controlPointCalculation(A, B, C, ratio=ratio, left=True)
            right = controlPointCalculation(A, B, C, ratio=ratio, left=False)
            leftWasZero = False
            if data[i].leftControl.toTuple() == (0.0, 0.0):
                # "setting left control point for index ", i
                leftWasZero = True
                data[i].setLeftControl(left.x, left.y)
            if data[i].rightControl.toTuple() == (0.0, 0.0):
                # "setting right control point for index ", i
                data[i].setRightControl(right.x, right.y)
                if not leftWasZero:
                    # "*balancing* right control point for index ", i
                    b = balanceControlPoint(data[i], False)
                    data[i].setRightControl(b.x, b.y)

    if len(data) >= 2:
        if data[0].rightControl.toTuple() == (0.0, 0.0):  # first profile point
            right = controlEndPointCalculation(data[0], data[1], ratio, start=True)
            data[0].setRightControl(right.x, right.y)
        if data[len(data) - 1].leftControl.toTuple() == (0.0, 0.0):  # last profile point
            left = controlEndPointCalculation(data[-2], data[-1], ratio, start=False)
            data[-1].setLeftControl(left.x, left.y)
    if len(data) >= 1:
        # "zeroing the last profile point's right control point"
        data[-1].setRightControl(0, 0)
    if len(data) >= 0:
        # "zeroing the first profile point's left control point"
        data[0].setLeftControl(0, 0)


def generateSetOfBezierCurvePoints(profilePoints):
    bezier_points = []
    rate_of_rise_points = []
    second_derivative_points = []
    for i in range(len(profilePoints) - 1):
        a = profilePoints[i].point
        b = profilePoints[i].rightControl
        c = profilePoints[i + 1].leftControl
        d = profilePoints[i + 1].point
        if b.x == 0 and b.y == 0:
            b = a
        if c.x == 0 and c.y == 0:
            c = d
        for time in range(int(round(a.x)), int(round(d.x))):
            p = bezierPointFromX(time, a, b, c, d)
            bezier_points.append(p.toTuple())
            rate_of_rise_points.append((p.x, p.gradient * 60))
            second_derivative_points.append((p.x, p.second_div * 60 * 60))
    return (bezier_points, rate_of_rise_points, second_derivative_points)
