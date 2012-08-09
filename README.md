# An API client for the VersionOne agile project management system.

NOTE: This software is preliminary and pre-beta quality.  We'd like your
input on design matters, notes about your use cases, and more pull requests!

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

  Asset instances are created on demand and cached so that instances with the same OID are always
  the same object.  You can retrieve an instance by passing an asset ID to an asset class:

      s = v1.Story(1005)
      
      
  Or by providing an OID Token:
  
      s = v1.asset_from_oid('Story:1005')
      
      print s is v1.Story(1005)   # True


### Lazyily loaded values and relations:

  Asset instances are created empty, or with query results if available. The server is
  accessed for attributes that aren't currently fetched.  A basic set of attributes is fetched
  upon the first unfound attribute.  
  
      epic = v1.Epic(324355)
      
      # No data fetched yet.
      print epic  #=>  Epic(324355)
      
      # Access an attribute.
      print epic.Name  #=> "Team Features"
      
      # Now some basic data has been fetched
      print epic       #=> Epic(324355).with_data({'AssetType': 'Epic',
                           'Description': "Make features easier for new team members", 'AssetState': '64',
                           'SecurityScope_Name': 'Projects', 'Number': 'E-01958', 'Super_Number': 'E-01902',
                           'Scope_Name': 'Projects', 'Super_Name': 'New Feature Development',
                           'Scope': [Scope(314406)], 'SecurityScope': [Scope(314406)],
                           'Super': [Epic(312659)], 'Order': '-24', 'Name': 'Team Features'})
                           
      # And further non-basic data is available, but will cause a request.
      print epic.CreateDate   #=>  '2012-05-14T23:45:14.124'
      
  The relationship network can be traversed at will, and assets will be fetched as needed.
      
      # Freely traverse the relationship graph
      print epic.Super.Scope.Name  #=> 'Products'
      
  Since the metadata is modeled as data, you can find the list of "Basic" attributes:
  
      basic_attr_names = list( v1.AttributeDefinition
                                 .where(IsBasic = "true")
                                 .select('Name')
                                 .Name
                             )
      

### Operations:

  Operations on assets can be initiated by calling the appropriate method on an asset instance:
  
      for story in epic.Subs:
        story.QuickSignup() 
        
  The asset instance data will be invalidated upon success, and thus re-fetched on the next
  attribute access.


### Iterating through all assets of a type

  The asset class is iterable to obtain all assets of that type. This is equivalent to the
  "query", "select" or "where" methods when given no arguments.
  
      print "Members: " + ', '.join(m.Name for m in v1.Member)
      
  The query objects also support accesing an attribute name, which will return an iterable of that
  attribute for all matched assets:
  
      # (If "Name" is not in the select list, we'll suffer an HTTP request per-member to fetch it.)
      
      matched = v1.Member.select('Name')
      names = matched.Name
      print "Members: " + ', '.join(names)
      
  
### Queries

#### Query Objects

  the `select()` and `where()` methods on asset instances return a query object
  upon which you can call more `.where()`'s and `.select()`'s.  Iterating through
  the query object will run the query.
      
  the `.first()` method on a query object will run the query and return the first result.
  
  Query results

#### Simple query syntax:

  Use `.where(Attr="value", ...)` to introduce "Equals" comparisons, and
  `.select("Attr", ...)` to append to the select list.
  
  Non-"Equal" comparisons are not supported (Use the advanced query syntax).

      for s in v1.Story.where(Name='Add feature X to main product"):
          print s.Name, s.CreateDate, ', '.join([owner.Name for owner in s.Owners])
          
      # Select only some attributes to reduce traffic
      
      for s in v1.Story.select('Name', 'Owners').where(Estimate='10'):
          print s.Name, [o.Name for o in s.Owners]
          
          
#### Advanced query, taking the standard V1 query syntax.

      for s in v1.Story.query("Estimate>5,TotalDone.@Count<10"):
          print s.Name



### Simple creation syntax:

  GOTCHA: All "required" attributes must be set, or the server will reject the data.
  
      from v1pysdk import V1Meta
      v1 = V1Meta(username='admin', password='admin')
      new_story = v1.Story.create(
        Name = 'New Story',
        Scope = v1.Scope.where(Name='2012 Projects').first()
        )
      # creation happens immediately. No need to commit.
      print new_story.CreateDate
      new_story.QuickSignup()
      print 'Owners: ' + ', '.join(o.Name for o in story.Owners)


### Simple update syntax.

  Nothing is written until V1Meta.commit() is called, and then all dirty assets are written out.

      story = v1.Story.where(Name='Super Cool Feature do over').first()
      story.Name = 'Super Cool Feature Redux'
      story.Owners = v1.Member.where(Name='Joe Koberg')      
      v1.commit()  # flushes all pending updates to the server

  The V1Meta object also serves as a context manager which will commit dirty object on exit.
      
      with V1Meta() as v1:
        story = v1.Story.where(Name='New Features').first()
        story.Owners = v1.Member.where(Name='Joe Koberg')
        
      print "Story committed implicitly."

### Polling (TODO)

  A simple callback api will be available to hook asset changes
  
      from v1meta import V1Meta
      from v1poll import V1Poller
      
      MAILBODY = """
      From: VersionOne Notification <notifier@versionone.mycorp.com>
      To: John Smith <cto@mycorp.com>
      
      Please take note of the high risk story '{0}' recently created in VersionOne.
      
      Link: {1}
      
      
      Thanks,
      
      Your VersionOne Software
      """.lstrip()
      
      def notify_CTO_of_high_risk_stories(story):
        if story.Risk > 10:
            import smtplib, time
            server = smtplib.SMTP('smtp.mycorp.com')
            server.sendmail(MAILBODY.format(story.Name, story.url))
            server.quit()
            story.CustomNotificationLog = (story.CustomNotificationLog +
                "\n Notified CTO on {0}".format(time.asctime()))
                
      with V1Meta() as v1:
        with V1Poller(v1) as poller:
          poller.run_on_new('Story', notify_CTO_of_high_risk_stories)
          
      print "Notification complete and log updated."
          
      
      
## Performance notes

  An HTTP request is made to the server the first time each asset class is referenced.
  
  Assets do not make a request until a data item is needed from them. Further attribute access
  is cached if a previous request returned that attribute. Otherwise a new request is made.
  
  The fastest way to collect and use a set of assets is to query, with the attributes
  you expect to use included in the select list.  The entire result set will be returned
  in a single HTTP transaction
  
  Writing to assets does not require reading them; setting attributes and calling the commit
  function does not invoke the "read" pipeline.  Writing assets requires one HTTP POST per dirty
  asset instance.
  
  When an asset is committed or an operation is called, the asset data is invalidated and will
  be read again on the next attribute access.

## TODO

  * Make things Moment-aware
  
  * Convert types between client and server (right now everything is a string)
  
  * Add debug logging
  
  * Beef up test coverage
  
    * Need to mock up server
    
  * Examples
  
    * provide an actual integration example
    
  * Asset creation templates and creation "in context of" other asset
  
  * Correctly handle multi-valued attributes including removal of values.
      
