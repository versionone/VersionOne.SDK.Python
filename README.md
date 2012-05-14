



An API client for the VersionOne agile project management system.




* Dynamic reflection of all V1 asset types

  Just instantiate a V1Meta.  All asset types defined on the server are available
  as attributes on the instance.  The metadata is only loaded once, so you must
  create a new instance of V1Meta to pick up metadata changes.

* Simple access to individual assets.

  Assets are created on demand and cached so that once instance always represents
  the same asset.  
  
* Lazyily loaded values and relations

  Asset instances are created with any data available, and query the server on-demand
  for attributes that aren't currently fetched. 

* Simple query syntax::

  for s in v1.Story.where(Name='Add feature X to main product"):
      print s.Name, s.CreateDate, [o.name for o in s.Owners]
      
* Simple creation syntax::

  new_story = v1.Story.create(Name='New Story', scope=v1.Scope(1002))
  
* Simple update syntax::

  v1.Story(1005).Name = 'Super Cool Feature Redux'
  v1.Owners = list( v1.Members.where(Name='Joe Koberg') )
  v1.commit()
  

