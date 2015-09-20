from .module import ModuleBase
from bson.objectid import ObjectId
import lib.faces as faces
import random

class Admin(ModuleBase):

    admins = []
    commands = ["admin", "adminlogin"]

    def __init__(self, core, db):
        super(Admin, self).__init__(core, db)
        return

    def adminlogin(self, args, nick, private):
        if not private:
            return
        if not args:
            return
        admin = self.db.admins.find_one({"_id": nick})
        if admin:
            if admin["pass"] == args[0]:
                self.admins.append(nick)
                return "You are now logged in."
        return "Incorrect user/pass."

    def logged_in(self, name):
        return name in self.admins

    def remove_admin(self, name):
        if name in self.admins:
            self.admins.remove(name)

    def admin(self, args, nick, private):
        if not self.logged_in(nick):
            return
        if not args:
            return
        return getattr(self, args[0])(args[1:], nick, private)

    def stats(self, args, nick, private):
        if not args:
            return
        if args[0] == "roll":
            pet_module = self.core.get_module('pets')
            if args[1] == "*":
                for pet in self.db.pets.find():
                    stats = pet_module.roll_stats()
                    self.db.pets.update(pet, { '$set': { 'stats': stats } })
                return "All pet stats rerolled."
            elif len(args) < 3:
                return "Usage: !admin stats roll <owner> <pet>"
            pet = pet_module.get_pet(args[2], args[1])
            if not pet:
                return "No pet found."
            stats = pet_module.roll_stats()
            self.db.pets.update(pet, { '$set': { 'stats': stats } })
            return "Pet stats rerolled."

    def kill(self, args, nick, private):
        if len(args) < 2:
            return "Usage: !admin kill <owner> <pet id>"
        pet_module = self.core.modules['pets']
        pet = pet_module.get_pet(args[1], args[0])
        pet_module.remove_pet_from_owner(pet, args[0])
        pet_module.kill_pet(pet, "Admin killed by {0}.".format(nick))
        return "Pet killed."

    def newegg(self, args, nick, private):
        if not args:
            return "Usage: !admin newegg <owner>"
        pet_module = self.core.modules['pets']
        message = pet_module.newegg(args, args[0], private)
        self.core.send_message(args[0], message, private)
        return "Egg created."

    def editattr(self, args, nick, private):
        if len(args) < 4:
            return "Usage: !admin editattr <owner> <pet id> <attr> <value>"
        pet_module = self.core.modules['pets']
        pet = pet_module.get_pet(args[1], args[0])
        if not pet:
            return "No pet found."

        if args[2] not in pet:
            return "Attribute not found."
        try:
            args[3] = int(args[3])
        except ValueError:
            pass
        self.db.pets.update(pet, { "$set": { args[2]: args[3] } })

        return "Attribute edited."

    def genface(self, args, nick, private):
        if not args:
            return "Usage: !admin genface <owner> <pet id>"

        pet_module = self.core.modules['pets']
        pet = pet_module.get_pet(args[1], args[0])
        if not pet:
            return "No pet found."

        face = faces.generate_face()
        self.db.pets.update(pet, { "$set": { "face": face } })

        return "Face generated: {0}".format(faces.get_face({"face": face}))

    def moduleload(self, args, nick, private):
        if not args:
            return "Usage: !admin moduleload <module>"
        self.core.load_module(args[0])
        return "Module {0} loaded.".format(args[0])

    def genalleles(self, args, nick, private):
        try:
            gen_module = self.core.modules['genetics']
        except KeyError:
            return "Genetics module not loaded."
        return gen_module.generate_attribute_alleles()
        
    def gengenes(self, args, nick, private):
        genetics_module = self.core.get_module('genetics')
        if not genetics_module:
            return "Genetics module not loaded."
        for pet in self.db.pets.find():
            genes = genetics_module.generate_pet_genes(pet)
            self.db.pets.update(pet, { '$set': { 'genes': genes } })

    def skewmetabolism(self, args, nick, private):
        pets = self.db.pets.find()
        for pet in pets:
           new_metabolism = random.randint(30000, 50000)
           self.db.pets.update(pet, { "$set": { "metabolism": new_metabolism } })

        return "Metabolisms randomised. Elfy_Sheep likes butts."

    def resurrect(self, args, nick, private):
        if len(args) < 2:
            return "Usage: !admin resurrect <pet ObjectID> <owner>"
        pet = self.db.graveyard.find_one({"_id": ObjectId(args[0])})
        if not pet:
            return "No pet found."
        owner = self.db.owners.find_one({"_id": args[1]})
        if not owner:
            return "No owner found."

        pet["hp"] = 100
        pet["food"] = 75

        self.db.owners.update(owner, { "$push": { "pets": pet["_id"] } })
        self.db.graveyard.remove(pet["_id"])
        self.db.pets.insert(pet)
        return "Green smoke engulfs the channel. With a flash, {0}'s pet is returned to them...".format(owner["_id"])
