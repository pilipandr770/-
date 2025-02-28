# Binance Trading Bot

This project is a trading bot for Binance that utilizes moving averages to make buy and sell decisions based on market trends. The bot is designed to automate trading on the Binance exchange using the Binance API.

## Project Structure

- `bot.py`: Contains the main logic for the trading bot, including functions for trading, calculating moving averages, and handling API interactions.
- `Dockerfile`: Used to build the Docker image for the bot. It specifies the base image, sets up the working directory, installs dependencies, and defines the command to run the bot.
- `docker-compose.yml`: Defines and runs multi-container Docker applications, specifying the services, networks, and volumes needed for the bot.
- `requirements.txt`: Lists the Python dependencies required for the bot, including libraries like `binance` and `requests`.

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd binance_bot
   ```

2. **Build the Docker Image**
   ```bash
   docker build -t binance_bot .
   ```

3. **Run the Bot using Docker Compose**
   ```bash
   docker-compose up
   ```

## Usage

- Ensure you have your Binance API key and secret set up in the environment variables or in a configuration file as required by the bot.
- The bot will automatically start trading based on the defined strategy using moving averages.

## Contributing

Feel free to submit issues or pull requests if you have suggestions or improvements for the bot.