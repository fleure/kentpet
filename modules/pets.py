import random
from decimal import Decimal, getcontext
from bson.objectid import ObjectId
import lib.faces as faces
from .module import ModuleBase

class Pets(ModuleBase):


    # Commands the module has.
    commands = ["pethelp", "pets", "kill", "petinfo", "petstats", "newegg", "feed", "namepet", "defaultpet", "vacation"]

    MAX_FOOD = 100
    TICK_EVERY = 60
    STAT_POOL = 15
    STATS = ['strength', 'intelligence', 'constitution', 'dexterity',
             'fabulous']
    max_pets = 3

    def __init__(self, core, db):
        super(Pets, self).__init__(core, db)
        return

    def tick(self):
        self.messages = {}
        self.process_pets()

        return self.messages

    def process_pets(self):
        for pet in self.db.pets.find():
            owner = self.db.owners.find_one({"pets": ObjectId(pet["_id"])})
            if owner and self.check_owner_vacation(owner["_id"]):
                continue
            update_fields = {}
            update_fields['growth'] = pet['growth'] + 1
            if(pet['growth'] >= pet['evolve']):
                self.evolve_pet(pet)
            elif(pet['level'] > 0):
                before_food = pet['food']
                new_food = self.decay_food(before_food, pet['metabolism'])
                update_fields['food'] = new_food
                if (new_food < self.MAX_FOOD*0.10) and (before_food >= self.MAX_FOOD*0.10):
                    name = pet['name']
                    if not name:
                        name = "One of your pets"
                    self.messages[owner["_id"]] = "{0} is starving.".format(name)
                    pass
                if(new_food <= self.MAX_FOOD*0.05):
                    getcontext().prec = 4
                    update_fields['hp'] = float(Decimal(pet['hp']) - Decimal(0.05))
                    if(update_fields['hp'] <= 0):
                        self.remove_pet_from_owner(pet, owner)
                        self.kill_pet(pet, "Starved to death")
                        self.messages[owner["_id"]] = "Your pet has died!"
                        return
            self.db.pets.update(pet, { "$set": update_fields } )

    def check_owner_vacation(self, nick):
        owner = self.db.owners.find_one({"_id": nick})
        try:
            return owner["vacation"]
        except KeyError:
            self.db.owners.update(owner, { "$set": { "vacation": False } })
            return False

    def vacation(self, arg, nick, private):
        if not arg or arg[0] not in ["on", "off"]:
            return "Usage: !vacation <on/off>"
        vacation = False
        if arg[0] == "on":
            vacation = True
        self.db.owners.update({"_id": nick}, { "$set": { "vacation": vacation } })
        return "Vacation mode set."

    def kill(self, arg, nick, private):
        if not arg:
            return "Usage: !kill <number/name>"
        pet = self.get_pet(arg, nick)
        if not pet:
            return "No pet found."
        name = pet['name']
        self.remove_pet_from_owner(pet, nick)
        self.kill_pet(pet, "Killed by {0}.".format(nick))
        if not name:
            name = "your pet"
        return "You murdered {0}. You monster.".format(name)

    def kill_pet(self, pet, cause):
        if cause:
            pet['death'] = cause
        owner = self.db.owners.find_one({"pets": ObjectId(pet["_id"])})
        if owner:
            pet['owner'] = owner
        self.db.graveyard.insert(pet)
        self.db.pets.remove(pet["_id"])

    def remove_pet_from_owner(self, pet, owner):
        owner = self.db.owners.find_one(owner)
        if "default" in owner and owner["default"] == pet["_id"]:
            self.db.owners.update(owner, { "$set": { "default": None } })
        self.db.owners.update(owner, { "$pull": { "pets": ObjectId(pet["_id"]) } })

    def decay_food(self, food, metabolism):
        food -= (random.random()*food)/(metabolism/self.TICK_EVERY)
        return food


    def get_pet(self, pet_id, owner=False):
        if type(pet_id) is list:
            pet_id = " ".join(pet_id)
        if owner:
            owner_record = self.core.get_owner(owner)
            if owner_record:
                is_num = True
                try:
                    pet_id = int(pet_id)
                except ValueError:
                    is_num = False
                if is_num:
                    if pet_id > 0 and len(owner_record['pets']) >= pet_id:
                        return self.db.pets.find_one({"_id": owner_record['pets'][pet_id - 1]})
                else:
                    for pet_record in owner_record['pets']:
                        pet = self.db.pets.find_one(pet_record)
                        if pet and pet['name'] == pet_id:
                            return pet
        else:
            return self.db.pets.find_one({"name": pet_id})
        return False
            
    def num_pets(self, owner):
        return len(self.core.get_owner(owner)['pets'])

    def pets(self, arg, nick, private):
        owner = self.db.owners.find_one({'_id': nick})
        pets = owner['pets']
        if len(pets) == 0:
            return 'No pets found.'

        message = ''
        for i, pet in enumerate(pets):
            message += '{0}: '.format(i+1)
            pet = self.db.pets.find_one(pet)
            if pet['level'] == 0:
                message += 'Egg '
            else:
                face = faces.get_face(pet)
                if face:
                    message += '{0} '.format(face)
                name = pet['name']
                if name:
                    message += '{0} '.format(name)

        return message[:-1]

    def defaultpet(self, arg, nick, private):
        if not arg:
            return "Usage: !defaultpet <number/name>"

        pet = self.get_pet(arg, nick)
        if not pet:
            return "No pet found."

        self.db.owners.update({"_id": nick}, { "$set": { "default": pet["_id"] } })
        return "Default pet set."

    def get_default_pet(self, owner):
        try:
            owner = self.db.owners.find_one({"_id": owner})
            return self.db.pets.find_one({"_id": owner["default"]})
        except KeyError:
            return None

    def process_pet_query(self, arg, nick):
        if arg and "--owner" in arg:
            try:
                nick = arg[arg.index("--owner") + 1]
                arg.remove("--owner")
                arg.remove(nick)
            except IndexError:
                pass

        if not arg:
            return self.get_default_pet(nick)
        else:
            return self.get_pet(arg, nick)

    def petinfo(self, arg, nick, private):

        pet = self.process_pet_query(arg, nick)
        if not pet:
            return "No pet found."
        message = "Pet info"

        face = faces.get_face(pet)
        if face:
            message += " // {0}".format(face)

        name = pet['name']
        if name != None:
            message += " // {0}".format(name)
        level = pet['level']
        if level == 0:
            message += " // Egg"
        else:
            message += " // Level {0}".format(level)
        hp = pet['hp']
        if hp > 0:
            message += " // HP: {0}".format(hp)
        food = pet["food"]
        if food >= 0:
            message += " // Food: {0}".format(int(food))
        return message

    def petstats(self, arg, nick, private):
        pet = self.process_pet_query(arg, nick)
        if not pet:
            return "No pet found."

        message = "Pet stats"
        name = pet['name']
        if name != None:
            message += " // {0}".format(name)
        level = pet['level']
        if level == 0:
            message += " // Egg"
            return message
        else:
            message += " // Level {0}".format(level)
        stats = pet['stats']
        for stat in stats:
            message += " // {0}: {1}".format(stat, stats[stat])
        return message

    def evolve_pet(self, pet):
        # Egg hatch
        owner = self.db.owners.find_one({"pets": pet["_id"]})
        update_fields = {}
        if pet['level'] == 0:
            update_fields['level'] = 1
            update_fields['growth'] = 0
            update_fields['evolve'] = 600
            update_fields['happy'] = 50
            update_fields['food'] = self.MAX_FOOD*0.75
            update_fields['hp'] = 100
            
            update_fields['stats'] = self.roll_stats()

            update_fields['face'] = faces.generate_face()

            self.messages[owner["_id"]] = "Your pet has hatched!"
        # Normal evolve
        else:
            update_fields['level'] = pet['level'] + 1
            update_fields['hp'] = 100
            update_fields['growth'] = 0
            update_fields['evolve'] = pet['evolve'] * 1.5
            self.messages[owner["_id"]] = "Your pet has evolved to level {0}!".format(update_fields['level'])
        self.db.pets.update(pet, { "$set": update_fields })

    def newegg(self, arg, nick, private):
        if self.check_owner_vacation(nick):
            return "You cannot generate a new egg when on vacation."
        if self.num_pets(nick) >= self.max_pets:
            return "You have reached the maximum number of pets."

        print("Generating new egg for {0}".format(nick))
        with open("attributes/colour") as f:
            colours = [line.rstrip() for line in f]
        colour = random.choice(colours)

        with open("attributes/sound") as f:
            sounds = [line.rstrip() for line in f]
        sound = random.choice(sounds)

        pet = {}
        pet['colour'] = colour
        pet['sound'] = sound
        pet['name'] = None
        pet['growth'] = 0
        pet['evolve'] = 60
        pet['happy'] = 50
        pet['food'] = -1
        pet['metabolism'] = 40000
        pet['fitness'] = 5
        pet['level'] = 0
        pet['hp'] = 100

        record_id = self.db.pets.insert_one(pet).inserted_id
        self.db.owners.update({ "_id": nick }, { "$push": { "pets": record_id } })
        return "You have received an egg! Its colour is {0}. It will hatch in one hour.".format(pet['colour'])

    def roll_stats(self):
        pool = self.STAT_POOL
        stats = {}

        for stat in self.STATS:
            stats[stat] = 1
        for x in range(pool):
            i = random.randint(0, len(self.STATS) - 1)
            stats[self.STATS[i]] += 1
        return stats

    def feed(self, arg, nick, private):
        if self.check_owner_vacation(nick):
            return "You cannot feed your pet when on vacation."
        pet = self.process_pet_query(arg[:-1], nick)
        if not pet:
            return "No pet found."
        message = "Pet info"
        if arg[-1] not in ["snack", "meal", "feast"]:
            return "Usage: !feed <number/name> snack|meal|feast"
        if pet['level'] == 0:
            return "You cannot feed eggs."

        amount = 10.0
        if arg:
            amount_string = arg[-1].lower()
            if amount_string == "meal":
                amount = 25.0
            elif amount_string == "feast":
                amount = 50.0

        new_food = pet['food']
        amount /= 100
        if new_food < self.MAX_FOOD:
            new_food += self.MAX_FOOD*amount
            if new_food > self.MAX_FOOD:
                new_food = self.MAX_FOOD
            self.db.pets.update(pet, { "$set": { "food": new_food } })
            return "You fed your pet. Food amount is now {0}".format(int(new_food))
        else:
            return


    def namepet(self, arg, nick, private):
        if len(arg) < 2:
            return "Usage: !namepet <number> <name>"
        pet = self.get_pet(arg[0], nick)
        if not pet:
            return "No pet found."
        if pet['name']:
            return "You cannot rename your pet."
        valid_name = False
        name = " ".join(arg[1:])
        try:
            name = float(name)
        except ValueError:
            valid_name = True
        if not valid_name:
            return "Invalid name."
            
        self.db.pets.update(pet, { "$set": {"name": name} })
        return "Your pet is now called {0}.".format(name)

    def pethelp(self, arg, nick, private):
        commands = []
        for module, module_object in self.core.modules.iteritems():
            commands.extend(module_object.commands)

        commands = map(lambda x: "!" + x, commands)

        return "Commands: {0}".format(commands)
