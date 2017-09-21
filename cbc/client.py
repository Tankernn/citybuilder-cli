from getpass import getpass
import websocket
import _thread
import json
import time

from cmd import Cmd

class MyPrompt(Cmd):

    def __init__(self, ws):
        super(MyPrompt, self).__init__()
        self.ws = ws

    def do_build(self, args):
        """Starts the construction of a building."""
        send_json(self.ws, {
            'type': "build",
            'name': args,
        })

    def do_research(self, args):
        """Starts the research of a new technology."""
        send_json(self.ws, {
            'type': "research",
            'name': args,
        })

    def do_train(self, args):
        """Starts the training of a unit."""
        args = args.split(" ")
        send_json(self.ws, {
            'type': "train",
            'name': args[0],
            'level': args[1] if len(args) > 1 else 1
        })

    def do_jobs(self, args):
        """List the current running jobs."""
        global player_data
        global server_config
        for job in player_data['jobs']:
            product = job['product']
            if product['type'] == "building":
                print("Upgrading {} to level {}.".format(server_config['building'][product['name']]['name'], player_data['buildings'][product['name']] + 1))
            elif product['type'] == "research":
                print("Researching {} level {}.".format(server_config['research'][product['name']]['name'], player_data['research'][product['name']] + 1))
            elif product['type'] == "unit":
                print("Training level {} {}.".format(product['level'], server_config['unit'][product['name']]['name']))
            elif product['type'] == "mission":
                print("Mission: {}".format(product['mission']['name']))
            else:
                print("Unknown job: {}".format(job))
            bar_width = 20
            remaining = job['finish_time'] - time.time()
            progress = remaining / job['product']['time']
            num_bars = bar_width - int(progress * bar_width)
            print("[" + num_bars * "#" + (bar_width - num_bars) * " " + "]" + str(int(remaining)) + "s remaining")
            print("-" * (bar_width + 10))
        if not player_data['jobs']:
            print("No jobs are currently running.")

    def do_missions(self, args):
        """List available missions."""
        global player_data
        global server_config
        for i, mission in enumerate(player_data['missions']):
            print("{}. {}".format(i + 1, mission['name']))
            print("Units required:")
            for unit, count in mission['units'].items():
                print("\t- {} x{}".format(server_config['unit'][unit]['name'], count))
            print("Rewards:")
            print("\tResources:")
            for resource, amount in mission['rewards']['resources'].items():
                print("\t- {} x{}".format(resource, amount))
            print("-" * 20)
        option = 0
        opt_len = len(player_data['missions'])
        while option not in range(1, opt_len + 1):
            print("[1-{}] or 'c' to cancel: ".format(opt_len), end="", flush=True)
            try:
                option = input()
                if option == 'c':
                    return
                else:
                    option = int(option)
            except ValueError:
                print("Please enter an integer.")
        mission = player_data['missions'][option - 1]
        units_required = dict(mission['units'])
        units = list()
        if mission['type'] == 'gather':
            for i, unit in enumerate(player_data['units']):
                if unit['type'] in units_required.keys() and units_required[unit['type']] > 0:
                    units.append(i)
                    units_required[unit['type']] -= 1
        if sum(units_required.values()) == 0:
            send_json(self.ws, {
                'type': "mission",
                'index': option - 1,
                'units': units,
            })
        else:
            print("Not enough units.")



    def do_resources(self, args):
        """List available resources."""
        global player_data
        for resource, amount in player_data['resources'].items():
            print("{}: {} / {} ({}/s)".format(
                resource.title(),
                int(amount),
                player_data['resources_max'][resource],
                player_data['resources_production'][resource]
            ))

    def do_buildings(self, args):
        """List the buildings of the city and their levels."""
        global player_data
        global server_config
        any_building = False
        for name, level in player_data['buildings'].items():
            if level > 0:
                any_building = True
                print("{}, level {}".format(server_config['building'][name]['name'], level))
        if not any_building:
            print("There are no buildings in this city.")

    def do_units(self, args):
        """List available units."""
        global player_data
        global server_config
        if player_data['units']:
            for unit in player_data['units']:
                print("{}, level {}".format(server_config['unit'][unit['type']]['name'], unit['level']))
        else:
            print("There are no units in this city.")

    def do_exit(self, args):
        """Exits the program."""
        print("Exiting.")
        raise SystemExit

    def default(self, line):
        print("Unknown command: " + line)

    def emptyline(self):
        pass

prompt = None

def send_json(ws, message):
    ws.send(json.dumps(message))

def on_message(ws, message):
    global player_data
    global server_config
    global prompt
    data = json.loads(message)
    if prompt is None and 'result' in data:
        if data['result'] == 0:
            prompt = MyPrompt(ws)
            prompt.prompt = '> '
            prompt.intro = 'Starting prompt...'
            _thread.start_new_thread(prompt.cmdloop, ())
            return
        elif data['result'] == 1:
            print("Unknown user/password combination.")
        elif data['result'] == 2:
            print("Username already taken.")
        elif data['result'] == 3:
            print("Not logged in.")
        ws.close()
    if 'username' in data:
        player_data = data
    elif 'server' in data:
        server_config = data

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

def connect():
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

def main():
    connect()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
