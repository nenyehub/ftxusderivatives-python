"""
LedgerX REST Client.
"""

from typing import Optional, Dict, Any, Tuple
from requests import Request, Session
from requests.exceptions import HTTPError, Timeout
import logging
from logging import Logger
import time
import json


class LxClient:
    _ENDPOINT = "https://api.ledgerx.com/"
    _TRADE_ENDPOINT = "https://trade.ledgerx.com/api/"

    def __init__(self, api_key=None) -> None:
        """Initializes LedgerX client with API key, http session, and logger."""
        self._session: Session = Session()
        self._api_key: str = api_key
        self._logger: Logger = logging.getLogger('root')  # TODO: Integrate this with setup_custom_logger
        self._retries = 0
        self._MAX_RETRIES = 3

    ############################################
    # HTTP Requests and Error Handling
    ############################################

    def _get(self, path: str, use_trade_api: bool = False, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, use_trade_api, params=params)

    def _post(self, path: str, use_trade_api: bool = False, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, use_trade_api, json=params)

    def _delete(self, path: str, use_trade_api: bool = False, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, use_trade_api, json=params)

    def _sign_request(self, request: Request) -> None:
        """Includes API Key in request headers."""
        if self._api_key:
            request.headers['Authorization'] = f'JWT {self._api_key}'

    def _request(self, method: str, path: str, use_trade_api: bool, **kwargs) -> Any:
        endpoint = self._ENDPOINT
        if use_trade_api:
            endpoint = self._TRADE_ENDPOINT
        url = endpoint + path
        request = Request(method, url, **kwargs)
        self._sign_request(request)
        prepared = request.prepare()
        response = self._session.send(prepared)

        # Request retry function.
        def retry():
            self._retries += 1
            if self._retries > self._MAX_RETRIES:
                raise Exception("Max retries on %s hit, raising. \n" % path +
                                "Request Parameters: % s \n" % json.dumps(kwargs) +
                                "Full url: %s" % url)
            else:
                return self._request(method, path, use_trade_api, **kwargs)

        # Response error-handling
        try:
            # Make non-200s throw
            response.raise_for_status()

        except HTTPError as e:
            # 400 - Bad Request.
            if response.status_code == 400:
                self._logger.error("400 bad request.")
                error = response.json()['error']

                if error == 'INVALID_TOKEN':
                    self._logger.error("API key incorrect or expired. Please check and restart.")
                    self._logger.error("Error: " + response.text)

                else:
                    self._logger.error("Error: " + response.text)

                exit(1)  # TODO: Replace all exit(1) calls w/ Exception classes

            # 401 - Unauthorized.
            if response.status_code == 401:
                self._logger.error("API Key unauthorized to perform the requested action.")
                self._logger.error("Error: " + response.text)
                exit(1)

            # 404 - Not Found.
            elif response.status_code == 404:
                self._logger.error("Unable to contact the LedgerX API (404)" +
                                   "Request: %s" % url)
                exit(1)

            # 429, Too Many Requests (ratelimit). Cancel orders & wait until rate limit reset.
            elif response.status_code == 429:
                self._logger.error("Ratelimited on current request. Sleeping, then trying again. " +
                                   "Try fewer order pairs. " +
                                   "Request: %s" % url)

                # Figure out how long we need to wait.
                sleep_time = int(response.headers['Retry-After'])  # seconds to wait.

                # Cancel orders.
                self._logger.warning("Canceling all orders.")
                self.cancel_all_orders()

                self._logger.error("Ratelimit will reset in %d seconds. Sleeping for %d seconds." % (sleep_time,
                                                                                                     sleep_time))
                time.sleep(sleep_time)

                # Retry the request
                return retry()

            # 503 - Service Unavailable. LedgerX temporary downtime.
            elif response.status_code == 503:
                self._logger.warning("Unable to contact the LedgerX API (503), retrying in 3 seconds. " +
                                     "Request: %s" % url)
                time.sleep(3)
                return retry()

            # If we haven't returned or re-raised yet, we get here.
            self._logger.error("Unhandled Error: %s: %s" % (e, response.text))
            self._logger.error("Endpoint was (%s)\n" % method +
                               "path was (%s):\n" % path +
                               "Request Parameters: %s" % json.dumps(kwargs))
            exit(1)

        except Timeout as e:
            # Timeout, re-run this request
            self._logger.warning("Timed out on request: %s" % url +
                                 "Keyword args: % s" % json.dumps(kwargs))
            return retry()

        # TODO: add ConnectionError retry logic

        # Reset retry counter on success
        self._retries = 0

        return response.json()

    ############################################
    # REST API Functions
    ############################################

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

    def get_account_balances(self) -> None:
        """Retrieves account balances. This is DEPRECATED, use WebSockets for account balance information instead."""
        return self._get('balance', use_trade_api=True)

