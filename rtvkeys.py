#!/usr/bin/python3

import argparse
import signal

from BlockThreadRpc import *
from BlockThreadFile import *
from utils import *

def get_args():
	parser = argparse.ArgumentParser(description='Retrieve public keys from blocks from 0 to depth')
	parser.add_argument('--mode', choices=['rpc', 'file'], default='file')
	parser.add_argument('-b', '--blocks-path', metavar='blocks_path', type=str, nargs='?', help='Blockchain path')
	parser.add_argument('-r', '--rpc-addr', metavar='rpc_addr', type=str, nargs='?', help='RPC address')
	parser.add_argument('-p', '--rpc-port', metavar='rpc_port', type=int, nargs='?', help='RPC port')
	parser.add_argument('-t', '--threads', metavar='threads', type=int, nargs='?', default="2", help='Number of threads')
	parser.add_argument('-q', '--queue-size', metavar='queue_max_size', type=int, nargs='?', default="50000", help='Maximum queue size')
	args = parser.parse_args()
	if args.mode == 'file' and (args.rpc_addr or args.rpc_port):
		parser.error('rpc options can only be set when --mode=rpc.')
	elif args.mode == 'rpc' and args.blocks_path:
		parser.error('files options can only be set when --mode=file.')

	return args

if __name__ == "__main__":
	args = get_args()

	if args.mode == 'rpc':
		if not args.rpc_port:
			port = 8332
		else:
			port = args.rpc_port
		if not args.rpc_addr:
			addr = None
		else:
			addr = args.rpc_addr
		test = RetrieveKeysRpc(addr, port, args.threads, args.queue_size)
	else:
		#TODO: for block mode, check if bitcoind isn't running
		if not args.blocks_path:
			path = '~/.bitcoin/blocks'
		else:
			path = args.blocks_path
		test = RetrieveKeysFile(path, args.threads, args.queue_size)

	# if Ctrl-C
	signal.signal(signal.SIGINT, test.stop)

	test.run()
	exit(0)
