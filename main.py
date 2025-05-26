import utils, save_data
from font_utils import *
import gui
import gui_utils
from group import Group
from tkinterdnd2 import TkinterDnD
from fontTools import ttLib
import PIL
import string
import copy

plugins, names, groups = [], [], []
layer, over_layer = None, None
current_glyph = 'g' # 本' # 'dkshade'
root = None
font = ttLib.TTFont(utils.path("files/1.otf"), recalcBBoxes=True)
font_origin = ttLib.TTFont(utils.path("files/1.otf"), recalcBBoxes=True)
tmp_font = ttLib.TTFont(utils.path("files/1.otf"), recalcBBoxes=True)
hbfont = None
img = PIL.Image.new("L", (200, 200),255) # ini img
units = 1
stop_process = False

from time import perf_counter
def time(msg):
    global last_time
    if not msg :
        print("["+current_glyph+"] ",end='')
        last_time = 0
    if msg == "end": print("")
    elif msg : print( msg+':',str(perf_counter()-last_time).replace('0','-')[0:5], end='  ' )
    last_time = perf_counter()

def get_current_img( key, compute=True ):
    global img
    if compute :
        # time(None)
        for g in groups: # apply algos to pixels
            if g.layers[0].active: # if group is active
                out = glyph_to_img_outline(key, font, g)

                for l in g.layers:
                    if l.active :
                        out = l.run(out)
                        if key is current_glyph : l.save(out) # dont save if txt preview
                if g.n > 0 : out = operator_img(out, prev_img, g.op)
            else:
                if g.n > 0 : out = prev_img
                if g.n== 0 :
                    blk = glyph_to_img_outline(key, font, g)
                    out = PIL.Image.new("L", (blk.width, blk.height),255)# if group is not active
            prev_img = out
        # time("algo")
        if key is current_glyph : img = out # save img if not txt preview
    else : out = img

    if params.display_paths and gui.visual_info :
        out = draw_paths(vectorization( out ), out)
        # time("vecto")
    if params.display_rules and gui.visual_info :
        out = draw_rules(out, key, font )
    # time("end")
    if gui.visual_info and over_layer and over_layer.img and over_layer.active : # show blue gost glyph
        mask = PIL.ImageOps.invert(over_layer.img).point(lambda i: i//3)
        out = out.convert('RGB')
        out.paste((80,160,255), (0,0), mask )
    return out



# import multiprocessing as multi
def text_to_font(txt, out_font, char_to_glyph=True, title='Progress', box=True):
    if char_to_glyph : # remove glyphs allready computed
        txt = utils.get_used_glyphs(txt, font, hbfont)
        gui_utils.used_glyphs.append('space')
        for i in gui_utils.used_glyphs:
            txt2 = [j for j in txt if j != i]
            txt = txt2

    # time(None) # without multi
    if box and len(txt)>0: box = gui_utils.LoadBox(gui.root, title )
    for i, key in enumerate(txt):
        if box:
            if box.stop or globals()['stop_process'] : globals()['stop_process']=True; break
            box.progress['value'] = int( (i/len(txt))*100 )
            box.txt.set('Computed glyph :\n[' + key +"]\n"+ str(i)+'/'+str(len(txt)) )
            gui.root.update() # gui.root.update_idletasks()

        global current_glyph
        old_current_glyph = current_glyph[:]
        current_glyph = key[:]
        gui.visual_info=False
        try: path_to_font(vectorization(get_current_img(key)),key, out_font)
        except Exception as e: print(key,'error',e)
        gui.visual_info=True
        current_glyph = old_current_glyph[:]
        gui_utils.used_glyphs.append(key)
    if box and len(txt)>0: box.top.destroy()
    # time("End")
    out_font = copy.deepcopy(font_origin)

    # time(None) # pool
    # gost_groups = [g.gost() for g in groups]
    # args = [(key, params, gost_groups, font) for key in txt]
    # with multi.Pool( utils.constrain(len(txt),2,multi.cpu_count()-1) ) as p:
    #     result = p.map(process_to_path, args, chunksize=10)
    #     p.terminate()
    # for r in result:
    #     path_to_font(r[0], r[1], out_font)
    # time('Pool[ glyph: '+str(len(txt))+' process: '+str(utils.constrain(len(txt),2,multi.cpu_count()-1))+']')


# def process_to_path(args): # only used with pool
#     (key, param, groups, font) = args
#     for g in groups: # apply algos to pixels
#         img = glyph_to_img_outline(key, font, g)
#         for l in g.layers:
#             if l.active : img = l.run(img)
#         if g.n > 0 : img = operator_img(img, prev_img, g.op)
#         prev_img = img
#     return (vectorization(img, param), key)


def process_font_export(path='', name=None, style=None, flag='all'):
    global font
    isString = False
    gs = font.getGlyphSet()
    if "all" in flag : # filter GLYPH SETS
        pass
    elif any(x in flag for x in gui.gs_flags):
        glyphs = ""
        if "punctuation" in flag : glyphs += string.punctuation
        if "digits" in flag : glyphs += string.digits
        if "uppercase" in flag : glyphs += string.ascii_uppercase
        if "lowercase" in flag : glyphs += string.ascii_lowercase
        gs = glyphs
        isString = True
    else:
        gs = flag
        isString = True

    text_to_font(gs, font, char_to_glyph=isString, title="Export font")

    # if font['glyf'] : font['maxp'].recalc(font)
    rename_font(font, name, style )
    font.save( utils.path( path )  )
    font = copy.deepcopy(font_origin)

def select_layer( selected ):
    global layer
    layer = selected
    for child in gui.gui_para.content.winfo_children(): child.destroy()
    for grp in groups :
        for lay in grp.layers :
            lay.gui_button.state(["!selected"])
    if selected :
        layer.gui_button.state(["selected"])
        layer.gui( gui.gui_para.content )
    gui.gui_para.updateContent()

    print('SELECT_LAYER : group',layer.group.n,' - layer', layer.n)

def new_layer(i, refresh=True):
    print('SELECT_LAYER : group',layer.group.n,' - layer', layer.n)
    layer.group.new_layer(i, refresh=refresh)

def new_group():
    groups.append( Group() )
    gui.refresh()
    print('NEW GROUP : ', layer.group.n)

def del_group(grp, select_last=True):
    if grp.n != 0 :
        print('DELETE GROUP : ', grp.n)
        g = groups[grp.n]
        for l in reversed(g.layers) : g.del_layer(l.n, False)
        if g.op_frame :   g.op_frame.destroy()
        if g.drag_frame : g.drag_frame.destroy()
        del groups[grp.n]
        for i in range(len(groups)) : groups[i].position(i)
        if select_last :
            if layer.group.n == grp.n : select_layer( groups[0].layers[-1] )
        gui.refresh()


def duplicate_layer( g=None, refresh=True ):
    if  layer.n != 0 : # do mnothing if selected layer is group path
        if g==None : g = layer.group
        l_old = layer
        g.new_layer(layer.ref_plugin, refresh=False)

        for name, val in utils.get_layer_attr( l_old ):
            setattr(layer, name, val)

        print('###',layer.active)
        if not layer.active : layer.toggle(refresh=False, unify=True)
        layer.gui( gui.gui_para.content )
        select_layer(layer)
        if refresh : gui.refresh()

def duplicate_group():
    g_old = layer.group
    new_group()
    for name, val in utils.get_layer_attr( g_old.layers[0] ): setattr(layer, name, val) # setup outline param
    for l in g_old.layers[1:] :
        select_layer(l)
        duplicate_layer( g = groups[-1], refresh=False )


def main():

    try: # test if LivingPath is allready running (bugfix cahn-hillard on MAC )
        si = utils.SingleInstance()
    except e:
        print("SingleInstance check error ",e)
        runApp()
    else :
        if si.is_running:
            print("This app is already running!")
        else :
            runApp()

def runApp():
        gui.root = TkinterDnD.Tk()  # notice - use this instead of tk.Tk()
        gui.root.config(cursor="watch");

        # gui.root.attributes('-alpha',0)
        gui.global_Interface(gui.root)
        # gui.root.overrideredirect(0) # desable update gui
        # gui.root.withdraw() # hide gui
        gui_utils.close_splash_screen()
        # gui.root.attributes('-alpha',1)

        try:                   gui.load_new_font( utils.path(save_data.readParamFile(1)) )
        except Exception as e: gui.load_new_font( utils.path("files/1.otf") )
        gui.show_glyph('next'); gui.show_glyph('prev') # regularize current glyph if not in font

        gui_utils.used_glyphs = list(font.getGlyphSet().keys())
        gui.root.config(cursor="")
        utils.check_time(gui.root)

        # gui.root.deiconify()
        # gui.root.overrideredirect(False) # desable update gui
        # gui_utils.set_full_screen(gui.root)
        gui.root.mainloop()
        si.clean_up()


if __name__ == "__main__":
    # multi.freeze_support() # multiprocessing compatibility for pyinstaller
    print('RUN FROM MAIN')
    main()
