Kaffelogic Studio
Installation on Linux systems

If you can successfully install and use one of the pre-built .deb or .rpm files, then you should do so.

If you need to install from sources, then be aware that this is not a standard Linux install. There is no configure and no makefile. You must use the script file ubuntu-dependencies.sh to ensure that the required dependencies are in place. You can run the script as

	$ sh ubuntu-dependencies.sh

or you may need to install these resources in a Python virtual environment. It depends on how you manage your Python development environment.

Installing the dependencies goes smoothly in Ubuntu 18, but everything gets more difficult with Ubuntu 20 with Python2 being deprecated.

When you set up a virtual environment it needs access to the system site packages
$ virtualenv -p python2 --system-site-packages venv
$ . venv/bin/activate
and also some of the Python2 dev tools may need to be copied across like this (for pyinstaller)
$ cp ~/kaffelogic-studio/venv/include ~/kaffelogic-studio/venv/local -r

You may also need to install pip2, inststructions here: https://linuxize.com/post/how-to-install-pip-on-ubuntu-20.04/

If you have trouble installing pip2 you may work around this by installing a virtual environment, which includes pip by default.

You also need to install fpm. See https://github.com/jordansissel/fpm for instructions. (You may also need apt install rpm, or simply ignore the error messages that relate to rpm.)

Once the dependencies are in place, you can test the system with

	$ cd [[folder you extracted to]]/kaffelogic-studio
	$ python2 'Kaffelogic Studio.py'

This should bring up a functional instance of Kaffelogic Studio. There will be a number of GTK errors and warnings shown in the terminal window. This is normal (it's a GTK/Wx thing). If Kaffelogic Studio doesn't open it means there are still dependencies to resolve, or maybe system configuration. If you discover any additional dependencies or configuration required to get it running on your system, please advise chris@kaffelogic.com so that they can be added to the documentation.

A build can then be done with 

	$ cd [[folder you extracted to]]/kaffelogic-studio
	$ sh ubuntu-build.sh

which will build an executable file using pyinstaller and package it using fpm, leaving an installable package in the Output folder. 

An install can then be done directly from that package by double-clicking on it in the File viewer.
