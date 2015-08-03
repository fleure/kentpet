class ModuleBase(object):

    messages = {}
    commands = []
    core = None
    db = None

    def __init__(self, core, db):
        self.core = core
        self.db = db
        return

    def tick(self):
        return
