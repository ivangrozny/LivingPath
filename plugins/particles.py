from base_plugin import Plugin
import gui_utils as gui
import gui as ui
import utils

import utils
import pymunk
import pymunk.autogeometry
from pymunk import Vec2d
from PIL import Image, ImageDraw

class Layer(Plugin):
    """attraction repultion particles field
    """
    def __init__(s):
        super(Layer, s).__init__()
        s.ini_space = pymunk.Space()

    def gui(s, frame):
        gui.Slider(frame, max=400, min=1, ini= 50, layer=s, name='size')     .grid(column=0, row=0, sticky='W')
        gui.Slider(frame, max=100, min=1, ini= 40, layer=s, name='quantity').grid(column=0, row=1, sticky='W')
        gui.Slider(frame, max=200, min=1, ini= 30, layer=s, name='repultion').grid(column=0, row=2, sticky='W')
        gui.Slider(frame, layer=s, min=0, max=2000, ini=300, name='time')    .grid(column=0, row=3, sticky='W')

        # gui.Slider(frame,layer=s,min=0.02, max=0.08, ini=0.055, format='%0.3f',name='k black').grid(column=0,row=5,sticky='W')
        gui.Checkbutton(frame, layer=s, name='display_border', ini=False).grid(column=0, row=4, pady=(20,0), sticky='W')
        gui.Slider(frame, max=100, min=1, ini= 1, layer=s, name='outline_width').grid(column=0, row=5, sticky='W')

        gui.Slider(frame, max=20, min=-20, ini=0, layer=s, name='gravity').grid(column=0, row=6, pady=20, sticky='W')
        # gui.Slider(frame, max=400, min=1, ini= 200, layer=s, name='x').grid(column=0, row=8, sticky='W')
        # gui.Slider(frame, max=200, min=1, ini= 50, layer=s, name='y').grid(column=0, row=9, sticky='W')
        # gui.Slider(frame, max=200, min=1, ini= 60, layer=s, name='z').grid(column=0, row=10, sticky='W')

    def run(s, img):
        s.space = s.ini_space.copy()
        img_draw = Image.new('L', img.size, 255)
        draw = ImageDraw.Draw(img_draw)

        s.space.gravity = (0.0, s.gravity)
        # s.space.collision_slop = s.c # Amount of overlap between shapes that is allowed.
        # s.space.damping = s.d # A value of 0.9 means that each body will lose 10% of its velocity per second.

        balls = []
        w, h = img.size[0], img.size[1]
        q =  100-s.quantity +1
        for x in range(w//q):
            for y in range(h//q):
                pos = x*q, y*q
                if img.getpixel((int(x*q), int(y*q))) < 127 :
                    mass = 100
                    radius = s.repultion
                    inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
                    body = pymunk.Body(mass, inertia)
                    # x = 100 # random.randint(115, 350)
                    body.position = x*q, y*q
                    shape = pymunk.Circle(body, radius, Vec2d(0, 0))
                    # shape.elasticity = s.b # do nothing
                    s.space.add(body, shape)
                    balls.append(shape)

        s.generate_geometry(img, s.space, draw)

        #  Update physics
        for x in range(s.time):
            s.space.step(0.01)

            if x % 50 == 0 :  #  remove
                balls_to_remove = []
                for ball in balls:
                    if not utils.is_over(ball.body.position,(0,0,w-1,h-1)) or True and img.getpixel(ball.body.position) > 127 :
                        balls_to_remove.append(ball)
                for ball in balls_to_remove:
                    s.space.remove(ball, ball.body)
                    balls.remove(ball)

        for ball in balls: # draw
            v = ball.body.position
            utils.ellipse(s.size, v.x, v.y, 0, draw)

        del draw
        del s.space
        return img_draw

    def generate_geometry(s, img, space, draw):
        def sample_func(point):
            try:
                p = int(point[0]), int(point[1])
                color = img.getpixel(p)
                return color
            except Exception as e:
                print(e)
                return 0

        line_set = pymunk.autogeometry.march_soft( # analyse img sub-sampled by 4
            pymunk.BB(0, 0, img.size[0]-1, img.size[1]-1), img.size[0]//4, img.size[1]//4, 50, sample_func
        )

        for polyline in line_set:
            line = pymunk.autogeometry.simplify_curves(polyline, 3)

            for i in range(len(line) - 1):
                p1 = line[i]
                p2 = line[i+1]
                s.shape = pymunk.Segment(space.static_body, p1, p2, s.outline_width)
                # s.shape.density = 1
                # s.shape.friction = s.d*1
                # s.shape.elasticity = s.e*1
                space.add(s.shape)
            if s.display_border and ui.visual_info : draw.line( line, fill=150, width=s.outline_width, joint="curve" )
            if s.display_border and ui.visual_info : utils.ellipse(s.outline_width, line[0][0], line[0][1], 150, draw) # close draw.line
