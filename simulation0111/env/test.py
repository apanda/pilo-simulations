import copy

class InterfaceMeta(type):
  def __init__(self, parents):
    self.parents = parents

  def __new__(cls, name, parents, dct):
    cls.parents = parents
    return super(InterfaceMeta, cls).__new__(cls, name, self.parents, dct)

class BaseClass1(object):
    def __init__(self):
        print "BaseClass1"
        d = self.class_b1_method
    def class_b1_method(self):
      print "class_b1_method"

class BaseClass2(object):
    def __init__(self):
        print "BaseClass2"

    def class_b2_method(self):
      print "class_b2_method"

class A(object):
    def __init__(self):
        print "A"
        super(A, self).__init__()
    
def GetClass(base_class):
    class Ret(A, base_class):
        def __init__(self):
            print "Ret"
            base_class.__init__(self)
    return Ret

r = GetClass(BaseClass1)()
r.class_b1_method()
