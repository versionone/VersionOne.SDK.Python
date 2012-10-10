import sys, datetime, csv, os

from v1pysdk import V1Meta


statuses = [
    'Not Started',
    'Ready for Dev',
    'Developing',
    'Ready for Test',
    'Testing',
    'Tested',
]

select_template = "Workitems:PrimaryWorkitem[Status.Name='{0}'].Estimate.@Sum"

def parsedate(d):
  return datetime.datetime.strptime(d, "%Y-%m-%d")

def as_of_times(start, end, hoursper=2):
  current = start
  while current <= end:
    yield current
    current += datetime.timedelta(hours=hoursper)

if __name__=="__main__":
    print sys.argv[1:5]
    username, password, sprintName, outputFolder = sys.argv[1:5]

    v1 = V1Meta('www7.v1host.com', 'V1Production', username, password)

    timebox = (v1.Timebox
                 .where(Name=sprintName)
                 .select("BeginDate", "EndDate")
                 .first()
              )
    
    startdate = parsedate(timebox.BeginDate)
    enddate = parsedate(timebox.EndDate)
    individual_times = as_of_times(startdate, enddate)
    
    select_list = [ select_template.format(status) for status in statuses ]
    
    results = (
        v1.Timebox
          .asof(individual_times)
          .where(Name=sprintName)
          .select(*select_list)
        )
          
    outfilename = os.path.join(outputFolder,  sprintName + ".dat")
    
    with open(outfilename, "w") as outfile:
        writer = csv.writer(outfile, delimiter="|")
        writer.writerow(['# Date'] + statuses)
        for result in results:
          row = [result.data[select_term] for select_term in select_list]
          writer.writerow(row)
    

