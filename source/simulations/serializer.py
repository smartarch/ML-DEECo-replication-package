from source.components.component import Component

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

