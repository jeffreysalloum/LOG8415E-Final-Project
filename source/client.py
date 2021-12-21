from configparser import ConfigParser
import csv
import os
import pickle
import socket

# Data dump file path.
dataFile = os.path.dirname(os.path.realpath(__file__)) + '/data/data_dump.csv'

# Query commands.
insert = 'INSERT INTO transactions VALUES ('
select = 'SELECT * FROM transactions WHERE id = '

# Sends INSERT and SELECT queries to a specified target (Proxy or Gatekeeper).
def main():
    
    # Store and read the config file.
    config = ConfigParser()
    config.readfp(open(r'cluster.cfg'))

    # Store the specified target (Proxy or Gatekeeper).
    target = config.get('Client', 'target')
    host = config.get(target, 'host')
    port = int(config.get(target, 'port'))
    
    print(host + ":" + str(port))
    
    # Prepare the socket to send queries to.
    s = socket.socket()
    s.connect((host, port))

    with open(dataFile, 'r') as f:
        rows = csv.reader(f)
        for row in rows:
            # skip first row.
            if 'firstname' in row: continue 

            print(row) 

            # INSERT query
            insert_cmd = insert + row[0] + ", '" + row[1] + "', '" + row[2] + "', '" + row[3] + "');"
            insert_cmd_type = 'insert'
            
            # SELECT query
            select_cmd = select + "'" + row[0] + "';"
            select_cmd_type = 'select'
            
            send(s, insert_cmd_type, insert_cmd)
            send(s, select_cmd_type, select_cmd)

    s.close()

# Sends a query using a socket.
def send(socket, cmd_type, cmd):
    # Data object used amongst sockets of this architecture.
    obj = {'type': cmd_type, 'command': cmd}
    pickledobj = pickle.dumps(obj)
    socket.send(pickledobj)
    data = socket.recv(1024)
    data=pickle.loads(data)
    # print('Server response: ' + data)

if __name__ == '__main__':
    main()