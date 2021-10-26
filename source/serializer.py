from yaml import load, dump
from yaml import Loader
import copy

class ComponentSerializer:
    """
        Creates a Serializer Object out of any live object 
        TO YAML converts an object to a YAML file
        (static) FROM YAML returns an object out of a YAML File
    """
    data : object()
    def __init__ (
                    self,
                    component):
        self.data = copy.deepcopy(component)

    def to_yaml (
                self,
                filename,
                append:True):
        file = open(filename, "a" if append else "w")
        yaml.dump(self.data,file)
        file.close()

    def from_yaml (filename):
        with open(filename, 'r') as stream:
            data_loaded = load(stream,Loader=Loader)
        return data_loaded

class WorldSerializer:
    world : object()

    def __init__ (
                    self,
                    listOfComponents):
        world= listOfComponents