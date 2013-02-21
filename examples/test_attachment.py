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
    Asset = story
    )



# right now, every access to the "file_data" property causes an HTTP request.
# in the future the SDK needs to cache this on reads and do dirty tracking / 
# commit managment for writes.

attachment.file_data = '\x00\xFF'*20000

print(len(attachment.file_data))


