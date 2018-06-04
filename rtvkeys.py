#!/usr/bin/python3

from bitcoin.rpc import RawProxy
import argparse
from sys import exit
from bitcoin.wallet import P2PKHBitcoinAddress

import db
from utils import *

class rtvkeys:
    p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    mod_sqrt_power = (p + 1) // 4

    def __init__(self, proxy):
        """
            p is the order (?) of the EC Bitcoin Blockchain.
        """
        self.proxy = proxy
        self.db = None

    def modular_sqrt(self, a):
        """
            Return n where n * n == a (mod p).
            If no such n exists, an arbitrary value will be returned. From pycoin.
        """
        return pow(a, self.mod_sqrt_power, self.p)

    def get_y(self, x, sign):
        """
            Get the Y coordinate from a public key.
            -x:     x coordinate
            -sign:  sign of Y
        """
        y_squared = (x**3 + 7) % self.p
        y = self.modular_sqrt(y_squared)
        if (sign == "02" and y & 1) or (sign == "03" and not y & 1) :
            return -y % self.p
        else:
            return y

    def run(self):
        """
            Go through the Blockchain and retreive keys.
        """
        self.db = db.db()
        total_blocks = self.proxy.getblockcount()
        last_block_db = self.db.get_last_block()
        log(str(total_blocks) + " blocks")

        if (last_block_db == None): last_block_db = 1

        if (total_blocks == last_block_db):
            if(self._is_block_complete(total_blocks)):
                log("Up to date.")
                exit(0)
            else:
                #TODO: change this, currently delete the entire block
                self.db.delete_last_block()

        if(self._is_block_complete(last_block_db) == False):
            self.db.delete_last_block()
            last_block_db -= 1

        speed = show_speed()
        while last_block_db < total_blocks:
            bhash = self.proxy.getblockhash(last_block_db + 1)
            block = self.proxy.getblock(bhash)
            log("retrieving block {}...\t{}".format(last_block_db+1, speed))

            keys = []
            for txid in block['tx']:
                data = self._get_keys(txid, last_block_db+1)
                if data == None or len(data) == 0:
                    continue
                keys += data
            self.db.add_keys(keys)
            last_block_db+=1

    def _is_block_complete(self, nb):
        """
            Verify if a block is complete.
            -nb:    block
        """
        #TODO: Replace txid by hash public key, so we don't miss keys
        bhash = self.proxy.getblockhash(nb)
        block = self.proxy.getblock(bhash)
        last_tr = block['tx'][len(block['tx'])-1]
        if(self.db.get_last_key_txid() == last_tr):
            return True
        else:
            return False

    def _get_keys(self, txid, block):
        """
            Retrieve all keys from a transaction and construct a list according
            to the db schema.
            -txid:  transaction id
            -block: block number
        """
        tx = self.proxy.getrawtransaction(txid)
        tx_d = self.proxy.decoderawtransaction(tx)

        keys = []
        return_keys = []
        for elt in tx_d['vin']:
            if 'coinbase' in elt.keys():
                continue
            if 'txinwitness' in elt.keys():
                tab = elt['txinwitness']
            elif 'scriptSig' in elt.keys():
                sc = elt['scriptSig']
                tab = [x for x in sc['asm'].split(' ')]

            #If there is a redeem script
            rds = [x for x in tab if x.startswith('5')]
            if (len(rds) != 0):
                for x in rds:
                    keys += [p for p in proxy.decodescript(x)['asm'].split(' ') if
                            p.startswith('02') or p.startswith('03') or
                            p.startswith('04')]
            else:
                keys += [p for p in tab if p.startswith('02') or p.startswith('03')
                        or p.startswith('04')]

            for key in keys:
                sign = key[:2]
                if sign != "04":
                    #Because sometimes very strange keys, and also because
                    #there are "0"
                    if (len(key) < 60 or len(key) > 70): continue
                    sx = '0x' + key[2:].upper()
                    x = int(sx, 16)
                    y = self.get_y(x, sign)
                    sy = "%X" % y
                    #keys.append([tx, nblock, hash, ])
                else:
                    if (len(key) < 120 or len(key) > 136): continue
                    sx = key[2:66].upper()
                    x = int(sx, 16)
                    sy = key[66:].upper()
                    y = int(sy, 16)

                hash = P2PKHBitcoinAddress.from_pubkey(bytes.fromhex(key), 0)

                return_keys.append([block, txid, str(hash), sx, sy])

            return return_keys

def get_args():
    parser = argparse.ArgumentParser(description='Retrieve public keys from blocks from 0 to depth')
    parser.add_argument('-r', '--rpc_addr', metavar='rpc_addr', type=str, nargs='?', help='RPC address')
    parser.add_argument('-p', '--rpc_port', metavar='rpc_port', type=int, nargs='?', default="8332", help='RPC port')
    return parser.parse_args()

def init_rpc_co(rpc_addr, rpc_port):
    try:
        if (rpc_addr):
            proxy = RawProxy(service_url=rpc_addr, service_port=rpc_port)
        else:
            proxy = RawProxy(service_port=rpc_port)
    except Exception as e:
        perror("Unable to connect: " + str(e))

    return proxy

if __name__ == "__main__":
    args = get_args()

    if (args.rpc_addr):
        proxy = init_rpc_co(args.rpc_addr, args.rpc_port)
    else:
        proxy = init_rpc_co(None, args.rpc_port)

    test = rtvkeys(proxy)
    test.run()
