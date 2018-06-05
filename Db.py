import sqlite3
from utils import *

class Db:
    def __init__(self, file="data.db"):
        self.filedb = file
        self.conn = None

    def _check_table(self):
        """
            Check if the tables exist.
        """
        c = self.conn.cursor()
        n = c.execute('''SELECT count(*) FROM sqlite_master WHERE type="table" AND name="keys"''')
        if (n.fetchone()[0]):
            return True
        else:
            return False

    def connect(self):
        """
            Connect to DB and check if tables exist.
        """
        try:
            self.conn = sqlite3.connect(self.filedb)
        except Exception as e:
            perror("sqlite connection: " + str(e))

        if(self._check_table() == False):
            self._create_table()

    def disconnect(self):
        """
            Connect to DB and check if tables exist.
        """
        self._commit()
        try:
            self.conn.close()
        except Exception as e:
            perror("sqlite disconnection: " + str(e))

    def _commit(self):
        try:
            self.conn.commit()
        except Exception as e:
            perror("sqlite commit: " + str(e))

    def _create_table(self):
        """
            Create table KEYS and DIFFERENCES.
            Also create a index on keys(hash) to search efficiently.
        """
        c = self.conn.cursor()
        c.execute('''CREATE TABLE keys (
                    id integer primary key autoincrement,
                    nblock integer,
                    txid text,
                    hash text,
                    count integer default 1,
                    x text,
                    y text
                    )''')

        c.execute('''CREATE TABLE differences (
                    origin,
                    list text,
                    FOREIGN KEY(origin) REFERENCES keys(id)
                    )''')

        c.execute('''CREATE INDEX hash_index ON keys(hash)''')

        self._commit()

    def add_keys(self, keys):
        """
            Add a key to the KEYS table, if the keys does not already exist.
            -keys:  should be a list of key
        """
        c = self.conn.cursor()
        keys = self._verify_double(keys)
        c.executemany('''INSERT INTO keys(nblock, txid, hash, x, y) VALUES (?,?,?,?,?)''', keys)
        self._commit()

    def get_last_block(self):
        """
            Return the block of the last added key.
        """
        c = self.conn.cursor()
        block = c.execute('''SELECT MAX(nblock) FROM keys''')
        nb = block.fetchone()
        if (nb[0]):
            return int(nb[0])
        else:
            return None

    def delete_last_block(self):
        """
            Delete keys from last block.
        """
        block = self.get_last_block()
        if block == None: block = 1
        c = self.conn.cursor()
        #TODO: change because O(n)
        c.execute('''DELETE FROM keys WHERE nblock=?''', (block,))
        self._commit()

    def get_last_key_txid(self):
        """
            Return txid of last key.
        """
        c = self.conn.cursor()
        block = self.get_last_block();
        txid = c.execute('''SELECT txid FROM keys WHERE nblock = ? ORDER BY id DESC LIMIT 1''', (block,))
        return txid.fetchone()

    def _verify_double(self, keys):
        """
            Verify if key in keys are already in the db. If so, delete it from
            the list and increment keys(count).
            -keys:  list of key
        """
        c = self.conn.cursor()
        nkeys = []
        keys = dict((x[2], x) for x in keys).values() # delete duplicates in list
        for key in keys:
            # keys_table.HASH-1 because there is no ID in the element
            r = c.execute('''SELECT count(*) FROM keys WHERE hash = ?''', (key[keys_table.HASH-1],))
            if (r.fetchone()[0]):
                c.execute('''UPDATE keys SET count=count+1 WHERE hash = ?''', (key[keys_table.HASH-1],))
                continue
            nkeys.append(key)
        return nkeys
