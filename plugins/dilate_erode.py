from base_plugin import Plugin
import gui_utils as gui

import cv2
import numpy as np
from PIL import Image

class Layer(Plugin):
    """outline font layer"""

    def gui(s, frame):
        gui.Slider(frame, max=200, ini=100, layer=s, name='contour_val').grid(column=1, row=1, sticky='W')
        gui.Slider(frame, min=2, max=20, ini=5, layer=s, name='kernel_size').grid(column=1, row=2, sticky='W')

    def run(s, img):

        img = np.array(img)

        # kernel = np.ones((s.kernel_size,s.kernel_size),np.uint8)
        kernel =  cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(s.kernel_size,s.kernel_size))
        if s.contour_val < 100 :
            img = cv2.dilate(img,kernel,iterations = 100-s.contour_val )
        else :
            img = cv2.erode(img,kernel,iterations = s.contour_val-100 )

        img = Image.fromarray(img)
        return img
