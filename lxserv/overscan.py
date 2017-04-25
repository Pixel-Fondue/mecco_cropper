# python

import lx
import lxu.command
import traceback
import modo
import cropper

DEFAULT_PASSNAME = 'overscan'
SUFFIX = '_overscan'

def restoreSelection(listSelections):
    """
    Used together with:
    global save_selection
    save_selection = lx.evalN("query sceneservice selection ? all")
    to save and later restore a selection in modo with
    bd_utils.restoreSelection(save_selection)
    """

    first = True
    for x in listSelections:
        lx.out("Restoring Selection: " + x)
        if first:
            lx.eval("select.item {%s} set" % x)
        else:
            lx.eval("select.item {%s} add" % x)
        first = False
        
class OverscanBase(lxu.command.BasicCommand):

    def basic_Execute(self, msg, flags):
        try:
            self.CMD_EXE(msg, flags)
        except Exception:
            lx.out(traceback.format_exc())
            
    def get_pass_name(self):
        return self.dyna_String(0, DEFAULT_PASSNAME)

    def CMD_EXE(self, msg, flags):
        # Get selection
        save_selection = lx.evalN("query sceneservice selection ? all")

        # Get Render Camera
        tracerCam = cropper.get_tracer_camera(SUFFIX) if cropper.get_tracer_camera(SUFFIX) else cropper.create_tracer_camera(SUFFIX, False)

        # Get Film Back
        apertureX = modo.Scene().renderCamera.channel('apertureX').get()
        apertureY = modo.Scene().renderCamera.channel('apertureY').get()

        # Get Render Resolution
        resX = cropper.resXChannel().get()
        resY = cropper.resYChannel().get()
        
        mode = self.get_mode()
        if mode == "pixels":
            newResX = self.get_resolution_x()
            newResY = self.get_resolution_y()
        elif mode == "percent":
            percent = self.get_percent()
            newResX = resX * percent
            newResY = resY * percent
            
        try:
            modo.Scene().item(cropper.GROUP_NAME)
        except LookupError:
            lx.eval('group.create {} pass empty'.format(cropper.GROUP_NAME))
            
        channels_list = [
            cropper.resXChannel(),
            cropper.resYChannel(),
            modo.Scene().renderItem.channel('cameraIndex'),
            tracerCam.channel('apertureX'),
            tracerCam.channel('apertureY')
        ]

        for channel in channels_list:
            if channel not in modo.Scene().item(cropper.GROUP_NAME).groupChannels:
                modo.Scene().item(cropper.GROUP_NAME).addChannel(channel)

        lx.eval('group.layer group:{%s} name:{%s} grpType:pass' % (cropper.GROUP_NAME, self.get_pass_name()))

        # Apply Overscan formula to width and height
        newApertureX = apertureX * (newResX / resX)
        newApertureY = apertureY * (newResY / resY)

        # Fill in new render resolution
        modo.Scene().renderItem.channel('resX').set(newResX)
        modo.Scene().renderItem.channel('resY').set(newResY)

        # Fill in new film back
        lx.eval('render.camera {%s}' % tracerCam.id)
        tracerCam.channel('apertureX').set(newApertureX)
        tracerCam.channel('apertureY').set(newApertureY)

        lx.eval('edit.apply')

        # Restore selection
        restoreSelection(save_selection)    

        notifier = cropper.CropperNotify()
        notifier.Notify(lx.symbol.fCMDNOTIFY_DATATYPE)
        
        
class OverscanPercent(OverscanBase):

    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('name', lx.symbol.sTYPE_STRING)
        self.dyna_Add('percent', lx.symbol.sTYPE_PERCENT)

    def get_mode(self):
        return "percent"
        
    def get_percent(self):
        return self.dyna_Float(1, 100.0)
        
    _first_run = True

    def cmd_Flags(self):
        return lx.symbol.fCMD_POSTCMD | lx.symbol.fCMD_MODEL | lx.symbol.fCMD_UNDO

    def cmd_DialogInit(self):
        if self._first_run:
            # Assign default values at first run
            self.attr_SetString(0, DEFAULT_PASSNAME)
            self.attr_SetFlt(1, 1.0)
            self.after_first_run()

    @classmethod
    def after_first_run(cls):
        cls._first_run = False
        
class OverscanPixels(OverscanBase):

    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('name', lx.symbol.sTYPE_STRING)
        self.dyna_Add('resX', lx.symbol.sTYPE_INTEGER)
        self.dyna_Add('resY', lx.symbol.sTYPE_INTEGER)

    def get_mode(self):
        return "pixels"
        
    def get_resolution_x(self):
        return self.dyna_Int(0, 0)
        
    def get_resolution_y(self):
        return self.dyna_Int(1, 0)

    _first_run = True

    def cmd_Flags(self):
        return lx.symbol.fCMD_POSTCMD | lx.symbol.fCMD_MODEL | lx.symbol.fCMD_UNDO

    def cmd_DialogInit(self):
        if self._first_run:
            # Assign default values at first run
            self.attr_SetString(0, DEFAULT_PASSNAME)
            self.attr_SetInt(1, 0)
            self.attr_SetInt(2, 0)
            self.after_first_run()

    @classmethod
    def after_first_run(cls):
        cls._first_run = False     
        
lx.bless(OverscanPercent, "cropper.overscanPercent")
lx.bless(OverscanPixels, "cropper.overscanPixels")
