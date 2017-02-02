## Serveralerts

Serveralerts is a script I wrote to help me manage a number of caching servers.

For some reason, Apple do not provide a method to add/remove/list email addresses that are
configured in the Alerts DB of Server.app

So this tool interacts with that database, and creates it if needed.

# Usage

```
# ./serveralerts.py 
Usage: serveralerts.py [options] arg1

Options:
  -h, --help            show this help message and exit
  -l, --list            List all current email recipients.
  -c, --create          Create the alertDB if it does not already exist.
  -a ADD, --add=ADD     Add an email address. Pass the new email address as
                        arg1
  -r REMOVE, --remove=REMOVE
                        Remove an email address. Pass the email to remove as
                        arg1
```

# Examples
```
./serveralerts.py --add john@pretendco.com

./serveralerts.py --remove john@pretendco.com
```


# Requirements
Server.app 5.1.5 or higher.