import time
import sqlite3
import logging

from blockchain_parser.script import *
from bitcoin.wallet import P2PKHBitcoinAddress

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
	BLOCK   = 1
	TXID    = 2
	HASH    = 3
	COUNT   = 4
	X       = 5
	Y       = 6

########## Common utils
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
MOD_SQRT_POWER = (P + 1) // 4

def get_y(x, sign):
	"""
		Retrieve Y coordinate if it's a compressed key.
		-x: X coordinate (int)
		-sign:  Sign in bytes
	"""
	y_squared = (x**3 + 7) % P
	y = pow(y_squared, MOD_SQRT_POWER, P)
	if (sign == 2 and y & 1) or (sign == 3 and not y & 1):
		return -y % P
	else:
		return y

def script_pubkey_parser(script):
	"""
		Retrieve keys in a script, recursive if a redeem script in it.
		-script:    the script (bytes)
	"""
	keys = []
	if script.value == 'INVALID_SCRIPT':
		return []
	for elt in script.operations:
		if type(elt) != bytes:
			continue
		if is_public_key(elt):
			keys.append(elt)
		elif elt[0] == 82: #0x82 == 5
			keys += script_pubkey_parser(Script(elt))
	return keys

def tx_to_keys(tx, block):
	"""
		Parse transaction inputs, then call script_pubkey_parser and get_y if needed
		and return a list of keys.
		-tx:    Transaction
		-block: Block number
	"""
	keys = []
	r = []
	for txinput in tx.inputs:
		sc = txinput.script
		keys += script_pubkey_parser(sc)

	for key in keys:
		if key[0] == 4 and len(key) == 65:
			x = key[1:33]
			y = key[33:]
		else:
			sign = key[0]
			x = int.from_bytes(key[1:], byteorder='big')
			y = get_y(x, sign)
			x = key[1:]
			y = y.to_bytes(32, byteorder='big')

		sx = x.hex().upper()
		sy = y.hex().upper()

		hash = P2PKHBitcoinAddress.from_pubkey(key, 0)
		r.append([block, tx.txid, str(hash), sx, sy])

	return r


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


#TODO: rewrite a function that measure time
class show_speed:
	"""
		Show how many blocks we compute per 10 minutes.
	"""
	def __init__(self, cur, nblock = None):
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
		if self.nblock:
			estimated_remaining_time = (((self.nblock - self.cur) * 10)/
										(60/average_sec_block))/60

		r += " {0:.2f}s/block".format(time_elapsed_since_last_block)
		r += "\t| {0:.2f}s/blocks".format(average_sec_block)
		if self.nblock:
			r += "\t| ~ time left: {0:d}h".format(int(estimated_remaining_time))
		return r
