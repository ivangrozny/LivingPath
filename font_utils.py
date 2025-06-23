import freetype as ft # pip install freetype-py
import numpy as np
from potrace import Bitmap # pip install potracer
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from PIL import ImageDraw, Image, ImageOps, ImageMath, ImageChops, ImageFont
import uharfbuzz as hb
import types
from matplotlib import font_manager
params = types.SimpleNamespace()
import utils, path_utils
import copy


def glyph_to_img(font, glyph): # unused
    pen = FreeTypePen( font.getGlyphSet() )
    font.getGlyphSet()[glyph].draw(pen)
    img = path_utils.pen_to_img( pen, font, glyph )
    return img


def glyph_to_img_outline(glyph, in_font, group):
    gs = in_font.getGlyphSet()
    if glyph not in gs : # garde fou
        return Image.new("L", (500, 1000),255)
    pen = FreeTypePen( gs )
    gs[glyph].draw(pen)
    outline = ft.Outline( pen.outline() )
    u = 1/ (in_font['head'].unitsPerEm /1000)
    pen = path_utils.ftoutline_contour( outline, group.layers[0], glyph, units=u )
    img = path_utils.pen_to_img( pen, in_font, glyph )
    return img.convert('L')

def move_to_reverse(a, ctx):
    ctx.moveTo( pt(a) )
    ctx.closePath()
    ctx.moveTo( pt(a) )
    ctx.lineTo( pt(a) )
def move_to(a, ctx):
    ctx.lineTo( pt(a) )
    ctx.closePath()
    ctx.moveTo( pt(a) )
def line_to(a, ctx):        ctx.lineTo( pt(a) )
def conic_to(a, b, ctx):    ctx.curveTo( pt(a), pt(b), pt(b))
def cubic_to(a, b, c, ctx): ctx.curveTo(  pt(a), pt(b), pt(c) )
def pt(a):
    coef = 64
    return (a.x//coef, a.y//coef)  # not sure about // : int or float


def glyph_to_font_outline(g, in_font, font, group):
    l = group.layers[0]
    gs = in_font.getGlyphSet()
    fpen = FreeTypePen( gs )
    gs[g].draw(fpen)
    outline = ft.Outline( fpen.outline() )

    if 'glyf' in font : pen = TTGlyphPen( font.getGlyphSet() )
    if 'CFF ' in font : pen = T2CharStringPen(gs[g].width, font.getGlyphSet())
    tpen = TransformPen(pen, (1, 0, 0, 1, 0, 0))

    stroker = ft.Stroker()
    width, linecap, join, limit =  l.outline_width, ft.FT_STROKER_LINECAP_BUTT, l.angle_join, l.angle_join_limit*1000
    stroker.set(width*20, linecap, join, limit)
    if not l.outline and width>100 :  stroker.set( (width-100)*20, linecap, join, limit)
    if not l.outline and width<=100 : stroker.set( (100-width)*20, linecap, join, limit)
    stroker.parse_outline(outline, False)

    n_points, n_contours = stroker.get_counts()
    with utils.new_outline(n_points, n_contours) as stroked_outline:
        if l.outline     : stroker.export(stroked_outline)
        if not l.outline and l.outline_width>100: stroker.export_border(outline.get_outside_border(),stroked_outline)
        if not l.outline and l.outline_width<=100: stroker.export_border(outline.get_inside_border(),stroked_outline)
        stroked_outline.decompose(tpen, move_to=move_to,line_to=line_to,conic_to=conic_to,cubic_to=cubic_to,shift=0,delta=0)
        tpen.closePath()

    if 'glyf' in font : font['glyf'][g] = pen.glyph(dropImpliedOnCurves=False)
    if 'CFF ' in font : font['CFF '].cff.topDictIndex[0].CharStrings[g] = pen.getCharString()


def vectorization(img, params=params):
    # C++ binding : pypotrace - version mac (a tester) https://github.com/flupke/pypotrace
    # full python : potracer - https://github.com/tatarize/potrace
    # Cython : pyAutoTrace - ça marche aussi - https://github.com/lemonyte/pyautotrace
    width = float(img.size[0])*params.accuracy
    wpercent = float(width)/float(img.size[0])
    height = int( float(img.size[1]) * float(wpercent) )
    img = img.resize((int(width),int(height)), Image.Resampling.LANCZOS)
    data = np.asarray(img) #  PIL image to a numpy array
    bmp = Bitmap(data) # Create a bitmap from the array
    path = bmp.trace( alphamax=params.curves_limit, opticurve=True, opttolerance=params.simplify_path) # turdsize=params.minimal_zone

    return path_utils.resize_path( path, 1/params.accuracy )


def path_to_font(path, glyph, font, path_type="potrace"):
    if not params.letter_spacing == 0 :
        font['hmtx'][glyph] = ( int(font['hmtx'][glyph][0] + params.letter_spacing) , font['hmtx'][glyph][1])
    gs = font.getGlyphSet()

    if 'glyf' in font : pen = TTGlyphPen( gs )
    if 'CFF ' in font :
        X = font['CFF '].cff[0].Private.nominalWidthX if 'nominalWidthX' in font['CFF '].cff[0].Private.rawDict else 0
        pen = T2CharStringPen(gs[glyph].width - X, gs); # gliphWidth - nominalWidthX (does -X is usefull ?)

    s = font['head'].unitsPerEm /1000 # some font are more than 1000 u/em
    tpen = TransformPen(pen, (s, 0, 0, -s, -utils.margin*s + path_utils.get_lsb(gs,glyph)*s, font['OS/2'].usWinAscent))
    if path_type == "potrace": path_to_pen(path,tpen)
    if path_type == "array":  array_to_pen(path,tpen)

    # pprint.pprint(vars(gs[glyph]))
    if 'glyf' in font : font['glyf'][glyph] = pen.glyph(dropImpliedOnCurves=True)
    if 'CFF ' in font :
        cs = pen.getCharString()
        cs.compile()
        font['CFF '].cff[0].CharStrings[glyph].bytecode = cs.bytecode
        font['CFF '].cff[0].CharStrings[glyph].calcBounds(gs) # not sure if useful

    # print( gs[glyph].width , font.getGlyphSet()[glyph].width ,font['hmtx'][glyph][0] )

def path_to_pen(path,tpen):
    for curve in path:
        tpen.moveTo(( curve.start_point.x , curve.start_point.y ))
        for segment in curve:
            x = segment.end_point.x
            y = segment.end_point.y
            if segment.is_corner:
                tpen.lineTo((segment.c.x, segment.c.y))
                tpen.lineTo((x, y))
            else:
                tpen.curveTo( (segment.c1.x,segment.c1.y), (segment.c2.x,segment.c2.y), (x, y))
        tpen.closePath()
def array_to_pen(arr,tpen):
    for cur in arr:
        tpen.moveTo(( cur[0][2] , cur[0][3] ))
        for seg in cur:
            x = seg[0]
            y = seg[1]
            if len(seg) == 4:
                tpen.lineTo((seg[2], seg[3]))
                tpen.lineTo((x, y))
            else:
                tpen.curveTo( (seg[2],seg[3]), (seg[4],seg[5]), (x, y))
        tpen.closePath() # pen or tpen ?

# -------------------------------------------------------------------------------------------
def text_to_img_PIL(txt):
    img = Image.new("RGB", (1000, 1000))
    d = ImageDraw.Draw(img)
    new_font = ImageFont.truetype(utils.path("out.otf"), size=148) # layout_engine=ImageFont.Layout.BASIC
    d.text((0, 200), txt, font=new_font, fill="#fff")
    return img

def char_in_font(unicode_char, font):
    '''check if a char is in font, return its glyphName'''
    for cmap in font['cmap'].tables:
        if cmap.isUnicode() or cmap.getEncoding() == 'utf_16_be':
            if ord(unicode_char) in cmap.cmap:
                # print(type(cmap))
                auxcn = cmap.cmap[ord(unicode_char)]
                # print(auxcn, type(auxcn))
                return auxcn if auxcn != '' else '<nil>'
    return ''

def text_to_img_HB(text, ttfont, hbfont):
    if  ttfont.flavor : return Image.new("L", (1, 1))
    s = 5
    # text = 'とは、主に兄妹姉以上継続'
    # takes metrics from inputed font with HB  & draw from TTFont object
    # base from https://fonttools.readthedocs.io/en/latest/pens/freetypePen.html
    # en1, en2, ar, ja = 'VA Typesetting', 'Jeff', 'صف الحروف', 'たいぷせっと'
    # (ar,  'files/1.ttf',     'rtl', 1374, -738, None, None, False, {"kern": True, "liga": True}),
    # (ja,  'files/1.otf',     'ltr', 880,  -120, 500,  -500, False, {"palt": True, "kern": True}),
    # (ja,  'files/1.otf',     'ttb', 880,  -120, 500,  -500, False, {"vert": True, "vpal": True, "vkrn": True})
    typo_ascender, typo_descender = ttfont['OS/2'].usWinAscent, ttfont['OS/2'].usWinDescent
    if 'hhea' in ttfont: h_ascender,h_descender = ttfont["hhea"].ascent,ttfont["hhea"].descent
    if 'vhea' in ttfont: v_ascender,v_descender = ttfont["vhea"].ascent,ttfont["vhea"].descent
    contain = False
    direction = 'ltr'
    features = {"kern": True, "liga": True}

    buf = hb.Buffer()
    buf.add_str(text)
    # buf.direction = direction

    try:
        if 'space' in ttfont.getReverseGlyphMap() :   # remplacement glyph
            buf.replacement_codepoint = hbfont.get_nominal_glyph(ord(" "))
            buf.not_found_glyph = hbfont.get_nominal_glyph(ord(" "))
            # buf.not_found_glyph = ttfont.getGlyphID('space')
    except Exception as e: pass

    buf.guess_segment_properties()
    # try:
    hb.shape(hbfont, buf, features)
    # except Exception as e: print(e)

    x, y = 0, 0
    pen = FreeTypePen( ttfont.getGlyphSet() )
    if buf.glyph_positions != None :
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            gid = info.codepoint
            transformed = TransformPen(pen, (1,0,0,1, x+pos.x_offset, y+pos.y_offset ))
            # g = ttfont.getBestCmap()[ord(' ')]
            # try: g = ttfont.getBestCmap()[ord(char)]
            # except Exception as e:
            #     print("(utils.py) Char to glyph error : '"+char+"'")
            # ttfont.getGlyphSet()[ g ].draw( transformed )

            try:
                ttfont.getGlyphSet()[ ttfont.getGlyphName(gid) ].draw( transformed )
            except Exception as e:
                raise
            # hbfont.draw_glyph_with_pen(gid, transformed)

            x += pos.x_advance + params.letter_spacing
            y += pos.y_advance

        offset, width, height = None, None, None
        if direction in ('ltr', 'rtl'):
            offset = (0, -h_descender//s)
            width  = x
            height = h_ascender - h_descender
        else:
            offset = (-v_descender//s, -y//s)
            width  = v_ascender - v_descender
            height = -y

        # img = pen.image(width=width/s, height=height/s, transform=Offset(*offset))
        # try:
        img = pen.image(width=width//s, height=height//s, transform=(1/s,0,0,1/s,*offset), contain=contain)
        # except Exception as e:
        #     print("harfbuzz error : ", e)
        #     img = Image.new('ARGB', (1, 1))
        img = ImageOps.invert(img.getchannel('A'))
    else: img = Image.new('L', (1, 1))
    return img

# -------------------------------------------------------------------------------------------
def operator_img(img, img2, op):
    if op==0 : img = ImageChops.darker( img, img2 )
    elif op==1 : img = ImageChops.add( ImageOps.invert(img), img2 )
    elif op==2 : img = ImageChops.add( img, ImageOps.invert(img2) )
    elif op==3 : img = ImageChops.lighter( img, img2 )
    elif op==4 : img = ImageOps.invert( ImageChops.difference(img, img2) )
    return img

def draw_rules(img, g, font): # draw visual beziers with PIL
    img = img.convert('RGB')
    draw = ImageDraw.Draw(img)
    # aaa = font['OS/2'].sTypoAscender; print(aaa); lineLabel(draw, (0,aaa, img.width,aaa), '#199', 2, 'sTypoAscender')
    # aaa = font['OS/2'].sTypoDescender; print(aaa); lineLabel(draw, (0,aaa, img.width,aaa), '#199', 2, 'sTypoDescender')
    # aaa = font['hhea'].ascender; print(aaa); lineLabel(draw, (0,aaa, img.width,aaa), '#199', 2, 'ascender')
    # aaa = font['hhea'].descender; print(aaa); lineLabel(draw, (0,aaa, img.width,aaa), '#199', 2, 'descender')

    s = font['head'].unitsPerEm /1000 # some font are more than 1000 u/em

    if hasattr(font['OS/2'], 'usWinAscent') : asc = font['OS/2'].usWinAscent /s
    elif hasattr(font['hhea'], 'ascender') : asc = font['hhea'].ascender /s
    else : asc = 4000

    if hasattr(font['OS/2'], 'usWinDescent') : des = font['OS/2'].usWinDescent /s
    elif hasattr(font['OS/2'], 'sTypoDescender') : des = abs(font['OS/2'].sTypoDescender) /s
    elif hasattr(font['hhea'], 'descender') : des = abs(font['hhea'].descender) /s
    else : des = 4000

    if hasattr(font['OS/2'], 'sCapHeight') : cap = font['OS/2'].sCapHeight /s
    elif hasattr(font['OS/2'], 'sTypoAscender') : cap = abs(font['OS/2'].sTypoAscender) /s
    else : cap = 4000

    if hasattr(font['OS/2'], 'sxHeight') : xheight = font['OS/2'].sxHeight /s
    else : xheight = 4000

    # print("metrics :", asc, des, cap, xheight)

    width = font.getGlyphSet()[g].width /s + params.letter_spacing
    m, mm = utils.margin, 35
    c = '#555' #(0, 127, 255)
    lineLabel(draw, (70,asc, width+m+mm,asc ), c, 2, 'base line')
    lineLabel(draw, (70,asc+des, width+m+mm,asc+des ), c, 2, 'descender')
    lineLabel(draw, (70,cap-des-m, width+m+mm,cap-des-m ), c, 2, 'cap')
    lineLabel(draw, (70,asc-xheight, width+m+mm,asc-xheight ), c, 2, 'xheight')
    lineLabel(draw, (70,m, width+m+mm,m), c, 2, 'ascender')

    lineLabel(draw, (width+m,m-mm, width+m,img.height), c, 2, str(int(width*s)), vert=img.height)
    lineLabel(draw, (m,m-mm, m,img.height), c, 2, '0', vert=img.height)

    return img

fontFile = font_manager.findfont(font_manager.FontProperties(family='arial'))
# print("local gui file loaded :", file)
arial = ImageFont.truetype(fontFile, 20)

def lineLabel(draw, coord, coul, width=2, txt='', vert=None):
    draw.line(coord, coul, width)
    pos = (coord[0],coord[1]+4) if not vert else (coord[0]+8,vert-20)
    draw.text(pos, txt, font=arial, fill='#222')

def draw_paths(path, img): # draw visual beziers with PIL
    if True : # params.display_points :
        img = ImageMath.eval("a+157", a=img)
        img = img.convert('RGB')
        draw = ImageDraw.Draw(img)
        bleu = (0, 127, 255)
        bleu2 = (0, 85, 180)
        for curve in path: # draw beziers
            last = curve.start_point
            for segment in curve:
                x = segment.end_point.x
                y = segment.end_point.y
                if not segment.is_corner:
                    draw.line((segment.c1.x,segment.c1.y,last.x,last.y), bleu2, width=2)
                    draw.line((segment.c2.x,segment.c2.y,x,y), bleu2, width=2)
                    utils.ellipse(4,segment.c1.x,segment.c1.y, bleu2, draw)
                    utils.ellipse(4,segment.c2.x,segment.c2.y, bleu2, draw)
                last = segment.end_point

        for curve in path: # then draw points
            for segment in curve:
                x = segment.end_point.x
                y = segment.end_point.y
                utils.ellipse( 7, x, y, bleu, draw)
                # rectangle(5, x, y, bleu, draw)
                if segment.is_corner:
                    utils.rectangle(5,segment.c.x,segment.c.y, bleu, draw)
            utils.ellipse(11,curve.start_point.x,curve.start_point.y, bleu, draw)
            utils.ellipse(7, curve.start_point.x,curve.start_point.y, "white", draw)
        del draw
    return img

# -------------------------------------------------------------------------------------------

# https://learn.microsoft.com/en-us/typography/opentype/spec/name#name-ids

import pprint
def rename_font(font, name, style):
    name_style = name +" "+ style
    regular_style = style.lower() in ('regular') #, 'italic', 'bold', 'bold italic')
    has_16, has_17, data = False, False, {}

    for record in font['name'].names:
        enc = record.getEncoding()
        id = record.nameID
        sys = record.platformID
        if id==16 : has_16 = True
        if id==17 : has_17 = True
        if sys not in data : data[sys] = record
        # if id==1 and sys==1: record.string = name.encode(enc) # windows
        # if id==1 and sys==3: record.string = name_style.encode(enc) # mac version ?
        if id==1: record.string = name.encode(enc)
        if id==2: record.string = style.encode(enc) if regular_style else 'Regular'.encode(enc)
        if id== 3 or id==5: record.string += str('; LivingPath 1.0 - '+name_style).encode(enc) # unique id, version id
        if id== 4: record.string = name_style.encode(enc) # full name
        if id== 6: record.string = str(name+"-"+style).replace(" ","").encode(enc) # PostScript name
        # if id == 9:  # Authors names
        # if id == 12:  # Autors URLs Links
        if id==1  and not regular_style : record.string = name_style.encode(enc)
        if id==16 and not regular_style : record.string = name.encode(enc)
        if id==17 and not regular_style : record.string = style.encode(enc)
        if id==16 and     regular_style : font['name'].names.remove(record)
        if id==17 and     regular_style : font['name'].names.remove(record)


    if not regular_style and (not has_16 or not has_17) :
        for v in data.values() :
            record = copy.deepcopy(v)
            record.nameID = 16
            record.string = name.encode(enc)
            font['name'].names.append(record)
            record = copy.deepcopy(v)
            record.nameID = 17
            record.string = style.encode(enc)
            font['name'].names.append(record)

    for record in font['name'].names: # font analyzer
        enc = record.getEncoding()
        id = record.nameID
        sys = record.platformID
        # print(id,sys,record.platEncID,record.langID,"---", record.string.decode(enc) )
        # pprint.pprint(vars(record))
    # pprint.pprint( font['name'] )

    if 'CFF ' in font:
        try:
            if 'FamilyName' in font['CFF '].cff[0].rawDict: font['CFF '].cff[0].FamilyName = name
            if 'FullName' in font['CFF '].cff[0].rawDict: font['CFF '].cff[0].FullName = name_style
            if 'Weight' in font['CFF '].cff[0].rawDict: font['CFF '].cff[0].Weight = style
            f.cff.fontNames = str(name+"-"+style).replace(" ","")
        except Exception as e:
            print(e)

    return font



#  from https://github.com/fonttools/fonttools/blob/8d3b9900976b6c77e33f899fc9e74e07dd09591a/Snippets/decompose-ttf.py
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
import pathops

def decomposeTTF(f):
    glyfTable = f["glyf"]
    glyphSet = f.getGlyphSet()

    for glyphName in glyphSet.keys():
        if not glyfTable[glyphName].isComposite():
            continue

        # record TTGlyph outlines without components
        dcPen = DecomposingRecordingPen(glyphSet)
        glyphSet[glyphName].draw(dcPen)

        # replay recording onto a skia-pathops Path
        path = pathops.Path()
        pathPen = path.getPen()
        dcPen.replay(pathPen)

        # remove overlaps
        path.simplify()

        # create new TTGlyph from Path
        ttPen = TTGlyphPen(None)
        path.draw(ttPen)
        glyfTable[glyphName] = ttPen.glyph()
