# ftxusderivatives-python
An unofficial Python wrapper for the [REST API](https://docs.ledgerx.com/reference/overview) of FTX US Derivatives, formerly known as LedgerX. I have no affiliation with FTX US Derivatives. Use this at your own risk.

## Features
- Implementation of all REST endpoints, detailed [here](https://docs.ledgerx.com/reference/overview)
- Simple handling of authentication

## Quick Start
[Register an account with FTX US Derivatives.](https://derivs.ftx.us/)

[Generate an API key](https://docs.ledgerx.com/docs/api-key) and configure permissions.

Clone the repository to your target directory. 

To run unit tests, enter your API key in the test file: `tests/test_rest_api.py`, and run `python -m pytest` in the project directory.

Here's some example code to get started with. 
```python
from rest.rest import LxClient

api_key = ""  # Put API key here
client = LxClient(api_key)

# list active swap contracts
swaps = client.list_contracts({  
	'active': True,  
	'derivative_type': 'day_ahead_swap',
})

# grab BTC next-day-swap contract ID
data = swaps['data']  
cbtc_swap = filter(lambda data: data['underlying_asset'] == 'CBTC', data)  
contract_id = next(cbtc_swap)['id']

# retrieve your position for a given contract
position = client.retrieve_contract_position(contract_id)

# get contract ticker
ticker = client.get_contract_ticker(contract_id)
```
## Under Development
 - WebSocket support w/ orderbook state machine 
 - Position PnL tracker

## Contributing 
Contributions, fixes, recommendations, and all other feedback is welcome. If you are fixing a bug, please open an issue first with all relevant details, and mention the issue number in the pull request.

### Contact 
I can be reached on discord at Nenye#5335. Otherwise, feel free to open a PR or Issue here.
