# Overview
A bot for tracking Amazon prices right in Discord!
Keep track of your favorite products and get notified when they go on sale via Discord direct messages.
More features coming soon! (e.g. price history, price graphs, etc.) Have a feature request? Open an issue!

# Installation
`pip3 install -r requirements.txt` to install dependencies.

You will also need a Discord bot token. You can get one [here](https://discordapp.com/developers/applications).

# Configuration
There is a `settings.env` file that you must fill out with your own information.
* `DISCORD_API_KEY` - Your Discord bot token
* `ALLOWED_GUILDS` - The guild ID of your Discord server(s) (separated by commas if multiple)
* `SQLITE_DB_PATH` - The path to your SQLite database file (e.g. `./amazon.db`)

# Usage
### Starting the Bot
`python3 main.py` to start the bot.

### Commands - Admin Management
Coming Soon 

### Commands -  Product Management
* `/amzn track <url>` - Add a product to the database, where `<url>` is the Amazon product URL
* `/az view_products` - List all your saved products
