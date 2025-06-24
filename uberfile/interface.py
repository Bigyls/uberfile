"""User interface functionality for UberFile."""
import os
import psutil
import socket
import subprocess
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from simple_term_menu import TerminalMenu
from colorama import Fore, Style

@dataclass
class UserInterface:
    """Handles user interaction and menu display."""

    def _get_network_interfaces(self) -> Dict[str, str]:
        """Get available network interfaces and their IPv4 addresses."""
        interfaces = {}
        net_if_addrs = psutil.net_if_addrs()

        for iface, addr in net_if_addrs.items():
            if iface == 'lo':  # Skip loopback
                continue
            for address in addr:
                if address.family == socket.AF_INET:
                    interfaces[iface] = address.address

        return interfaces

    def select_interface(self) -> str:
        """Let user select a network interface or input custom address."""
        interfaces = self._get_network_interfaces()
        menu_list = [f"{iface} ({addr})" for iface, addr in interfaces.items()]
        menu_list.append("Custom")

        menu = TerminalMenu(menu_list, title="Interface/address serving the files?")
        selection = menu.show()

        if selection == len(menu_list) - 1:  # Custom option
            print("(custom) Interface/address serving the files?")
            return input(Fore.RED + Style.BRIGHT + '> ' + Style.RESET_ALL)
        else:
            return interfaces[menu_list[selection].split(' ')[0]]

    def select_protocol(self) -> str:
        """Let user select the file transfer protocol."""
        protocols = ['HTTP', 'HTTPS', 'FTP', 'SMB', 'SCP']
        menu = TerminalMenu(protocols, title="Which protocol do you want to use?")
        selection = menu.show()
        return protocols[selection]

    def select_port(self, protocol: str) -> str:
        """Let user select a port or input custom port."""
        default_ports = {
            'HTTP': '80',
            'HTTPS': '443',
            'FTP': '21',
            'SMB': '445',
            'SCP': '22'
        }

        menu_list = [
            f'Default ({default_ports.get(protocol, "80")})',
            'Custom'
        ]

        menu = TerminalMenu(menu_list, title=f"Port for {protocol}?")
        selection = menu.show()

        if selection == 1:  # Custom option
            print(f"(custom) Port for {protocol}?")
            return input(Fore.RED + Style.BRIGHT + '> ' + Style.RESET_ALL)
        else:
            return default_ports.get(protocol, '80')

    def select_os(self) -> str:
        """Let user select target operating system."""
        menu_list = ['windows', 'linux']
        menu = TerminalMenu(menu_list, title="What operating system is the target running?")
        selection = menu.show()
        return menu_list[selection]

    def select_command_type(self, available_types: List[str]) -> str:
        """Let user select command type from available options."""
        menu = TerminalMenu(sorted(available_types), title="What type of command do you want?")
        selection = menu.show()
        return sorted(available_types)[selection]

    def select_file(self, current_dir: str) -> str:
        """Let user select input file."""
        menu_list = ["fzf resources", "fzf my-resources", "fzf all"]
        menu_list += [f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f))]

        menu = TerminalMenu(menu_list, title="Which file do you want the target to download?")
        selection = menu.show()
        selected = menu_list[selection]

        if selected.startswith("fzf"):
            if selected == "fzf resources":
                cmd = "find /opt/resources | fzf"
            elif selected == "fzf my-resources":
                cmd = "find /opt/my-resources | fzf"
            else:
                cmd = "fzf"

            try:
                result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            except subprocess.SubprocessError:
                print(f"{Fore.RED}Failed to run fzf command{Style.RESET_ALL}")
                return self.select_file(current_dir)  # Retry selection

        return selected

    def select_output_file(self, input_file: str, os_type: str) -> str:
        """Let user select output file name and location."""
        menu_list = [f'Same filename ({input_file})']

        if os_type == "windows":
            menu_list.append(f'Same filename in temp (C:\\Windows\\Temp\\{input_file})')
        elif os_type == "linux":
            menu_list.append(f'Same filename in /tmp (/tmp/{input_file})')

        menu_list.append('Custom')

        menu = TerminalMenu(menu_list, title="Filename to write on the target machine?")
        selection = menu.show()

        if selection == len(menu_list) - 1:  # Custom option
            print("(custom) Filename to write on the target machine?")
            return input(Fore.RED + Style.BRIGHT + '> ' + Style.RESET_ALL)
        elif selection == 0:  # Same filename
            return input_file
        else:  # OS-specific temp directory
            if os_type == "windows":
                return f'C:\\Windows\\Temp\\{input_file}'
            else:
                return f'/tmp/{input_file}'

    def display_commands(self, commands: List[tuple], cmdline: str) -> None:
        """Display generated commands and command line."""
        print()
        for i, (notes, command) in enumerate(commands, 1):
            notes_text = f'{notes} ' if notes else ''
            print(f'{Fore.BLUE}{Style.BRIGHT}[{i}] {notes_text}{Style.RESET_ALL}{command}\n')

        print(f'{Fore.RED}{Style.BRIGHT}CLI command used\n{Style.RESET_ALL}{cmdline}\n')
