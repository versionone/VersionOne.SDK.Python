# An API client for the VersionOne agile project management system.


## Overview

### Dynamic reflection of all V1 asset types:

  Just instantiate a V1Meta.  All asset types defined on the server are available
  as attributes on the instance.  The metadata is only loaded once, so you must
  create a new instance of V1Meta to pick up metadata changes.  Each asset class
  comes with properties for all asset attributes and operations.
  
      from v1pysdk import V1Meta
      
      v1 = V1Meta()  # Assumes localhost/VersionOne.Web, credentials Admin/Admin
      
      v1 = V1Meta(
             address = 'v1server.mycompany.com',
             instance = 'VersionOne',
             username = 'jsmith',
             password = 'swordfish'
             )

      Story = v1.Story
      print dir(Story)
      #  ['Actuals', 'AffectedByDefects', 'AllocatedDetailEstimate', 'AllocatedToDo', 'AssetState',
          'AssetType', 'Attachments', 'Benefits', 'BlockingIssues', 'Breakdown', 'CanConvertToDefect',
          'CanUpdate', 'Category', 'ChangeComment', 'ChangeDate', 'ChangeDateUTC', 'ChangeReason',
          'ChangeSets', 'ChangedBy', 'CheckBreakdown', 'CheckCopy', 'CheckDeepCopy', 'CheckInactivate',
          'CheckMakeTemplate', 'CheckQuickClose', 'CheckQuickSignup', 'CheckReactivate',
          'CheckShallowCopy', 'CheckSplit', 'Children', 'ChildrenAndDown', 'ChildrenAndMe',
          'ChildrenMeAndDown', 'ClosedEstimate', 'CompleteEstimate', 'CompletedInBuildRuns',
          'ConvertToDefect', 'Copy', 'CreateComment', 'CreateDate', 'CreateDateUTC', 'CreateReason',
          'CreatedBy', 'Custom_AnalysisStatus', 'Custom_AutoEmailCount', 'Custom_EmailAttempts',
          'Custom_EstimateMe2', 'Custom_ITKahnbahn', 'Custom_LastAutoEmail', 'Custom_SFDCAccountID',
          'Custom_SFDCDate', 'Custom_SFDCLastActivity', 'Custom_ScheduledOn',
          'Custom_ServicesClassofService', 'Custom_StyleStatus3', 'Custom_TestCustomField',
          'Custom_TestType', 'Customer', 'DeepCopy', 'Delete', 'Dependants', 'Dependencies',
          'Description', 'DetailEstimate', 'Estimate', 'EstimatedAllocatedDone', 'EstimatedDone',
          'FakeAssetState', 'Goals', 'ID', 'Ideas', 'IdentifiedIn', 'Inactivate', 'Inactive',
          'IncompleteEstimate', 'IsClosed', 'IsCompleted', 'IsDead', 'IsDeletable', 'IsDeleted',
          'IsInactive', 'IsReadOnly', 'IsUndeletable', 'Issues', 'Jeopardy', 'Key', 'LastVersion',
          'Links', 'MakeTemplate', 'MentionedInExpressions', 'Messages', 'Moment', 'MorphedInto',
          'MyLastChangeMoment', 'Name', 'Number', 'OpenEstimate', 'Order', 'OriginalEstimate', 'Owners',
          'Parent', 'ParentAndMe', 'ParentAndUp', 'ParentMeAndUp', 'Prior', 'Priority', 'QuickClose',
          'QuickSignup', 'Reactivate', 'Reference', 'RequestedBy', 'Requests', 'RetireComment',
          'RetireDate', 'RetireDateUTC', 'RetireReason', 'RetiredBy', 'Risk', 'Scope', 'SecurityScope',
          'ShallowCopy', 'Source', 'Split', 'SplitFrom', 'SplitFromAndMe', 'SplitFromAndUp',
          'SplitFromMeAndUp', 'SplitTo', 'SplitToAndDown', 'SplitToAndMe', 'SplitToMeAndDown', 'Status',
          'Subs', 'SubsAndDown', 'SubsAndMe', 'SubsMeAndDown', 'Super', 'SuperAndMe', 'SuperAndUp',
          'SuperMeAndUp', 'Team', 'Timebox', 'ToDo', 'Undelete', 'Value', 'Viewers', 'WasAnEpic',
          '__class__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattribute__', '__hash__',
          '__init__', '__metaclass__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__',
          '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__',
          '_v1_asset_type_name', '_v1_asset_type_xml', '_v1_commit', '_v1_execute_operation',
          '_v1_get_single_attr', '_v1_getattr', '_v1_refresh', '_v1_setattr', '_v1_v1meta',
          'create', 'from_query_select', 'idref', 'pending', 'query', 'select', 'where', 'with_data'
          ]


### Simple access to individual assets:

  Assets are created on demand and cached so that once instance always represents
  the same asset.

      s = v1.Story(1005)
      
      print s is v1.Story(1005)   # True
      


### Lazyily loaded values and relations:

  Asset instances are created with any data available, and query the server on-demand
  for attributes that aren't currently fetched.  A basic set of attributes is fetched
  upon the first unfound attribute.  The relationship network can be traversed at will
  and assets will be fetched as needed
  
      e = v1.Epic(324355)
      
      # No data fetched yet.
      print e  #=>  Epic(324355)
      
      # Access an attribute.
      print epic.Name  #=> "Implement Team Features"
      
      # Now some data has been fetched
      print epic       #=> Epic(324355).with_data({'AssetType': 'Epic', 'Description': "Make featuers easier for new team members",
                           'AssetState': '64', 'SecurityScope_Name': 'Projects', 'Number': 'E-01958', 'Super_Number': 'E-01902',
                           'Scope_Name': 'Projects', 'Super_Name': 'New Feature Development', 'Scope': [Scope(314406)],
                           'SecurityScope': [Scope(314406)], 'Super': [Epic(312659)], 'Order': '-24', 'Name': 'Team Features'})
      
      # Freely traverse the relationship graph
      print epic.Super.Scope.Name  #=> 'Products'
      

### Operations:

  Operations on assets can be initiated by calling the appropriate method on an asset instance:
  
      for story in epic.Subs:
        story.QuickSignup() 


### Simple query syntax:

      for s in v1.Story.where(Name='Add feature X to main product"):
          print s.Name, s.CreateDate, ', '.join([owner.Name for owner in s.Owners])
          
      # Select only some attributes to reduce traffic
      
      for s in v1.Story.select('Name', 'Owners').where(Estimate='10'):
          print s.Name, [o.Name for o in s.Owners]
          
          
### Advanced query, taking the standard V1 query syntax.

      for s in v1.Story.query("Estimate>5,TotalDone.@Count<10"):
          print s.Name


### Simple creation syntax:

  GOTCHA: All "required" attributes must be set, or the server will reject the data.

      new_story = v1.Story.create(Name='New Story', scope=v1.Scope(1002))
      # creation happens immediately. No need to commit.
      print new_story


### Simple update syntax.

  Nothing is written until V1Meta.commit() is called, and then all dirty assets are written out.

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
      
