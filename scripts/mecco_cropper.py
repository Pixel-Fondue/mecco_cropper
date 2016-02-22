# python

# Cropper is open source, but not free.
# If you like it, please purchase one copy per user at mechanicalcolor.com
# Thanks!
# --Adam

import lx
import modo

GROUP_NAME = 'mecco_regions'
DEFAULT_PASSNAME = 'quick crop'

ARG = lx.arg()


def quick_user_value(value_handle, value_type='string', nicename='', default=''):
    if lx.eval('query scriptsysservice userValue.isDefined ? %s' % value_handle) == 0:
        lx.eval('user.defNew %s %s' % (value_handle, value_type))

    try:
        lx.eval('user.def %s username {%s}' % (value_handle, nicename))
        lx.eval('user.def %s type %s' % (value_handle, value_type))
        lx.eval('user.value %s {%s}' % (value_handle, default))
        lx.eval('user.value %s' % value_handle)
        return lx.eval('user.value %s value:?' % value_handle)

    except:
        return False


def get_render_region():
    return {
        'left': float(modo.Scene().renderItem.channel('regX0').get()),
        'right': float(modo.Scene().renderItem.channel('regX1').get()),
        'top': float(modo.Scene().renderItem.channel('regY0').get()),
        'bottom': float(modo.Scene().renderItem.channel('regY1').get())
    }


def region_size():
    rr = get_render_region()
    return [
        (abs(rr['right'] - rr['left'])),
        (abs(rr['bottom'] - rr['top']))
    ]


def frame_size():
    return [
        int(modo.Scene().renderItem.channel('resX').get()),
        int(modo.Scene().renderItem.channel('resY').get())
        ]


def film_offset():
    return [
        float(modo.Scene().renderCamera.channel('offsetX').get()),
        float(modo.Scene().renderCamera.channel('offsetY').get())
    ]


def get_target_frame():
    rr = region_size()
    frame = frame_size()
    return [
        int(round(frame[0] * rr[0])),
        int(round(frame[1] * rr[1])),
    ]


def create_pass(dialog=False):
    try:
        if dialog in ('true', 'yes', 'affirmative', 'yup', 1, True):
            pass_name = quick_user_value('mecco_cropper_passName', 'string', 'Pass Name', DEFAULT_PASSNAME)
            if not pass_name:
                pass_name = DEFAULT_PASSNAME
        else:
            pass_name = DEFAULT_PASSNAME

        lx.eval('group.layer group:{{{}}} name:{{{}}} grpType:pass'.format(GROUP_NAME, pass_name))

    except:
        lx.eval('group.layer group:{{{}}} name:{{{}}} grpType:pass'.format(GROUP_NAME, DEFAULT_PASSNAME))


def add_channels_to_pass_group(axis):
    channels_list = [
        modo.Scene().renderItem.channel('resX'),
        modo.Scene().renderItem.channel('resY'),
        modo.Scene().renderCamera.channel('offsetX'),
        modo.Scene().renderCamera.channel('offsetY'),
        modo.Scene().renderCamera.channel('aperture{}'.format(axis))
        ]

    for channel in channels_list:
        modo.Scene().item(GROUP_NAME).addChannel(channel)


def get_target_offset(new_aperture):
    rr = get_render_region()
    frame = frame_size()
    offset = film_offset()

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
        ((rr['left']+rr['right'])/2 - .5) * x_step + offset[0],
        ((rr['top']+rr['bottom'])/2 - .5) * -y_step + offset[1],
    ]

    return offset


def deactivate_pass():
    passes = [i for i in modo.Scene().item(GROUP_NAME).itemGraph('itemGroups').forward() if i.type == lx.symbol.a_ACTIONCLIP]
    for pass_ in passes:
        pass_.actionClip.SetActive(0)


def set_channels(target_frame, target_offset, axis):
    modo.Scene().renderItem.channel('resX').set(target_frame[0]),
    modo.Scene().renderItem.channel('resY').set(target_frame[1]),
    modo.Scene().renderCamera.channel('offsetX').set(target_offset[0]),
    modo.Scene().renderCamera.channel('offsetY').set(target_offset[1]),
    modo.Scene().renderCamera.channel('aperture{}'.format(axis)).set(target_offset[1])


def get_apertures():
    return [
        modo.Scene().renderCamera.channel('apertureX').get(),
        modo.Scene().renderCamera.channel('apertureY').get()
        ]


def active_pass():
    try:
        passes = [i for i in modo.Scene().item(GROUP_NAME).itemGraph('itemGroups').forward() if i.type == lx.symbol.a_ACTIONCLIP]

        for pass_ in passes:
            if pass_.actionClip.Active():
                return pass_

        return False
    
    except:
        return False


def activate_latest_pass():
    passes = [i for i in modo.Scene().item(GROUP_NAME).itemGraph('itemGroups').forward() if i.type == lx.symbol.a_ACTIONCLIP]
    max(passes, key=lambda p: p.index).actionClip.SetActive(1)


def get_target_aperture():
    frame = frame_size()
    ratio = float(max(frame)) / min(frame)

    aperture = get_apertures()
    apr_ratio = float(max(aperture)) / min(aperture)

    if ratio <= apr_ratio:
        if aperture[0] > aperture[1]:
            aperture[0] = aperture[1] * ratio
        elif aperture[0] < aperture[1]:
            aperture[1] = aperture[0] * ratio

    return aperture


def main():
    if active_pass():
        deactivate_pass()

    elif modo.Scene().renderItem.channel('region').get():
        target_aperture = get_target_aperture()
        target_frame = get_target_frame()
        target_offset = get_target_offset(target_aperture)
        long_axis = 'X' if target_frame[0] >= target_frame[1] else 'Y'

        modo.Scene().renderItem.channel('region').set(False)

        try:
            modo.Scene().item(GROUP_NAME)
        except:
            lx.eval('group.create %s pass empty' % GROUP_NAME)


        add_channels_to_pass_group(long_axis)

        create_pass(ARG)
        activate_latest_pass()

        set_channels(target_frame, target_offset, long_axis)

    else:
        try:
            activate_latest_pass()
        except:
            pass

main()
