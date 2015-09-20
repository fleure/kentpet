#!/usr/bin/python
import irc.bot as ircbot
import irc.schedule as schedule
import json, datetime, threading, time
import traceback
import sys
from imp import reload
from pymongo import MongoClient

class KentPetBot(ircbot.SingleServerIRCBot):

    server = None
    channel = None
    client = None
    ident = None
    mongo = None
    pets = None
 

    modules = {}
    commands = {}


    def __init__(self, channel, nickname, server, mongo, ident, port=6666):
        ircbot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.server = server
        self.ident = ident
        self.channel = channel
        self.mongo = mongo

        pets = self.load_module("pets")
        with open("default_modules") as f:
            modules = [line.rstrip() for line in f]
        for module in modules:
            self.load_module(module)
            

    def load_module(self, module):
        print("Loading module {0}".format(module))
        load = __import__("modules.{0}".format(module), fromlist=[module.capitalize()])
        if module in self.modules:
            load = reload(load)
        self.modules[module] = getattr(load, module.capitalize())(self, self.mongo['kentpet'])

        for cmd in self.modules[module].commands:
            self.commands[cmd] = module
        return self.modules[module]

    # Only unloads module from kentpet's internal reference. Python doesn't seem to be
    # able to unload modules.
    def unload_module(self, module):
        if module in self.modules:
            self.commands = {k:self.commands[k] for k in self.commands if self.commands[k] != module}
            del self.modules[module]


    def get_module(self, module):
        try:
            return self.modules[module]
        except KeyError:
            return None

    def tick(self):
        while(True):
            for module_name in self.modules:
                module = self.modules[module_name]
                messages = module.tick()
                if messages:
                    for msg in messages:
                        self.send_message(msg, messages[msg], 0)
            time.sleep(60)


    def on_welcome(self, c, e):
        if self.ident:
            print("Identifying with nickserv...")
            c.privmsg(self.ident['nickserv'], "identify {0}".format(self.ident['password']))
            print("Waiting 10 seconds to confim identification...")
            time.sleep(10)
        print("Joining channel...")
        c.join(self.channel)
        self.client = c
        thr = threading.Thread(target=self.tick)
        thr.daemon = True
        thr.start()

    def on_nick(self, c, e):
        # Lazy
        self.modules['admin'].remove_admin(e.source.nick)

    def on_pubmsg(self, c, e):
        if e.arguments[0][0] == "!":
            arg = e.arguments[0][1:].split()
            self.do_cmd(c, e, arg)

    def on_privmsg(self, c, e):
        if e.arguments[0][0] == "!":
            arg = e.arguments[0][1:].split()
            self.do_cmd(c, e, arg, private=1)


    def do_cmd(self, c, e, arg, private=0):
        if not arg:
            return
        nick = e.source.nick
        if arg[0] not in self.commands:
            return

        if not self.get_owner(nick):
            self.mongo['kentpet'].owners.insert_one({"_id": nick, "pets": [], "server": self.server})
        module = self.commands[arg[0]]
        try:
            message = getattr(self.modules[module], arg[0])(arg[1:], nick, private)
            if message:
                self.send_message(nick, message, private)
        except Exception as err:
            print(traceback.format_exc())

    def send_message(self, nick, msg, private):
        if nick == 0:
            self.client.privmsg(self.channel, msg)
            return
        if private:
            self.client.privmsg(nick, "{0}: {1}".format(nick, msg))
        else:
            self.client.privmsg(self.channel, "{0}: {1}".format(nick, msg))

    def get_owner(self, owner):
        return self.mongo['kentpet'].owners.find_one({"_id": owner, "server": self.server})
            

def main():
    json_data = open('settings.json')
    settings = json.load(json_data)
    json_data.close()
    ident = None
    if settings['ident']:
        ident = settings['ident']
    
    db_server = settings['mongo']['server']
    db_port = settings['mongo']['port']
    print("Connection to MongoDB server...")
    client = MongoClient(db_server, db_port)
    try:
        client.server_info()
    except ServerSelectionTimeoutError:
        sys.exit("MongoDB connection timed out. Check settings.json and "
                 "a server is running at that address and port."
        )
    bot = KentPetBot(settings['channel'], settings['nick'], settings['server'], client, ident)
    print("Starting...")
    bot.start()


if __name__ == "__main__":
    main()
