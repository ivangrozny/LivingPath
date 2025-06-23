import sys, os
import pathlib
import ctypes
import contextlib
import freetype as ft # freetype-py
import numpy as np
import uharfbuzz as hb
margin = 100

def load_plugins():
    plugins, names = [], []
    # alternative to importlib :
    from plugins import blur
    from plugins import polygonize
    # from plugins import polygonize2
    from plugins import pixel
    from plugins import quality_loss
    from plugins import noise
    from plugins import dilate_erode
    from plugins import seam_carving
    from plugins import center_line_vectors
    from plugins import center_line_pixels
    from plugins import particles
    # from plugins import particles2
    from plugins import cahn_hilliard
    # from plugins import cahn_hilliard2
    from plugins import reaction_diffusion
    for i in sys.modules.keys() :
        if i.startswith("plugins.") :
            plugins.append( eval(i.split('.')[1]) )
            names.append( i.split('.')[1] )
    # for i in os.listdir( path("plugins") ):
    #     if not i.startswith("__") and i.endswith(".py") :
    #         name = i.split('.')[0]
    #         print("LOADED PLUGIN : " + name)
    #         plugins.append( importlib.import_module("plugins." + name) )
    #         names.append( name )
    return plugins, names
############## DATA ######################################################
def path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    relative_path.replace('/', os.path.sep)

    return os.path.join(base_path, relative_path)

def path_name(path): return pathlib.Path(path).stem
def path_ext(path): return pathlib.Path(path).suffix
def path_dir(path): return pathlib.Path(path).parent

def get_layer_attr(l):
    data = []
    for attr in dir(l) :
        value = getattr(l, attr)
        if not callable(value) and not (attr.startswith(("__","gui_")) or attr in ("group","frame","name","n") ) :
            data.append( (attr, value) )
            # print('---', attr, type(value).__name__)
    return data

def next_key(dict, key):
    keyList = sorted(dict.keys(), key=len )
    for i,v in enumerate(keyList):
        if v == key:
            return keyList[ (i+1) % len(keyList) ]
    return keyList[0]
def prev_key(dict, key):
    keyList = sorted(dict.keys(), key=len )
    for i,v in enumerate(keyList):
        if v == key:
            return keyList[ (i-1) % len(keyList) ]
    return keyList[0]
def next_item(list, glyph):
    for i in range(len(list)) :
        if list[i] == glyph :
            return list[i+1 % len(list)]
def prev_item(list, glyph):
    for i in range(len(list)) :
        if list[i] == glyph :
            return list[i-1 % len(list)]

            ############## MATHS ######################################################

def mapping(x,a,b,A,B):
    return  ((x-a)/(b-a)) * (B-A) + A

def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def ellipse(size,x,y, fill, draw):
    s = int(size/2)
    draw.ellipse((x-s,y-s,x+s,y+s), fill )
def rectangle(size,x,y, fill, draw):
    s = int(size/2)
    draw.rectangle((x-s,y-s,x+s,y+s), fill )
def is_over(pos, z):
    if pos[0] > z[0] and pos[0] < z[2]:
        if pos[1] > z[1] and pos[1] < z[3]:
            return True
    return False
def constrain(val, min_val, max_val):
    if   val < min_val: val = min_val
    elif val > max_val: val = max_val
    return val

def get_used_glyphs(txt, ttfont, hbfont):
    charlist = np.unique(list(txt)).tolist()
    glyphs = []
    # for i in charlist : # try to convert without huarfbuzz
    #     try:
    #         glyphs.append(font.getBestCmap()[ord(i)] )
    #     except Exception as e:
    #         print("(utils.py) Char to glyph error : '"+i+"'")

    features = {"kern": True, "liga": True} # convert glyphs name with huarfbuzz
    buf = hb.Buffer()
    buf.add_str(txt)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, features)

    for info in buf.glyph_infos:
        gid = info.codepoint
        glyphs.append( ttfont.getGlyphName(gid) )

    return np.unique(glyphs).tolist()


def cutWords(txt):
    n = 7 # char per words
    words = txt.split(' ')
    out = []
    for w in words :
        if len(w) > 14 :
            list = [w[i:i+n] for i in range(0, len(w), n)]
            list[-1] += ' '
            out.extend(list)
        else :
            out.append( w + ' ' )
    return out

def center_window(window, resize=True):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    if resize: window.geometry(f"{width}x{height}+{x}+{y}")
    if not resize: window.geometry(f"{1}x{1}+{x}+{y}")

    ############## DRAW PIL ######################################################

def ellipse(size,x,y, fill, draw):
    s = int(size/2)
    draw.ellipse((x-s,y-s,x+s,y+s), fill )
def rectangle(size,x,y, fill, draw):
    s = int(size/2)
    draw.rectangle((x-s,y-s,x+s,y+s), fill )

    ############## fontTools outlines ######################################################

@contextlib.contextmanager
def new_outline(n_points, n_contours):
    library = ft.get_handle()
    raw_ft_outline = ft.FT_Outline()
    err = ft.FT_Outline_New( library, ft.FT_UInt(n_points), ft.FT_Int(n_contours), ctypes.byref(raw_ft_outline) )
    if err: raise ft.FT_Exception(err)
    try:
        raw_ft_outline.n_points   = 0
        raw_ft_outline.n_contours = 0
        yield ft.Outline(raw_ft_outline)
    finally:
        ft.FT_Outline_Done(library, ctypes.byref(raw_ft_outline))

############## check time ######################################################
import sys
import os

try:
    import fcntl
except ImportError:
    fcntl = None

LOCK_PATH = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "lock")
OS_WIN = False
if 'win32' in sys.platform.lower():
    OS_WIN = True


class SingleInstance:
    def __init__(self):
        self.fh = None
        self.is_running = False
        self.do_magic()

    def do_magic(self):
        if OS_WIN:
            try:
                if os.path.exists(LOCK_PATH):
                    os.unlink(LOCK_PATH)
                self.fh = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except EnvironmentError as err:
                if err.errno == 13:
                    self.is_running = True
                else:
                    raise
        else:
            try:
                self.fh = open(LOCK_PATH, 'w')
                fcntl.lockf(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except EnvironmentError as err:
                if self.fh is not None:
                    self.is_running = True
                else:
                    raise

    def clean_up(self):
        # this is not really needed
        try:
            if self.fh is not None:
                if OS_WIN:
                    os.close(self.fh)
                    os.unlink(LOCK_PATH)
                else:
                    fcntl.lockf(self.fh, fcntl.LOCK_UN)
                    self.fh.close() # ???
                    os.unlink(LOCK_PATH)
        except Exception as err:
            # logger.exception(err)
            raise # for debugging porpuses, do not raise it on production
