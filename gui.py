import main, utils, font_utils, save_data, wiki, specimen, ttf2otf
import gui_utils as gu
from PIL import ImageTk, Image
from fontTools.ttLib import TTFont
import tkinter as tk
from tkinter import TclError, ttk, Tk, Frame, Menu, Label, filedialog
from tkinterdnd2 import DND_FILES
from functools import partial
from iso639 import language  # python-iso639 and not iso639
import uharfbuzz as hb
from hyperglot import checker, parse, languages
from playsound3 import playsound # before pip-install: pip install --upgrade setuptools wheel
import re
import platform
from copy import deepcopy
import pprint
visual_info = False

def global_Interface(root):
    main.plugins, main.names = utils.load_plugins() # has to be loaded here
    setup_root(root)
    setup_menubar()

    global gui_zone, gui_para, gui_glob, gui_info
    s = ttk.Style()
    s.configure('red.TFrame', background='#f00')
    frm_style = 'Card.TFrame'
    frm_style = ''
    gui_foot = ttk.Frame(root, style=frm_style)
    gui_info = ttk.Frame(gui_foot, style=frm_style)
    gui_zone = ttk.Frame(root, style=frm_style, takefocus=False)
    ctn_para = ttk.Frame(root, style=frm_style)
    gui_glob = ttk.Frame(ctn_para, style=frm_style)
    gui_view = ttk.Frame(root, style=frm_style)

    grip = ttk.Sizegrip(gui_foot)
    grip.pack(side='right', anchor='se', expand=False, padx=(0, 5), pady=(0, 5))
    grip.bind('<Button-1>', lambda x: root.state('normal') )

    gui_foot.pack(side='bottom', fill='x', expand=True, anchor='s', pady=(5,0), padx=(10,0) )
    gui_info.pack(side='left', fill='x', expand=False, anchor='s')
    gui_zone.pack(side='top', fill='x', expand=False, anchor='n', padx=(15,0), pady=(10,20))
    ctn_para.pack(side='left', fill='y', expand=False, anchor='sw', padx=0, pady=0)
    gui_glob.pack(side='bottom', fill=None, expand=False, anchor='sw', padx=(20,0), pady=(20,0))
    gui_view.pack(side='top', fill='both', expand=True, anchor='n', pady=0)
    # keep min space width in gui_zone
    ttk.Frame(gui_zone, style=frm_style, height=int(0.17*root.winfo_screenheight()), width=2).grid(rowspan=1000, column=0, row=0, padx=0, pady=0 )


    global b_rules, b_paths
    b_rules = gu.Checkbutton(gui_glob, name='display_rules', ini=False)
    s_space = gu.Slider(gui_glob, min=-150,max=250, name='letter_spacing',callback=b_rules.select)
    b_rules.pack(anchor='w', pady=(20,20))
    s_space.pack(anchor='w', pady=(0,10),  padx=(0,40)) # padx to prevent gui_para pushing gui_view
    global vecto
    vecto = ttk.LabelFrame(gui_glob, text="vectorization options", padding=(10, 10))
    vecto.pack(anchor='sw', padx=(0,0), pady=(0,0), fill='both', ipady=0, ipadx=0)
    vecto.bind("<Enter>", lambda _: open_vecto_indicator() )
    vecto.bind("<Leave>", lambda _: close_vecto_indicator() )
    b_paths = gu.Checkbutton(vecto, name='display_paths', ini=False, slow=True)
    b_paths.pack(anchor='w')
    gu.Slider(vecto, min=0.01, max=2, name='accuracy', format='%0.2f', ini=1,callback=b_paths.select).pack(anchor='w')
    gu.Slider(vecto, max=1.5, name='simplify_path', format='%0.2f', ini=0.45,callback=b_paths.select).pack(anchor='w')
    gu.Slider(vecto, max=1.34, name='curves_limit', format='%0.2f', ini=0.90,callback=b_paths.select).pack(anchor='w')
    # gu.Slider(vecto, max=500, name='min' , ini=2).pack(anchor='w')
    close_vecto()

    gui_para = gu.ScrolledFrame(ctn_para, side='left', takefocus=False )
    gui_para.pack(side='top', fill='y', expand=True, anchor='nw' )

    global gui_font_info
    gui_font_info = dict.fromkeys(['name','format','unit','numG','glyph'])
    for i, k in enumerate(gui_font_info) :
        gui_font_info[k] = tk.StringVar()
        ttk.Label(gui_info, textvariable=gui_font_info[k] ).grid(column=i, row=0, padx=20, pady=(5,10) )

    refresh_button = gu.ButtonImage(root, text="refresh", size=24, hover=True, img_name="update", command = refresh_txt)
    refresh_butto2 = gu.ButtonImage(root, text="text",    size=24, hover=True, img_name="text", command = new_wiki)
    refresh_butto2.place(in_=gui_zone, relx=1, rely=1, x=-30, y=-50, anchor="ne")
    refresh_button.config(style='big.TButton')
    refresh_butto2.config(style='big.TButton')

    global img_letter, frame_txt
    frame_ltr = ttk.Frame(gui_view, style=frm_style)
    frame_txt = gu.ScrolledFrame(gui_view, side='right', speed=70)

    gui_view.columnconfigure(0, weight=1, uniform='a')
    gui_view.columnconfigure(1, weight=1, uniform='a')
    frame_ltr.grid(row=0,column=0, sticky='ewns')
    frame_txt.grid(row=0,column=1, sticky='ewns')

    img = ImageTk.PhotoImage(main.img)
    img_letter = Label(frame_ltr, image=img)
    # img_letter.pack(side = 'top')
    img_letter.place(relx=.5, rely=.5, anchor="center")

    for w in frame_ltr, img_letter:
        w.bind('<MouseWheel>', gu.scroll_letter)
        w.bind('<Button-1>', lambda x: show_glyph("next") )
        w.bind('<Button-3>', lambda x: show_glyph("prev") )

    global img_txt
    img_txt = []
    for i in range(6):
        img_txt.append( Label(frame_txt.content, image=ImageTk.PhotoImage(main.img)) )
        img_txt[i].pack( ipadx=0, ipady=0,  fill='x', expand=True)

    wiki.get_wiki_langs()
    try: wiki.set_wiki_lang( save_data.readParamFile(0) )
    except: wiki.set_wiki_lang( 'en' )
    refresh_butto2.update()
    refresh_button.place(in_=gui_zone, relx=1, rely=1, x=-30-4-refresh_butto2.winfo_width() , y=-50, anchor="ne")

    main.new_group()
    # main.new_layer(11) # test

def open_vecto(*args):
    global vecto
    for widget in vecto.winfo_children(): widget.pack( )
    vecto.bind('<Button-1>', close_vecto )
def close_vecto(*args):
    global vecto
    for widget in vecto.winfo_children(): widget.pack_forget()
    b_paths.pack(anchor="w")
    vecto.bind('<Button-1>', open_vecto )
def open_vecto_indicator():  global vecto ; vecto["text"] = "vectorization options ..."
def close_vecto_indicator(): global vecto ; vecto["text"] = "vectorization ..."



def refresh(compute=True, clear_glyphs=True):
    if compute and clear_glyphs : gu.used_glyphs.clear()
    global visual_info
    visual_info=True
    img = main.get_current_img(main.current_glyph, compute=compute)
    m = 0 # font_utils.imgMargin
    img = img.crop((m, m, img.width-m, img.height-m)).resize((img.width//2,img.height//2),1)
    refresh_img(img_letter, img)

def refresh_txt(compute=True):
    if not compute : gu.used_glyphs = list(main.font.getGlyphSet().keys())
    root.config(cursor="watch");
    root.update_idletasks()
    # main.time(None)

    # print('\n',frame_txt.container.winfo_width(),
    #         frame_txt.canvas.winfo_width(),
    #         frame_txt.content.winfo_width(),
    #         frame_txt.yscrollbar.winfo_width())
    ctn_width = frame_txt.container.winfo_width()-30

    main.text_to_font(wiki.title, main.tmp_font, title="Process title", box=compute)
    # main.time("process title")
    refresh_img(img_txt[0], text_titre(wiki.title, ctn_width, 130)) ; frame_txt.updateContent()
    # main.time("display title")
    main.text_to_font(wiki.start, main.tmp_font, title="Process subtitle", box=compute)
    refresh_img(img_txt[1], text_block(wiki.start, 85, ctn_width ))
    main.text_to_font(wiki.sum, main.tmp_font, title="Process text", box=compute)
    refresh_img(img_txt[2], text_block(wiki.sum, 55, ctn_width ))
    refresh_img(img_txt[3], text_block_double(wiki.sum, 45, ctn_width ))
    refresh_img(img_txt[4], text_block('From wikipedia creative commons', 45, ctn_width ))

    # main.text_to_font("LivingPath", main.tmp_font, title="Process title")
    # refresh_img(img_txt[0], text_titre("LivingPath", ctn_width, 200)) ; frame_txt.updateContent()
    # txt2 = "Generative font modification software. February 2025"
    # main.text_to_font(txt2, main.tmp_font, title="Process title")
    # refresh_img(img_txt[1], text_titre(txt2, ctn_width, 100)) ; frame_txt.updateContent()

    # main.text_to_font("LivingPath", main.tmp_font, title="Process text" )
    # refresh_img(img_txt[0], text_titre("LivingPath", ctn_width, 150))

    frame_txt.updateContent()
    # main.time("all texts")
    root.config(cursor="")
    main.stop_process=False
    refresh(clear_glyphs=False)
    if not compute : gu.used_glyphs.clear()

def refresh_img(label, img):
    img = ImageTk.PhotoImage(img)
    label.configure( image = img )
    label.image = img
    label.update()

def text_line(txt, w, h, dir='rl'):
    img = font_utils.text_to_img_HB(txt, main.tmp_font, main.hbfont)
    img.thumbnail((w,h+22), Image.Resampling.LANCZOS)
    img = img.crop((0, 22, img.width, h+22 ))
    return img #

def text_titre(txt, w, h, dir='rl'):
    bg = Image.new('L', (w, 3000), (255))
    stack, y = '', 0
    for word in utils.cutWords(txt):
        if len(stack) < 7 :
            stack += word
        else:
            bg.paste( text_line(stack,w*2+1000,h,dir='rl'), (0,y) )
            y += h
            stack = word
    if stack != '' : bg.paste( text_line(stack,w*2+1000,h,dir='rl'), (0,y) )

    bg = bg.crop((0, 0, w, y+h ))
    return bg

def text_block(txt, txt_size, w, dir='rl' ):
    bg = Image.new('L', (w+500, 4000), (255))
    i, y, x, max, lh = 0, 0, 0, 0, 0
    for word in utils.cutWords(txt) :
        img = main.text_to_img_HB(word, main.tmp_font, main.hbfont)
        img.thumbnail((3000, txt_size), Image.Resampling.LANCZOS)
        lh = img.height
        if x+img.width > bg.width :
            y += lh # interlignage
            if max < x : max = x # line width max
            x = 0
            if y > bg.height-lh : break
        bg.paste(img, (x, y) )
        x += img.width
    bg = bg.crop((0, 0, max, y+lh+40 ))
    bg.thumbnail((w, 2000), Image.Resampling.LANCZOS)
    return bg

def text_block_double(txt, txt_size, w, dir='rl'):
    words = txt.split(' ')
    txt1 = ' '.join( words[0:len(words)//2] )
    txt2 = ' '.join( words[len(words)//2:] )
    bg = Image.new('L', (w, 3000), (255))
    img = text_block(txt1, txt_size, w//2-20, dir='rl' )
    im2 = text_block(txt2, txt_size, w//2-20, dir='rl' )
    bg.paste(img, (0,0) )
    bg.paste(im2, (img.width+40,0) )
    bg = bg.crop((0, 0, w, max(img.height,im2.height) ))
    return bg

def show_glyph(flag='', char=''):
    glyph_set = main.font.getGlyphSet()
    if flag=='prev': main.current_glyph = utils.prev_key(glyph_set, main.current_glyph)
    if flag=='next': main.current_glyph = utils.next_key(glyph_set, main.current_glyph)

    try: # input key to glyph name
        saved = main.current_glyph[:]
        if char != '': main.current_glyph = font_utils.char_in_font(char, main.font)
    except Exception as e:
        main.current_glyph = saved[:]
    if main.current_glyph == "" : main.current_glyph = saved[:]

    if 'glyf' in main.font :
        g = main.font['glyf'][main.current_glyph]
        if g.isComposite(): refresh()
            # show_glyph('next' if flag=='' else flag) #skip composite
        elif g.numberOfContours > 0: refresh()
        else :
            show_glyph('next' if flag=='' else flag)  #skip
            print('glyph has no contour', g.numberOfContours)

    elif 'CFF ' in main.font : refresh()
    else :
        show_glyph('next' if flag=='' else flag)  #skip
        print('missing CFF or GLYF table ...')

    gui_font_info['glyph'].set( " [ " + str(main.current_glyph) + " ]" )

def drop(root,e):
    if e.data[0] == '{': e.data = e.data[1:-1]
    ext = str(utils.path_ext(e.data)).lower()
    print(ext)
    if ext in ('.ttf','.otf','.woff','.woff2') : load_new_font(e.data)
    if ext.lower() == '.lvp' : save_data.load_data(e.data)

def load_new_font(data):
    if hasattr(root,'config') and data : root.config(cursor="watch");
    gui_font_info['name'].set("... Font Loading ..."), root.update() # _idletasks not working

    main.font.close()
    main.font = TTFont( utils.path(data), recalcBBoxes=True, checkChecksums=1, recalcTimestamp=True )
    gui_font_info['numG'].set( " " + str(main.font['maxp'].numGlyphs) + " glyphs" )
    gui_font_info['unit'].set( " " + str(main.font['head'].unitsPerEm) + " units" )

    fail = False # detect valid fonts
    if 'fvar' in main.font : fail = True
    elif main.font.flavor :
        gui_font_info['format'].set( main.font.flavor.upper() ) # WOFF
        result = { "label:" : "There is no text preview\nfor WOFF and WOFF2 fonts." }
        gu.AskBox(root, "WOFF fonts warning", result,  btn1='ok')
    elif 'CFF ' in main.font :
        gui_font_info['format'].set( "OTF" )
    elif 'glyf' in main.font :
        gui_font_info['format'].set( "TTF" )
        gui_font_info['name'].set("... Convert TTF font to OTF ..."), root.update() # _idletasks not working
        try : ttf2otf.convert(main.font, subroutinize=False)
        except : fail = True
    else: fail = True

    if fail :
        result = { "label:" : "Unrecognised font\n(maybe a variable font)" }
        gu.AskBox(root, "Unrecognised font", result,  btn1='ok')
        load_new_font(main.font_origin.reader.file.name)
        return None

    main.font_origin = deepcopy(main.font)
    main.tmp_font = deepcopy(main.font)
    main.units = 1/ (main.font['head'].unitsPerEm /1000) # some font are more than 1000 u/em
    main.hbfont = hb.Font( hb.Face( hb.Blob.from_file_path(utils.path(data)) ) ) # load metric with uharfbuzz

    try:
        refresh()
    except: # if droped font has no main.current_glyph
        show_glyph('next')

     # unused Font checker (slower than CharsetChecker)
    # check = checker.FontChecker( utils.path(data) )
    # typo = check.get_supported_languages(decomposed=True, supportlevel=SupportLevel.BASE.value, validity=LanguageValidity.DRAFT.value)
    # for k,v in typo.items(): print("typo got : ", len(v), k)
    typo = {}
    # checkGlyph = checker.CharsetChecker( parse.parse_font_chars(main.font) )
    # typo = checkGlyph.get_supported_languages(decomposed=True)
    # for k,v in typo.items(): print("typo got : ", len(v), k)

    gui_font_info['name'].set("... languages analysys ..."), root.update() # _idletasks not working
    print('languages analysys...')
    checkGlyph = checker.CharsetChecker( parse.parse_font_chars(main.font) )
    hg_langs = languages.Languages() # langs data to get speakers
    combo = []
    counter = 0
    for k in wiki.langs : # build available wikiKeys list
        try:
            l = language.Language.match(k)
            a = checkGlyph.supports_language( l.part3 , decomposed=False)
            combo.append( (k, re.sub(r'\([^)]*\)','',l.name), hg_langs[l.part3]['speakers'] if hg_langs[l.part3]['speakers'] else 0, a) )
            if a : counter += 1
        except Exception as e:
            pass
    combo = sorted(combo, key=lambda k:k[2], reverse=True ) # sort by lang speakers
    # for v in combo: print(v[0],v[1],v[2])

    print("wiki",len(wiki.langs),"- combo",len(combo), '[',counter,']')
    print()
    menu_items['Language'].delete(0, "end") # populate menu/language
    menu_items['Language'].add_command( label='[ ] supported by font')#, state='disable' )
    menu_items['Language'].add_separator()
    for lang in combo :
        lab = '[ '+lang[1]+' ]' if lang[3] else '  '+lang[1] # [] on supported lang
        menu_items['Language'].add_command( label=lab, command=partial(set_lang, lang[0]) )

    main.font_name = str(main.font['name'].getName(16, 3, 1))
    main.font_style = str(main.font['name'].getName(17, 3, 1))
    if main.font_name == 'None' : main.font_name = str(main.font['name'].getName(1, 3, 1))
    if main.font_style == 'None' : main.font_style = str(main.font['name'].getName(2, 3, 1))
    gui_font_info['name'].set( "Input font :  " + main.font_name + " - " + main.font_style )

    refresh_txt(compute=False)
    save_data.writeParamFile(data,1) # save font path


def new_wiki():
    root.config(cursor="watch"); root.update_idletasks()
    wiki.get_wiki(); root.config(cursor="")
    refresh_txt(compute=True)
def set_lang(lang):
    root.config(cursor="watch"); root.update_idletasks()
    wiki.set_wiki_lang(lang); root.config(cursor="")
    save_data.writeParamFile(lang,0)
    refresh_txt(compute=False)

def production_esc(root): root.destroy()
def show_about_menu(): gu.show_about_menu(root)
def show_shortcut_menu(): gu.show_shortcut_menu(root)
#----------------------------------------------------------------------------------
def setup_menubar():
    menubar = Menu(root)
    global menu_items
    menu_items = dict.fromkeys( [ 'File', 'New layer', 'New group', 'Language' ] )
    for key, val in menu_items.items():
        menu_items[key] = Menu(menubar)
        menubar.add_cascade( label=key, menu=menu_items[key] )

    ctrl = "Meta" if platform.system() == "Darwin" else "Ctrl"
    menu_items['File'].add_command(label='Import font',command=import_font,accelerator=ctrl+'+N' )
    menu_items['File'].add_command(label='Export font',command=export_font,accelerator=ctrl+'+E')
    menu_items['File'].add_separator()
    menu_items['File'].add_command(label='Save project',command=save_data.dump,accelerator=ctrl+'+S')
    menu_items['File'].add_command(label='Open project',command=save_data.load,accelerator=ctrl+'+O' )
    menu_items['File'].add_separator()
    menu_items['File'].add_command( label='Shortcuts & controls',command=show_shortcut_menu)
    if ctrl!="Meta": menu_items['File'].add_command( label='About LivingPath',command=show_about_menu)
    if ctrl=="Meta": root.createcommand('tkAboutDialog', show_about_menu) #set about menu for mac
    for i in range(len(main.plugins)) :
        if "diffusion" in main.names[i] :
            menu_items['New layer'].add_command( label="reaction-diffusion (experimental)", command=partial(main.new_layer,i) )
        else:
            menu_items['New layer'].add_command( label=main.names[i].replace('_',' '), command=partial(main.new_layer,i) )
    menu_items['New layer'].add_separator()
    menu_items['New layer'].add_command(label='Duplicate layer',command=main.duplicate_layer)# ,accelerator=ctrl+'+V')
    menu_items['New group'].add_command(label='New group',command=main.new_group,accelerator=ctrl+'+G')
    menu_items['New group'].add_separator()
    menu_items['New group'].add_command(label='Duplicate group',command=main.duplicate_group,accelerator=ctrl+'+Shift+G')
    root.configure(menu=menubar)
#----------------------------------------------------------------------------------
gs_flags = ('all','custom...','basic latin','lowercase','uppercase','digits','punctuation' )
def export_font(): # gui ask family name and style
    result = {
    'Font family name': main.font_name + ' LivingPath',
    'Font style': main.font_style,
    'combo:Glyph set': gs_flags,
    'check:Save .lvp parameters file': False,
    'check:Generate font specimen': False }
    gu.AskBox(root, 'Name your font', result, selectPath_export)

def selectPath_export(data): # gui select folder to save font
    style, ffname = data['Font style'], data['Font family name']
    fullName = ffname.replace(' ', '_') + "-" + style

    ext = ('Open Type Font','*.otf')
    if main.font.flavor == 'woff' : ext = ('Web Open Font','*.woff')
    if main.font.flavor == 'woff2' : ext = ('Web Open Font 2','*.woff2')
    file_path = filedialog.asksaveasfilename( title='Export Font File',
        initialdir=utils.path,
        defaultextension = '.'+str(main.font.flavor) if main.font.flavor else ".otf" ,
        filetypes=( ext, ('All files','*.*') ),
        confirmoverwrite=True,
        initialfile = fullName
    )
    if file_path:
        root.config(cursor="watch");
        ext = utils.path_ext(file_path)
        file_name = utils.path_name(file_path)

        print("file_path:", file_path)
        print("data:", data)
        if data['check:Generate font specimen']:
            specimen.save( file_path, file_name, ext, ffname+' '+style, wiki.title, wiki.sum, wiki.start )
        if data['check:Save .lvp parameters file']:
            save_data.dumpFile(str(utils.path_dir(file_path))+'/'+str(file_name)+'_parameters.lvp')

        gu.used_glyphs.clear()
        main.process_font_export(file_path, name=ffname, style=style, flag=data['combo:Glyph set'])

        root.config(cursor="")
        playsound( utils.path('files/export.wav') )

def import_font():
    filename = filedialog.askopenfilename(  title='Open Font file',
        initialdir=utils.path,
        defaultextension=('.otf','.ttf','.woff','.woff2'),
        filetypes=( ('Font files',('*.otf','*.ttf','*.woff','*.woff2')), ('All files','*.*') )
    )
    load_new_font(filename)
#----------------------------------------------------------------------------------

def setup_root(mainRoot):
    global root
    root = mainRoot
    # utils.check_time(root)
    root.title('LivingPath')
    gu.set_icon(root)

    # import ctypes # Fixe image bad resolution (Windows)
    # ctypes.windll.shcore.SetProcessDpiAwareness(1)
    ws, hs = root.winfo_screenwidth(), root.winfo_screenheight()
    wm, hm = ws/10, hs/10
    # root.geometry('%dx%d+%d+%d' % (ws-wm, hs-hm, ws/2-(ws-wm)/2, hs/2-(hs-hm)/2))
    # root.geometry("{}x{}+-7+0".format(ws-0,hs-50))
    if platform.system() == "Darwin" : root.geometry("{}x{}+0+0".format(ws,hs))
    if platform.system() == "Windows": root.state('zoomed')
    if platform.system().startswith('Linux'): root.attributes('-zoomed', True)
    # root.geometry('%dx%d+%d+%d' % (ws-550, hs-100, 0, 0)) #production
    # if ws < 2000 : root.geometry("{0}x{1}+0+0".format(ws,hs))
    # if ws < 1500 : root.attributes("-fullscreen", True)
    # root['background'] = 'white' # for linux distro ?

    # gu.set_full_screen(root)
    scaleFactor = root.winfo_fpixels('1i')/72
    print('scaleFactor', scaleFactor)

    # gu.splash_screen(root)
    root.tk.call('tk', 'scaling', 1.5 )
    root.minsize( round(900) , round(650) )
    root.tk.call("source", utils.path("files/azure.tcl")) # theme
    root.tk.call("set_theme", "light")
    # s = ttk.Style(root) #  style mac...
    # s.theme_use('aqua')
    root.drop_target_register(DND_FILES) # drag & drop
    root.resizable()
    root.dnd_bind('<<Drop>>', lambda e: drop(root, e) )
    style = ttk.Style()
    style.layout('no_indicatoron.TCheckbutton', # pathfinders buttons
        [('Checkbutton.padding', {'sticky': 'nsew', 'children': [
            # ('Checkbutton.indicator', {'side': 'left', 'sticky': '' }),
            # ('Checkbutton.focus', { 'sticky': 'nsew', 'children': [
                ('Checkbutton.label', {'sticky': 'nswe' })
            # ]})
        ]})]
    )
    style.map('no_indicatoron.TCheckbutton', padding="1", compound="center" )
    style.configure('cover.TFrame', background="white")
    style.configure("custom.TButton", padding=[2,2,2,2])
    style.configure("big.TButton", padding=[4,4,4,4])
    # style.configure('gray.TButton',  padding=[3,3,3,3])
    # style.map('transparent.TButton', foreground=[('pressed', 'blue'), ('active', 'white')] )
    # style.configure('transparent.TButton', foreground="white", padding=[3,3,3,3])
    # style.layout('transparent.TButton', # delete button background
    # [('Button.border', {'border': '1', 'children':
    #     [('Button.focus', {'children':
    #         [('Button.padding', {'children':
    #             [('Button.label', {'expand': '1','sticky': 'nswe'})],
    #         'sticky': 'nswe'})],
    #     'sticky': 'nswe'})],
    # 'sticky': 'nswe'})]
    # )

    # root.option_add('*tearOff', 0)

    # layout on the root window
    root.columnconfigure(0, weight=0) # ????????
    root.columnconfigure(1, weight=0)

    # import tkinter.font as tkFont
    # default_font = tkFont.nametofont("TkTextFont")
    # default_font.configure(size=round(12/scaleFactor))
    # root.option_add("*Font", default_font)

    # general key control
    # root.bind("<Escape>", lambda x: production_esc(root))
    root.bind("<Right>", lambda x: show_glyph('next'))
    root.bind("<Left>", lambda x: show_glyph('prev'))
    root.bind('<Return>', lambda x: new_wiki() )
    root.bind('<space>', lambda x: refresh_txt() )
    ctrl = "Command" if platform.system() == "Darwin" else "Control"
    root.bind("<"+ctrl+"-n>", lambda x: import_font() )
    root.bind("<"+ctrl+"-e>", lambda x: export_font() )
    root.bind("<"+ctrl+"-s>", lambda x: save_data.dump() )
    root.bind("<"+ctrl+"-o>", lambda x: save_data.load() )
    root.bind("<"+ctrl+"-v>", lambda x: main.duplicate_layer() )
    root.bind("<"+ctrl+"-g>", lambda x: main.new_group() )
    root.bind("<"+ctrl+"-Shift-G>", lambda x: main.duplicate_group() )

    root.bind("<Key>", key)

def key(event): show_glyph(char=event.char)
#----------------------------------------------------------------------------------


if __name__ == "__main__":
    print('RUN FROM GUI')
    main.main()
