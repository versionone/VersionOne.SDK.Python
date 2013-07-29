import unittest

class NoneDeref(object):
  def __getattr__(self, attr):
    return self
  
  def __getstate__(self):
    return None
    
  def __setstate__(self, state):
    pass
  
  def __str__(self):
    return "None"
  
  def __nonzero__(self):
    return False
  
  def __bool__(self):
    return False
  
class NoneDerefTest(unittest.TestCase):
  def setUp(self):
    self.object = NoneDeref()

  def test_any_attribute_is_present_and_falsy(self):
    self.assertFalse(self.object.foo)
    self.assertFalse(self.object.bar)
  
  def test_object_is_falsy(self):
    self.assertFalse(self.object)

  def test_object_can_be_pickled(self):
    import pickle
    
    s = pickle.dumps(self.object)
    n = pickle.loads(s)
    self.assertFalse(n)
    self.assertFalse(self.object.foo)
    self.assertFalse(self.object.bar)
  
  def test_object_converts_to_None_string(self):
    self.assertEqual(str(self.object), "None")

if __name__ == "__main__":
  unittest.main()
