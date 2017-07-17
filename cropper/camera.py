# python

import modo
import lx
import datetime

CAM_TAG = 'CROP'
GROUP_NAME = 'mecco_regions'

def get_tracer_camera(SUFFIX):
    if modo.Scene().renderCamera.hasTag(CAM_TAG) == False:
        return None

    if SUFFIX in modo.Scene().renderCamera.getTags()[CAM_TAG]:
        return None

    tagValue = modo.Scene().renderCamera.getTags()[CAM_TAG] + SUFFIX

    for i in modo.Scene().iterItems():
        if i is not modo.Scene.renderCamera and i.hasTag(CAM_TAG):
            if i.getTags()[CAM_TAG] == tagValue:
                return i

    return None
    
def create_tracer_camera(SUFFIX, offsets):
    camera = modo.Scene().addItem('camera')
    renderCam = modo.Scene().renderCamera

    camera.channel('visible').set('allOff')
    camera.channel('lock').set('on')
    camera.name = renderCam.name + SUFFIX
    camera.setParent(renderCam)

    tagValue = ''.join([i for i in str(datetime.datetime.now()) if i.isalnum()])
    camera.setTag(CAM_TAG, tagValue + SUFFIX)
    renderCam.setTag(CAM_TAG, tagValue)

    channels_to_link = [
        'wposMatrix',
        'wrotMatrix',
        'focalLen',
        'size',
        'squeeze',
        'dof',
        'focusDist',
        'fStop',
        'irisBlades',
        'irisRot',
        'irisBias',
        'distort',
        'motionBlur',
        'blurLen',
        'blurOff',
        'stereo',
        'stereoEye',
        'stereoComp',
        'ioDist',
        'convDist',
        'target',
        'clipDist',
        'clipping'
    ]

    for channel in channels_to_link:
    	lx.eval("channel.link add {%s:%s} {%s:%s}" % (renderCam.id, channel, camera.id, channel))

    if offsets:
        channels_to_copy = [
            'apertureX',
            'apertureY',
            'offsetX',
            'offsetY'
        ]
    else:
        channels_to_copy = [
            'apertureX',
            'apertureY',
        ]

    for channel in channels_to_copy:
        camera.channel(channel).set(renderCam.channel(channel).get())

    return camera
    
def resXChannel():
    if modo.Scene().renderCamera.channel('resOverride').get() == 1:
        return modo.Scene().renderCamera.channel('resX')
    else:
        return modo.Scene().renderItem.channel('resX')
        
def resYChannel():
    if modo.Scene().renderCamera.channel('resOverride').get() == 1:
        return modo.Scene().renderCamera.channel('resY')
    else:
        return modo.Scene().renderItem.channel('resY')