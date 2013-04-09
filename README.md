# v1pysdk #
Copyright (c) 2012 VersionOne, Inc.
All rights reserved.

A Python API client for the VersionOne agile project management system.

This software is preliminary and pre-beta quality. We would like your 
input on design matters, notes about your use cases, and more pull requests! 

This product includes software developed at VersionOne 
(http://versionone.com/). This product is open source and is licensed 
under a modified BSD license, which reflects our intent that software 
built with a dependency on v1pysdk can be commercial or open source, 
as the authors see fit.

## Overview


### Authenticating via Oauth2

  We recommend using Oauth 2.0 to authenticate with the VersionOne instance.  This prevents your client
  from storing user credentials, and allows the user to manage permissions for multiple registered client applications.

  This library uses Google's oauth2 library and its secrets and credentials file formats.
  You must use another tool that writes these files before this library can be used to gain access to a VersionOne instance.
  Once the files exist and are valid, authentication is automatic based on the stored secrets and credentials.

  Our brief Oauth2 example program can be used to write that file. See https://github.com/versionone/versionone-oauth2-examples/tree/master/python27

### Dynamic reflection of all V1 asset types:

  Just instantiate a V1Meta.  All asset types defined on the server are available
  as attributes on the instance.  The metadata is only loaded once, so you must
  create a new instance of V1Meta to pick up metadata changes.  Each asset class
  comes with properties for all asset attributes and operations.
  
      from v1pysdk import V1Meta
      
      v1 = V1Meta()  # Assumes localhost/VersionOne.Web
      
      v1 = V1Meta(
             address = 'v1server.mycompany.com',
             instance = 'VersionOne'
             )

      Story = v1.Story
      
      my_story = Story(1005) # internal numeric ID
      
      print my_story.CreateDate, my_story.Name
      


### Simple access to individual assets:

  Asset instances are created on demand and cached so that instances with the same OID are always
  the same object.  You can retrieve an instance by passing an asset ID to an asset class:

      s = v1.Story(1005)
      
      
  Or by providing an OID Token:
  
      s = v1.asset_from_oid('Story:1005')
      
      print s is v1.Story(1005)   # True


### Lazyily loaded values and relations:

  NOTE: Making requests synchronously for attribute access on each object is costly.  We recommend
  using the query syntax to select, filter, aggregate, and retrieve values from related assets 
  in a single HTTP transaction.

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
  
      # WARNING: Lots of HTTP requests this way.
      members = list(v1.Member)                               # HTTP request to get the list of members.
      print "Members: " + ', '.join(m.Name for m in members)  # HTTP request per member to fetch the Name
      
      # A much better way, requiring a single HTTP access via the query mechanism.
      members = v1.Member.select('Name')
      print "Members: " + ', '.join(m.Name for m in members)  # HTTP request to return list of members with Name attribute.

      # There is also a shortcut for pulling an attribute off all the results
      members = v1.Member.select('Name')
      print "Members: " + ', '.join(members.Name)
 
  
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

  The "query" operator will take arbitrary V1 "where" terms for filtering.

      for s in (v1.Story
                  .filter("Estimate>'5',TotalDone.@Count<'10'")
                  .select('Name')):
          print s.Name


#### Advanced selection, taking the standard V1 selection syntax.

  The "select" operator will allow arbitrary V1 "select" terms, and will add
  them to the "data" mapping of the result with a key identical to the term used.
  
    select_term = "Workitems:PrimaryWorkitem[Status='Done'].Estimate.@Sum"
    total_done = ( v1.Timebox
                     .where(Name="Iteration 25")
                     .select(select_term)
                 )
    for result in total_done:
      print "Total 'Done' story points: ", result.data[select_term]
    

#### Advanced Filtering and Selection

  get a list of all the stories dedicated people are working on

  writer = csv.writer(outfile)
  results = (v1.Story
               .select('Name', 'CreateDate', 'Estimate', 'Owners.Name')
               .filter("Owners.OwnedWorkitems.@Count='1'"))
  for result in results:
     writer.writerow((result['Name'], ', '.join(result['Owners.Name'])))
                      
      
### Simple creation syntax:

  GOTCHA: All "required" attributes must be set, or the server will reject the data.
  
      from v1pysdk import V1Meta
      v1 = V1Meta()
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


### Attachment Contents

  Attachment file bodies can be fetched or set with the special "file_data" attribute on Attachment instances. 

  See the v1pysdk/tests/test_attachment.py file for a full example.

### As Of / Historical Queries

  Queries can return data "as of" a specific point in the past.  The .asof() query term can
  take a list (or multiple positional parameters) of timestamps or strings in ISO date format.
  The query is run for each timestamp in the list.  A single iterable is returned that will
  iterate all of the collected results.  The results will all contain a data item "AsOf" with
  the "As of" date of that item.  Note that the "As of" date is not the date of the previous
  change to the item, but rather is exactly the same date passed into the query.  Also note
  that timestamps such as "2012-01-01" are taken to be at the midnight starting that day, which
  naturally excludes any activity happening during that day.  You may want to specify a timestamp
  with a specific hour, or of the following day.
  
  TODO: what timezone is used?
  
      with V1Meta() as v1:
        results = (v1.Story
                     .select("Owners")
                     .where(Name="Fix HTML5 Bug")
                     .asof("2012-10-10", "2012-10-11")
                  )
        for result in results:
            print result.data['AsOf'], [o.Name for o in result.Owners]
      
      
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
    
#### Installation

run `python setup.py install`, or just copy the v1pysdk folder into your PYTHONPATH.


## License ##

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are 
met:

* Redistributions of source code must retain the above copyright 
  notice, this list of conditions and the following disclaimer.
  
* Redistributions in binary form must reproduce the above copyright 
  notice, this list of conditions and the following disclaimer in the 
  documentation and/or other materials provided with the distribution.
  
* Neither the name of VersionOne, Inc. nor the names of its 
  contributors may be used to endorse or promote products derived from 
  this software without specific prior written permission of 
  VersionOne, Inc.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED 
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, 
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON 
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR 
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF 
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF 
SUCH DAMAGE.
