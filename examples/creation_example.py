

from v1pysdk import V1Meta

v1 = V1Meta()

new_story = v1.Story.create(Name="New Story", Scope=v1.Scope(1002))

new_story.Owners = [v1.Member(20)]

v1.commit()


