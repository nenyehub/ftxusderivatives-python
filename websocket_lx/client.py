import json
from collections import defaultdict
from typing import DefaultDict, List, Dict, Set
import time

from websocket_lx.websocket_manager import WebsocketManager


class LxWebsocketClient(WebsocketManager):
    _ENDPOINT = 'wss://api.ledgerx.com/ws'

    def __init__(self, api_key: str = None) -> None:
        super().__init__()
        self._api_key = api_key
        self._initial_open_order_count = 0
        self._reset_data()

    def _on_open(self, ws):
        self._reset_data()

    def _reset_data(self) -> None:
        self._subscriptions: Set[int] = set()
        self._orderbook_timestamps: DefaultDict[int, float] = defaultdict(float)
        self._book_tops: DefaultDict[int, List[float]] = defaultdict(lambda: [0, 0, 0, 0])
        self._open_positions: DefaultDict[int, Dict[str, int]] = defaultdict(dict)
        self._account_balances: DefaultDict[str, Dict[str, float]] = defaultdict(dict)
        self._last_heartbeat_timestamp: int = 0  # Nanosecond timestamp

        self._subscriptions.clear()
        self._orderbook_timestamps.clear()
        self._book_tops.clear()
        self._open_positions.clear()
        self._account_balances.clear()

    def _get_url(self) -> str:
        if self._api_key:
            return self._ENDPOINT + f"?token={self._api_key}"
        else:
            return self._ENDPOINT

    def subscribe(self, contract_id: int) -> None:
        """Subscribe to orderbook tops for a given contract."""
        self._logger.info(f"LedgerX: Subscribed to orderbook top for contract_id: {contract_id}")
        self._subscriptions.add(contract_id)

    def unsubscribe(self, contract_id: int) -> None:
        """Unsubscribe from orderbook tops for a given contract."""
        self._logger.info(f"LedgerX: Unsubscribed from orderbook tops for contract_id: {contract_id}")
        self._subscriptions.remove(contract_id)

    def get_last_heartbeat_timestamp(self):
        return self._last_heartbeat_timestamp

    def get_book_top(self, contract_id: int) -> List[float]:
        """Returns the best [bid, bid_size, ask, ask_size] for a given contract_id."""
        return self._book_tops[contract_id]

    def get_book_timestamp(self, contract_id: int) -> float:
        """Returns local-time timestamp of last orderbook update for a given contract."""
        return self._orderbook_timestamps[contract_id]

    def get_open_position(self, contract_id: int) -> Dict:
        """Returns open position info for a given contract_id.
        https://docs.ledgerx.com/reference/market-data-feed#open_positions_update
        """
        return self._open_positions[contract_id]

    def get_account_balances(self) -> Dict:
        """Returns account balances.
        https://docs.ledgerx.com/reference/market-data-feed#collateral_balance_update
        """
        return self._account_balances

    def _handle_state_manifest_message(self, message: Dict) -> None:
        self._initial_open_order_count = message['state_manifest']['open_order_count']
        self._logger.debug(f"LedgerX: Open Orders: {self._initial_open_order_count}")

    def _handle_open_positions_update_message(self, message: Dict) -> None:
        for position in message['positions']:
            contract_id = position['contract_id']
            del position['contract_id']
            self._open_positions.update({contract_id: position})

    def _handle_collateral_balance_message(self, message: Dict) -> None:
        """Updates account collateral balances."""
        def convert_units(symbol, value):
            """Converts from cents, satoshis, and gweis to dollars, BTC, and ETH respectively."""
            if symbol == 'USD':
                return value / 100
            elif symbol in ['BTC', 'CBTC']:
                return value / 10**8
            elif symbol == 'ETH':
                return value / 10**9

        # Convert currency units to USD, BTC, and ETH and update account balances.
        balances = message['collateral']
        for key in balances.keys():
            self._account_balances.update(
                {
                    key: {symbol: convert_units(symbol, value) for symbol, value in balances[key].items()}
                }
            )

        # TODO: Log account balances changed.

    def _handle_book_top_message(self, message: Dict) -> None:
        contract_id = message['contract_id']
        bid = message['bid']
        bid_size = message['bid_size']
        ask = message['ask']
        ask_size = message['ask_size']
        self._book_tops[contract_id] = [bid / 100, bid_size, ask / 100, ask_size]  # convert from cents to usd
        self._orderbook_timestamps[contract_id] = time.time()

    def _handle_heartbeat_message(self, message: Dict) -> None:
        """Records local-time of last received server heartbeat."""
        self._last_heartbeat_timestamp = time.time_ns()

    def _on_message(self, ws, raw_message: str) -> None:
        message = json.loads(raw_message)
        if 'type' not in message:
            return  # TODO: add handling for global state updates. track auth or unatuh status

        message_type = message['type']

        # Initial connection message. Includes open order count.
        if message_type == 'state_manifest':
            self._handle_state_manifest_message(message)

        # Account State Update: Updated list of account positions on all currently active contracts.
        if message_type == 'open_positions_update':
            self._handle_open_positions_update_message(message)

        # Account State Update: Current collateral balances.
        if message_type == 'collateral_balance_update':
            self._handle_collateral_balance_message(message)

        # Top of Book Feed: Top-of-orderbook for a given contract_id.
        if message_type == 'book_top':
            if message['contract_id'] in self._subscriptions:
                self._handle_book_top_message(message)

        # Exchange heartbeat. Monitors exchange life.
        if message_type == 'heartbeat':
            self._handle_heartbeat_message(message)
