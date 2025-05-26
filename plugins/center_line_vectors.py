from base_plugin import Plugin
import gui_utils as gui
import utils, path_utils

import numpy as np
from PIL import Image
# from numba import jit , njit
from autotrace import Bitmap # pip install pyautotrace
import main
import cv2 # pip install opencv-python


class Layer(Plugin):
    """
    Center-line made with AutoTrace lib
     https://github.com/lemonyte/pyautotrace
     https://github.com/autotrace/autotrace
    """

    def __init__(s):
        super(Layer, s).__init__()

    def gui(s, frame):
        s.outline = True
        s.corner_join_limit = 160
        s.corner_join = 2
        gui.Slider(frame, layer=s, min=1, max=300, name='outline_width', ini=110 ).pack(anchor='w')


        gui.Optionbutton(frame, layer=s, nbr=3, ini=2, pos='inline', name='outline_cap', img_name='end').pack(anchor='w')


        gui.Slider(frame, layer=s, max=1, min=0.01, ini= 0.2,format='%0.2f', name='algo_resolution', slow=True).pack(anchor='w', pady=(25,0))
        gui.Slider(frame, layer=s, max=20, min=0.2, ini=1,format='%0.1f', name='smooth' ).pack(anchor='w')
        gui.Slider(frame, layer=s, max=20, min=0, ini=1,format='%0.1f', name='smooth2' ).pack(anchor='w')
        gui.Slider(frame, layer=s, max=15, min=0, ini=0.0,format='%0.1f', name='line_threshold' ).pack(anchor='w')
        gui.Slider(frame, layer=s, max=180,  name='corner_threshold', ini=100).pack(anchor='w')

        gui.Slider(frame, layer=s, max=2,  name='add_i_dot', ini=1, format='%0.1f').pack(anchor='w', pady=(25,0))
        gui.Slider(frame, layer=s, max=180,  name='i_dot_angle', ini=0).pack(anchor='w')


    def run(s, img):
        originSize = img.size

        if s.add_i_dot != 0 :
            img = s.detect_points(img);

        img = img.resize( (int(img.width*s.algo_resolution), int(img.height*s.algo_resolution)), Image.NEAREST)
        w = img.width
        h = img.height


        img = np.asarray(img.convert("RGB"))

        bitmap = Bitmap(img)
        vector = bitmap.trace(
            centerline = True,
            line_threshold=s.line_threshold,
            width_weight_factor = 1,
            line_reversion_threshold = s.line_threshold*2,
            preserve_width = True,
            remove_adjacent_corners = True,
            filter_iterations = s.smooth2,
            error_threshold = s.smooth,
            color_count = 2,
            corner_surround = 40*s.algo_resolution,
            corner_threshold = s.corner_threshold,
            despeckle_level = 0 )


        img = Image.fromarray(img)
        img = img.resize(originSize, 1)

        u = main.units
        descender = main.font['OS/2'].usWinDescent
        m = utils.margin/u
        outline = path_utils.autotrace_to_ftoutline(vector,
            (1/s.algo_resolution/u,0,0,1/s.algo_resolution/u,-m, -descender-2*m ))

        pen = path_utils.ftoutline_contour(outline, s, main.font.getGlyphSet(), opened=True, units=main.units )

        img = path_utils.pen_to_img(pen, main.font, main.current_glyph)

        return img


    def detect_points(s,img):
        img = np.asarray(img).astype(np.uint8)

        params = cv2.SimpleBlobDetector_Params()
        params.filterByColor = True
        params.blobColor = 0
        params.minThreshold = 10;
        params.maxThreshold = 200;
        params.filterByArea = True
        params.minArea = 500
        params.maxArea = 50000
        params.filterByCircularity = True
        params.minCircularity = 0.7
        params.filterByConvexity = True
        params.minConvexity = 0.9
        params.filterByInertia = True
        params.minInertiaRatio = 0.001
        detector = cv2.SimpleBlobDetector_create(params)
        keypoints = detector.detect(img)

        for i in keypoints:
            r = int(i.size*0.5*s.add_i_dot)
            cv2.circle(img, (int(i.pt[0]),int(i.pt[1])), int(r*1)+5,255,-1) # cache white circle
            cv2.ellipse(img,(int(i.pt[0]),int(i.pt[1])), (int(r*0.5), r), s.i_dot_angle,0,360,100,-1)


        # circles = cv2.HoughCircles(img,cv2.HOUGH_GRADIENT,s.circle,s.lim, param1=s.a,param2=s.b,minRadius=s.min,maxRadius=s.max)
        # if circles is not None:
        #     circles = np.uint16(np.around(circles))
        #     for i in circles[0,:]:
        #         cv2.circle(img,(i[0],i[1]),int(i[2]*1.3)+5,255,-1) # cache white circle
        #         cv2.ellipse(img,(i[0],i[1]), (int(i[2]*0.5), i[2]), s.i_dot_angle,0,360,100,-1)
        #         print("(circle)")


        return Image.fromarray(img)
