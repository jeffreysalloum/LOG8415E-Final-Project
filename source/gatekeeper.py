from configparser import ConfigParser
import pickle
import socket
import re

# Validators.
insertValidator = re.compile(r"(^insert into transactions values)")
selectValidator = re.compile(r"(^select \* from transactions where id = '2\d{3}';)")

# Validates the parsed data's command, preventing possible security issues (i.e. SQL Injections).
def validate(data):
    cmd_type, cmd = parse_data(data)
    isCmdValidated = False
    if cmd_type=='insert':
        isCmdValidated = bool(insertValidator.match(cmd))
    elif cmd_type=='select':
        isCmdValidated = bool(selectValidator.match(cmd))
    return isCmdValidated

# Extracts the command and command type from the received data.
def parse_data(data):
    data=pickle.loads(data)
    type = 'insert' if data['type']=='insert' else 'select'
    command = data['command']

    return type, command

# Stores and reads the config file.
def loadConfig():
    config = ConfigParser()
    config.readfp(open(r'cluster.config'))
    return config

config = loadConfig()

# Forwards SQL queries (post-semantic validation) to a trusted host. 
def main():
    # Gatekeeper information (Port & Target (Trusted host)).
    gatekeeperPort = int(config.get('Gatekeeper', 'port'))
    gatekeeperTarget = config.get('Gatekeeper', 'target')

    # Listening socket for the Gatekeeper.
    listener = socket.socket()
    listener.bind(('', gatekeeperPort))
    listener.listen(1)
    c, addr = listener.accept()
    print('connection from: ' + str(addr))

    # sender to the trusted host
    sender = socket.socket()
    sender.connect(config.get(gatekeeperTarget, 'host'), config.get(gatekeeperTarget, 'port'))

    while True:
        data = c.recv(2048)
        if not data: break

        if validate(data):
            pickledobj = pickle.dumps(data)
            sender.send(pickledobj)

        else: break

    sender.close()
    listener.close()

if __name__ == '__main__':
    main()