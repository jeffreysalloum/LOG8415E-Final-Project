from configparser import ConfigParser
from random import randint
import mysql.connector
import os
import pickle
import socket
import time

# Stores and reads the config file.
def loadConfig():
    config = ConfigParser()
    config.readfp(open(r'cluster.cfg'))
    return config

# Config file.
config = loadConfig()
nodes = ['Master', 'Slave1', 'Slave2']

# Cluster Information
numSlaves = int(config.get('ClusterInfo', 'slaveCount'))

# Proxy Information
pingCount = int(config.get('ProxyInfo', 'pingCount'))
mode = config.get('ProxyInfo', 'mode')

# Sends queries depending on a Proxy distribution mode.
def main():
    proxyPort = int(config.get('Proxy', 'port'))

    # Listening socket.
    listener = socket.socket()
    listener.bind(('', proxyPort))
    listener.listen(1)
    c, addr = listener.accept()

    print('connection from: ' + str(addr))

    while True:
        data = c.recv(2048)

        if not data: break

        # Extract the command and command type from the received data.
        cmd_type, command = parse_data(data)
        print(command)

        if cmd_type == 'insert':
            insert(c, command, config.get('Master', 'host'))
        elif cmd_type == 'select':
            target = get_target()
            select(c, command, config.get(target, 'host'))

    listener.close()

# Reads data object and extracts command and command type.
def parse_data(data):
    data=pickle.loads(data)
    type = 'insert' if data['type']=='insert' else 'select'
    command = data['command']

    return type, command

# Connects to the cluster's MySQL database and executes an INSERT query. 
def insert(conn, command, ip):
    print("INSERTING")

    # Connect to the database.
    db = mysql.connector.connect(
        host = ip,
        user="test",
        password="testpwd",
        database="sakila")
    cursor = db.cursor()
    cursor.execute(command)
    db.commit()
    cursor.close()
    response = {'handled by':"master", 'response': "OK"}
    response = pickle.dumps(response)
    conn.send(response)
    print("INSERTING...DONE")

# Connects to the cluster's MySQL database and executes an SELECT query. 
def select(conn, command, ip):
    print("SELECTING")
    
    # Connect to the database.
    db = mysql.connector.connect(
        host = ip,
        user="test",
        password="testpwd",
        database="sakila")
    cursor = db.cursor()
    cursor.execute(command)
    result = cursor.fetchall()
    cursor.close()
    response = {'handled by':"master", 'result': result}
    response = pickle.dumps(response)
    conn.send(response)
    print("SELECTING...DONE")

# Determine the target depending on the specified distribution mode.
def get_target():
    modes = {
        'direct' : direct,
        'random' : randIp,
        'customized' : customized,
    }
    return modes[mode]()

# Targets the Master.
def direct():
    return nodes[0]

# Targets a random slave.
def randIp():
    rand = randint(1, numSlaves)
    return nodes[rand]

# Targets the current node with lowest ping.
def customized():
    slaveTimes = []
    for slaveIndex in range(0, numSlaves):
        host = config.get(nodes[slaveIndex], 'host')
        slaveTimes.append(get_ping_time(host))
    return nodes[slaveTimes.index(min(slaveTimes))]

# Retrieve a host's ping.
def get_ping_time(host):
    start = time.time()
    os.system('ping -c 1 {}'.format(host))
    return time.time() - start

if __name__ == '__main__':
    main()