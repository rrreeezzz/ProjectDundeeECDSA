import sqlite3
from utils import *

class db:
    def __init__(self, file="data.db"):
        self.conn = self._connect(file)
        if(self._check_table() == False):
            self._create_table()

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

    def _connect(self, file):
        try:
            return sqlite3.connect(file)
        except Exception as e:
            perror("sqlite connection: " + str(e))

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

    def close_connection(self):
        try:
            self.conn.close()
        except Exception as e:
            perror("sqlite close connection: " + str(e))

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
        block = c.execute('''SELECT nblock FROM keys ORDER BY id DESC LIMIT 1''')
        nb = block.fetchone()
        if (nb):
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
        txid = c.execute('''SELECT txid FROM keys ORDER BY id DESC LIMIT 1''')
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
            print(key[2])
            # keys_table.HASH-1 because there is no ID in the tables
            r = c.execute('''SELECT count(*) FROM keys WHERE hash = ?''', (key[keys_table.HASH-1],))
            if (r.fetchone()[0]):
                c.execute('''UPDATE keys SET count=count+1 WHERE hash = ?''', (key[keys_table.HASH-1],))
                continue
            nkeys.append(key)
        return nkeys
