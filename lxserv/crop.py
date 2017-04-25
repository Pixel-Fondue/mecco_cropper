# python

import lx
import lxu.command
import lxifc
import traceback
import modo
import cropper

DEFAULT_PASSNAME = 'crop'
SUFFIX = '_cropper'
   
def get_render_region():
    return {
        'left': modo.Scene().renderItem.channel('regX0').get(),
        'right': modo.Scene().renderItem.channel('regX1').get(),
        'top': modo.Scene().renderItem.channel('regY0').get(),
        'bottom': modo.Scene().renderItem.channel('regY1').get()
    }


def get_target_frame():
    render_region = get_render_region()

    return [
        int(cropper.resXChannel().get()) * abs(render_region['right'] - render_region['left']),
        int(cropper.resYChannel().get()) * abs(render_region['bottom'] - render_region['top']),
    ]


def get_target_offset():
    proportional_aperture = get_proportional_aperture()

    frame = [
        int(cropper.resXChannel().get()),
        int(cropper.resYChannel().get())
    ]

    offset = [
        modo.Scene().renderCamera.channel('offsetX').get(),
        modo.Scene().renderCamera.channel('offsetY').get()
    ]

    render_region = get_render_region()

    x_step = 1
    y_step = x_step

    if frame[0] == frame[1]:
        x_step = proportional_aperture[1]
        y_step = proportional_aperture[1]

    elif frame[0] > frame[1]:
        mdf = float(frame[0]) / frame[1]
        x_step = proportional_aperture[0]
        y_step = proportional_aperture[0] / mdf

    elif frame[0] < frame[1]:
        mdf = float(frame[1]) / frame[0]
        x_step = proportional_aperture[1] / mdf
        y_step = proportional_aperture[1]

    offset = [
        ((render_region['left']+render_region['right'])/2 - .5) * x_step + offset[0],
        ((render_region['top']+render_region['bottom'])/2 - .5) * -y_step + offset[1],
    ]

    return offset


def deactivate_pass():
    graph_kids = modo.Scene().item(cropper.GROUP_NAME).itemGraph('itemGroups').forward()
    passes = [i for i in graph_kids if i.type == lx.symbol.a_ACTIONCLIP]

    for pass_ in passes:
        pass_.actionClip.SetActive(0)


def active_pass():
    try:
        modo.Scene().item(cropper.GROUP_NAME)
    except LookupError:
        return None

    graph_kids = modo.Scene().item(cropper.GROUP_NAME).itemGraph('itemGroups').forward()
    passes = [i for i in graph_kids if i.type == lx.symbol.a_ACTIONCLIP]

    for pass_ in passes:
        if pass_.actionClip.Active():
            return pass_

    return None


def activate_latest_pass():
    try:
        graph_kids = modo.Scene().item(cropper.GROUP_NAME).itemGraph('itemGroups').forward()
    except (NameError, LookupError):
        return

    passes = [i for i in graph_kids if i.type == lx.symbol.a_ACTIONCLIP]
    max(passes, key=lambda p: p.index).actionClip.SetActive(1)


def get_proportional_aperture():
    frame = [
        int(cropper.resXChannel().get()),
        int(cropper.resYChannel().get())
    ]

    ratio = float(max(frame)) / min(frame)

    aperture = [
        modo.Scene().renderCamera.channel('apertureX').get(),
        modo.Scene().renderCamera.channel('apertureY').get()
    ]

    apr_ratio = float(max(aperture)) / min(aperture)

    if ratio <= apr_ratio:
        if aperture[0] > aperture[1]:
            aperture[0] = aperture[1] * ratio

        elif aperture[0] < aperture[1]:
            aperture[1] = aperture[0] * ratio

    return aperture


def get_target_aperture():
    target_frame = get_target_frame()
    proportional_aperture = get_proportional_aperture()

    render_region = get_render_region()

    region_size = [
        render_region['right'] - render_region['left'],
        render_region['bottom'] - render_region['top']
    ]

    target_aperture = [
        proportional_aperture[0] * region_size[0],
        proportional_aperture[1] * region_size[1]
    ]

    return target_aperture

class Cropper(lxu.command.BasicCommand):

    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('name', lx.symbol.sTYPE_STRING)

    def basic_Execute(self, msg, flags):
        try:
            self.CMD_EXE(msg, flags)
        except Exception:
            lx.out(traceback.format_exc())

    def CMD_EXE(self, msg, flags):
        pass_name = self.dyna_String(0) if self.dyna_IsSet(0) else DEFAULT_PASSNAME

        tracerCam = cropper.get_tracer_camera(SUFFIX) if cropper.get_tracer_camera(SUFFIX) else cropper.create_tracer_camera(SUFFIX, True)

        modo.Scene().renderItem.channel('region').set(False)
        lx.eval("view3d.renderCamera")

        try:
            modo.Scene().item(cropper.GROUP_NAME)
        except LookupError:
            lx.eval('group.create {} pass empty'.format(cropper.GROUP_NAME))

        channels_list = [
            cropper.resXChannel(),
            cropper.resYChannel(),
            modo.Scene().renderItem.channel('cameraIndex'),
            tracerCam.channel('offsetX'),
            tracerCam.channel('offsetY'),
            tracerCam.channel('apertureX'),
            tracerCam.channel('apertureY')
        ]

        for channel in channels_list:
            if channel not in modo.Scene().item(cropper.GROUP_NAME).groupChannels:
                modo.Scene().item(cropper.GROUP_NAME).addChannel(channel)

        lx.eval('group.layer group:{%s} name:{%s} grpType:pass' % (cropper.GROUP_NAME, pass_name))

        target_frame = get_target_frame()
        target_offset = get_target_offset()
        target_aperture = get_target_aperture()

        modo.Scene().renderItem.channel('resX').set(target_frame[0])
        modo.Scene().renderItem.channel('resY').set(target_frame[1])
        lx.eval('render.camera {%s}' % tracerCam.id)
        tracerCam.channel('offsetX').set(target_offset[0])
        tracerCam.channel('offsetY').set(target_offset[1])
        tracerCam.channel('apertureX').set(target_aperture[0])
        tracerCam.channel('apertureY').set(target_aperture[1])

        lx.eval('edit.apply')

        notifier = cropper.CropperNotify()
        notifier.Notify(lx.symbol.fCMDNOTIFY_DATATYPE)


class CropperToggle(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('quick', lx.symbol.sTYPE_BOOLEAN)
        self.basic_SetFlags(0, lx.symbol.fCMDARG_OPTIONAL)

    def basic_Execute(self, msg, flags):
        if active_pass():
            deactivate_pass()

        elif modo.Scene().renderItem.channel('region').get():
            arg = ' {%s}' % DEFAULT_PASSNAME if self.dyna_Bool(0) else ''
            lx.eval('cropper.crop{}'.format(arg))

        else:
            activate_latest_pass()

class CropperDisable(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)

    def basic_Execute(self, msg, flags):
        if active_pass():
            deactivate_pass()

class CropperClearAll(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)

    def basic_ButtonName(self):
        return "Delete All Crops"

    def basic_Execute(self, msg, flags):
        try:
            modo.Scene().removeItems(modo.Scene().item(cropper.GROUP_NAME))
        except:
            pass

        hitlist = set()
        for i in modo.Scene().iterItems():
            if i.hasTag(cropper.CAM_TAG):
                if SUFFIX in i.getTags()[cropper.CAM_TAG]:
                    hitlist.add(i)

            if i.hasTag(cropper.CAM_TAG):
                i.setTag(cropper.CAM_TAG, None)

        for hit in hitlist:
            modo.Scene().removeItems(hit)

        notifier = cropper.CropperNotify()
        notifier.Notify(lx.symbol.fCMDNOTIFY_DATATYPE)

lx.bless(CropperToggle, "cropper.toggleButton")
lx.bless(CropperDisable, "cropper.disable")
lx.bless(Cropper, "cropper.crop")
lx.bless(CropperClearAll, "cropper.clearAll")
