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
