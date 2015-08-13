from .module import ModuleBase
from os import listdir
from os.path import isfile, join
import random
import lib.faces as faces

class Genetics(ModuleBase):

    commands = []

    def __init__(self, core, db):
        super(Genetics, self).__init__(core, db)
        return

    def get_attribute_files(self):
        return [ f for f in listdir("attributes/") if isfile(join("attributes/",f))]

    def generate_attribute_alleles(self):
        attribute_files = self.get_attribute_files()
        for attributes in attribute_files:
            alleles = []
            with open("attributes/{0}".format(attributes)) as f:
                for index, l in enumerate(f):
                    alleles.append(random.getrandbits(1))
            self.db.genetics.alleles.update({"_id": attributes}, {"$set": {"alleles": alleles} }, upsert=True)
        return "Alleles generated."

    def generate_pet_genes(self):
        attribute_files = self.get_attribute_files()
        face_attributes = faces.get_face_attributes()
        attributes = {}
        attributes["face"] = {}
        for attribute in attribute_files:
            data = open("attributes/{0}".format(attribute)).readlines()
            data = [line.rstrip() for line in data]
            if attribute in face_attributes:
                attributes["face"][attribute] = data
            else:
                attributes[attribute] = data

        for pet in self.db.pets.find():
            genes = self.construct_gene_tree(attributes, pet)
            self.db.pets.update(pet, { "$set": { "genes": genes } })
        return "Pet genes generated."

    def construct_gene_tree(self, attributes, pet):
        leaf = {}
        for attribute, value in attributes.items():
            if type(value) is dict:
                leaf[attribute] = self.construct_gene_tree(value, pet[attribute])
            else:
                leaf[attribute] = [pet[attribute], random.choice(value)]
        return leaf

    def breed(self, arg, nick, private):
       return 
