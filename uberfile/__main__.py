"""Main entry point for UberFile."""
import os
import sys
import logging
import argparse
from typing import Optional
from pyperclip import copy
from colorama import Fore, Style

from .commands import CommandContext, create_default_registry
from .server import ServerConfig, FileServer
from .interface import UserInterface


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate a file downloader/uploader command',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-lp', '--lport', dest='LPORT', type=str,
                      help='Server port')
    parser.add_argument('-lh', '--lhost', dest='LHOST', type=str,
                      help='Server address')
    parser.add_argument('-t', '--target-os', dest='TARGETOS', type=str,
                      choices={"windows", "linux"},
                      help='Target machine operating system')
    parser.add_argument('-d', '--command', dest='TYPE', type=str,
                      help='command')
    parser.add_argument('-D', '--input-folder', default=os.getcwd(),
                      dest='INPUTFOLDER', type=str,
                      help='Folder where file is located')
    parser.add_argument('-f', '--input-file', dest='INPUTFILE', type=str,
                      help='File to be downloaded in local folder (or full path)')
    parser.add_argument('-o', '--output-file', dest='OUTPUTFILE', type=str,
                      help='File to write on the target machine')
    parser.add_argument('-l', '--list', dest='LIST', action='store_true',
                      help='Print all the commands UberFiles can generate')
    parser.add_argument('-p', '--protocol', dest='PROTOCOL', type=str,
                      choices={'HTTP', 'HTTPS', 'FTP', 'SMB', 'SCP'},
                      help='Transfer protocol to use')

    return parser.parse_args()


def list_commands(registry) -> None:
    """List all available commands."""
    print(f'{Fore.BLUE}{Style.BRIGHT}Windows commands{Style.RESET_ALL}')
    for command_type in sorted(registry.get_command_types('windows')):
        print(f'   - {command_type}')
    print()
    print(f'{Fore.BLUE}{Style.BRIGHT}Linux commands{Style.RESET_ALL}')
    for command_type in sorted(registry.get_command_types('linux')):
        print(f'   - {command_type}')
    sys.exit(0)


def is_elf_or_shell(filepath: str) -> bool:
    """Check if a file is an ELF binary or a shell script."""
    try:
        with open(filepath, 'rb') as f:
            start = f.read(4)
            if start == b'\x7fELF':
                return True
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline()
            if first_line.startswith("#!"):
                return True
        if filepath.endswith('.sh'):
            return True
    except Exception:
        pass
    return False


def get_target_os(options, ui):
    return options.TARGETOS or ui.select_os()


def get_lhost(options, ui):
    return options.LHOST or ui.select_interface()


def get_protocol(options, ui):
    return options.PROTOCOL or ui.select_protocol()


def get_lport(options, ui, protocol):
    return options.LPORT or ui.select_port(protocol)


def get_command_type(options, registry, target_os, protocol, ui, logger):
    command_type = options.TYPE
    if not command_type:
        available_types = registry.get_command_types(target_os, protocol)
        if not available_types:
            logger.error(f"No commands available for {protocol} protocol on {target_os}")
            sys.exit(1)
        command_type = ui.select_command_type(available_types)
    return command_type


def get_input_file(options, ui):
    return options.INPUTFILE or ui.select_file(options.INPUTFOLDER)


def get_output_file(options, input_file, target_os, ui):
    return options.OUTPUTFILE or ui.select_output_file(os.path.basename(input_file), target_os)


def generate_command_tuples(commands, context, target_os, input_file, output_file):
    command_tuples = []
    needs_chmod = False
    if target_os == 'linux' and os.path.isfile(input_file):
        needs_chmod = is_elf_or_shell(input_file)
    for cmd in commands:
        command = cmd.generate(context)
        if target_os == 'linux' and needs_chmod:
            command = f"{command}; chmod +x {output_file}"
        command_tuples.append((cmd.notes, command))
    return command_tuples


def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    options = parse_arguments()
    registry = create_default_registry()

    if options.LIST:
        list_commands(registry)

    ui = UserInterface()
    target_os = get_target_os(options, ui)
    lhost = get_lhost(options, ui)
    protocol = get_protocol(options, ui)
    lport = get_lport(options, ui, protocol)
    command_type = get_command_type(options, registry, target_os, protocol, ui, logger)
    input_file = get_input_file(options, ui)
    output_file = get_output_file(options, input_file, target_os, ui)

    context = CommandContext(
        lhost=lhost,
        lport=lport,
        input_file=os.path.basename(input_file),
        output_file=output_file,
        protocol=protocol
    )

    commands = registry.get_commands(target_os, command_type, protocol)
    if not commands:
        logger.error(f"No commands found for type: {command_type} with protocol: {protocol}")
        sys.exit(1)

    cmdline = (f'{sys.argv[0]} --lhost {lhost} --lport {lport} '
               f'--target-os {target_os} --command {command_type} '
               f'--input-file {input_file} --output-file {output_file} '
               f'--protocol {protocol}')

    command_tuples = generate_command_tuples(commands, context, target_os, input_file, output_file)
    ui.display_commands(command_tuples, cmdline)
    copy(command_tuples[0][1])

    server_config = ServerConfig(
        host=lhost,
        port=int(lport),
        directory=os.path.dirname(input_file) or os.getcwd(),
        input_file=input_file,
        protocol=protocol
    )

    server = FileServer(server_config)
    if not server.serve():
        sys.exit(1)


if __name__ == '__main__':
    main()
