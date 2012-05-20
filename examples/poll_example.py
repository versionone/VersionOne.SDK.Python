
from v1meta import V1Meta

from v1poll import V1Poller

def build_fax_file(story):
    with open('fax.out', 'w') as f:
        f.write(story.Name + '\n')
        f.write(story.CreateDate + '\n'
        f.write(', '.join(o.Name for o in story.Owners) + '\n')
    
with V1Meta() as v1:
  with V1Poller(v1) as poller:    
    poller.run_on_new('Story', fax_to_russia)

