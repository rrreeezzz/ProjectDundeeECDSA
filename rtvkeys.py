#!/usr/bin/python3

from bitcoin.rpc import RawProxy
import argparse
from sys import exit
from queue import Queue
import threading
import signal

from BlockThread import BlockThread
from QueueProcessThread import QueueProcessThread
from Db import Db
from utils import *

class rtvkeys:
    def __init__(self, rpc_addr, rpc_port, nthreads, queue_max_size = 1000):
        """
            p is the order (?) of the EC Bitcoin Blockchain.
        """
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
        self.init_rpc_co()
        db = Db()
        db.connect()

        total_blocks = self.proxy.getblockcount()
        last_block_db = db.get_last_block()
        logging.info(str(total_blocks) + " blocks")

        # if nothing in database, start at block 1
        if (last_block_db == None): last_block_db = 1
        logging.info(str(last_block_db) + " last block")

        if (total_blocks == last_block_db):
            if(self._is_block_complete(total_blocks, db)):
                logging.info("Up to date.")
                exit(0)
            else:
                #TODO: change this, currently delete the entire block
                db.delete_last_block()

        if(self._is_block_complete(last_block_db, db) == False):
            #TODO: change this, currently delete the entire block
            db.delete_last_block()
            last_block_db -= 1

        #For test purpose
        last_block_db = 210000
        total_blocks = 210500

        #Don't need db connection anymore
        db.disconnect()

        #Create thread to process queue data
        bdthread = QueueProcessThread(args=(self.queue, self.queue_max_size))
        bdthread.start()
        bdthread.name = "bdthread"

        #Create threads that retrieve keys from block
        threads = []
        for i in range(self.nthreads):
            t = BlockThread(args=(self.queue, self.rpc_addr, self.rpc_port))
            t.start()
            threads.append(t)

        speed = show_speed(total_blocks, last_block_db)
        while last_block_db < total_blocks:
            if self.stopped:
                success("Stopping...")
                for t in threads:
                    if t == threading.current_thread(): continue
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

    def _is_block_complete(self, nb, db):
        """
            Verify if a block is complete.
            -nb:    block
            -db:    database connection
        """
        #TODO: Replace txid by hash public key, so we don't miss keys
        bhash = self.proxy.getblockhash(nb)
        block = self.proxy.getblock(bhash)
        last_tr = block['tx'][len(block['tx'])-1]
        if(db.get_last_key_txid() == last_tr):
            return True
        else:
            return False

    def stop(self, signal, frame):
        """
            If Ctrl-C, set self.stop to True.
        """
        self.stopped = True

def get_args():
    parser = argparse.ArgumentParser(description='Retrieve public keys from blocks from 0 to depth')
    parser.add_argument('-r', '--rpc_addr', metavar='rpc_addr', type=str, nargs='?', help='RPC address')
    parser.add_argument('-p', '--rpc_port', metavar='rpc_port', type=int, nargs='?', default="8332", help='RPC port')
    parser.add_argument('-t', '--threads', metavar='threads', type=int, nargs='?', default="10", help='Number of threads')
    parser.add_argument('-q', '--queue-size', metavar='queue_max_size', type=int, nargs='?', default="10000", help='Maximum queue size')
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()

    if (args.rpc_addr):
        test = rtvkeys(args.rpc_addr, args.rpc_port, args.threads, args.queue_max_size)
    else:
        test = rtvkeys(None, args.rpc_port, args.threads, args.queue_size)

    # if Ctrl-C
    signal.signal(signal.SIGINT, test.stop)

    test.run()
    exit(0)
