



class Attachment(object):
    def set_blob(self, blob):
        return self._v1_meta.set_attachment_blob(self, blob)
        
    def get_blob(self):
        return self._v1_meta.get_attachment_blob(self)
        
    file_data = property(get_blob, set_blob)
    
    
    
special_classes = locals()

