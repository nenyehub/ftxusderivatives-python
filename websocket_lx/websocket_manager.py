import json
import time
from threading import Thread, Lock
import logging
from logging import Logger

from websocket import WebSocketApp

# TODO: Replace print statements with logging.


class WebsocketManager:
    _CONNECT_TIMEOUT_S = 5
    _ENDPOINT = None

    def __init__(self):
        self.connect_lock = Lock()
        self.ws = None
        self._logger: Logger = logging.getLogger('root')  # TODO: Integrate this with setup_custom_logger

    def _get_url(self):
        raise NotImplementedError()

    def _on_message(self, ws, message):
        raise NotImplementedError()

    def send(self, message):
        self.connect()
        self.ws.send(message)

    def send_json(self, message):
        self.send(json.dumps(message))

    def _connect(self):
        assert not self.ws, "ws should be closed before attempting to connect"

        self.ws = WebSocketApp(
            self._get_url(),
            on_message=self._wrap_callback(self._on_message),
            on_close=self._wrap_callback(self._on_close),
            on_error=self._wrap_callback(self._on_error),
        )

        wst = Thread(target=self._run_websocket, args=(self.ws,))
        wst.daemon = True
        wst.start()

        # Wait for socket to connect
        ts = time.time()
        while self.ws and (not self.ws.sock or not self.ws.sock.connected):
            if time.time() - ts > self._CONNECT_TIMEOUT_S:
                self.ws = None
                return

    def _wrap_callback(self, f):
        def wrapped_f(ws, *args, **kwargs):
            if ws is self.ws:
                try:
                    f(ws, *args, **kwargs)
                except Exception as e:
                    raise Exception(f'Error running websocket callback: {e}')
        return wrapped_f

    def _run_websocket(self, ws: WebSocketApp) -> None:
        try:
            ws.run_forever(ping_interval=15)
        except Exception as e:
            raise Exception(f'Unexpected error while running websocket: {e}')
        finally:
            self._logger.debug("Error occurred. Function will return.")

    def _reconnect(self, ws: WebSocketApp) -> None:
        assert ws is not None, '_reconnect should only be called with an existing ws'
        if ws is self.ws:
            self.ws = None
            ws.close()
            self.connect()

    def close(self):
        if self.ws:
            self.ws.close()

    def connect(self) -> None:
        if self.ws:
            return
        with self.connect_lock:
            while not self.ws:
                self._connect()
                if self.ws:
                    self._logger.info(f"Connection with URL: {self._ENDPOINT}")
                    return

    def _on_close(self, ws: WebSocketApp, code, raw_msg) -> None:
        self._logger.debug(f"LedgerX: WebSocket connection closed: Code: {code}, Msg: {raw_msg}")
        if code:
            self._logger.debug("LedgerX: WebSocket reconnecting...")
            self._reconnect(ws)  # Only reconnect if there is an error code.

    def _on_error(self, ws: WebSocketApp, error) -> None:  # TODO: Add type hint for 'error'...
        self._logger.debug(f"LedgerX: WebSocket Error: {error}")
        self._reconnect(ws)

    def reconnect(self) -> None:
        if self.ws is not None:
            self._reconnect(self.ws)
