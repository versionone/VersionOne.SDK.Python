import sys

from v1pysdk import V1Meta

try:
  server, instance_path, username, password = sys.argv[1:5]
except ValueError:
  print("Please supply command line arguments")



v1 = V1Meta(server, instance_path, username, password)


story = v1.Story.create(
    Name = "New Story",
    Scope = "Scope:0"
    #Scope = v1.Scope.where(Name="Product XYZ").first()
    )

attachment = v1.Attachment.create(
    Name= "New attachment",
    Content = "",
    ContentType = "application/octet-stream",
    Filename = "test.dat",
    Asset = story)

v1.set_attachment_blob(attachment, '\x00\xFF'*20000)

print len(v1.get_attachment_blob(attachment))
