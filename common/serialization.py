import csv

class Report:
    def write (self,component,timeStep):
        self.context += str(timeStep) + ","
        for key in component.__dict__:
            self.context += f"{component.__dict__[key]},"
        self.context = self.context[:-1]+"\n" 

    def __init__ (self, componentClass):
        self.context = componentClass.header + "\n"
        componentClass.reporter = self.write
  
    def export (self, filename):
        file = open (filename,'w')
        file.write(self.context)
        file.close()

    def __str__ (self):
        return self.context

class Log:
    def __init__(self,header):
        self.records = [ header ]

    def register (self,newData):
        self.records.append(newData)
    
    def add (self,newData):
        currentRecord = self.records[-1]
        for i in range(len(currentRecord)):
            currentRecord[i] = currentRecord[i] + newData[i]
        self.records[-1] = currentRecord

    def export(self,filename):
        with open(filename, 'w', newline='') as myFile:
            wr = csv.writer(myFile)
            for rec in self.records:
                wr.writerow(rec)
