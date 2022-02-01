"""
LedgerX REST Client.
"""

from typing import Optional, Dict, Any
from requests import Request, Session, Response


class LxClient:
    _ENDPOINT = "https://api.ledgerx.com/"
    _TRADE_ENDPOINT = "https://trade.ledgerx.com/api/"

    def __init__(self, api_key=None) -> None:
        """Initializes LedgerX client with API key and http session."""
        self._session = Session()
        self._api_key = api_key

    def _get(self, path: str, use_trade_api: bool = False, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, use_trade_api, params=params)

    def _post(self, path: str, use_trade_api: bool = False, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, use_trade_api, json=params)

    def _delete(self, path: str, use_trade_api: bool = False, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, use_trade_api, json=params)

    def _request(self, method: str, path: str, use_trade_api: bool, **kwargs) -> Any:
        endpoint = self._ENDPOINT
        if use_trade_api:
            endpoint = self._TRADE_ENDPOINT
        request = Request(method, endpoint + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())  # TODO: investigate req prepare
        return self._process_response(response)

    def _sign_request(self, request: Request) -> None:
        """Includes API Key in request headers."""
        prepared = request.prepare()  # TODO: investigate req prepare
        request.headers['Authorization'] = f'JWT {self._api_key}'

    def _process_response(self, response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise  # TODO: investigate raise
        else:
            return data  # return successful query response

    # REST API Functions

    def list_contracts(self, params: Optional[Dict[str, Any]] = None) -> dict:
        """Returns a list of contracts.
        https://docs.ledgerx.com/reference/listcontracts

        Args:
            params: dict
                Query parameters, {'param_name': value} pairings.

        Returns:
            contracts: dict
                List of contracts.
        """
        return self._get('trading/contracts', use_trade_api=False, params=params)

    def list_traded_contracts(self, params: Optional[Dict[str, Any]] = None) -> dict:
        """Returns a list of contracts that you have traded.
        https://docs.ledgerx.com/reference/tradedcontracts

        Args:
            params: dict
                Query parameters, {'param_name': value} pairings.

        Returns:
            contracts: dict
                List of contracts.
        """
        return self._get('trading/contracts/traded', use_trade_api=False, params=params)

    def retrieve_contract(self, contract_id: int) -> dict:
        """Returns contract details for a single contract ID.
        https://docs.ledgerx.com/reference/retrievecontract

        Args:
            contract_id: int
                ID of record to fetch.

        Returns:
            contract: dict
                Contract details.
        """
        return self._get(f'trading/contracts/{contract_id}', use_trade_api=False)

    def retrieve_contract_position(self, contract_id: int) -> dict:
        """Returns your position for a given contract.
        https://docs.ledgerx.com/reference/positioncontract

        Args:
            contract_id: int
                ID of record to fetch.

        Returns:
            position: dict
                Position details.
        """
        return self._get(f'trading/contracts/{contract_id}/position', use_trade_api=False)

    def get_contract_ticker(self, contract_id: int, params: Optional[Dict[str, Any]] = None) -> dict:
        """Snapshot information about the current best bid/ask, 24h volume, and last trade.
        https://docs.ledgerx.com/reference/contractticker

        Args:
            contract_id: int
                ID of record to fetch.
            params: dict
                Query parameters, {'param_name': value} pairings.

        Returns:
            ticker: dict
                Ticker information for the specified contract. All prices in cents.
        """
        return self._get(f'trading/contracts/{contract_id}/ticker', use_trade_api=False, params=params)

    def list_positions(self, params: Optional[Dict[str, Any]] = None) -> dict:
        """Returns all your positions.
        https://docs.ledgerx.com/reference/listpositions

        Args:
            params: dict
                Query parameters, {'param_name': value} pairings.

        Returns:
            contracts: dict
                List of positions.
        """
        return self._get('trading/positions', use_trade_api=False, params=params)

    def list_position_trades(self, contract_id: int, params: Optional[Dict[str, Any]] = None) -> dict:
        """Returns a list of your trades for a given position.
        https://docs.ledgerx.com/reference/tradesposition

        Args:
            contract_id: int
                ID of record to fetch.
            params: dict
                Query parameters, {'param_name': value} pairings.

        Returns:
            trades: dict
                List of trades.
        """
        return self._get(f'trading/positions/{contract_id}/trades', use_trade_api=False, params=params)

    def list_trades(self, params: Optional[Dict[str, Any]] = None) -> dict:
        """Returns a list of your trades.
        https://docs.ledgerx.com/reference/listtrades

        Args:
            params: dict
                Query parameters, {'param_name': value} pairings.

        Returns:
            trades: dict
                List of trades.
        """
        return self._get('trading/trades', use_trade_api=False, params=params)

    def list_all_trades(self, params: Optional[Dict[str, Any]] = None) -> dict:
        """Returns a list of all trades in the market.
        https://docs.ledgerx.com/reference/globalstrade

        Args:
            params: dict
                Query parameters, {'param_name': value} pairings.

        Returns:
            trades: dict
                List of trades.
        """
        return self._get('trading/trades/global', use_trade_api=False, params=params)

    def list_transactions(self, params: Optional[Dict[str, Any]] = None) -> dict:
        """Returns a list of all debits and credits to your accounts.
        https://docs.ledgerx.com/reference/gettransactions

        Args:
            params: dict
                Query parameters, {'param_name': value} pairings.

        Returns:
            transactions: dict
                List of transactions.
        """
        return self._get('funds/transactions', use_trade_api=False, params=params)

    def list_open_orders(self) -> dict:
        """Get all resting limit orders directly from the exchange.
        https://docs.ledgerx.com/reference/open-orders

        Returns:
            orders: dict
                Returns a list of your open orders.
        """
        return self._get('open-orders', use_trade_api=True)

    def create_order(self,
                     order_type: str,
                     contract_id: int,
                     is_ask: bool,
                     swap_purpose: str,
                     size: int,
                     price: int,
                     volatile: Optional[bool] = False) -> dict:
        """Place an order.
        https://docs.ledgerx.com/reference/create-order

        Returns:
            message_id: dict
                Returns the message id, or mid, of the order.
        """
        return self._post('orders', use_trade_api=True, params={
            'order_type': order_type,
            'contract_id': contract_id,
            'is_ask': is_ask,
            'swap_purpose': swap_purpose,
            'size': size,
            'price': price,
            'volatile': volatile
        })

    def cancel_all_orders(self) -> str:
        """Delete all outstanding orders associated with your MPID (the whole organization).
        https://docs.ledgerx.com/reference/cancel-all

        Returns:
            response_code: str
                200 Success, 400 Bad Request
        """
        return self._delete('orders', use_trade_api=True)

    def cancel_single_order(self, message_id: str, contract_id: int) -> str:
        """Cancel a single resting limit order.
        https://docs.ledgerx.com/reference/cancel-single

        Args:
            message_id: str
                The message id (mid) of the original order.
            contract_id: int
                The contract ID of the original order.

        Returns:
            response_code: str
                200 Success, 400 Bad Request
        """
        return self._delete(f'orders/{message_id}', use_trade_api=True, params={'contract_id': contract_id})

    def cancel_and_replace(self, message_id: str, contract_id: str, price: int, size: int) -> str:
        """Atomically swap an existing resting limit order with a new resting limit order. Price, side, and size may be changed.
        https://docs.ledgerx.com/reference/cancel-replace

        Args:
            message_id: str
                The message ID (mid) of the original order.
            contract_id: str
                The contract ID of the original order (cannot be changed in a cancel-replace).
            price: int
                The limit price of the new order in cents (USD) per contract. Must be a whole dollar amount.
            size: int
                How many units of the contract to transact for the new order.

        Returns:
            response_code: str
                200 Success, 400 Bad Request
        """
        return self._post(f'orders/{message_id}/edit', use_trade_api=True, params={
            'contract_id': contract_id,
            'price': price,
            'size': size
        })

    def get_contract_orderbook_state(self, contract_id: int):
        """Atomically swap an existing resting limit order with a new resting limit order. Price, side, and size may be changed.
        https://docs.ledgerx.com/reference/book-state-contract

        Args:
            contract_id: str
                The contract ID of the original order (cannot be changed in a cancel-replace).

        Returns:
            response_code: str
                200 Success, 400 Bad Request
        """
        return self._get(f'book-states/{contract_id}', use_trade_api=True)
