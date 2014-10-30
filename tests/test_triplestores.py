from rest_framework.test import APITestCase
from rest_framework.test import APIRequestFactory, APIClient, \
    force_authenticate
from oaks_rest_api.views import TripleStoreList
from oaks_rest_api.tests.common import setup_user


class TestTripleStoresView(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.user = setup_user()
        self.view = TripleStoreList.as_view()
        self.uri = '/v1/geo/data/triple-stores/'

    def test_not_authenticated_uri(self):
        """
        not authorized access not allowed
        """
        request = self.factory.get(self.uri)
        response = self.view(request)
        response.render()
        self.assertEqual(response.status_code, 401,
            'Expected Response Code 401, received {0} instead.'
                         .format(response.status_code))

    def test_authenticated_uri(self):
        """
        ensure that uri is authorized access only
        """
        request = self.factory.get(self.uri)
        force_authenticate(request, self.user)
        response = self.view(request)
        response.render()
        self.assertEqual(response.status_code, 200,
            'Expected Response Code 200, received {0} instead.'
                         .format(response.status_code))

    def test_post(self):
        """
        testing upload a triple store file
        """
        pass
