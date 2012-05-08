



from v1pysdk.main import *

def on_new_story(story):
   c = jira_server.connect()
   c.create_issue({
       name: story.name,
       priority: story.status
       })
   
   story.reference = c.jira_id
   
Assets.Story.register_new(on_new_story)


def on_epic_close(epic):
  if epic.priority > 3: # CEO wants to see these
    result = query("epic.subsanddown.doneEffort.@sum")
    
    

    

from v1pysdk.main import *

joe = Assets.Member.find(name="Joe")

for story in Assets.Story.query_all():
  story.owner = joe
  
  
  
    
