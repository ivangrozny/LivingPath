import freetype as ft # pip install freetype-py
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from PIL import Image, ImageOps
import utils
import pprint
# -------------------------------------------------------------------------------------------

def pen_to_img(pen, font, g): # has to be FreeTypePen
    gs = font.getGlyphSet()
    if g not in gs : # garde fou, utile ? ou pas
        return Image.new("L", (500, 1000),255)
    s = 1/ (font['head'].unitsPerEm /1000) # some font are more than 1000 u/em (and main unreachable)

    # boundsPen = BoundsPen( font.getGlyphSet() )
    # gs[g].draw(boundsPen)
    # print("[[[   ", int(gs[g].width*s), gs[g].lsb, gs[g].tsb, g, boundsPen.bounds  )

    m = utils.margin
    lsb =  - get_lsb(gs,g)
    height = font['OS/2'].usWinAscent*s + font['OS/2'].usWinDescent*s + 2*m
    width = ( gs[g].width + lsb )*s + 2*m
    try:  # garde fou, utile ? ou pas
        img = pen.image(contain=True,width=width,height=height,transform=(s,0,0,s, m + lsb, font['OS/2'].usWinDescent*s +2*m))
    except e: return Image.new("L", (500, 1000),255)
    img = ImageOps.invert(img.getchannel('A'))
    return img

def get_lsb(gs,g): # bugfix for Thai & Lao alphabets (got big negative lsb)
    lsb = gs[g].lsb
    if lsb > utils.margin : lsb = 0
    return lsb
# -------------------------------------------------------------------------------------------

def ftoutline_contour(outline, layer, gs=None, offset=(1,0,0,1,0,0), opened=False, units=1 ):
    pen = FreeTypePen( gs )
    tpen = TransformPen(pen, offset)
    stroker = ft.Stroker()
    width, linecap, join, limit = layer.outline_width, layer.outline_cap if opened else ft.FT_STROKER_LINECAP_BUTT, layer.corner_join, layer.corner_join_limit*1000
    coef = 70 # outline slider coef
    stroker.set( int(width/units*20), linecap, join, limit)
    if not layer.outline and layer.outline_width>100 :  stroker.set( int((width-100)*coef/units), linecap, join, limit)
    if not layer.outline and layer.outline_width<=100 : stroker.set( int((100-width)*coef/units), linecap, join, limit)
    stroker.parse_outline(outline, opened)

    n_points, n_contours = stroker.get_counts()
    with utils.new_outline(n_points, n_contours) as stroked_outline:
        if layer.outline     : stroker.export(stroked_outline)
        if not layer.outline and layer.outline_width>100: stroker.export_border(outline.get_outside_border(),stroked_outline)
        if not layer.outline and layer.outline_width<=100: stroker.export_border(outline.get_inside_border(),stroked_outline)
        tpen.moveTo( (0,0) )
        stroked_outline.decompose(tpen, move_to=move_to_reverse,line_to=line_to,conic_to=conic_to,cubic_to=cubic_to,shift=0,delta=0)
        tpen.closePath()

    return pen

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
    return (utils.constrain(a.x//coef,-4000,4000),
            utils.constrain(a.y//coef,-4000,4000))  # constrain aberations
            # not sure about // : int or float
# -------------------------------------------------------------------------------------------

def autotrace_to_ftoutline( vector, offset=(1,0,0,1,0,0) ):
    pen = FreeTypePen( None )
    tpen = TransformPen(pen, offset)
    for path in vector.paths :
        v1 = path.splines[0]
        tpen.moveTo((v1.points[0].x,v1.points[0].y))
        for v in path.splines:
            if v.degree==1: # LINEARTYPE
                tpen.lineTo((v.points[0].x,v.points[0].y))
                tpen.lineTo((v.points[1].x,v.points[1].y))
            if v.degree==3: # CUBICTYPE
                tpen.curveTo( (v.points[1].x,v.points[1].y), (v.points[2].x,v.points[2].y), (v.points[3].x,v.points[3].y))
        tpen.endPath()
    return ft.Outline( pen.outline() )
# -------------------------------------------------------------------------------------------

def cv2_to_ftoutline( vector, offset=(1,0,0,1,0,0) ): # cv2 open polygons
    pen = FreeTypePen( None )
    tpen = TransformPen(pen, offset)
    for path in vector :
        tpen.moveTo((path[0][0][0], path[0][0][1]))
        # print("Path:", path[0][0][0],path[0][0][1], "pts:",len(path))
        for v in path :
            tpen.lineTo((v[0][0],v[0][1]))
        tpen.endPath()
    return ft.Outline( pen.outline() )
# -------------------------------------------------------------------------------------------



def resize_path( path, s ):
    for curve in path:
        for segment in curve:
            segment.end_point.x *= s
            segment.end_point.y *= s
            if segment.is_corner:
                segment.c.x *= s
                segment.c.y *= s
            else:
                segment.c1.x *= s
                segment.c1.y *= s
                segment.c2.x *= s
                segment.c2.y *= s
    return path


def path_to_array( path ): # unused for now
    arr = []
    for curve in path:
        cur = []
        for segment in curve:
            seg = []
            seg.append( segment.end_point.x )
            seg.append( segment.end_point.y )
            if segment.is_corner:
                seg.append( segment.c.x )
                seg.append( segment.c.y )
            else:
                seg.append( segment.c1.x )
                seg.append( segment.c1.y )
                seg.append( segment.c2.x )
                seg.append( segment.c2.y )
            cur.append(seg)
        arr.append(cur)
    return arr
