# WARNING

Real bad code here (for now)

# Description
## TL;DR
This program go through the Bitcoin's blockchain and retrieve all the public keys in a sqlite database by querying a full node's rpc.
## !TL;DR
**TODO** \
The DB schema for now is:
- Table keys
  - **ID**
  - **BLOCK**   block height
  - **TXID**    transaction txid
  - **HASH**    bitcoin address
  - **COUNT**   times met
  - **X, Y**    coordinates of the EC point

# Releases
- 0.1 [04/06/2018]: Works, but really bad performance
- 0.2 [06/06/2018]: Using multithreading and queue, but still, too long 

# TODO
- Rewrite the core functions

