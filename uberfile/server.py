"""Server functionality for serving files using different protocols."""
import os
import ssl
import logging
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Optional, Tuple
from dataclasses import dataclass

@dataclass
class ServerConfig:
    """Configuration for the file server."""
    host: str
    port: int
    directory: str
    input_file: str
    protocol: str = 'HTTP'  # Default to HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None


class FileServer:
    """A server that can handle multiple file transfer protocols."""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.cert_path = os.path.expanduser('~/.config/uberfile/cert.pem')
        self.key_path = os.path.expanduser('~/.config/uberfile/key.pem')

    def validate_file(self) -> Tuple[bool, Optional[str]]:
        """Validate that the input file exists and is accessible."""
        if not os.path.isabs(self.config.input_file):
            full_path = os.path.join(self.config.directory, self.config.input_file)
        else:
            full_path = self.config.input_file

        if not os.path.exists(full_path):
            return False, f"Input file not found: {full_path}"

        if not os.path.isfile(full_path):
            return False, f"Path exists but is not a file: {full_path}"

        if not os.access(full_path, os.R_OK):
            return False, f"File exists but is not readable: {full_path}"

        return True, None

    def generate_self_signed_cert(self) -> bool:
        """Generate a self-signed certificate for HTTPS."""
        try:
            os.makedirs(os.path.dirname(self.cert_path), exist_ok=True)

            # Generate private key and self-signed certificate
            cmd = [
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
                '-keyout', self.key_path,
                '-out', self.cert_path,
                '-days', '365',
                '-nodes',  # No passphrase
                '-subj', '/CN=uberfile'
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to generate certificate: {e}")
            return False

    def serve_http(self) -> bool:
        """Start an HTTP server."""
        try:
            os.chdir(self.config.directory)
            handler = SimpleHTTPRequestHandler
            server = HTTPServer((self.config.host, self.config.port), handler)

            self.logger.info(f"HTTP server started at http://{self.config.host}:{self.config.port}")
            self.logger.info(f"Serving files from: {self.config.directory}")
            self.logger.info("Press Ctrl+C to stop the server")

            server.serve_forever()
            return True

        except Exception as e:
            self.logger.error(f"HTTP server error: {e}")
            return False

    def serve_https(self) -> bool:
        """Start an HTTPS server with SSL/TLS."""
        try:
            # Generate certificate if it doesn't exist
            if not (os.path.exists(self.cert_path) and os.path.exists(self.key_path)):
                if not self.generate_self_signed_cert():
                    return False

            os.chdir(self.config.directory)
            handler = SimpleHTTPRequestHandler
            httpd = HTTPServer((self.config.host, self.config.port), handler)

            # Create SSL context
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(self.cert_path, self.key_path)

            # Wrap socket with SSL
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

            self.logger.info(f"HTTPS server started at https://{self.config.host}:{self.config.port}")
            self.logger.info(f"Serving files from: {self.config.directory}")
            self.logger.info("Using self-signed certificate")
            self.logger.info("Press Ctrl+C to stop the server")

            httpd.serve_forever()
            return True

        except Exception as e:
            self.logger.error(f"HTTPS server error: {e}")
            return False

    def serve_ftp(self) -> bool:
        """Start an FTP server using Python's pyftpdlib."""
        try:
            # Check if pyftpdlib is installed
            subprocess.run(["pip", "show", "pyftpdlib"], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            self.logger.info("Installing pyftpdlib...")
            try:
                subprocess.run(["pip", "install", "pyftpdlib"], check=True)
            except subprocess.CalledProcessError:
                self.logger.error("Failed to install pyftpdlib")
                return False

        try:
            from pyftpdlib.authorizers import DummyAuthorizer
            from pyftpdlib.handlers import FTPHandler
            from pyftpdlib.servers import FTPServer

            authorizer = DummyAuthorizer()
            authorizer.add_anonymous(self.config.directory, perm="elr")

            handler = FTPHandler
            handler.authorizer = authorizer

            server = FTPServer((self.config.host, self.config.port), handler)
            self.logger.info(f"FTP server started at ftp://{self.config.host}:{self.config.port}")
            self.logger.info(f"Serving files from: {self.config.directory}")
            self.logger.info("Press Ctrl+C to stop the server")

            server.serve_forever()
            return True

        except Exception as e:
            self.logger.error(f"FTP server error: {e}")
            return False

    def serve_smb(self) -> bool:
        """Start an SMB server using smbserver.py."""
        try:
            cmd = [
                "/root/.local/bin/smbserver.py",
                "-smb2support",
                "EXEGOL",
                self.config.directory,
                "-username", "uberfile",
                "-password", "exegol4thewin"
            ]

            self.logger.info(f"SMB server started at smb://{self.config.host}")
            self.logger.info(f"Serving files from: {self.config.directory}")
            self.logger.info("Share name: EXEGOL")
            self.logger.info("Username: uberfile")
            self.logger.info("Password: exegol4thewin")
            self.logger.info("Press Ctrl+C to stop the server")

            process = subprocess.Popen(cmd)
            try:
                process.wait()
                return True
            except KeyboardInterrupt:
                process.terminate()
                return True

        except Exception as e:
            self.logger.error(f"SMB server error: {e}")
            return False

    def serve_scp(self) -> bool:
        """
        For SCP, we don't actually start a server since it uses SSH.
        Instead, we provide instructions for setting up SSH access.
        """
        self.logger.info("SCP/SSH Server Setup Instructions:")
        self.logger.info("1. Ensure SSH server is installed and running")
        self.logger.info("2. Configure SSH to allow the target user to connect")
        self.logger.info("3. The file will be served from: " + self.config.directory)
        self.logger.info("\nNote: SCP uses SSH, so make sure the SSH service is running and properly configured.")
        return True

    def serve_ftps(self) -> bool:
        """Start an FTPS server (FTP over SSL/TLS)."""
        try:
            # Generate certificate if it doesn't exist
            if not (os.path.exists(self.cert_path) and os.path.exists(self.key_path)):
                if not self.generate_self_signed_cert():
                    return False

            # Install pyftpdlib if not present
            try:
                subprocess.run(["pip", "show", "pyftpdlib"], capture_output=True, check=True)
            except subprocess.CalledProcessError:
                self.logger.info("Installing pyftpdlib...")
                subprocess.run(["pip", "install", "pyftpdlib"], check=True)

            from pyftpdlib.authorizers import DummyAuthorizer
            from pyftpdlib.handlers import TLS_FTPHandler
            from pyftpdlib.servers import FTPServer

            authorizer = DummyAuthorizer()
            authorizer.add_anonymous(self.config.directory, perm="elr")

            handler = TLS_FTPHandler
            handler.certfile = self.cert_path
            handler.keyfile = self.key_path
            handler.authorizer = authorizer
            handler.tls_control_required = True
            handler.tls_data_required = True

            server = FTPServer((self.config.host, self.config.port), handler)
            self.logger.info(f"FTPS server started at ftps://{self.config.host}:{self.config.port}")
            self.logger.info(f"Serving files from: {self.config.directory}")
            self.logger.info("Using SSL/TLS encryption")
            self.logger.info("Press Ctrl+C to stop the server")

            server.serve_forever()
            return True

        except Exception as e:
            self.logger.error(f"FTPS server error: {e}")
            return False

    def serve_webdav(self) -> bool:
        """Start a WebDAV server."""
        try:
            # Install wsgidav if not present
            try:
                subprocess.run(["pip", "show", "wsgidav"], capture_output=True, check=True)
            except subprocess.CalledProcessError:
                self.logger.info("Installing wsgidav...")
                subprocess.run(["pip", "install", "wsgidav"], check=True)

            from wsgidav.wsgidav_app import WsgiDAVApp
            from wsgidav.fs_dav_provider import FilesystemProvider
            from wsgidav.server.server_cli import run_server

            provider = FilesystemProvider(self.config.directory)

            config = {
                "host": self.config.host,
                "port": self.config.port,
                "provider_mapping": {"/": provider},
                "verbose": 1,
            }

            if self.config.protocol.upper() == 'WEBDAVS':
                config.update({
                    "ssl_certificate": self.cert_path,
                    "ssl_private_key": self.key_path,
                })

                # Generate certificate if needed
                if not (os.path.exists(self.cert_path) and os.path.exists(self.key_path)):
                    if not self.generate_self_signed_cert():
                        return False

            app = WsgiDAVApp(config)

            protocol = "https" if self.config.protocol.upper() == 'WEBDAVS' else "http"
            self.logger.info(f"WebDAV server started at {protocol}://{self.config.host}:{self.config.port}")
            self.logger.info(f"Serving files from: {self.config.directory}")
            if self.config.protocol.upper() == 'WEBDAVS':
                self.logger.info("Using SSL/TLS encryption")
            self.logger.info("Press Ctrl+C to stop the server")

            run_server(app, config)
            return True

        except Exception as e:
            self.logger.error(f"WebDAV server error: {e}")
            return False

    def serve(self) -> bool:
        """Start the appropriate server based on the protocol."""
        is_valid, error = self.validate_file()
        if not is_valid:
            self.logger.error(error)
            return False

        protocol_handlers = {
            'HTTP': self.serve_http,
            'HTTPS': self.serve_https,
            'FTP': self.serve_ftp,
            'FTPS': self.serve_ftps,
            'SMB': self.serve_smb,
            'SCP': self.serve_scp,
            'WEBDAV': self.serve_webdav,
            'WEBDAVS': self.serve_webdav
        }

        handler = protocol_handlers.get(self.config.protocol.upper())
        if not handler:
            self.logger.error(f"Unsupported protocol: {self.config.protocol}")
            return False

        try:
            return handler()
        except KeyboardInterrupt:
            self.logger.info("\nServer stopped by user")
            return True
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            return False
