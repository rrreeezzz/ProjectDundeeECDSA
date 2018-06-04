import time

class bcolors:
    HEADER      = '\033[95m'
    OKBLUE      = '\033[94m'
    OKGREEN     = '\033[92m'
    WARNING     = '\033[93m'
    FAIL        = '\033[91m'
    ENDC        = '\033[0m'
    BOLD        = '\033[1m'
    UNDERLINE   = '\033[4m'

class keys_table:
    ID      = 0
    BLOCK  = 1
    TXID   = 2
    HASH    = 3
    COUNT   = 4
    X       = 5
    Y       = 6

def perror(e):
    print(bcolors.FAIL + "[-]" + bcolors.ENDC + " " + e)
    exit(1)

def success(s):
    print(bcolors.OKGREEN + "[+]" + bcolors.ENDC + " " + s)

def log(s):
    print(bcolors.OKBLUE + "[+] Info: " + bcolors.ENDC + " " + s)

class show_speed:
    """
        Show how many blocks we compute per 10 minutes.
    """
    def __init__(self):
        now = time.time()
        self.start = now
        self.counter = 0
        self.time_since_last_block = now

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        now = time.time()
        time_elapsed_since_start = now - self.start
        self.counter += 1
        time_elapsed_since_last_block = now - self.time_since_last_block
        self.time_since_last_block = now
        return "{0:.2f}s/block\t|\t{1:.2f}s/blocks".format(time_elapsed_since_last_block
                                                ,time_elapsed_since_start/self.counter)
