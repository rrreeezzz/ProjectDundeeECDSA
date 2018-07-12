from blockchain_parser.blockchain import Blockchain
from utils import *
import threading
from QueueProcessThread import QueueProcessThread
from queue import Queue
from Db import Db
from time import sleep

class RetrieveKeysFile:
	def __init__(self, path, nthreads, queue_max_size = 50000):
		self.path = path
		self.nthreads = nthreads
		self.queue_max_size = queue_max_size
		self.queue = Queue(queue_max_size)
		self.stopped = False

	def run(self):
		"""
			Start the threads:
				BlockThread = retrieve keys from a block
				QueueProcessThread = process data on the queue when it is full
		"""
		db = Db()
		db.connect()

		last_block_db = db.get_last_block()

		# if nothing in database, start at block 1
		if (last_block_db == None): last_block_db = 1
		logging.info(str(last_block_db) + " last block in db")

		#Don't need db connection anymore
		db.disconnect()

		#Create thread to process queue data
		bdthread = QueueProcessThread(args=(self.queue, self.queue_max_size))
		bdthread.start()
		bdthread.name = "bdthread"

		#Create threads that retrieve keys from block
		threads = []
		for i in range(self.nthreads):
			t = BlockThreadFile(args=(self.queue))
			t.start()
			threads.append(t)

		blockchain = Blockchain(self.path)

		speed = show_speed(last_block_db)
		for block in blockchain.get_ordered_blocks(self.path + '/index', start=last_block_db, cache='index_cache.pickle'):
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
			distributed = False
			while distributed == False:
				sleep(0.1*self.nthreads)
				for t in threads:
					if t.is_working() == False:
						t.set_block(block)
						distributed = True
						logging.info("{}\tretrieving block {}...{}".format(t.name, block.height, speed))
						break

		return

	def stop(self, signal, frame):
		"""
			If Ctrl-C, set self.stop to True.
		"""
		self.stopped = True


class BlockThreadFile(threading.Thread):
	"""
		A block, a thread. Using RPC.
	"""

	def __init__(self, args=()):
		super(BlockThreadFile, self).__init__()
		self.queue = args
		self.block = None
		self._stop_event = threading.Event()

	def run(self):
		while(1):
			if self.queue.qsize() > self.qeue.maxsize/2:
				self.queue.join()
			if self.stopped() and self.block == None:
				logging.info('%s Stopped', self.name)
				break
			if self.block:
				keys = []
				for tx in self.block.transactions:
					data = tx_to_keys(tx, self.block.height)
					if data == None or len(data) == 0:
						continue
					keys += data
				keys = dict((x[2], x) for x in keys).values() # delete duplicates in list
				for elt in keys:
					self.queue.put(elt)
				self.block = None

		return

	def is_working(self):
		"""
			Return True if working.
		"""
		if self.block:
			return True
		else:
			return False

	def set_block(self, block):
		"""
			Set self.nblock.
			-nblock:    block number
		"""
		self.block = block

	def stop(self):
		self._stop_event.set()

	def stopped(self):
		return self._stop_event.is_set()
