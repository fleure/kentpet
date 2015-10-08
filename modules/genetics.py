from .module import ModuleBase
from os import listdir
from os.path import isfile, join
from math import ceil
import random
import lib.faces as faces
import threading

class Genetics(ModuleBase):

    commands = ["breed", "acceptbreed", "declinebreed"]
    requests = {}

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

    def gather_attributes(self):
        attribute_files = self.get_attribute_files()
        attributes = {}
        for attribute in attribute_files:
            data = open("attributes/{0}".format(attribute)).readlines()
            data = [line.rstrip() for line in data]
            attributes[attribute] = data
        return attributes

    def get_attribute_index(self, attribute, element):
        data = open("attributes/{0}".format(attribute)).readlines()
        data = [line.rstrip() for line in data]
        return data.index(element)

    def get_attribute_allele(self, attribute, element):
        index = self.get_attribute_index(attribute, element)
        return self.db.genetics.alleles.find_one({'_id': attribute})['alleles'][index]

    def generate_pet_genes(self, pet):
        return self.construct_gene_tree(self.gather_attributes(), pet)

    def construct_gene_tree(self, attributes, pet):
        leaf = {}
        for attribute, value in attributes.items():
            if type(value) is dict:
                leaf[attribute] = self.construct_gene_tree(value, pet[attribute])
            else:
                leaf[attribute] = random.choice(value)
        return leaf

    def breed(self, arg, nick, private):
        if len(arg) < 2:
            return "Usage: !breed <pet 1> [--owner owner] <pet 2>"
        if len(self.db.owners.find_one(nick)["pets"]) >= self.core.get_module("pets").MAX_PETS:
            return "You already have the maximum number of pets."
        other_owner = None
        if "--owner" in arg:
            try:
                other_owner = arg[arg.index("--owner") + 1]
                arg.remove("--owner")
                arg.remove(other_owner)
            except IndexError:
                pass
        pet_module = self.core.get_module("pets")
        petA = pet_module.process_pet_query(arg[0], nick)
        petB = pet_module.process_pet_query(arg[1:], nick)
        if not petA:
            return "First pet not found."
        if not petB:
            return "Second pet not found."
        if petA["level"] == 0:
            return "First pet is an egg."
        if petB["level"] == 0:
            return "Second pet is an egg."

        if other_owner:
            if nick in self.requests:
                if arg[0] in self.requests[nick]:
                    return "You already have a breeding request for that owner."

            self.core.send_message(other_owner, 
                                "{0} has requested to breed their pet ({1}) with your pet ({2}).".format(
                                    nick,
                                    arg[0],
                                    arg[1]),
                                    True
            )
            self.core.send_message(other_owner,
                                 "PM me with \"!acceptbreed <owner>\" or "
                                 "\"!declinebreed <owner>\" to accept or "
                                 "decline.",
                                 True
            )

            if nick not in self.requests:
                self.requests[nick] = {}
            self.requests[nick][other_owner] = [petA, petB]

            return "Request sent, awaiting response."
        else:
            self.breed_pets(petA, petB, nick)

    def breed_pets(self, petA, petB, owner):
        # Choose half of the stats to inherit
        pet_module = self.core.get_module('pets')
        stats_available = pet_module.STATS
        stats = random.sample(stats_available, int(len(stats_available)/2))
        new_pet = pet_module.get_base_pet_stats()
        new_pet['stats'] = {}
        new_pet['genes'] = {}
        new_pet['parents'] = [petA['_id'], petB['_id']]
        new_stats = [x for x in stats_available if x not in stats]
        parents = [petA, petB]
        stats_used = 0
        # Randomly pick parent to inherit from for each stat to inherit
        for stat in stats:
            parent = random.choice(parents)
            new_pet['stats'][stat] = parent['stats'][stat]
            stats_used += parent['stats'][stat]
        # Randoly distribute the remaining points
        for stat in new_stats:
            new_pet['stats'][stat] = 1
        for x in range(pet_module.STAT_POOL - stats_used):
            i = random.randint(0, len(new_stats) - 1)
            new_pet['stats'][new_stats[i]] += 1

        # Inherit physical features from parents
        attributes = self.get_attribute_files()
        for attribute in attributes:
            choices = []
            visible = random.getrandbits(1)
            for parent in parents:
                if visible:
                    choices.append(parent[attribute])
                else:
                    choices.append(parent['genes'][attribute])
            choice_alleles = [self.get_attribute_allele(attribute, element) for element in choices]
            total = sum(choice_alleles)
            if total == 0:
                carry = random.choice(choices)
                visible_choices = []
                with open("attributes/{0}".format(attribute)) as f:
                    for i, element in enumerate(f):
                        if self.db.genetics.alleles.find_one({'_id': attribute})['alleles'][i] == 0:
                            visible_choices.append(element.rstrip())
                visible = random.choice(visible_choices)
            elif total == 1:
                visible = choices.pop(choice_alleles.index(1))
                carry = choices[0]
            else:
                random.shuffle(choices)
                visible = choices[0]
                carry = choices[1]
            
            new_pet[attribute] = visible
            new_pet['genes'][attribute] = carry
        
        record_id = self.db.pets.insert_one(new_pet).inserted_id
        self.db.owners.update({ "_id": owner }, { "$push": { "pets": record_id } })
        self.core.send_message(owner, "You have received a new egg from breeding. It will hatch in one hour.", False)

    def acceptbreed(self, arg, nick, private):
        return self.resolve_breed_request(arg, nick, private, True)

    def declinebreed(self, arg, nick, private):
        return self.resolve_breed_request(arg, nick, private, False)

    def resolve_breed_request(self, arg, nick, private, accept):
        if not private:
            return
        if not arg:
            return "Usage: ![acceptbreed][declinebreed] <requester>"
        if arg[0] not in self.requests or nick not in self.requests[arg[0]]:
            return "That user has not made a request with you."

        if accept:
            pets = self.requests[arg[0]][nick]
            thr = threading.Thread(target=self.breed_pets, args=pets + [arg[0]])
            thr.deamon = True
            thr.start()
            return "Request accepted."
        else:
            return "Request declined."
