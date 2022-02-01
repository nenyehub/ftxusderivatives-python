from rest.rest import LxClient
import pytest

api_key = ""  # TODO: Put your API key here


class TestRestApi:
    def test_list_contracts(self):
        client = LxClient(api_key=api_key)
        contracts = client.list_contracts({
            'active': True,
            'derivative_type': 'day_ahead_swap',
            'asset': 'CBTC'
        })
        data = contracts['data']
        assert data[0]['derivative_type'] == 'day_ahead_swap'
        assert data[0]['underlying_asset'] == 'CBTC'

    @pytest.mark.skip(reason="Not implemented.")
    def test_list_traded_contracts(self):
        raise NotImplementedError()

    def test_retrieve_contract(self):
        client = LxClient(api_key=api_key)
        contract_list = client.list_contracts({
            'active': True,
            'derivative_type': 'day_ahead_swap',
            'asset': 'CBTC'
        })
        data = contract_list['data']
        label = data[0]['label']
        contract_id = data[0]['id']

        contract = client.retrieve_contract(contract_id)
        assert contract['data']['id'] == contract_id
        assert contract['data']['label'] == label

    @pytest.mark.skip(reason="Not implemented.")
    def test_retrieve_position_for_contract(self):
        raise NotImplementedError()

    @pytest.mark.skip(reason="Not implemented.")
    def test_get_contract_ticker(self):
        raise NotImplementedError()

    @pytest.mark.skip(reason="Not implemented.")
    def test_list_positions(self):
        raise NotImplementedError()

    @pytest.mark.skip(reason="Not implemented.")
    def test_list_position_trades(self):
        raise NotImplementedError()

    @pytest.mark.skip(reason="Not implemented.")
    def test_list_trades(self):
        raise NotImplementedError()

    @pytest.mark.skip(reason="Not implemented.")
    def test_list_all_trades(self):
        raise NotImplementedError()

    @pytest.mark.skip(reason="Not implemented.")
    def test_list_open_orders(self):
        raise NotImplementedError()

    @pytest.mark.skip(reason="Not implemented.")
    def test_create_order(self):
        raise NotImplementedError()

    @pytest.mark.skip(reason="Not implemented.")
    def test_cancel_all_orders(self):
        raise NotImplementedError()

    @pytest.mark.skip(reason="Not implemented.")
    def test_cancel_single_order(self):
        raise NotImplementedError()

    @pytest.mark.skip(reason="Not implemented.")
    def test_cancel_and_replace(self):
        raise NotImplementedError()

    def test_get_contract_orderbook_state(self):
        client = LxClient(api_key=api_key)
        contract_list = client.list_contracts({
            'active': True,
            'derivative_type': 'day_ahead_swap',
            'asset': 'CBTC'
        })
        data = contract_list['data']
        contract_id = data[0]['id']

        book_state = client.get_contract_orderbook_state(contract_id)
        assert book_state['data']['contract_id'] == contract_id
