from v1pysdk import V1Meta

v1 = V1Meta(
         address = 'www14.v1host.com',
         instance = 'v1sdktesting',
         username = 'admin',
         password = 'admin'
         )

term="Actuals.Value.@Sum"
for task in v1.Task.select("Name",term):
    if('Actuals.Value.@Sum' in task.data):
        print task['Name']
        print task['Actuals.Value.@Sum']