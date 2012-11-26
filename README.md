#`delete-unused-en-tags`

The quick, destructive way to remove unused tags from your Evernote account.
=====================

## Requirements

This has been tested with Python 2.7.2 on Mac OS X 10.8.2. No guarantees what will happen if you use other versions of Python.

You'll be prompted for your dev token. You can enable (and retrieve) your dev token at this URL:

https://www.evernote.com/api/DeveloperToken.action

This application won't work without a developer token.

## Usage

Run `python main.py` with no arguments. Enter your dev token when prompted.

## Caveats

This software **will** delete tags from your account (assuming they're not attached to any notes). 

I really can't overstate this. Only use this if you know what you're doing. I won't be held responsible if this kills your cat and eats all of that chocolate cake in the fridge. 

To determine which tags are in use, it's necessary to retrieve the metadata about each note in your account. This can take time, so be patient. Also, this operation will occasionally time out, but the script knows what to do when that happens. If the operation times out more than five times, the script will exit. You can increase this threshold by increasing `MAX_TIMEOUTS`.

#### That said...

There are a couple of built-in sanity checks here:

`TEST` is a boolean constant defined at the top of the file. When it's set to `True`, no tags will be deleted. It's set to `True` by default, so if you want to actually remove unused tags from your account, set it to `False`.

`MAX_DELETE` is a numeric counter that can be used to limit the number of tags that can be deleted in a single run. If you don't want to use this "runaway freight train" failsafe, set it to `0`.