from base_plugin import Plugin
import gui_utils as gui

import numpy as np
from PIL import Image, ImageOps
from tqdm import tqdm

import platform
if platform.system() == "Windows":
    from scipy.fft import ifft2, fft2
else :
    import torch
    global device
    # device = torch.device('cpu')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class Layer(Plugin):
    """
     Cahn-Hilliard equation using an implicit pseudospectral algorithm
     https://github.com/elvissoares/PyCahnHilliard/blob/master/cahnhilliard.py
    """

    def __init__(s):
        super(Layer, s).__init__()

    def gui(s, frame):

        gui.Slider(frame, max=0.5, min=0.01, ini= 0.1,format='%0.2f', layer=s, name='size', slow=True).pack(anchor='nw')
        gui.Slider(frame,layer=s,min=0.5, max=2, ini=1.0, format='%0.3f',name='depth').pack(anchor='nw')
        gui.Slider(frame,layer=s,min=0., max=0.5, ini=.1, format='%0.3f',name='noise').pack(anchor='nw')
        gui.Slider(frame, layer=s, min=1, max=1000, ini=50, name='recomposition', slow=True).pack(anchor='nw')
        # gui.Checkbutton(frame, layer=s, name='invert', ini=False).pack(anchor='nw')
        gui.Slider(frame, min=30, max=230, ini=127, layer=s, name='threshold').pack(anchor='nw', pady=(20,0))
    def run(s, img):

        if platform.system() == "Windows": # numpy version
            originSize = img.size
            img = img.resize( (int(img.width*s.size), int(img.height*s.size)), Image.NEAREST)

            w = img.height
            h = img.width

            Nsteps =s.recomposition
            dt = 0.1
            N = 256
            c_hat = np.empty((w,h), dtype=np.complex64)
            dfdc_hat = np.empty((w,h), dtype=np.complex64)
            c = np.empty((Nsteps,w,h), dtype=np.float32)

            dx = 1.0
            noise = s.noise
            c0 = 0.5
            rng = np.random.default_rng(12345)
            arr = np.array(img.getdata())
            c[0] = np.reshape( (s.depth-arr/255)/2, ( -1, img.width))
            c[0] = c[0] + noise*rng.standard_normal(c[0].shape)

            W = 2.0
            M = 1.0 # mobility
            kappa = 0.5 #gradient coeficient

            kx = np.fft.fftfreq(w, d=dx)*2*np.pi
            ky =  np.fft.fftfreq(h, d=dx)*2*np.pi
            K = np.array(np.meshgrid(kx , ky ,indexing ='ij'), dtype=np.float32)
            K2 = np.sum(K*K,axis=0, dtype=np.float32)

            # The anti-aliasing factor
            kmax_dealias = kx.max()*2.0/3.0 # The Nyquist mode
            dealias = np.array((np.abs(K[0]) < kmax_dealias )*(np.abs(K[1]) < kmax_dealias ),dtype =bool)

            def finterf(c_hat): return kappa*ifft2(K2*c_hat**2).real # The interfacial free energy density f(c) = Wc^2(1-c)^2 """
            def fbulk(c): return W*c**2*(1-c)*c**2                   # The bulk free energy density f(c) = Wc^2(1-c)^2 """
            def dfdc(c): return 2*W*(c*(1-c)**2-(1-c)*c**2)          # The derivative of bulk free energy density f(c) = Wc^2(1-c)^2 """

            c_hat[:] = fft2(c[0])
            for i in range(0,Nsteps):
                dfdc_hat[:] = fft2(dfdc(c[i-1])) # the FT of the derivative
                dfdc_hat[:] = fft2( np.array(dfdc( np.array(c[i-1], dtype=np.float32) ), dtype=np.float32)) # the FT of the derivative
                dfdc_hat *= dealias # dealising
                c_hat[:] = (c_hat-dt*K2*M*dfdc_hat)/(1+dt*M*kappa*K2**2) # updating in time
                c[i] = ifft2(c_hat).real # inverse fourier transform


        else : # pyTorch version (unix os)

            originSize = img.size
            img = img.resize( (int(1+img.width*s.size), int(1+img.height*s.size)), Image.LANCZOS)

            h = img.width
            w = img.height
            Nsteps =s.recomposition
            dt = 0.1
            c_hat = torch.empty((w,h), dtype=torch.complex64,device=device)
            dfdc_hat = torch.empty_like(c_hat)
            c = torch.empty((Nsteps,w,h), dtype=torch.float32,device=device)

            noise = s.noise
            rng = np.random.default_rng(12345)

            arr = np.array(img.getdata())
            img_ini =  np.empty((w,h), dtype=np.float32)
            img_ini = np.reshape( (s.depth-arr/255)/2, ( -1, img.width))
            # img_ini = np.reshape( (s.depth-arr/255)/2, ( -1, img.height))
            c[0] = torch.tensor( img_ini + noise*rng.standard_normal((w,h)) ,dtype=torch.float32, device=device)

            # print('c0 = ',c[0].mean().cpu().numpy())

            W = 2.5
            M = 1.0 # mobility
            kappa = 0.5 #gradient coeficient

            kx = torch.fft.fftfreq(w, d=( (w/4)*np.pi) /w )*2*np.pi
            ky = torch.fft.fftfreq(h, d=( (h/4)*np.pi) /h )*2*np.pi
            Kx,Ky = torch.meshgrid(kx,ky,indexing ='ij')
            K = torch.stack((Kx,Ky)).to(device)
            K2 = torch.sum(K*K,dim=0)

            # The anti-aliasing factor
            # kcut = kx.max()*2.0/3.0 # The Nyquist mode
            # dealias = (torch.abs(K[0]) < kcut )*(torch.abs(K[1]) < kcut )

            def finterf(c_hat): return kappa*torch.fft.ifftn(K2*c_hat**2).real
            def fbulk(c): return W*c**2*(1-c)*c**2
            def dfdc(c): return 2*W*(c*(1-c)**2-(1-c)*c**2)

            c_hat[:] = torch.fft.fftn(c[0])
            for i in tqdm(range(1,Nsteps), leave=False): # leave opt will print timer
                dfdc_hat[:] = torch.fft.fftn(dfdc(c[i-1])) # the FT of the derivative
                # dfdc_hat *= dealias # dealising
                c_hat[:] = (c_hat-dt*K2*M*dfdc_hat)/(1+dt*M*kappa*K2**2) # updating in time
                c[i] = torch.fft.ifftn(c_hat).real # inverse fourier transform
                # error = torch.abs(c[i].sum()-cint)/cint

            # print('c = ',c[-1].mean().cpu().numpy())
            # print('relative_error = ',error.cpu().numpy())
            # print("R&D - Time Elapsed : " + str(time() - t) )

        img = np.clip( c[-1] * 255, 0, 255 )
        img = Image.fromarray(np.uint8(img))
        img = ImageOps.invert(img)
        img = img.resize(originSize, 1)
        img = img.point( lambda p: 255 if p > s.threshold else 0 )
        return img
