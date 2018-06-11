from bitcoin.rpc import RawProxy
from blockchain_parser.transaction import Transaction
import threading
from utils import *
from QueueProcessThread import QueueProcessThread
from queue import Queue
from Db import Db
from time import sleep

class RetrieveKeysRpc:
	def __init__(self, rpc_addr, rpc_port, nthreads, queue_max_size = 50000):
		self.rpc_addr = rpc_addr
		self.rpc_port = rpc_port
		self.proxy = None
		self.nthreads = nthreads
		self.queue_max_size = queue_max_size
		self.queue = Queue(queue_max_size)
		self.stopped = False

	def init_rpc_co(self):
		try:
			if (self.rpc_addr):
				self.proxy = RawProxy(service_url=self.rpc_addr, service_port=self.rpc_port)
			else:
				self.proxy = RawProxy(service_port=self.rpc_port)
		except Exception as e:
			perror("Unable to connect: " + str(e))

	def run(self):
		"""
			STart the threads:
				BlockThread = retrieve keys from a block
				QueueProcessThread = process data on the queue when it is full
		"""
		db = Db()
		db.connect()

		self.init_rpc_co()
		total_blocks = self.proxy.getblockcount()
		logging.info(str(total_blocks) + " blocks")

		last_block_db = db.get_last_block()

		# if nothing in database, start at block 1
		if (last_block_db == None): last_block_db = 1
		logging.info(str(last_block_db) + " last block in db")

		#For test purpose
		# last_block_db = 210000
		# total_blocks = 210500

		#Don't need db connection anymore
		db.disconnect()

		#Create thread to process queue data
		bdthread = QueueProcessThread(args=(self.queue, self.queue_max_size))
		bdthread.start()
		bdthread.name = "bdthread"

		#Create threads that retrieve keys from block
		threads = []
		for i in range(self.nthreads):
			t = BlockThreadRpc(args=(self.queue, self.rpc_addr, self.rpc_port))
			t.start()
			threads.append(t)

		speed = show_speed(last_block_db, total_blocks)
		while last_block_db < total_blocks:
			sleep(0.1*self.nthreads)
			if self.stopped:
				success("Stopping...")
				for t in threads:
					if t == threading.current_thread(): continue #TODO: do we need this anymore ?
					elif t.name == bdthread.name: continue
					t.stop()
				for t in threads:
					t.join()
				bdthread.stop()
				bdthread.join()
				success("bye")
				break #TODO = ugly
			for t in threads:
				if t.is_working() == False:
					t.set_block(last_block_db+1)
					logging.info("{}\tretrieving block {}...{}".format(t.name, last_block_db+1, speed))
					last_block_db += 1

		return

	def stop(self, signal, frame):
		"""
			If Ctrl-C, set self.stop to True.
		"""
		self.stopped = True


class BlockThreadRpc(threading.Thread):
	"""
		A block, a thread. Using RPC.
	"""

	def __init__(self, args=()):
		super(BlockThreadRpc, self).__init__()
		self.queue = args[0]
		self.rpc_addr = args[1]
		self.rpc_port = args[2]
		self.proxy = None
		self.nblock = 0
		self._stop_event = threading.Event()

	def init_rpc_co(self):
		try:
			if (self.rpc_addr):
				self.proxy = RawProxy(service_url=self.rpc_addr, service_port=self.rpc_port)
			else:
				self.proxy = RawProxy(service_port=self.rpc_port)
		except Exception as e:
			perror("Unable to connect: " + str(e))

	def run(self):
		while(1):
			if self.stopped() and self.nblock == 0:
				logging.info('%s Stopped', self.name)
				break
			if self.nblock:
				self.init_rpc_co()
				#logging.info('%s running with %s', self.name, self.nblock)
				keys = []
				bhash = self.proxy.getblockhash(self.nblock)
				block = self.proxy.getblock(bhash)
				for txid in block['tx']:
					tx = self.proxy.getrawtransaction(txid)
					tx_d = Transaction(bytes.fromhex(tx))
					data = tx_to_keys(tx_d, self.nblock)
					if data == None or len(data) == 0:
						continue
					keys += data
				keys = dict((x[2], x) for x in keys).values() # delete duplicates in list
				for elt in keys:
					if self.queue.full():
						self.queue.join()
					self.queue.put(elt)
				self.nblock = 0
				del(self.proxy)
				self.proxy = None
		return

	def is_working(self):
		"""
			Return True if working.
		"""
		if self.nblock:
			return True
		else:
			return False

	def set_block(self, nblock):
		"""
			Set self.nblock.
			-nblock:    block number
		"""
		self.nblock = nblock

	def stop(self):
		self._stop_event.set()

	def stopped(self):
		return self._stop_event.is_set()
