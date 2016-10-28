import lx, lxu.command, modo

BLESS = "cropper.focalLength"

class commandClass(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        cameraName = modo.Scene().renderCamera.id

        modo.Scene().renderCamera.select()
        lx.eval('select.channel {%s:focalLen} add' % cameraName)
        lx.eval('tool.set channel.haul on')

lx.bless(commandClass, BLESS)
