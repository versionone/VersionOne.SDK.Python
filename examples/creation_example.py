

from v1pysdk import V1Meta

v1 = V1Meta()

new_story = v1.Story.create(
                      Name = "New Story", 
                      Scope = v1.Scope(1002),
                      )


new_story.Owners = list(v1.Member.where(Name="Admin"))

v1.commit()


