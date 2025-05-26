from utils import *
import font_utils, gui, gui_utils
from PIL import ImageTk, Image
import tkinter as tk
from tkinter import TclError, ttk, Tk, Frame, Menu, Label, Entry
from functools import partial
from tkhtmlview import HTMLLabel
import platform
import importlib
used_glyphs = []
slow_icon = '⏳'
if platform.system().startswith('Linux') or platform.system() == "Darwin" : slow_icon = '[slow]'


class Slider(ttk.Frame):
    def __init__(s, context, size=200, min=0,max=100, layer=None, name='', format="%d", flag='', ini=0, slow=False, callback=None):
        super(Slider, s).__init__(context)
        s.callback = callback
        s.format = format
        s.name = name.replace(' ', '_')
        s.flag = flag
        s.ini = ini
        s.layer = font_utils.params if layer == None else layer
        if not hasattr(s.layer, s.name) : s.set_attach_val(ini) # set ini only at layer init

        s.val = ttk.Label(s, text = s.format % s.get_attach_val()) # display fix slider number
        s.val.grid(column=1, row=1, sticky=tk.W, padx=5 )
        s.slider_var = tk.DoubleVar()
        s.slider = ttk.Scale(s, from_=min, to_=max, length=size, orient='horizontal', style='Tick.TScale', variable=s.slider_var )
        s.slider_var.set( s.get_attach_val() )
        s.slider.configure(command = s.update)
        s.slider.bind('<Button-1>', s.onclick)
        s.slider.bind('<Button-2>', lambda x: s.set_ini() )
        s.slider.bind('<Button-3>', lambda x: s.set_ini() )
        # s.slider.bind('<ButtonRelease-1>', s.update_eco) # unused
        s.slider.grid(column=0, row=1, sticky=tk.W)

        s.title = ttk.Label(s, text = name.replace('_',' ') if not slow else name.replace('_', ' ')+'  '+slow_icon )
        s.title.grid(column=0, row=0, sticky=tk.W)
        s.increment = 2


    def update(s, event):
        s.val.configure(text=s.get())
        if ( s.flag!='eco' ) and getattr( s.layer, s.name )!= None :
        # if ( s.flag!='eco' and not font_utils.display_points ) and getattr( s.layer, s.name )!= None :
            s.set_attach_val()
            if s.callback : s.callback()
            gui.show_glyph()

    def update_eco(s, event):
        if ( s.flag=='eco' ) and getattr( s.layer, s.name )!= None :
        # if ( s.flag=='eco' or font_utils.display_points ) and getattr( s.layer, s.name )!= None :
            s.set_attach_val()
            if s.callback : s.callback()
            gui.show_glyph()

    def set_attach_val(s, val=None ):
        if val==None : val = s.get() # if not ini
        if s.format == '%d' : setattr(s.layer, s.name, int(val))
        if s.format != '%d' : setattr(s.layer, s.name, float(val))
    def get_attach_val(s):
        return getattr(s.layer, s.name)
    def get(s):
        return s.format % float( s.slider.get() )
    def switch(s): switch(s)
    def set_ini(s): # set to ini val (right click)
        s.slider.set(s.ini)
        s.set_attach_val(s.ini)
        return 'break'
    def onclick(s, e): # disable click on slider ( that caused bug with heavy computing load )
        if s.slider.identify(e.x, e.y) == 'Horizontal.TickScale.trough': return 'break'
        else: return None


class LockSliders(ttk.Frame):
    def __init__(s, context, ini, slider1, slider2):
        super(LockSliders, s).__init__(context)
        s.s1, s.s2 = Slider(s,**slider1), Slider(s,**slider2)
        s.s1.grid(row=0, column=0, sticky='w')
        s.s2.grid(row=1, column=0, sticky='w')
        s.layer = s.s1.layer
        s.name = s.s1.name+s.s2.name
        s.ico_on = get_img('lock-on.png', (20,50))
        s.ico_off = get_img('lock-off.png', (20,50))
        s.b = ttk.Checkbutton( s, style='no_indicatoron.TCheckbutton', command=s.toggle, takefocus=False)
        gui.root.update()
        s.b.grid(row=0, column=1, rowspan=3, sticky='s', pady=(0,3))
        s.b.bind('<Enter>', s.onEnter )
        s.b.bind('<Leave>', s.onLeave )
        if hasattr(s.layer, s.name) : s.lock = not getattr( s.layer, s.name )
        else : s.lock = not ini # set ini only at layer init
        s.toggle()
    def toggle(s):
        s.lock = not s.lock
        if s.lock: s.b['image'], s.s1.callback, s.s2.callback = s.ico_on, s.set_s2, s.set_s1
        else:      s.b['image'], s.s1.callback, s.s2.callback = s.ico_off, None, None
        if s.lock and s.s2.get() != s.s1.get() :
            s.set_s2()
            gui.show_glyph()
        setattr(s.layer, s.name, s.lock)
    def set_s1(s):
        s.s1.slider_var.set( s.s2.get() ) # update slider without trigger command
        s.s1.val.configure(text=s.s2.get()) # update label
        s.s1.set_attach_val() # update attached layer val
    def set_s2(s):
        s.s2.slider_var.set( s.s1.get() ) # update slider without trigger command
        s.s2.val.configure(text=s.s1.get()) # update label
        s.s2.set_attach_val() # update attached layer val
    def switch(s, flag=None): switch(s.s1,s.s2,s.b, flag=flag)
    def onEnter(s, e): s.b['image'] = s.ico_off if s.lock else s.ico_on
    def onLeave(s, e): s.b['image'] = s.ico_on if s.lock else s.ico_off

class Checkbutton(ttk.Frame):
    def __init__(s, context, layer=None, name='', ini=False, slow=False, callback=None):
        super(Checkbutton, s).__init__(context)
        s.context = context
        s.callback = callback
        s.name = name.replace(' ', '_')
        s.layer = font_utils.params if layer == None else layer
        s.var = tk.StringVar()
        if not hasattr(s.layer, s.name) : s.set_attach_val(ini) # set ini only at layer init
        s.var.set( s.get_attach_val() )
        s.check = ttk.Checkbutton( s, text=name.replace('_',' ') if not slow else name.replace('_', ' ')+'  '+slow_icon, variable=s.var )
        s.check.configure(command=s.update, takefocus=0)
        s.check.grid(column=0, row=0, sticky=tk.W)

    def update(s, val='undefined'):
        if getattr( s.layer, s.name ) != None and val != int(s.var.get()):
            if val != 'undefined': s.var.set(val)
            s.set_attach_val()
            if s.callback : s.callback()
            gui.show_glyph()

    def set_attach_val(s, val=False):
        if not val : val = s.var.get()
        setattr(s.layer, s.name, int(val or 0))

    def get_attach_val(s):
        return getattr(s.layer, s.name)

    def select(s):
        if int(s.var.get()) == 0 : s.check.invoke()

#--------------------------------------------------------------------------------
class ButtonImage(ttk.Button):
    def __init__(s, context, img_name="", flag=None, hover=None, style="custom.TButton", size=20, *args,**kwargs):
        super(ButtonImage, s).__init__(context, style=style, *args,**kwargs)
        s.img_name = img_name
        s.flag = flag
        s.hover = hover
        s.active = True
        if img_name :
            s.ico_on  = get_img(img_name+'-on.png', (size,size))
            s.ico_off = get_img(img_name+'-off.png', (size,size))
            s.ico_on_alt = get_img(img_name+'-on-alt.png', (size,size)) if s.flag in ('click','drag') else None
            s.ico_off_alt = get_img(img_name+'-off-alt.png', (size,size)) if s.flag in ('click','drag') else None

            if hover : s.bind('<Enter>', s.enter )
            if hover : s.bind('<Leave>', s.leave )
            if not hover : s.enter(None)
            if hover : s.leave(None)

    def setCommand(s, c): s.config( command = c )

    def enter(s,e):
        s['image'] = s.ico_on  if s.active else s.ico_off
        if s.flag=='click': s['image'] = s.ico_on  if s.active else s.ico_off
        if s.hover:         s['image'] = s.ico_on
        if s.flag=='drag':  s['image'] = s.ico_on if s.active else s.ico_off
    def leave(s,e):
        s['image'] = s.ico_off if s.active else s.ico_off_alt if s.flag=='click' else s.ico_on ;
        if s.hover : s['image']=s.ico_off
        if s.flag=='drag' : s['image'] = s.ico_on_alt if s.active else s.ico_off_alt

    def toggle(s, layer_is_active=True):
        s.active = not s.active
        s.enter(None)


#--------------------------------------------------------------------------------

class Optionbutton(ttk.Frame):
    def __init__(s, context, layer=None, nbr=0, ini=0, pos='inline', name='', img_name=None, callback=None):
        super(Optionbutton, s).__init__(context)
        s.layer = font_utils.params if layer == None else layer
        s.name = name.replace(' ', '_')
        if img_name : name = img_name
        s.label = ttk.Label(s, text = s.name.replace('_',' ')+" : ")
        s.label.grid(column=0, row=0, sticky=tk.W, padx=0, pady=0 )
        s.callback = callback
        s.ico_off, s.ico_on, s.b = [], [], []
        for i in range(nbr) :
            s.ico_on.append( get_img(name+'-on-'+str(i)+'.png', (20,20)) )
            s.ico_off.append( get_img(name+'-off-'+str(i)+'.png', (20,20)) )
            s.b.append( ttk.Checkbutton(s, style='no_indicatoron.TCheckbutton',
                command=partial(s.set,i), takefocus=False ) )
            s.b[i].grid( row=0, column=i+1, padx=(0,0) )
            s.b[i].bind('<Enter>',  partial(s.onEnter, i) )
            s.b[i].bind('<Leave>',  partial(s.onLeave, i) )

        if hasattr(s.layer, s.name) : ini = getattr(s.layer, s.name) # set ini only at layer init
        s.set(ini, refresh=False)

    def set(s, i, refresh=True):
        s.var = i
        for i in range(len(s.b)) : s.b[i]['image'] = s.ico_on[i] if i==s.var else s.ico_off[i]
        setattr(s.layer, s.name, int(s.var or 0))
        if s.callback : s.callback()
        if refresh: gui.refresh()

    def onEnter(s, i, e): s.b[i]['image']=s.ico_on[i]
    def onLeave(s, i, e):
        if s.var != i: s.b[i]['image']=s.ico_off[i]

#----------------------------------------------------------------------------------

def switch(*elems, flag=None):
    for gui_elem in elems:
        for child in gui_elem.winfo_children():
            if hasattr(child, 'state'):
                print("state",child["state"]) # idk why not working without this print...
                if flag==False: child.configure(state='disabled')
                if flag==True : child.configure(state='normal')
                if flag==None :
                    if child["state"] == "normal": child.configure(state='disabled')
                    else: child.configure(state='normal')
                    # child.state(["disabled"]) # not working (ttk)
#----------------------------------------------------------------------------------

class Separator(ttk.Separator):
    def __init__(s, context, layer=None ):
        super(Separator, s).__init__(context)

#----------------------------------------------------------------------------------
def get_img(name, size=0):
    img = Image.open(path('files/theme/'+name))
    size = ( round(size[0]), round(size[1]) )
    img = img.resize(size, resample=Image.Resampling.LANCZOS)

    img = ImageTk.PhotoImage(img)

    # reduce image with TK insted of PIL (DPI pb with both)
    # img = tk.PhotoImage(file=path('files/theme/'+name))

    # img.subsample(4)
    return img


#----------------------------------------------------------------------------------

class ScrolledFrame(): # https://github.com/nikospt/tk-ScrolledFrame/
    def __init__( s, parent, side='right', axis='y', speed=15, *args, **kwargs):
        s.container = ttk.Frame(parent)
        s.canvas = tk.Canvas( s.container, *args, **kwargs)
        s.content = ttk.Frame(s.canvas)
        s.parent = parent
        s.root = parent.winfo_toplevel()
        s.side = side
        s.speed = speed
        s.xscrollbar = None
        s.yscrollbar = None
        if axis == 'y' or axis == 'xy' or axis == 'yx' or axis == 'both':
            s.yscrollbar = ttk.Scrollbar( s.container, orient='vertical', command=s.canvas.yview)
        if axis == 'x' or axis == 'xy' or axis == 'yx' or axis == 'both':
            s.xscrollbar = ttk.Scrollbar( s.container, orient='horizontal', command=s.canvas.xview)
        s.contentId = s.canvas.create_window( (0,0), window=s.content, anchor='nw')
        s.root.bind("<Configure>", s.resize)


    def updateContent(s):
        s.content.update()
        if s.yscrollbar != None :
            s.yscrollbar.pack( side=s.side,  fill='y', padx=(5,5) )
            # s.canvas.configure( yscrollcommand=s.yscrollbar.set, scrollregion="0 0 0 %s" % s.content.winfo_height() )
            s.canvas.configure( yscrollcommand=s.yscrollbar.set, scrollregion=s.canvas.bbox("all"), yscrollincrement=s.speed )
            if s.canvas.yview() == (0.0, 1.0) : # content fit container
                if s.side=="left": s.yscrollbar.place(width=0, height=0) # hide
                [s.UnBindMouseWheel(x) for x in [s.content,s.canvas,s.container]]
            else :
                # s.yscrollbar.pack_forget()
                if s.side=="left": s.yscrollbar.place(anchor="nw", width=20, height=s.container.winfo_height()) # show
                [s.BindMouseWheel(x) for x in [s.content,s.canvas,s.container]]
                s.bindChildren( s.content)

        s.canvas.pack( side='top', fill='y', expand=True, padx=(20,0) if s.side=="left" else (0,0) )
        s.container.update()
        s.resize()

    def BindMouseWheel(s, widget):
        if s.root.call('tk', 'windowingsystem') == 'x11':
            widget.bind('<Button-4>',s.scrolldown)
            widget.bind('<Button-5>',s.scrollup)
        else: widget.bind('<MouseWheel>',s.scrollMouseWheel)
    def UnBindMouseWheel(s, widget):
        if s.root.call('tk', 'windowingsystem') == 'x11':
            widget.unbind('<Button-4>')
            widget.unbind('<Button-5>')
        else: widget.unbind('<MouseWheel>')

    def scrollMouseWheel(s,e):
        if e.delta > 100 or e.delta < -100 : # detect windows scrolling style
            s.canvas.yview_scroll( int(-1*e.delta/120), 'units' ) # windows proof
        else :
            s.canvas.yview_scroll( int(-1*e.delta),     'units' ) # mac proof
    def scrolldown(s,e): s.canvas.yview_scroll( int(-1 ), 'units' ) # linux
    def scrollup(s,e):   s.canvas.yview_scroll( int( 1 ), 'units' ) # linux

    def bindChildren(s,widget):
        children = widget.winfo_children()
        if len(children) != 0:
            for child in enumerate(children):
                s.BindMouseWheel(child[1])
                s.bindChildren(child[1])

    def grid(s,*args, **kwargs): s.container.grid(*args,**kwargs)
    def pack(s,*args, **kwargs): s.container.pack(*args,**kwargs)

    def resize(s,*args):
        height = min( [s.content.winfo_height(), s.parent.winfo_height()-10 ] )
        s.canvas.configure( height=height, width=s.content.winfo_width() )
def scroll_letter(e):
    if e.delta > 0 : gui.show_glyph('prev')
    if e.delta < 0 : gui.show_glyph('next')

# def get_calling_module():
#     name = inspect.getmodule(inspect.stack()[2][0]).__name__.split('.')[-1]
#     print('get calling module', name)
#     return font_utils if name == 'gui' else get_plugin(name)

#----------------------------------------------------------------------------------
def set_icon(widget):
    if platform.system()=="Windows" :
        widget.iconbitmap(default=path('files/logo2.ico'))
    elif platform.system()=="Darwin" :
        widget.iconphoto(True, ImageTk.PhotoImage(Image.open(path('files/logo.png'))))
    else :
        widget.iconphoto(True, ImageTk.PhotoImage(Image.open(path('files/logo.png'))))

#----------------------------------------------------------------------------------
class AskBox(object):
    root = None
    def __init__(s, root, title, data=None, callback=None, btn1='Export', btn2='Cancel'):
        """ data = <sequence> (dictionary, key) to associate with user input
        (providing a sequence for data creates an entry for user input) """
        s.root = root
        s.root.attributes("-fullscreen", False)
        s.top = tk.Toplevel(s.root)
        s.top.title(title)
        s.top.attributes('-topmost', 'true')
        s.callback = callback
        frame = ttk.Frame(s.top)
        frame.pack(fill='both', expand=True, padx=50, pady=50)

        s.entries = {}
        for key, val in data.items():
            if (key.startswith('combo:')):
                label = ttk.Label(frame, text=key[6:])
                label.pack(fill='x', expand=True, padx=0, pady=(20,0))
                s.entries[key] = ttk.Combobox(frame, values=val)
                s.entries[key].pack(fill='x', expand=True, pady=10)
                s.entries[key].current(0)
            elif (key.startswith('check:')):
                s.entries[key] = tk.IntVar()
                check = ttk.Checkbutton(frame, text=key[6:], variable=s.entries[key])
                check.pack(fill='x', expand=True, pady=(20,0))
                s.entries[key].set(val)
            elif (key.startswith('label:')):
                label = ttk.Label(frame, text=val)
                label.pack(fill='x', expand=True, padx=0, pady=(20,20))
            else :
                label = ttk.Label(frame, text=key)
                label.pack(fill='x', expand=True, padx=0, pady=(20,0))
                s.entries[key] = ttk.Entry(frame)
                s.entries[key].pack(fill='x', expand=True, pady=10)
                s.entries[key].insert(0, val)

        b_submit = ttk.Button(frame, text=btn1)
        b_submit['command'] = lambda: s.entry_to_dict(data)
        b_submit.pack(side='left', padx=0, pady=(20,0))

        b_cancel = ttk.Button(frame, text=btn2)
        b_cancel['command'] = s.top.destroy
        b_cancel.pack(side='left', padx=(20,0), pady=(20,0))
        s.top.bind('<Return>', lambda event=None: b_submit.invoke() )
        s.top.bind('<Escape>', lambda event=None: b_cancel.invoke() )
        center_window(s.top)

    def entry_to_dict(s, data):
        if s.callback:
            for key, val in data.items():
                entry = s.entries[key].get()
                if entry:
                    data[key] = entry
            s.top.destroy()
            s.callback(data)
        else: s.top.destroy()

class LoadBox(object):
    root = None
    def __init__(s, root, title):
        """ Loading bar """
        s.root = root
        s.root.attributes("-fullscreen", False)
        s.top = tk.Toplevel(s.root)
        s.top.title(title)
        s.top.attributes("-topmost", True)
        s.root.eval(f'tk::PlaceWindow {str(s.top)} center')
        frame = ttk.Frame(s.top)
        frame.pack(fill='both', expand=True, padx=50, pady=30)

        s.txt = tk.StringVar()
        ttk.Label(frame, textvariable=s.txt).pack(fill='x', expand=True, padx=0, pady=(0,0))

        s.progress = ttk.Progressbar( frame, value=0, length=100, mode="determinate" )
        s.progress.pack(fill='x', expand=True, padx=0, pady=(20,0))

        s.stop = False
        b_cancel = ttk.Button(frame, text='Skip')
        b_cancel['command'] = s.cancel
        b_cancel.pack(side='bottom', padx=50, pady=(20,20))
        s.top.bind('<Escape>', lambda event=None: b_cancel.invoke() )


    def cancel(s):
        s.stop = True

#----------------------------------------------------------------------------------
def show_about_menu(root):
    root.attributes("-fullscreen", False)
    top = tk.Toplevel(root, borderwidth=0, padx=0, pady=0) # je ne suis pas arrivé à retirer le border 2px
    #top.attributes('-topmost', 'true')
    top.title("About LivingPath")
    frame = ttk.Frame(top)
    frame.pack(fill='both', expand=True, padx=(0,0), pady=(0,50), ipadx=0, ipady=0)

    img = Image.open(path('files/header.jpg'))
    tkimage = ImageTk.PhotoImage( img.resize(tuple(i//2 for i in img.size)) )
    label = ttk.Label(frame, image = tkimage)
    label.image = tkimage
    label.update()
    label.pack(padx=0, pady=0, ipadx=0, ipady=0)
    with open(path('files/about.html')) as f:
        HTMLLabel(frame, html=f.read(), highlightbackground='white', background="#ffffff", takefocus=False, height=30 ).pack(padx=0, pady=0, ipadx=0, ipady=0)

    top.bind('<Escape>', lambda event=None: top.destroy() )
    top.bind('<Return>', lambda event=None: top.destroy() )
    center_window(top)

def show_shortcut_menu(root):
    top = tk.Toplevel(root)
    root.attributes("-fullscreen", False)
    top.attributes('-topmost', 'true')
    top.title("LivingPath shortcuts & controls")
    frame = ttk.Frame(top)
    frame.pack(fill='both', expand=True, padx=20, pady=40)

    with open(path('files/shortcut.html')) as f:
        HTMLLabel(frame,html=f.read(),highlightbackground='white',background="white", takefocus=False,height=25,width=70).pack(side='left')
    with open(path('files/shortcut2.html')) as f:
        content = f.read().replace('@#$',slow_icon)
        HTMLLabel(frame,html=content,highlightbackground='white',background="white", takefocus=False,height=25,width=70).pack(side='right')

    top.bind('<Escape>', lambda event=None: top.destroy() )
    top.bind('<Return>', lambda event=None: top.destroy() )
    center_window(top)



#----------------------------------------------------------------------------------
def close_splash_screen():
    if platform.system() != "Darwin" and '_PYI_SPLASH_IPC' in os.environ and importlib.util.find_spec("pyi_splash"):
        import pyi_splash
        pyi_splash.update_text('UI Loaded ...')
        pyi_splash.close()
