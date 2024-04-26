# Donate to Veterans

Donate to Veterans using Venmo. This was built during my first hackathon at HSHacks in 2023.

## setup

To setup the server environment, run `python -m venv .` in the root of the project. Then, execute `. ./bin/activate` and you should be in the virtual environment. Lastly, run `pip install flask venmo_api` to install all the dependencies. Now, exit using by running `exit`.

## running

To run the server, execute `./run.sh`.

## configuration

All configuration files are located in the `config` directory in the current working directory. They are used to preserve settings between server starts for convenience. Keep all the configuration files secret as they contain valuable information.

`access_token.txt` contains an access token used to access Venmo's API.

`email.txt` contains information about the sender's email. The sender's email will be used to send thank you emails to donators.
