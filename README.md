# pollbot
Telegram poll bot - run all sorts of different polls, such as polls with multiple options, polls with different evaluation strategies, or polls where you can see who voted for what.

Check out the [official instance](https://t.me/polytope_bot) if all you want is to use this bot.

### But, Telegram has native polls now!
Yes, that's true. But this bot still has a few more features ;)

## Usage
Simply text the `/start` command to the bot and it will guide you through the creation of a new poll.

## Poll types

* __Basic poll:__ A straightforward first-past-the-post poll.
* __Subset poll:__ Lets you vote for any subset of the available options
* __Instant runoff poll:__ Lets you define an order of preference and picks the option which is preferred by most.
* __Instant runoff poll with fallback tie-breaking:__ Like instant runoff, but tries extra hard to break ties.
* __Open poll:__ Like basic poll, but you can see who voted for what.
* __Basic poll with custom description:__ Like basic poll, but lets you add a custom text to the poll message.
* __Single transferable vote poll:__ Similar to instant runoff, but multiple choices will be elected.
* __Open poll with custom description:__ Like open poll, but lets you add a custom text to the poll message.
* __Instant runoff poll with custom description:__ Like instant runoff, but with a custom description
* __Multiple options poll:__ Lets you vote for multiple options
* __Open multiple options poll:__ Lets you vote for multiple options, and people can see who voted for what.
* __Doodle:__ Lets you pick the preferred out of multiple options, with yes-no-ifneedbe answers


## Running it yourself

Since you're here on my Github, perhaps you wanted to run your own poll bot instance?
Feel free! Simply install the required python packages from `requirements.txt` and then create a config file for your bot.

The config file looks like this:
```
token: "123456789:ThisIsYourTelegramBotSecretToken1234"
db: "votes.db" 
```
The `db` entry is the path of the SQLite database in which debt information is stored. Provide a file name, and a sqlite file will automatically be created.
