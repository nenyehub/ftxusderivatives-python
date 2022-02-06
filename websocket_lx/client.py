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
        self._book_tops: DefaultDict[int, List[float]] = defaultdict(lambda: [0, 0, 0, 0])
        self._reset_data()

    def _on_open(self, ws):
        self._reset_data()

    def _reset_data(self) -> None:
        self._subscriptions: Set[int] = set()
        self._orderbook_timestamps: DefaultDict[int, float] = defaultdict(float)
        self._orderbook_timestamps.clear()

    def _get_url(self) -> str:
        if self._api_key:
            return self._ENDPOINT + f"?token={self._api_key}"
        else:
            return self._ENDPOINT

    def subscribe(self, contract_id: int) -> None:
        """Subscribe to ticker information for a given contract."""
        self._subscriptions.add(contract_id)

    def unsubscribe(self, contract_id: int) -> None:
        """Unsubscribe from ticker information for a given contract."""
        self._subscriptions.remove(contract_id)

    def book_top(self, contract_id: int) -> List[int]:
        return self._book_tops[contract_id]

    def _handle_book_top_message(self, message: Dict) -> None:
        contract_id = message['contract_id']
        bid = message['bid']
        bid_size = message['bid_size']
        ask = message['ask']
        ask_size = message['ask_size']
        self._book_tops[contract_id] = [bid / 100, bid_size, ask / 100, ask_size]  # convert from cents to usd
        self._orderbook_timestamps[contract_id] = time.time()

    def _on_message(self, ws, raw_message: str) -> None:
        message = json.loads(raw_message)
        if 'type' not in message:
            return  # TODO: add handling for global state updates. track auth or unatuh status

        message_type = message['type']

        if message_type == 'book_top':
            if message['contract_id'] in self._subscriptions:
                self._handle_book_top_message(message)
