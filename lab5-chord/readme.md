implemented a simplified version of the chord distributed hash table using grpc and protobuf.

## registry

Registry is responsible for registering and deregistering the nodes.

- You must initialize your random generator with seed 0.

Registry features:

- It holds a dictionary of id and address port pairs of all registered nodes.
- Forms a finger-table for a specific node.
- Helps a node to join the ring.
- Every node knows about the registry.
- It is the only centralized part of the chord.
- There are no nodes in the ring at the start of the registry.

Run command:

- ```python3 Registry.py <ipaddr>:<port> <m>```

- Registry has several command-line arguments:
    - ipaddr - ip address registry should run on.
    - port - port number registry should run on.
    - m - size of key (in bits). Thus, max size of the chord ring.
- Run command example:
    - python3 Registry.py 5000 

### Methods

1. register(ipaddr, port)
1. deregister(id)
1. populate_finger_table(id)
1. get_chord_info()

__register(ipaddr, port):__

This method is invoked by a new node to register itself. It is responsible to register
the node with given ipaddr and port. I.e., assigns an id from identified space.
Id is chosen randomly from range [0, 2m-1]. If the generated id already exists, it
generates another one until there is no collision.
Returns:
If successful: tuple of (node’s assigned id, m)
If unsuccessful: tuple of (-1, error message explaining why it was unsuccessful)
It fails when the Chord is full, i.e. there are already 2m nodes in the ring.


__deregister(id):__

This method is responsible for deregistering the node with the given id.
Returns:
If successful: tuple of (True, success message)
If unsuccessful: tuple of (False, error message)

__populate_finger_table(id):__

This method is responsible for generating the dictionary of the pairs (id, ipaddr:port)
that the node with the given id can directly communicate with.
Also, this method should find the predecessor of the node with the given id - the next
node reverse clockwise. For example, if there are no nodes between nodes with ids
31 and 2, then the predecessor of node 2 is node 31.
Returns:
Predecessor of the node with the given id, finger table of the node with the given id
(list of pairs (id, ipaddr:port)).

__get_chord_info():__

This is the only method called by the client. This method returns the information
about the chord ring (all registered nodes): list of (node id, ipaddr:port).
Example:

- (2, 127.0.0.1:5002)
- (12, 127.0.0.1:5003)
- (20, 127.0.0.1:5004)

### How to format a finger table

???

## node

A node of a chord ring.

- Initially is not a part of the chord
- call registry method in registry to register itself
- requests the IDs from its successors
    - ??
- calls the populate_finger_table function of the Registry every second (only if it was successfully registered in the ring)
- calls the deregister function of the Registry on exit.
- Stores some keys (data) of the chord.
- Able to save and remove data.

Run command:
- ```python3 Node.py <registry-ipaddr>:<registry-port> <ipaddr>:<port>```
- Command-line arguments:
    - ```<registry-ipaddr>:<registry-port>``` - ip address and a port number of the Registry.
    - ```<ipaddr>:<port>``` - ip address and a port number this node will be listening to.

### methods

1. get_finger_table()
1. save(key, text)
1. remove(key)
1. find(key)
1. quit()

### Lookup procedure:

???

## client

Client is a command line user interface to interact with the chord ring. It continuously listens to the user's input and has several commands.

run command:

- python3 Client.py

#### commands

1. ```connect <ipaddr>:<port>```
1. ```get_info```
1. ```save “key” <text>```
1. ```remove key```
1. ```find key```
1. ```quit```

```connect <ipaddr>:<port>```: 

Establish a connection with a node or a registry on a given address. The client should be able to distinguish between a registry and a node. If there is no registry/node on this address, print the corresponding message. If the connection is successful, print the corresponding message

```get_info```

Calls get_chord_info() if connected to a registry. Or get_finger_table() if connected to a node. And prints the result.

```save “key” <text>```

Example:

- save “some key” some “text” here
- key: some key
- text: some “text” here

It tells the connected node to save the text with the given key. Prints the result.

```remove key```:

It tells the connected node to remove the text with the given key. Prints the result.

```find key```: 

It tells the connected node to find a node with the key. Prints the result.

```quit```:

Stop and exit client.