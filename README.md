# Uberfile
Uberfile is a simple command-line tool aimed to help pentesters quickly generate file downloader one-liners in multiple contexts (wget, curl, powershell, certutil...).
This project code is based on my other similar project for one-liner reverseshell generation [Shellerator](https://github.com/ShutdownRepo/shellerator).

This project is installed by default in the pentesting OS [Exegol](https://github.com/ShutdownRepo/Exegol)

![Example (with menus)](https://raw.githubusercontent.com/ShutdownRepo/uberfile/main/assets/example-menus.gif)

# Install
The install is pretty simple, just clone this git and install the requirements.
```
pipx install --system-site-packages --force git+https://github.com/Bigyls/uberfile
```

# Usage
Usage is dead simple too.
```
uberfile
```
If required options are not set, the tool will start in TUI (Terminal User Interface) with pretty menus but CLI works like a charm too.

![Example (without menus)](https://raw.githubusercontent.com/ShutdownRepo/uberfile/main/assets/example-no-menus.gif)

# Sources
Some commands come from the following links
- https://www.ired.team/
- https://medium.com/@PenTest_duck/almost-all-the-ways-to-file-transfer-1bd6bf710d65
