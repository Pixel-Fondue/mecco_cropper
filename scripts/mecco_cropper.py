# python

# Cropper is open source, but not free.
# If you like it, please purchase one copy per user at mechanicalcolor.com
# Thanks!
# --Adam

import lx
import lxu.select


GROUP_NAME = 'mecco_regions'
DEFAULT_PASSNAME = 'quick crop'

arg = lx.arg()
lx.out("arg=%s"%arg)


def quick_user_value(valHandle, valType='string', nicename='', default=''):
    if lx.eval('query scriptsysservice userValue.isDefined ? %s' % valHandle) == 0:
        lx.eval('user.defNew %s %s' % (valHandle, valType))

    try:
        lx.eval('user.def %s username {%s}' % (valHandle, nicename))
        lx.eval('user.def %s type %s' % (valHandle, valType))
        lx.eval('user.value %s {%s}' % (valHandle, default))
        lx.eval('user.value %s' % valHandle)
        return lx.eval('user.value %s value:?' % valHandle)
    except:
        return False


def get_render_id():
    return lx.eval('query sceneservice item.ID ? {Render}')


def get_camera_id():
    try:
        renderCamera = lx.eval("render.camera ?")
    except:
        renderCamera = "Camera"
    return lx.eval('query sceneservice item.ID ? {%s}' % renderCamera)


def get_pass_group_id():
    item_id = False
    n = lx.eval("query sceneservice item.N ?")
    # Loop through the items in the scene

    for i in range(n):
        # Get the item name
        item_name = lx.eval("query sceneservice item.name ? %s" % i)
        if item_name == GROUP_NAME:
            # Get the item ID
            item_id = lx.eval("query sceneservice item.id ? %s" % i)
            break
    return item_id


def select_render():
    scene = lxu.select.SceneSelection().current()
    render_object = scene.AnyItemOfType(lx.symbol.i_CIT_RENDER)
    lx.eval('select.item {%s} set' % render_object.Ident())


def select_camera():
    lx.eval('select.item {%s} add' % get_camera_id())


def select_pass_group():
    item_id = get_pass_group_id()
    if item_id != False:
        lx.eval('select.item %s set' % item_id)
        return True
    else:
        return False


def create_pass_group():
    item_id = get_pass_group_id()
    if item_id != False:
        lx.eval('select.item %s set' % item_id)
    else:
        lx.eval('group.create %s pass empty' % GROUP_NAME)


def get_render_region():
    render_id = get_render_id()
    return {
        'left': lx.eval('item.channel regX0 ? item:%s' % render_id ),
        'right': lx.eval('item.channel regX1 ? item:%s' % render_id ),
        'top': lx.eval('item.channel regY0 ? item:%s' % render_id ),
        'bottom': lx.eval('item.channel regY1 ? item:%s' % render_id )
    }


def region_size():
    rr_val = get_render_region()
    return {
        'x': (abs(rr_val['right'] - rr_val['left'])),
        'y': (abs(rr_val['bottom'] - rr_val['top']))
    }


def set_region_state(p_state):
    lx.eval('item.channel region %s item:Render' % p_state)


def frame_size():
    render_id = get_render_id()
    x = int(lx.eval('item.channel resX ? item:%s' % render_id))
    y = int(lx.eval('item.channel resY ? item:%s' % render_id))
    return {'x': x, 'y': y}


def film_offsets():
    camera_id = get_camera_id()
    x = float(lx.eval('item.channel offsetX ? item:%s' % camera_id))
    y = float(lx.eval('item.channel offsetY ? item:%s' % camera_id))
    return {'x': x, 'y': y}


def target_frame_size():
    r = region_size()
    f = frame_size()
    return {
        'x': int(round(f['x'] * r['x'])),
        'y': int(round(f['y'] * r['y'])),
    }


def create_pass(dialog):
    try:
        if dialog != 'false':
            pass_name = quick_user_value('mecco_cropper_passName', 'string', 'Pass Name', DEFAULT_PASSNAME)
        else:
            pass_name = DEFAULT_PASSNAME
        if pass_name == False:
            pass_name = DEFAULT_PASSNAME
        lx.eval('group.layer name:{%s}' % pass_name)
    except:
        lx.eval('group.layer name:{%s}' % DEFAULT_PASSNAME)


def add_channels_to_pass_group(p_max_value):
    lx.eval('select.drop channel')
    render_id = get_render_id()
    camera_id = get_camera_id()

    channels_list = [
        '{%s:resX}' % render_id,
        '{%s:resY}' % render_id,
        '{%s:offsetX}' % camera_id,
        '{%s:offsetY}' % camera_id,
        ]

    if p_max_value == 'x':
        channels_list.append('{%s:apertureX}' % camera_id)
    else:
        channels_list.append('{%s:apertureY}' % camera_id,)

    for channel in channels_list:
        try:
            lx.eval('select.channel %s add' % channel)
        except:
            pass

    # add channels
    try:
        lx.eval('!!group.edit add chan item:%s' % get_pass_group_id())
    except:
        pass


def max_val(p_target_frame_size):
    if p_target_frame_size['x'] >= p_target_frame_size['y']:
        return 'x'
    else:
        return 'y'


def get_offsets(p_new_apertures):
    rr_val = get_render_region()
    f = frame_size()
    offsets = film_offsets()

    x_step = 1
    y_step = x_step
    if f['x'] == f['y']:
        x_step = p_new_apertures['y']
        y_step = p_new_apertures['y']
    elif f['x'] > f['y']:
        mdf = float(f['x']) / float(f['y'])
        x_step = p_new_apertures['x']
        y_step = p_new_apertures['x'] / mdf
    elif f['x'] < f['y']:
        mdf = float(f['y']) / float(f['x'])
        x_step = p_new_apertures['y'] / mdf
        y_step = p_new_apertures['y']

    offset = {
        'x': ((rr_val['left']+rr_val['right'])/2 - .5) * x_step + offsets['x'],
        'y': ((rr_val['top']+rr_val['bottom'])/2 - .5) * -y_step + offsets['y'],
    }

    return offset


def reset_pass():
    try:
        lx.eval('layer.active {} type:pass')
    except:
        return False


def set_channels(p_target_frame_size, p_target_offset, p_new_aperture, p_target_aperture):
    render_id = get_render_id()
    camera_id = get_camera_id()

    lock_value = lx.eval("item.channel locator$lock ? item:%s" % camera_id)

    channels_list = [
        ['locator$lock', 'off', camera_id],
        ['resX', p_target_frame_size['x'], render_id],
        ['resY', p_target_frame_size['y'], render_id],
        ['offsetX', p_target_offset['x'], camera_id],
        ['offsetY', p_target_offset['y'], camera_id],
        ['locator$lock', lock_value, camera_id]
    ]

    if p_target_aperture == 'x':
        channels_list.append(['apertureX', p_new_aperture, camera_id])
    else:
        channels_list.append(['apertureY', p_new_aperture, camera_id])

    for channel in channels_list:
        lx.eval('item.channel %s %s item:%s' %(channel[0], channel[1], channel[2]))

    lx.eval('edit.apply')


def get_apertures():
    ax = lx.eval('item.channel apertureX ? item:%s' % get_camera_id())
    ay = lx.eval('item.channel apertureY ? item:%s' % get_camera_id())
    return {'x': ax, 'y': ay}


def crop_is_active():
    if select_pass_group() == True:
        try:
            active_layer = lx.eval("layer.active ? type:pass")
        except:
            active_layer = False
        if active_layer:
            return True
        else:
            return False
    else:
        return False


def region_is_active():
    try:
        render_id = get_render_id()
        active = lx.eval("item.channel region ? item:%s" % render_id)
    except:
        return 0
    return active


def activate_latest_pass():
    pass_group_id = get_pass_group_id()
    if pass_group_id != False:
        lx.eval('select.item %s set' % pass_group_id)
        group = lx.eval('group.current ? pass')
        if group:
            passes = [lx.eval('query sceneservice actionclip.id ? %s' % i)
                      for i in xrange(lx.eval('query sceneservice actionclip.N ?'))]

            members = [x
                       for x in lx.evalN('query sceneservice group.itemMembers ? {%s}' % group)
                       if lx.eval('query sceneservice item.type ? {%s}' % x) == 'actionclip']

            if members:
                members.sort(key=lambda x: passes.index(x))
                lx.eval('layer.active {%s} type:pass' % members[-1])


def get_frame_ratio():
    f_size = frame_size()
    if f_size['x'] >= f_size['y']:
        return float(f_size['x']) / float(f_size['y'])
    else:
        return float(f_size['y']) / float(f_size['x'])


def get_aperture_ratio():
    aperture = get_apertures()
    if aperture['x'] >= aperture['y']:
        return float(aperture['x']) / float(aperture['y'])
    else:
        return float(aperture['y']) / float(aperture['x'])


def get_new_apertures():
    ratio = get_frame_ratio()
    aperture = get_apertures()

    apr_ratio = get_aperture_ratio()

    if ratio <= apr_ratio:
        if aperture['x'] > aperture['y']:
            aperture['x'] = aperture['y'] * ratio
        elif aperture['x'] < aperture['y']:
            aperture['y'] = aperture['x'] * ratio

    return aperture


def get_aperture_values(p_new_apr):
    reg_size = region_size()
    f_size = frame_size()
    mv_rs = max_val(target_frame_size())

    if mv_rs == 'x':
        if f_size['x'] > f_size['y']:
            return ['x', p_new_apr['x'] * reg_size['x']]
        if f_size['x'] == f_size['y']:
            return ['x', p_new_apr['y'] * reg_size['x']]
        if f_size['x'] < f_size['y']:
            return ['y', p_new_apr['y'] * reg_size['y']]
    else:
        return ['y', p_new_apr['y'] * reg_size['y']]


def main():
    select_render()
    select_camera()

    new_apertures = get_new_apertures()
    target_aperture, apr_value = get_aperture_values(new_apertures)

    if crop_is_active():
        select_pass_group()
        reset_pass()

    elif region_is_active():
        set_region_state(False)
        create_pass_group()
        create_pass(arg)
        add_channels_to_pass_group(target_aperture)
        set_channels(target_frame_size(), get_offsets(new_apertures), apr_value, target_aperture)

    elif get_pass_group_id() != False:
        activate_latest_pass()

main()