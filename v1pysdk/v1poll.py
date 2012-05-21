


from v1meta import V1Meta

import sqlite3
from collections import defaultdict


class V1Poll(object):
    def __init__(self, filename='versionone_poll_state.sqlite'):
        self.datafile_name = filename
        self.db = sqlite3.connect(self.datafile_name)
        self.registrations = defaultdict(list)
              
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
        
        
        
        previously_called_handlers = 
        newly_registered_handlers = 
        
        previously_polled_asset_types = 
        newly_registered_asset_types = 
        
        for asset_type in previously_polled_asset_types:
          
          
        
        for row in rows:
          registered_funcs = self.registrations[row['asset_type']]
          
          
        
            
        