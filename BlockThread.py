from bitcoin.wallet import P2PKHBitcoinAddress
from bitcoin.rpc import RawProxy
import threading
from utils import *

class BlockThread(threading.Thread):
    """
        A block, a thread.
    """
    p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    mod_sqrt_power = (p + 1) // 4

    def __init__(self, args=()):
        super(BlockThread, self).__init__()
        self.queue = args[0]
        self.rpc_addr = args[1]
        self.rpc_port = args[2]
        self.proxy = None
        self.nblock = 0
        self._stop_event = threading.Event()
        self.init_rpc_co()

    def init_rpc_co(self):
        try:
            if (self.rpc_addr):
                self.proxy = RawProxy(service_url=self.rpc_addr, service_port=self.rpc_port)
            else:
                self.proxy = RawProxy(service_port=self.rpc_port)
        except Exception as e:
            perror("Unable to connect: " + str(e))

    def modular_sqrt(self, a):
        """
            Return n where n * n == a (mod p).
            If no such n exists, an arbitrary value will be returned. From pycoin.
        """
        return pow(a, self.mod_sqrt_power, self.p)

    def get_y(self, x, sign):
        """
            Get the Y coordinate from a compressed key.
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
        while(1):
            if self.stopped() and self.nblock == 0:
                logging.info('%s Stopped', self.name)
                break
            if self.nblock:
                #logging.info('%s running with %s', self.name, self.nblock)
                keys = []
                bhash = self.proxy.getblockhash(self.nblock)
                block = self.proxy.getblock(bhash)
                for txid in block['tx']:
                    data = self._get_keys(txid, self.nblock)
                    if data == None or len(data) == 0:
                        continue
                    keys += data
                keys = dict((x[2], x) for x in keys).values() # delete duplicates in list
                for elt in keys:
                    self.queue.put(elt)
                self.nblock = 0
        return

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
