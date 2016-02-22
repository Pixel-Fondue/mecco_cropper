#Must be inside a folder called 'lxserv' somewhere in a MODO search path.

import lx
import lxu.command
import modo

GROUP_NAME = 'mecco_regions'
DEFAULT_PASSNAME = 'quick crop'


def quick_user_value(value_handle, value_type='string', nicename='', default=''):
    if lx.eval('query scriptsysservice userValue.isDefined ? {}'.format(value_handle)) == 0:
        lx.eval('user.defNew {} {}'.format(value_handle, value_type))

    try:
        lx.eval('user.def {} username {{{}}}'.format(value_handle, nicename))
        lx.eval('user.def {} type {}'.format(value_handle, value_type))
        lx.eval('user.value {} {{{}}}'.format(value_handle, default))
        lx.eval('user.value {}'.format(value_handle))
        return lx.eval('user.value {} value:?'.format(value_handle))

    except:
        return None


def get_target_frame():
    render_region = {
        'left': float(modo.Scene().renderItem.channel('regX0').get()),
        'right': float(modo.Scene().renderItem.channel('regX1').get()),
        'top': float(modo.Scene().renderItem.channel('regY0').get()),
        'bottom': float(modo.Scene().renderItem.channel('regY1').get())
    }

    return [
        int(round(int(modo.Scene().renderItem.channel('resX').get()) * abs(render_region['right'] - render_region['left']))),
        int(round(int(modo.Scene().renderItem.channel('resY').get()) * abs(render_region['bottom'] - render_region['top']))),
    ]


def get_target_offset(new_aperture):
    frame = [
        int(modo.Scene().renderItem.channel('resX').get()),
        int(modo.Scene().renderItem.channel('resY').get())
    ]

    offset = [
        float(modo.Scene().renderCamera.channel('offsetX').get()),
        float(modo.Scene().renderCamera.channel('offsetY').get())
    ]

    render_region = {
        'left': float(modo.Scene().renderItem.channel('regX0').get()),
        'right': float(modo.Scene().renderItem.channel('regX1').get()),
        'top': float(modo.Scene().renderItem.channel('regY0').get()),
        'bottom': float(modo.Scene().renderItem.channel('regY1').get())
    }

    x_step = 1
    y_step = x_step

    if frame[0] == frame[1]:
        x_step = new_aperture[1]
        y_step = new_aperture[1]

    elif frame[0] > frame[1]:
        mdf = float(frame[0]) / frame[1]
        x_step = new_aperture[0]
        y_step = new_aperture[0] / mdf

    elif frame[0] < frame[1]:
        mdf = float(frame[1]) / frame[0]
        x_step = new_aperture[1] / mdf
        y_step = new_aperture[1]

    offset = [
        ((render_region['left']+render_region['right'])/2 - .5) * x_step + offset[0],
        ((render_region['top']+render_region['bottom'])/2 - .5) * -y_step + offset[1],
    ]

    return offset


def deactivate_pass():
    graph_kids = modo.Scene().item(GROUP_NAME).itemGraph('itemGroups').forward()
    passes = [i for i in graph_kids if i.type == lx.symbol.a_ACTIONCLIP]

    for pass_ in passes:
        pass_.actionClip.SetActive(0)


def active_pass():
    try:
        modo.Scene().item(GROUP_NAME)
    except:
        return None

    graph_kids = modo.Scene().item(GROUP_NAME).itemGraph('itemGroups').forward()
    passes = [i for i in graph_kids if i.type == lx.symbol.a_ACTIONCLIP]

    for pass_ in passes:
        if pass_.actionClip.Active():
            return pass_

    return None


def activate_latest_pass():
    graph_kids = modo.Scene().item(GROUP_NAME).itemGraph('itemGroups').forward()
    passes = [i for i in graph_kids if i.type == lx.symbol.a_ACTIONCLIP]

    max(passes, key=lambda p: p.index).actionClip.SetActive(1)


def get_latest_pass():
    graph_kids = modo.Scene().item(GROUP_NAME).itemGraph('itemGroups').forward()
    passes = [i for i in graph_kids if i.type == lx.symbol.a_ACTIONCLIP]
    return max(passes, key=lambda p: p.index)


def get_target_aperture():
    frame = [
        int(modo.Scene().renderItem.channel('resX').get()),
        int(modo.Scene().renderItem.channel('resY').get())
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



class mecco_cropper(lxu.command.BasicCommand):
    
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('name', lx.symbol.sTYPE_STRING)

    def basic_Execute(self, msg, flags):
        pass_name = self.dyna_String(0)

        if not pass_name:
            pass_name = DEFAULT_PASSNAME

        target_aperture = get_target_aperture()
        target_frame = get_target_frame()
        target_offset = get_target_offset(target_aperture)
        long_axis = 'X' if target_frame[0] >= target_frame[1] else 'Y'

        modo.Scene().renderItem.channel('region').set(False)

        try:
            modo.Scene().item(GROUP_NAME)
        except:
            lx.eval('group.create {} pass empty'.format(GROUP_NAME))

        channels_list = [
            modo.Scene().renderItem.channel('resX'),
            modo.Scene().renderItem.channel('resY'),
            modo.Scene().renderCamera.channel('offsetX'),
            modo.Scene().renderCamera.channel('offsetY'),
            modo.Scene().renderCamera.channel('aperture{}'.format(long_axis))
        ]

        for channel in channels_list:
            if channel not in modo.Scene().item(GROUP_NAME).groupChannels:
                modo.Scene().item(GROUP_NAME).addChannel(channel)

        lx.eval('group.layer group:{{{}}} name:{{{}}} grpType:pass'.format(GROUP_NAME, pass_name))

        modo.Scene().renderItem.channel('resX').set(target_frame[0]),
        modo.Scene().renderItem.channel('resY').set(target_frame[1]),
        modo.Scene().renderCamera.channel('offsetX').set(target_offset[0]),
        modo.Scene().renderCamera.channel('offsetY').set(target_offset[1]),
        modo.Scene().renderCamera.channel('aperture{}'.format(long_axis)).set(target_offset[1])

        lx.eval('edit.apply')


class mecco_cropper_toggle(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('name', lx.symbol.sTYPE_STRING)
        self.basic_SetFlags(0, lx.symbol.fCMDARG_OPTIONAL)

    def basic_Execute(self, msg, flags):
        if active_pass():
            deactivate_pass()
        elif modo.Scene().renderItem.channel('region').get():
            arg = self.dyna_String(0) if self.dyna_String(0) else ''
            lx.eval('mecco.cropper {}'.format(arg))
        else:
            try:
                activate_latest_pass()
            except:
                pass
        
lx.bless(mecco_cropper_toggle, "mecco.cropperToggle")
lx.bless(mecco_cropper, "mecco.cropper")
