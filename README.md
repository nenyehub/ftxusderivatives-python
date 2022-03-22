# ftxusderivatives-python
An unofficial Python wrapper for the [REST and WebSocket APIs](https://docs.ledgerx.com/reference/overview) of FTX US Derivatives, formerly known as LedgerX. I have no affiliation with FTX US Derivatives. Use this at your own risk.

## Features
- Implementation of all REST endpoints, detailed [here](https://docs.ledgerx.com/reference/overview)
- WebSocket implementation: live orderbook tops, account balances, open positions info, server heartbeat, reconnect logic
- Simple handling of authentication
- HTTP request error handling and retry logic
- Logging support

## Quick Start
[Register an account with FTX US Derivatives.](https://derivs.ftx.us/) *[optional]*

[Generate an API key](https://docs.ledgerx.com/docs/api-key) and configure permissions. *[optional]*

Install ftxusderviatives-python: `pip install ftxusderivatives-python`

Here's some example code to get started with. Note that API calls required authentication will not work if you do not
enter your API key.

```python
###############################
# REST API Example
###############################
from rest_lx.rest import LxClient

api_key = ""  # TODO: Put API key here

# Init REST client
client = LxClient(api_key=api_key)

# list active day-ahead-swap contracts
swaps = client.list_contracts({
    'active': True,
    'derivative_type': 'day_ahead_swap',
})

# grab BTC day-ahead-swap contract ID
data = swaps['data']
cbtc_swap = filter(lambda data: data['underlying_asset'] == 'CBTC', data)
contract_id = next(cbtc_swap)['id']
print(f"BTC swap contract_id: {contract_id}")

# retrieve your position for BTC day-ahead-swap contract
position = client.retrieve_contract_position(contract_id)
print(f"BTC swap position: {position}")

# get BTC day-ahead-swap contract ticker
ticker = client.get_contract_ticker(contract_id)
print(f"BTC swap ticker: {ticker}")

###############################
# WebSocket Example
###############################
from websocket_lx.client import LxWebsocketClient
import time

# Init WebSocket client
ws = LxWebsocketClient(api_key=api_key)

# Subscribe to orderbook-top feed for BTC day-ahead-swap contract
ws.subscribe(contract_id=contract_id)
ws.connect()

# Grab orderbook-top for BTC day-ahead-swap once a second
while True:
    top = ws.get_book_top(contract_id=contract_id)
    print(top)
    time.sleep(1)
```

## Contributing 
Contributions, fixes, recommendations, and all other feedback is welcome. If you are fixing a bug, please open an issue first with all relevant details, and mention the issue number in the pull request.

### Contact 
I can be reached on discord at Nenye#5335, or through email at nenye@ndili.net. Otherwise, feel free to open a PR or Issue here.
