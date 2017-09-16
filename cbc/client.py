from getpass import getpass
import websocket
import _thread
import json

from cmd import Cmd

class MyPrompt(Cmd):

    def __init__(self, ws):
        super(MyPrompt, self).__init__()
        self.ws = ws

    def do_build(self, args):
        """Starts the construction of a building."""
        send_json(self.ws, {
            'type': "build",
            'building': args,
        })

    def do_jobs(self, args):
        """List the current running jobs."""
        global player_data
        for job in player_data['jobs']:
            product = job['product']
            if product['type'] == "building":
                print("Upgrading {} to level {}.".format(product['name'].title(), player_data['buildings'][product['name']] + 1))
            elif product['type'] == "unit":
                print("Training level {} {}.".format(product['level'], product['name'].title()))
            else:
                print("Unknown job: " + job)

    def do_resources(self, args):
        """List available resources."""
        global player_data
        for resource, amount in player_data['resources'].items():
            print(resource.title() + ": " + str(amount))

    def do_buildings(self, args):
        """List the buildings of the city and their levels."""
        global player_data
        for name, level in player_data['buildings'].items():
            if level > 0:
                print("{}, level {}".format(name.title(), level))

    def do_exit(self, args):
        """Exits the program."""
        print("Exiting.")
        raise SystemExit

    def default(self, line):
        print("Unknown command: " + line)

    def emptyline(self):
        pass

def send_json(ws, message):
    ws.send(json.dumps(message))

def on_message(ws, message):
    global player_data
    data = json.loads(message)
    if 'username' in data:
        player_data = data

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(username, password, register=False):
    def run(ws):
        send_json(ws, {
            'type': "register" if register else "login",
            'username': username,
            'password': password,
        })
    return run

def main():
    ws = websocket.WebSocketApp("ws://localhost:6060",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)

    option = 0
    while option not in (1, 2):
        print("1. Login")
        print("2. Register")
        print("> ", end="", flush=True)
        option = int(input())

    print("Username: ", end="", flush=True)
    username = input()
    password = getpass()
    ws.on_open = on_open(username, password, option == 2)
    def run(*args):
        ws.run_forever()
    _thread.start_new_thread(run, ())

    prompt = MyPrompt(ws)
    prompt.prompt = '> '
    prompt.cmdloop('Starting prompt...')

if __name__ == "__main__":
    main()
