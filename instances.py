import weakref

"""
This module allows you to obtain a list of all instances of a class.
To use it you must derive your class from InstancesCollector, or 
include InstancesCollector as a mixin class. Then you can obtain a list of all instances
using the module function instancesOf(class).

This module copes with deletion of instances of your class.

In python 2.7 it is advisable to avoid the use of super() when defining __init__ unless you are certain 
that the class you are mixing in with has been derived from (object). Specify the meta classes explicitly,
as in the following example. Otherwise the super() hierarchy might not work properly.

In python 3 it is recommended to always use super().

for example

class SafeTimer(wx.Timer, InstancesCollector):
    def __init__(self, *args, **kwargs):
        InstancesCollector.__init__(self)
        wx.Timer.__init__(self, *args, **kwargs)
        print ("init SafeTimer")

    @staticmethod
    def stopAllTimers():
        for timer in instancesOf(SafeTimer):
            timer.Stop()
            print ("Stopping", timer)

     
"""

class InstancesCollector(object):
    _classes = {}

    def __init__(self):
        super(InstancesCollector, self).__init__()
        r = weakref.ref(self, InstancesCollector._cleanup)
        InstancesCollector._classes[r] = type(self)
        try:
            type(self)._instances.append(r)
        except:
            type(self)._instances = [r]
        # print ("init InstancesCollector", type(self) )

    @staticmethod
    def _cleanup(ref):
        InstancesCollector._classes[ref]._instances.remove(ref)
        del InstancesCollector._classes[ref]
        # print ("InstancesCollector _cleanup", ref)

def instancesOf(cls):
    if hasattr(cls, '_instances'):
        return [x() for x in cls._instances]
    else:
        return []
