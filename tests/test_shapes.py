from rest_framework.test import APITestCase
from rest_framework.test import APIRequestFactory, APIClient, \
    force_authenticate
from oaks_rest_api.views import ShapeList
from oaks_rest_api.tests.common import setup_user
import os
#from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
#import StringIO
from django.test.client import encode_multipart, RequestFactory

#def get_temp_file():
#    io = StringIO.StringIO()

class TestShapesViews(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.view = ShapeList.as_view()
        self.user = setup_user()
        self.uri = '/v1/geo/data/shapes/'


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


    def test_post_shape_file(self):
        """
        testing upload a shape file
        """
        path = os.path.dirname(os.path.realpath(__file__))

        shp = open(path+'/points.shp', 'rb')
        dbf = open(path+'/points.dbf', 'rb')
        shx = open(path+'/points.shx', 'rb')



        params = {
            'shp': SimpleUploadedFile(
            name=shp.name, content=shp.read(), content_type='application/x-esri-shape'),
                  'dbf': SimpleUploadedFile(
                      name=dbf.name, content=dbf.read(),
                      content_type='application/x-dbf'),
                  'shx': SimpleUploadedFile(
                      name=shx.name, content=shx.read(),
                      content_type='application/x-esri-shape-index'),

                  'format_file': 'nt',
                  'class_store': 'type',
                  'name': 'point',
                  'attribute': 'osm_id',
                  'target_store': 'GeoSparql',
                  'ontology_NS_prefix': 'geo',
                  'ignore': 'UNK',
                  'ns_URI': 'http://www.opengis.net/ont/geosparql',
                  'ontology_NS': 'http://www.opengis.net/ont/geosparql',
                  'source_RS': '',
                  'target_RS': '',
                  'ns_prefix': '',
                  'default_lang': 'en',
                  'feature_string': 'points',
                  'input_file': 'ppp',
                  'output_file': 'points',
                  'type_wkt': 'point',


        }

        shp.close()
        shx.close()
        dbf.close()

        #content = encode_multipart('test', params)

       # print content


        request = self.factory.post(self.uri, params)
        #request = self.factory.post(self.uri, content
        #                            ,content_type='multipart/form-data; boundary=test')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        response.render()

        self.assertEqual(response.status_code, 201,
            'Expected Response Code 201, received {0} instead.'
                         .format(response.status_code))
