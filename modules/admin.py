from .module import ModuleBase
import lib.faces as faces

class Admin(ModuleBase):

    admins = []
    commands = ["admin", "adminlogin", "genalleles"]

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
            if len(args) < 3:
                return "Usage: !admin stats roll <owner> <pet>" 
            owner = args[1]
            pets = loadDB("pets")
            if owner not in pets:
                return "No pet found."
            self.pet_controller.distribute_stats(pets[owner])
            saveDB("pets", pets)
            return "Pet stats rerolled."

    def kill(self, args, nick, private):
        pets = loadDB("pets")
        del pets[args[0]]
        saveDB("pets", pets)
        return "Pet killed."

    def newegg(self, args, nick, private):
        if not args:
            return
        nick = args[0]
        if self.pet_controller.has_pet(nick):
            return
        self.pet_controller.newegg(args, nick, private)
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
        if not self.logged_in(nick):
            return
        if not args:
            return "Usage: !admin moduleload <module name>"

        self.pet_controller.bot.load_module(args[0])
        return "Module {0} loaded.".format(args[0])

    def genalleles(self, args, nick, private):
        try:
            gen_module = self.core.modules['genetics']
        except KeyError:
            return "Genetics module not loaded."
        return gen_module.generate_attribute_alleles()
        
    def gengenes(self, args, nick, private):
        try:
            gen_module = self.core.modules['genetics']
        except KeyError:
            return "Genetics module not loaded."
        return gen_module.generate_pet_genes()
