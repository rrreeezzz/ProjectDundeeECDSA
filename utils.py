import time
import sqlite3
import logging

class bcolors:
    HEADER      = '\033[95m'
    OKBLUE      = '\033[94m'
    OKGREEN     = '\033[92m'
    WARNING     = '\033[93m'
    FAIL        = '\033[91m'
    ENDC        = '\033[0m'
    BOLD        = '\033[1m'
    UNDERLINE   = '\033[4m'

########## DB Specs
class keys_table:
    ID      = 0
    BLOCK  = 1
    TXID   = 2
    HASH    = 3
    COUNT   = 4
    X       = 5
    Y       = 6

########## Log function
# TODO: replace by logging module
def perror(e):
    print(bcolors.FAIL + "[-]" + bcolors.ENDC + " " + e)
    exit(1)

def success(s):
    print(bcolors.OKGREEN + "[+]" + bcolors.ENDC + " " + s)




logging.basicConfig(level=logging.INFO,
                    format=bcolors.OKBLUE + "[+] Info: "
                    + bcolors.ENDC + " "'%(message)s',
                    )

class show_speed:
    """
        Show how many blocks we compute per 10 minutes.
    """
    def __init__(self, nblock, cur):
        now = time.time()
        self.start = now
        self.counter = 0
        self.time_since_last_block = now
        self.nblock = nblock
        self.cur = cur

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        r = ""
        now = time.time()
        self.cur += 1

        #average sec per blocks
        time_elapsed_since_start = now - self.start
        self.counter += 1
        average_sec_block = time_elapsed_since_start/self.counter

        #time las block
        time_elapsed_since_last_block = now - self.time_since_last_block
        self.time_since_last_block = now

        #estimated remaining time
        #1 block every ~ 10 minutes
        estimated_remaining_time = (((self.nblock - self.cur) * 10)/
                                    (60/average_sec_block))/60

        r += " {0:.2f}s/block\t|".format(time_elapsed_since_last_block)
        r += " {0:.2f}s/blocks\t|".format(average_sec_block)
        r += " ~ time left: {0:d}h".format(int(estimated_remaining_time))
        return r
