

# objects here will be mixed into the dynamically created asset type classes
# based on name.

# This lets us extend certain asset types without having to give up the generic
# dynamic meta implementation  

class Attachment(object):
    def set_blob(self, blob):
        return self._v1_v1meta.set_attachment_blob(self, blob)
        
    def get_blob(self):
        return self._v1_v1meta.get_attachment_blob(self)
        
    file_data = property(get_blob, set_blob)
    


# the special_classes mapping will be used to lookup mixins by asset type name. 
special_classes = locals()

