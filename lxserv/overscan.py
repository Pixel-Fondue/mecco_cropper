# python

import lx
import lxu.command
import traceback
from notifier import CropperNotify

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

    def CMD_EXE(self, msg, flags):
        # Get selection
        save_selection = lx.evalN("query sceneservice selection ? all")

        # Get Render Camera
        render_camera = lx.eval("render.camera ?")
        lx.eval("select.item {%s} set" % render_camera)

        # Get Film Back
        apertureX = lx.eval("item.channel apertureX ?")
        apertureY = lx.eval("item.channel apertureY ?")

        # Get Render Resolution
        lx.eval("select.item Render")
        resX = float(lx.eval("item.channel resX ?"))
        resY = float(lx.eval("item.channel resY ?"))
        
        mode = self.get_mode()
        if mode == "pixels":
            newResX = self.get_resolution_x()
            newResY = self.get_resolution_y()
        elif mode == "percent":
            percent = self.get_percent()
            newResX = resX * percent
            newResY = resY * percent

        # Apply Overscan formula to width and height
        newApertureX = apertureX * (newResX / resX)
        newApertureY = apertureY * (newResY / resY)

        # Fill in new render resolution
        lx.eval("render.res 0 %s" % newResX)
        lx.eval("render.res 1 %s" % newResY)

        # Fill in new film back
        lx.eval("select.item {%s} set" % render_camera)
        lx.eval("item.channel apertureX %s" % newApertureX)
        lx.eval("item.channel apertureY %s" % newApertureY)

        # Restore selection
        restoreSelection(save_selection)    

        notifier = CropperNotify()
        notifier.Notify(lx.symbol.fCMDNOTIFY_DATATYPE)
        
        
class OverscanPercent(OverscanBase):

    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('percent', lx.symbol.sTYPE_PERCENT)

    def get_mode(self):
        return "percent"
        
    def get_percent(self):
        return self.dyna_Float(0, 100.0)
        
    _first_run = True

    def cmd_Flags(self):
        return lx.symbol.fCMD_POSTCMD | lx.symbol.fCMD_MODEL | lx.symbol.fCMD_UNDO

    def cmd_DialogInit(self):
        if self._first_run:
            # Assign default values at first run
            self.attr_SetFlt(0, 1.0)
            self.after_first_run()

    @classmethod
    def after_first_run(cls):
        cls._first_run = False
        
class OverscanPixels(OverscanBase):

    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
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
            self.attr_SetInt(0, 0)
            self.attr_SetInt(1, 0)
            self.after_first_run()

    @classmethod
    def after_first_run(cls):
        cls._first_run = False     
        
lx.bless(OverscanPercent, "cropper.overscanPercent")
lx.bless(OverscanPixels, "cropper.overscanPixels")
