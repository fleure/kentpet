##Kentpet

Kentpet is an atrociously written IRC bot pet keeping game, that provides zero value to the human race. It involves caring for and growing pets through a hideous chatroom based interface.

##Prerequisites

* Python 2.7.3
* Python irc library (https://pypi.python.org/pypi/irc)
* mongodb 3.0.5
* PyMongo 3.0.3

##Getting Started

Clone this repo to wherever you want with git.

```
git clone https://github.com/fleure/kentpet.git
```

Edit the settings.json file to match the settings for the bot you desire. The ident section is optional, if you do not have or require nickserv identification then simply remove the ident, nickserv and password fields.

An example edited from the default, with ident removed:

```
{
    "nick": "kentpet",
    "server": "b0rk.uk.quakenet.org",
    "channel": "#aeiou",
    "mongo": {
        "server": "vps-26484.com",
        "port": 27017
    }
}
```

Install and setup mongo. Ensure it is where settings.json is looking for it. Start the mongod service. Kentpet will write to the "kentpet" database in this server. Namespace collision is unlikely.

Finally, in the project's root directory, run the following:

```
./kentpet.py
```

To generate a new egg, say the following in the channel the kentpet bot is in, or via PM:

```
!newegg
```

You will receive a new egg, and it will hatch after an hour.

You can have multiple pets that can be referenced either by their number (First pet is 1, second pet is 2, if first pet dies then the second pet becomes 1, etc) or their name (!namepet <number> <name> to name it).

Once it has hatched, you will need to feed it to keep it alive.
```
!feed 1 meal
```

Again, this can be done in the channel or via PM. You can also feed it a smaller "snack", or a much heartier "meal". Like their meatspace counterparts, pets have a tendency to die if not regularly fed.

You can see your pet's credentials and status with:

```
!petinfo 1
```

and

```
!petstats 1
```

As your pet defies the grave, it will slowly grow and level up.

If you're tired of using a number/name, you can set the default pet number with

```
!defaultpet number
```

##Admin

Kentpet comes with an admin module that lets you tweak the game or pets, or be a power hungry abuser of power. You will have to open a mongo shell and add users to the "admins" collection manually, like so:

```
db.admins.insert({"name": "password"})
```

Where "name" is the case-sensitive name of the admin's ircname, and the password is the one they will use to log in with. To log in to the admin module, PM the bot the following:

```
!adminlogin <password>
```

Once logged in, you have access to various admin commands. The core usage is editing pets:

```
!admin editattr user pet attribute value
```

With example values:

```
!admin editattr gonzo 2 hp 100
```

See the admin module for more available commands.

##Writing a module

Kentpet has the aim of being as modular as possible, with the "pets" module being the core functionality. Modules are put, unconventionaly, in the modules directory. The module.py contains the ModuleBase class which all modules should inherit from, as it contains the very core functionality needed.

All modules have a tick() method. This doesn't have to do anything, but if you want something to be processed on every tick of the game, insert your functionality there.

Beyond that, feel free to implement whatever functionality you want in the module. The two key things to work with:

* User commands are exported in the "commands" list defined in the ModuleBase. These act as one-to-one mappings of the !<command> and method name (For example !feed maps to feed() in the pets module). They also take three arguments: arg which is a list of the space seperate words of the user's command, nick of the user who called the command, and private, which is a True/False flag for whether the command came from PM or not. 
* Pet data can be accessed in the "pets" collection of the database, but it is often easier to call core.get_module("pets") and call find_pet(pet_id, [owner]) from that module. Pet id can be a pet name or the number, and owner is an optional String to pass. Without the owner, however, only the first pet matching a String name pet_id will be found. All pets are generated with a unique collection id as per mongo's requirements. Owner data is kept in the "owners" collection and their name acts as their id.

All called methods in the module can return a string message to be directed back at the user who called the command. Simply return the String, no need to specify their name. Returning False means nothing will be sent.

##Why Mongo?

Mongo gets a lot of flak, but for a small project like this it works nicely. Schema-free and lazy evaluation is all this project really requires, and it is very simple to setup.

##Why "Kentpet"?

Kentpet was created as a simple time waster for a group of friends who attended the University of Kent in Canterbury, UK, and have a borderline unhealthy obsession with creating IRC bot projects for their little home on Freenode.
