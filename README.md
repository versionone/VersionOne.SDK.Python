



# An API client for the VersionOne agile project management system.


## Overview

### Dynamic reflection of all V1 asset types:

  Just instantiate a V1Meta.  All asset types defined on the server are available
  as attributes on the instance.  The metadata is only loaded once, so you must
  create a new instance of V1Meta to pick up metadata changes.
  
      from v1pysdk import V1Meta
      
      v1 = V1Meta()  # Assumes localhost/VersionOne.Web, credentials Admin/Admin
      
      v1 = V1Meta(
             address = 'v1server.mycompany.com',
             instance = 'VersionOne',
             username = 'jsmith',
             password = 'swordfish'
             )


### Simple access to individual assets:

  Assets are created on demand and cached so that once instance always represents
  the same asset.

      s = v1.Story(1005)
      
      print s is v1.Story(1005)   # True
      


### Lazyily loaded values and relations:

  Asset instances are created with any data available, and query the server on-demand
  for attributes that aren't currently fetched. 


### Simple query syntax:

      for s in v1.Story.where(Name='Add feature X to main product"):
          print s.Name, s.CreateDate, ', '.join([owner.Name for owner in s.Owners])


### Simple creation syntax:

      new_story = v1.Story.create(Name='New Story', scope=v1.Scope(1002))
      # creation happens immediately. No need to commit.
      print new_story


### Simple update syntax:

      story = v1.Story(1005)
      story.Name = 'Super Cool Feature Redux'
      story.Owners = list( v1.Members.where(Name='Joe Koberg') )
      
      v1.commit()  # flushes all pending updates to the server


## TODO

  * Make things Moment-aware
  
  * Convert types between client and server (right now everything is a string)
  
  * Add debug logging
  
  * Beef up test coverage
  
    * Need to mock up server
    
  * Examples
  
    * provide an actual integration example
    
  * Asset creation templates and creation "in context of" other asset
      
