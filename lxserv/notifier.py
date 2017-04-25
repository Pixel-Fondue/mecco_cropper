# python

import lx
import lxifc

class CropperNotify(lxifc.Notifier):
    masterList = {}

    def noti_Name(self):
        return "cropper.notifier"

    def noti_AddClient(self,event):
        self.masterList[event.__peekobj__()] = event

    def noti_RemoveClient(self,event):
        del self.masterList[event.__peekobj__()]

    def Notify(self, flags):
        for event in self.masterList:
            evt = lx.object.CommandEvent(self.masterList[event])
            evt.Event(flags)

lx.bless(CropperNotify, "cropper.notifier")
