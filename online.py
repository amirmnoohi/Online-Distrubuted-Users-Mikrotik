import pandas as pd
from librouteros import connect
import json
import os
from sys import exit

from rich.align import Align
from rich.console import Console
from rich.table import Table
from rich import print
from urllib.request import Request, urlopen

console = Console()

schema = {
    'username': pd.Series(dtype='str'),
    'Type': pd.Series(dtype='str'),
    'Server Name': pd.Series(dtype='str'),
    'Server IP': pd.Series(dtype='str'),
    'Source/Loca Address': pd.Series(dtype='str'),
    'Destination/Remote Address': pd.Series(dtype='str'),
    'TX Bytes': pd.Series(dtype='int'),
    'RX Bytes': pd.Series(dtype='int'),
    'Uptime': pd.Series(dtype='str')
}

connections = pd.DataFrame(data=schema)


def pretty(data):
    from prettytable import PrettyTable
    x = PrettyTable()
    x.field_names = ['#', *data.columns.values]
    for index, row in data.iterrows():
        x.add_row([index, *row])
    print(x)


def get_connections():
    get_PPP_connections()
    get_SOCKS_connections()


def get_PPP_connections():
    for server in servers['PPP']:
        try:
            api = connect(host=server['IP'], username='admin', password=server['PASSWORD'])
        except KeyboardInterrupt:
            exit()
        except:
            server['Status'] = '[bold red]OFFLINE[/bold red]'
            continue

        server['Status'] = '[bold green]ONLINE[/bold green]'
        api_connections = api.path('ppp', 'active')
        for item in list(api_connections):
            if len(item) == 11:
                connections.loc[len(connections.index)] = [item['name'], 'PPP', server['NAME'],
                                                           server['IP'], item['caller-id'], item['address'],
                                                           0, 0, item['uptime']]


def get_SOCKS_connections():
    for server in servers['SOCKS']:
        try:
            api = connect(host=server['IP'], username='admin', password=server['PASSWORD'])
        except KeyboardInterrupt:
            exit()
        except:
            server['Status'] = '[bold red]OFFLINE[/bold red]'
            continue

        server['Status'] = '[bold green]ONLINE[/bold green]'
        api_connections = api.path('ip', 'socks', 'connections')
        for item in list(api_connections):
            if len(item) == 7:
                connections.loc[len(connections.index)] = [item['user'], 'SOCKS', server['NAME'],
                                                           server['IP'], item['src-address'], item['dst-address'],
                                                           item['tx'], item['rx'], 'N/A']


def load_servers(file):
    response = urlopen(Request('https://url of servers json', headers={'User-Agent': 'Mozilla/5.0'})) # Should be changed

    global servers
    servers = json.loads(response.read())

    result = {'PPP': [], 'SOCKS': []}
    for server in servers['PPP']:
        result['PPP'].append({**{'Type': 'PPP'}, **server, **{'Status': '[bold green]ONLINE[/bold green]'}})

    for server in servers['SOCKS']:
        result['SOCKS'].append({**{'Type': 'SOCKS'}, **server, **{'Status': '[bold green]ONLINE[/bold green]'}})

    servers = result


def show_servers():
    table = Table(title="Servers list")

    table.add_column("Type", no_wrap=True, justify="center")
    table.add_column("Name", no_wrap=True, justify="center")
    table.add_column("IP", no_wrap=True, justify="center")
    table.add_column("PASSWORD", no_wrap=True, justify="center", style='conceal')
    table.add_column("Status", no_wrap=True, justify="center", style='blink2')

    for server in servers['PPP']:
        table.add_row(*server.values())

    for server in servers['SOCKS']:
        table.add_row(*server.values())
    console.print(Align.center(table))


def show_connections(connections):
    global cnts
    cnts = connections.groupby(['username', 'Type'], as_index=False).agg(
        lambda x: x.sum() if x.dtype == 'int64' else x.head(1))

    table = Table(title="Online Users")
    table.add_column("Username", no_wrap=True, justify="center")
    table.add_column("Type", no_wrap=True, justify="center")
    table.add_column("Server Name", no_wrap=True, justify="center")
    table.add_column("Server IP", no_wrap=True, justify="center")
    table.add_column("Source/Loca Address", no_wrap=True, justify="center")
    table.add_column("Destination/Remote Address", no_wrap=True, justify="center")
    table.add_column("TX Bytes", no_wrap=True, justify="center")
    table.add_column("RX Bytes", no_wrap=True, justify="center")
    table.add_column("Uptime", no_wrap=True, justify="center")

    for cnt in cnts.iterrows():
        cnt = [str(i) for i in cnt[1].values]
        table.add_row(*cnt)
    console.print(Align.center(table))


def show_onlines():
    table = Table(title="Online Stats")
    table.add_column("All", no_wrap=True, justify="center")
    table.add_column("PPP", no_wrap=True, justify="center")
    table.add_column("SOCKS", no_wrap=True, justify="center")
    table.add_row(*[str(len(cnts)), str(len(cnts[cnts['Type'] == 'PPP'])), str(len(cnts[cnts['Type'] == 'SOCKS']))])
    console.print(Align.center(table))

def main():
    with console.status("[bold blue]Fetching Server List...[/bold blue]",
                        spinner_style="bold blue") as status:
        load_servers("onlines.json")

    with console.status("[bold blue]Fetching Connections...(press CTRL + C to stop)[/bold blue]",
                        spinner_style="bold blue") as status:
        get_connections()
        os.system("cls")
        show_servers()
        show_connections(connections)
    show_onlines()

    try:
        i = 0
        while True:
            with console.status("[bold blue]Refreshing...(press CTRL + C to stop)[/bold blue]",
                                spinner_style="bold blue") as status:
                get_connections()
                os.system("cls")
                show_servers()
                show_connections(connections)
            show_onlines()
            print(f"Round Number: {i}")
            i = i + 1
            connections.drop(connections.index, inplace=True)

    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
