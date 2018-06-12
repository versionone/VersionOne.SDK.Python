


from .v1meta import V1Meta

import sqlite3
from collections import defaultdict


class V1Poll(object):
    def __init__(self, meta=None, filename='versionone_poll_state.sqlite'):
        if not meta:
          meta = V1Meta()
        self.datafile_name = filename
        self.db = sqlite3.connect(self.datafile_name)
        self.registrations = defaultdict(list)
     
    def __enter__(self):
        return self
    
    def __exit__(self):
        self.poll()
        
    def run_on_new(self, asset_type_name, handler_function):
        self.registrations[asset_type_name].append(handler_function)
        raise NotImplementedError
        
    def poll(self):
        raise NotImplementedError
        for asset_type, callback in self.registrations.items():
            callback_id = callback.__module__ + '.' + callback.__name__
        rows = self.db.query("""
            select asset_type, min(last_moment)
            from v1_poll_data
            group by asset_type
            """)
        
        # if asset type has never been registered, 
        # just put the current moment in the file as the last
        # seen moment for all newly registered funcs
        
        # if it has been, get the earliest "previous moment"
        # query that asset type for everything since that moment
        # walk through, calling the handler funcs conditionally only if
        #  they have not been called for that moment
        
        
        
        previously_called_handlers = None
        newly_registered_handlers = None
        
        previously_polled_asset_types = None
        newly_registered_asset_types = None
        
        for asset_type in previously_polled_asset_types:
            pass
          
        for row in rows:
          registered_funcs = self.registrations[row['asset_type']]
          
          
        
            
        
