import multiprocessing
from threading import Thread

class Process(Thread):
    """
    A process is a thread with a queue of incoming messages, and an
    "environment" that keeps track of all processes and queues.
    """
    def __init__(self, env, id):
        super(Process, self).__init__()
        self.inbox = multiprocessing.Manager().Queue()
        self.env = env
        self.id = id

    def run(self):
        try:
            self.body()
            self.env.removeProc(self.id)
        except EOFError:
            print("Exiting..")

    def getNextMessage(self):
        return self.inbox.get()

    def sendMessage(self, dst, msg):
        self.env.sendMessage(dst, msg)

    def deliver(self, msg):
        self.inbox.put(msg)
