import sqlite3
from utils import *
import threading
from Db import Db
from time import sleep

class QueueProcessThread(threading.Thread):

    def __init__(self, args=()):
        super(QueueProcessThread, self).__init__()
        self.queue = args[0]
        self.queue_max_size = args[1]
        self.db = None
        self._stop_event = threading.Event()

    def run(self):
        """
            Add a key to the KEYS table, if the keys does not already exist.
        """
        self.db = Db()
        self.db.connect()
        while(1):
            if self.stopped():
                self.empty_queue()
                self.db.disconnect()
                break
            if self.queue.full() > self.queue_max_size/2:
                logging.info("Emptying queue...")
                self.empty_queue()

        return

    def empty_queue(self):
        keys = []
        while self.queue.empty() == False:
                keys.append(self.queue.get())
                self.queue.task_done()
        self.db.add_keys(keys)

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
