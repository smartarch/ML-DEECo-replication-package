import csv


class Report:
    def write(self, component, timeStep):
        self.context += str(timeStep) + ","
        for key in component.__dict__:
            self.context += f"{component.__dict__[key]},"
        self.context = self.context[:-1] + "\n"

    def __init__(self, componentClass):
        self.context = componentClass.header + "\n"
        componentClass.reporter = self.write

    def export(self, filename):
        file = open(filename, 'w')
        file.write(self.context)
        file.close()

    def __str__(self):
        return self.context


class Log:
    def __init__(self, header):
        self.records = [header]
        self.columns = len(header)

    def register(self, newData):
        self.records.append(newData)

    def add(self, newData):
        currentRecord = self.records[-1]
        for i in range(len(currentRecord)):
            currentRecord[i] = currentRecord[i] + newData[i]
        self.records[-1] = currentRecord

    def average(self, begin=0, end=1):
        assert begin < end, "begining index must be less than ending index"
        # ignoring first column
        datalist = self.records[1:][begin:end]
        count = end - begin
        averageList = [sum([sublist[i] for sublist in datalist]) / count for i in range(self.columns)]
        return averageList

    def totalRecord(self):
        datalist = self.records[2:]
        count = len(datalist)
        if count == 0:
            return []
        averageList = [sum([sublist[i] for sublist in datalist]) / count for i in range(self.columns)]
        return averageList

    def export(self, filename):
        with open(filename, 'w', newline='') as myFile:
            wr = csv.writer(myFile)
            for rec in self.records:
                wr.writerow(rec)

    def exportNumeric(self, filename):
        with open(filename, 'w', newline='') as myFile:
            wr = csv.writer(myFile)
            wr.writerow(self.records[0])
            for rec in self.records[1:]:
                wr.writerow([f"{k:.2f}" for k in rec])
