import sys
import getopt


import functools
import socket
import struct
import threading

from plug_interface import LanguageModule

class LanguageServer:
    port : int
    module : LanguageModule
    server_socket : socket
    transition2id: dict
    id2transition: dict

    def __init__(self, port, module):
        self.port = port
        self.module = module
        self.transition2id = {}
        self.id2transition = {}

    def create_server_socket(self):
        """Creates a a listening socket for a plug runtime on given port"""
        print("Listening on port " + str(self.port))
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.server_socket.bind(("", self.port))

    def listenx(self, client_socket=None, client_address=None):
        if client_socket == None:
            client_socket, client_address = self.server_socket.accept()

        print("Client ", str(client_address), " connected")
        try:
            alive = self.handle_request(client_socket)
            while alive:
                alive = self.handle_request(client_socket)
        finally:
            client_socket.close()

    def start(self):
        self.create_server_socket()

        self.server_socket.listen(5)
        #self.listenx()

        while True:
            client_socket, client_address = self.server_socket.accept()
            threading.Thread(target = self.listenx, args = (client_socket, client_address)).start()

        self.server_socket.close()

    def send_int(self, value, sock):
        message = bytearray(4)
        struct.pack_into("<i", message, 0, value)
        sock.send(message)

    def recv_int(self, sock):
        return int(struct.unpack("<i", sock.recv(4))[0])

    def receive_configuration(self, sock):
        size = self.recv_int(sock)
        return self.module.marshaller.deserialize_configuration(sock.recv(size))

    def send_configuration(self, configuration, sock):
        buffer = self.module.marshaller.serialize_configuration(configuration)
        self.send_int(len(buffer), sock)
        sock.send(buffer)

    def send_configurations(self, configurations, sock):
        self.send_int(len(configurations), sock)
        for configuration in configurations:
            self.send_configuration(configuration, sock)

    def receive_transition(self, sock):
        size = self.recv_int(sock)
        return self.module.marshaller.deserialize_transition(sock.recv(size))

    def send_transition(self, transition, sock):
        buffer = self.module.marshaller.serialize_transition(transition)
        self.send_int(len(buffer), sock)
        sock.send(buffer)

    def send_transitions(self, transitions, sock):
        self.send_int(len(transitions), sock)
        for transition in transitions:
            self.send_transition(transition, sock)

    def receive_payload(self, sock):
        size = self.recv_int(sock)
        return self.module.marshaller.deserialize_payload(sock.recv(size))

    def send_payload(self, payload, sock):
        buffer = self.module.marshaller.serialize_payload(payload)
        self.send_int(len(buffer), sock)
        sock.send(buffer)

    def initial_configurations(self, sock):

        configurations = self.module.transition_relation.initial_configurations()

        self.send_configurations(configurations, sock)

    def fireable_transitions_from(self, sock):
        configuration = self.receive_configuration(sock)

        fireables = self.module.transition_relation.fireable_transitions_from(configuration)

        self.send_transitions(fireables, sock)

    def fire_one_transition(self, sock):

        source = self.receive_configuration(sock)
        transition = self.receive_transition(sock)

        [configurations, payload] = self.module.transition_relation.fire_one_transition(source, transition)
        self.send_configurations(configurations, sock)
        self.send_payload(payload, sock)

    def send_string(self, string, sock):
        """Sends a string in UTF-8"""
        if (string == None):
            data = bytearray(4)
            struct.pack_into("<i", data, 0, -1)
            sock.send(data)
        else:
            raw = string.encode("utf-8")
            raw_count = len(raw)
            data = bytearray(4)
            struct.pack_into("<i", data, 0, raw_count)
            sock.send(data)
            sock.send(raw)

    def send_configuration_item(self, item, sock):
        """Sends one configuration item"""
        self.send_string(item.get("type", ""), sock)
        self.send_string(item.get("name", ""), sock)
        self.send_string(item.get("icon", ""), sock)

        children = item.get("children", [])
        self.send_configuration_items(children, sock)

    def send_configuration_items(self, items, sock):
        """Sends configuration items"""
        message = bytearray(4)
        struct.pack_into("<i", message, 0, len(items))
        sock.send(message)
        for child in items:
            self.send_configuration_item(child, sock)

    def configuration_items(self, sock):
        configuration = self.receive_configuration(sock)
        self.send_configuration_items(self.module.runtime_view.configuration_items(configuration), sock)

    def fireable_transition_description(self, sock):
        transition = self.receive_transition(sock)
        self.send_string(self.module.runtime_view.fireable_transition_description(transition), sock)

    def receive_atomic_propositions(self, sock):
        """Receives atomic propositions to register"""
        atoms_count = self.recv_int(sock)
        result = []
        for _ in range(0, atoms_count):
            atom_size = self.recv_int(sock)
            raw_proposition = bytearray(atom_size)
            sock.recv_into(raw_proposition)
            result.append(raw_proposition.decode("utf-8"))
        return result

    def send_ints(self, ints, sock):
        """Sends an array of integers"""
        idx_count = len(ints)
        message = bytearray(4 + idx_count * 4)
        struct.pack_into("<i", message, 0, idx_count)
        current = 4
        for value in ints:
            struct.pack_into("<i", message, current, value)
            current += 4
        sock.send(message)

    def register_atomic_propositions(self, sock):
        propositions = self.receive_atomic_propositions(sock)
        result = self.module.atom_evaluator.register_atomic_propositions(propositions)
        self.send_ints(result, sock)

    def send_valuations(self, valuations, sock):
        """Sends valuations for atomic propositions"""
        value_count = len(valuations)
        message = bytearray(4 + value_count)
        struct.pack_into("<i", message, 0, value_count)
        current = 4
        for value in valuations:
            try:
                struct.pack_into("B", message, current, value)
            except:
                struct.pack_into("B", message, current, False)
            current += 1
        sock.send(message)

    def atomic_proposition_valuations(self, sock):
        configuration = self.receive_configuration(sock)
        result = self.module.atom_evaluator.atomic_proposition_valuations(configuration)
        self.send_valuations(result, sock)

    def extended_atomic_proposition_valuations(self, sock):
        source = self.receive_configuration(sock)
        transition = self.receive_transition(sock)
        payload = self.receive_payload(sock)
        target = self.receive_configuration(sock)

        result = self.module.atom_evaluator.extended_atomic_proposition_valuations(source, transition, payload, target)

        self.send_valuations(result, sock)

    def api(self, sock) -> dict:
        return {
            1: functools.partial(self.initial_configurations, sock),
            2: functools.partial(self.fireable_transitions_from, sock),
            3: functools.partial(self.fire_one_transition, sock),
            4: functools.partial(self.register_atomic_propositions, sock),
            5: functools.partial(self.atomic_proposition_valuations, sock),
            6: functools.partial(self.extended_atomic_proposition_valuations, sock),
            10: functools.partial(self.configuration_items, sock),
            11: functools.partial(self.fireable_transition_description, sock)
        }

    def handle_request(self, client_socket):
        """Reads first 2 bytes from request to identify the request"""
        header = bytearray(2)
        client_socket.recv_into(header)
        unpacked = struct.unpack("<BB", header)
        #print(unpacked.__repr__())
        if unpacked[0] == 1:
            self.api(client_socket).get(unpacked[1], "Unknown request: " + unpacked[1].__repr__())()
            return True
        else:
            print("Received EOS")
            return False


def server(soup_module):
    port = 1234
    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hp:", ["port="])
    except getopt.GetoptError:
        print('remote.py -p port')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('remote.py -p port')
            sys.exit()
        elif opt in ("-p", "--port"):
            port = arg

    print("Starting model on port: " + str(port))

    LanguageServer(int(port), soup_module()).start()

#if __name__ == "__main__":

    # port = 12345
    # try:
    #     opts, _ = getopt.getopt(sys.argv[1:], "hp:", ["port="])
    # except getopt.GetoptError:
    #     print ( 'remote.py -p port' )
    #     sys.exit(2)
    #
    # for opt, arg in opts:
    #     if opt == '-h':
    #         print ( 'remote.py -p port' )
    #         sys.exit()
    #     elif opt in ("-p", "--port"):
    #         port = arg
    #
    # print ( "Starting model on port: " + str(port) )
    #
    # LanguageServer(int(port), alice_bob_peterson()).start()

