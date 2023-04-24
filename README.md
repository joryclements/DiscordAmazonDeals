# DiscordAmazonDeals

DiscordAmazonDeals is a Discord bot that makes it easy for users to add, manage, and track Amazon items. It monitors the price of specified products and sends notifications via Discord whenever there's a change. Using Python, this bot simplifies price tracking and saves you time and effort.
<img width="328" alt="Screenshot 2023-04-24 at 11 27 46 AM" src="https://user-images.githubusercontent.com/70959739/234046724-eb32b2a6-0867-4be8-88ea-51165257c4fb.png">


## Features
- Add and remove Amazon items for tracking
- Manage tracked items with ease
- Receive real-time price change notifications on Discord
- Customizable notification settings
- Supports multiple users and servers

<img width="1169" alt="Screenshot 2023-04-24 at 11 28 24 AM" src="https://user-images.githubusercontent.com/70959739/234046767-b36be152-abdc-4cb0-a160-371ddf796f07.png">
<img width="447" alt="Screenshot 2023-04-24 at 11 37 43 AM" src="https://user-images.githubusercontent.com/70959739/234046768-f8be5d3f-7382-470f-9bef-a1ed3f8c19ee.png">


## Getting Started
These instructions will help you set up a local copy of the project and run it on your machine.

### Prerequisites

Before cloning the repository, ensure you have Python installed on your device. If not, follow the official guide below to install it:

- [Python](https://www.python.org/downloads/)

Additionally, you'll need a Discord account and server to which you can add the bot. Create a new bot and generate a token using the following guide:

- [Creating a Discord bot](https://discordpy.readthedocs.io/en/stable/discord.html)

### Installation
1. Clone the repository using git: `git clone https://github.com/joryclements/DiscordAmazonDeals`
2. Change into the project directory and install the required dependencies by running the following commands: `cd DiscordAmazonDeals/  && pip install -r requirements.txt`
3. Update the `settings.env` file with your Discord bot token and list of allowed guilds.

## Running the Discord Bot
Once the dependencies have been installed and the configuration file updated, you can run the bot with the following command: `python bot.py`

## Built With
* Python 
* Discord.py - An API wrapper for Discord written in Python
