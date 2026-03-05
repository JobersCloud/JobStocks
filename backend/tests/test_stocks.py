"""Tests de endpoints de stocks: búsqueda, detalle, auth requerida."""
from unittest.mock import patch


class TestStocksAuth:
    def test_stocks_requires_auth(self, client):
        """GET /api/stocks sin autenticación devuelve 401."""
        response = client.get('/api/stocks')
        assert response.status_code == 401

    def test_stocks_search_requires_auth(self, client):
        """GET /api/stocks/search sin autenticación devuelve 401."""
        response = client.get('/api/stocks/search')
        assert response.status_code == 401

    def test_stocks_detail_requires_auth(self, client):
        """GET /api/stocks/<codigo> sin autenticación devuelve 401."""
        response = client.get('/api/stocks/ABC123')
        assert response.status_code == 401


class TestStocksEndpoints:
    @patch('controllers.stock_controller.StockController.get_all')
    def test_stocks_with_api_key(self, mock_get_all, client):
        """GET /api/stocks con API key válida funciona."""
        mock_get_all.return_value = []

        with patch('utils.auth.ApiKeyModel.validate') as mock_validate:
            mock_validate.return_value = {
                'user_id': 1,
                'username': 'testuser',
                'nombre': 'Test Key'
            }
            response = client.get('/api/stocks?connection=1',
                                  headers={'X-API-Key': 'test-key-123'})
            assert response.status_code == 200
