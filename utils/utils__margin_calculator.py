import __constants
import math

def correct_aoi(x1, x2, y1, y2, angle):
    if(angle < __constants.angle_b):
        x1, x2, y1, y2 = correct_small_aoi(x1, x2, y1, y2)

    x1, x2, y1, y2 = correct_error_margins_on_aoi(x1, x2, y1, y2)

    return [x1, x2, y1, y2]

def correct_small_aoi(x1, x2, y1, y2):
    """
    Small AOI's (small is defined by a minimal viewers angle)
    must be enlarged to enable detection of hits for this object.
    Since the objects are small and the height of the screen is typically
    low, we don't calculate margins for y1 and y2.

    - Returns:
        x1, x2, y1, y2: coordinates of the AOI with margins applied on the x-coordinates
    - Params:
        x1, x2, y1, y2: coordinates of the AOI we need to enlarge
    """
    center_x = x1 + (x2 - x1) / 2
    width = x2 - x1
    m = abs(center_x)
    angle_c = math.degrees(math.atan(m/__constants.d))
    angle_e = angle_c - (__constants.angle_b/2)
    n = math.tan(math.radians(angle_e))*__constants.d    
    nx = (abs(m)-abs(n))*2
    margin = (nx - width)/2

    return [x1 - margin, x2 + margin, y1, y2]

def correct_error_margins_on_aoi(x1, x2, y1, y2):
    """
    All AOI's need an error margin. This error margin depends on the position
    of the AOI of the screen and the size of the AOI.

    - Returns:
        x1, x2, y1, y2: coordinates of the AOI with error margins applied on the x-coordinates
    - Params:
        x1, x2, y1, y2: coordinates of the AOI we need corrected for error margins
    """

    # Calculate distances
    center_box_x = (x2 - x1)/2 + x1
    center_box_y = (y1 - y2)/2 + y2

    # Calculate x1 with margin
    delta_x = abs(x1 - __constants.screen_middle_x)
    delta_y = abs(center_box_y - __constants.screen_middle_y)
    m = math.sqrt(math.pow(delta_x, 2) + math.pow(delta_y, 2))
    angle_z = math.degrees(math.atan(m/__constants.d))
    angle_y = angle_z - __constants.angle_a
    n = math.tan(math.radians(angle_y)) * __constants.d
    mx1 = m - n
    x1_with_margin = x1 - mx1

    # Calculate x2 with margin
    delta_x = abs(x2 - __constants.screen_middle_x)
    delta_y = abs(center_box_y - __constants.screen_middle_y)
    b = math.sqrt(math.pow(delta_x, 2) + math.pow(delta_y, 2))
    angle_f = math.degrees(math.atan(b/__constants.d))
    angle_g = angle_f + __constants.angle_a
    c = math.tan(math.radians(angle_g)) * __constants.d
    mx2 = c - b
    x2_with_margin = x2 + mx2

    # Calculate y2, y1 with margin
    delta_x = abs(center_box_x - __constants.screen_middle_x)
    delta_y = abs(center_box_y - __constants.screen_middle_y)
    p = math.sqrt(math.pow(delta_x, 2) + math.pow(delta_y, 2))
    angle_v = math.degrees(math.atan(p/__constants.d))
    angle_q = angle_v + __constants.angle_a
    o = math.tan(math.radians(angle_q)) * __constants.d
    my = o - p

    y2_with_margin = y2 + my # NB: margin y for both y's is the same
    y1_with_margin = y1 - my

    return [x1_with_margin, x2_with_margin, y1_with_margin, y2_with_margin]