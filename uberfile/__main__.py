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


def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Parse command line arguments
    options = parse_arguments()
    
    # Create command registry
    registry = create_default_registry()
    
    # List commands if requested
    if options.LIST:
        list_commands(registry)
    
    # Create user interface
    ui = UserInterface()
    
    # Get target OS
    target_os = options.TARGETOS or ui.select_os()
    
    # Get server address
    lhost = options.LHOST or ui.select_interface()
    
    # Get transfer protocol
    protocol = options.PROTOCOL or ui.select_protocol()
    
    # Get server port (after protocol selection)
    lport = options.LPORT or ui.select_port(protocol)
    
    # Get command type
    command_type = options.TYPE
    if not command_type:
        available_types = registry.get_command_types(target_os, protocol)
        if not available_types:
            logger.error(f"No commands available for {protocol} protocol on {target_os}")
            sys.exit(1)
        command_type = ui.select_command_type(available_types)
    
    # Get input file
    input_file = options.INPUTFILE
    if not input_file:
        input_file = ui.select_file(options.INPUTFOLDER)
    
    # Get output file
    output_file = options.OUTPUTFILE
    if not output_file:
        output_file = ui.select_output_file(os.path.basename(input_file), target_os)
    
    # Create command context
    context = CommandContext(
        lhost=lhost,
        lport=lport,
        input_file=os.path.basename(input_file),
        output_file=output_file,
        protocol=protocol
    )
    
    # Get commands for the selected type
    commands = registry.get_commands(target_os, command_type, protocol)
    if not commands:
        logger.error(f"No commands found for type: {command_type} with protocol: {protocol}")
        sys.exit(1)
    
    # Generate command line string
    cmdline = (f'{sys.argv[0]} --lhost {lhost} --lport {lport} '
              f'--target-os {target_os} --command {command_type} '
              f'--input-file {input_file} --output-file {output_file} '
              f'--protocol {protocol}')
    
    # Generate commands and add chmod +x for shell scripts if needed
    command_tuples = []
    for cmd in commands:
        command = cmd.generate(context)
        if target_os == 'linux' and output_file.endswith('.sh'):
            command = f"{command}; chmod +x {output_file}"
        command_tuples.append((cmd.notes, command))
    
    # Display commands
    ui.display_commands(command_tuples, cmdline)
    
    # Copy first command to clipboard
    copy(command_tuples[0][1])
    
    # Start the server
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
