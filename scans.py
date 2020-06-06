from sardana.macroserver.macro import Macro, macro, Type
import numpy as np
import tqdm
import time
from tango import DeviceProxy, DevState


@macro([["integ_time", Type.Float, None, "Integration time"],
        ["accums", Type.Integer, None, "number of accumulations"]])
def acquire(self, integ_time, accums):
    """Do a one-point time scan"""
    self.execMacro('accumulations', accums)
    self.execMacro('timescan', '0', integ_time)

@macro([["integ_time", Type.Float, None, "Integration time"],
        ["accums", Type.Integer, None, "number of accumulations"]])
def acquire_xmcd(self, integ_time, accums):
    """Do a one-point time scan"""
    self.execMacro('acquire', integ_time, accums)
    helicity = self.getMotor('helicity')
    self.execMacro('umv', 'helicity', -helicity.position)
    self.output('Waiting 5s for beamline to settle.')
    time.sleep(5)

    self.execMacro('acquire', integ_time, accums)

@macro()
def lvroi(self):
    mte = DeviceProxy('maxi/pi_mte/1')
    lv = DeviceProxy('maxi/lavuecontroller/volta')
    roi_lv = eval(lv.DetectorROIs)
    lx0, ly0, lx1, ly1 = roi_lv['rois'][0]
    mte.set_roi([1340 - lx1, 1340 - lx0, 1300 - ly1, 1300 - ly0])

@macro()
def roi_center(self):
    mte = DeviceProxy('maxi/pi_mte/1')
    mte.set_roi([650, 800, 570, 720])

@macro()
def roi_no_BS(self):
    mte = DeviceProxy('maxi/pi_mte/1')
    mte.set_roi([687, 763, 561, 635])

@macro()
def fullchip(self):
    mte = DeviceProxy('maxi/pi_mte/1')
    mte.set_binning(1)

@macro()
def stopccd(self):
    ccd = DeviceProxy('maxi/PI_MTE/1')
    ccd.stop()

@macro([["integ_time", Type.Float, 0.1, "Integration time"] ])
def preview(self, integ_time):
    ccd = DeviceProxy('maxi/PI_MTE/1')
    ccd.stop()
    time.sleep(.1)
    ccd.accumulations = 1
    ccd.exposure = 1000 * integ_time
    ccd.preview()

@macro([["accums", Type.Integer, 1, "Nr of accumulations"] ])
def accumulations(self, n):
    ccd = DeviceProxy('maxi/PI_MTE/1')
    ccd.accumulations = n

@macro([['npulses', Type.Integer, None, "number of IR pulses"],
        ['freq', Type.Float, 10, "target frequency (software timing!)"]])
def IRpulses(self, npulses, freq):
    '''Sets port 6 to high (-> IR shutter) and sends a defined number of
    pulses on port 4 (-> IR trigger) before returning port 6 to low'''
    niusb = DeviceProxy('maxi/NI6501/volta')
    niusb.Frequency = freq
    niusb.ActivePort = 4
    niusb.npulses = npulses
    niusb.Port_1_6 = True
    time.sleep(2)
    niusb.train_async()
    while niusb.state() == DevState.RUNNING:
        time.sleep(0.2)
    time.sleep(1)
    niusb.Port_1_6 = False
    

@macro()
def acquire_darks(self):
    # 0.28s full chip
    self.execMacro('repeat 20 "acquire 0.28 10"')
    # 4.5s full chip
    self.execMacro('repeat 20 "acquire 4.5 10"')

@macro()
def acquire_darks_no_BS(self):
    self.execMacro('repeat 5 "acquire 0.07 100"')
    self.execMacro('repeat 5 "acquire 0.035 100"')
    self.execMacro('repeat 5 "acquire 0.009 100"')
    self.execMacro('repeat 5 "acquire 0.025 100"')
    self.execMacro('repeat 5 "acquire 0.03 100"')
    self.execMacro('repeat 5 "acquire 0.02 100"')
    self.execMacro('repeat 5 "acquire 0.008 100"')
    self.execMacro('repeat 5 "acquire 0.005 100"')
    
    

@macro()
def acquire_darks_fullchip(self):
    self.execMacro('repeat 10 "acquire 4.6 10"')
    self.execMacro('repeat 10 "acquire 0.2 10"')
    self.execMacro('repeat 10 "acquire 2.9 10"')
    self.execMacro('repeat 10 "acquire 0.1 10"')
    self.execMacro('repeat 10 "acquire 4.0 10"')
    self.execMacro('repeat 10 "acquire 0.22 10"')
    self.execMacro('repeat 10 "acquire 4.5 10"')
    self.execMacro('repeat 10 "acquire 0.15 10"')
    self.execMacro('repeat 10 "acquire 3.5 10"')
    self.execMacro('repeat 10 "acquire 0.13 10"')
    self.execMacro('repeat 10 "acquire 3.0 10"')
    self.execMacro('repeat 10 "acquire 3.2 10"')
    self.execMacro('repeat 10 "acquire 0.3 10"')
    self.execMacro('repeat 10 "acquire 4.4 10"')
    
    

@macro([["mode", Type.String, 'auto', "shutter mode (open, close, auto)"]])
def shutter(self, mode):
    ccd = DeviceProxy('maxi/PI_MTE/1')
    modes = {'auto': 1, 'close': 2, 'open': 3}
    try:
        ccd.shutter_mode = modes[mode]
    except KeyError:
        self.output('Unknown mode, expecting "open", "close" or "auto"')

@macro([["I_max", Type.Float, None, "Max current"],
        ["ncycles", Type.Integer, None, "Max current"]])
def demag(self, I_max, ncycles):
    steps = np.linspace(0, 5, ncycles)
    curr = I_max * np.exp(-steps) * np.cos(np.arange(ncycles) * np.pi)
    magnet = self.getMotor('magnet')
    for c in tqdm.tqdm(curr):
        magnet.move(c)
    magnet.move(1e-7)



@macro([["current", Type.Float, None, "current after saturation"],
        ["wp_angle", Type.Float, None, "waveplate angle"]])
def prepare_shot(self, current, wp_angle):
    magnet = self.getMotor('magnet')
    magnet.move(1)
    self.output('saturating')
    time.sleep(.5)
    magnet.move(current)
    self.output(f'setting magnet to {current}')
    wp = self.getMotor('las_int')
    wp.move(wp_angle)
    self.output(f'moving waveplate to {wp_angle}')
    self.output(f'1A -> {current:.2f}A, 1 shot @ {wp_angle} deg')


@macro()
def adjust_exposure(self):
    ccd = DeviceProxy('maxi/pi_mte/1')
    maxint = ccd.image.max()
    return ccd.exposure * 58000 / maxint / 1000

@macro()
def test(self):
    t = self.execMacro('adjust_exposure')
    self.output(t.getResult())

@macro()
def hysteresis(self):
    ccd = DeviceProxy('maxi/pi_mte/1')
    currents = np.concatenate([
        np.linspace(0.6, 0.15, 5),
        np.linspace(0.15, -0.6, 80)[1:]
        ])
    mag = self.getMotor('magnet')
    
    ccd.accumulations = 1
    self.execMacro('ct 0.05')
    for i in range(5):
        t = self.execMacro('adjust_exposure').getResult()
        self.execMacro(f'ct {t:.3f}')
    
    for i, c in enumerate(currents):
        mag.move(c)
        self.output(f'magnet: {c}')
        t = self.execMacro('adjust_exposure').getResult()
        self.output(f'exposure time: {t:.3f}')
        if i % 20 == 0:
            ccd.accumulations = 10
            self.execMacro(f'acquire_xmcd {t:.3f}')
        else:
            ccd.accumulations = 20
            self.execMacro(f'acquire {t:.3f}')
    

@macro()
def hyst_wrapper(self):
    self.execMacro('hysteresis')
    while time.time() < 1591248600:
        time.sleep(10)
    self.execMacro('hysteresis')
    

@macro([["integ_time", Type.Float, None, "Integration time"],
        ["accums", Type.Integer, None, "number of accumulations"],
        ["repeats",Type.Integer, None, "number of repeats"]])
def repeat_xmcd(self, integ_time, accums, repeats):
    """Do a one-point time scan"""
    for i in range(repeats):
        self.execMacro('acquire', integ_time, accums)
    helicity = self.getMotor('helicity')
    self.execMacro('umv', 'helicity', -helicity.position)
    self.output('Waiting 5s for beamline to settle.')
    time.sleep(5)
    for i in range(repeats):
        self.execMacro('acquire', integ_time, accums)
