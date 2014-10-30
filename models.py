"""API Models for oaks_rest_api application"""
from django.db import models
from django.conf import settings
import binascii
import os
from hashlib import sha1

#required params for triplegeo
TGEO_PARAMS = {
    'name': 'name',
    'class': 'type',
    'target_store': 'GeoSparql',
    'ns_uri':'http://geoknow.eu/geodata#',
    'ontology_ns': 'http://www.opengis.net/ont/geosparql#',
    'ontology_ns_prefix': 'geo',
    'ignore': 'UNK'
}

TGEO_WKT_OBJECTS = (
    ('point', 'Point'),
    ('polygon', 'Polygon'),
    ('multipolygon', 'MultiPolygon'),
)

TGEO_LANGUAGES = (
    ('en', 'English'),
    ('it', 'Italian'),
)

TGEO_STORE_FORMATS = (
    ('rdf', 'RDF/XML'),
    ('n3', 'N3'),
    ('nt', 'N-TRIPLES'),
    ('ttl', 'TURTLE'),
)

class ShapeFile(models.Model):
    shp = models.FileField(upload_to=settings.UPLOAD_SHAPE, max_length=200)
    dbf = models.FileField(upload_to=settings.UPLOAD_SHAPE, max_length=200)
    shx = models.FileField(upload_to=settings.UPLOAD_SHAPE, max_length=200)
    prj = models.FileField(upload_to=settings.UPLOAD_SHAPE, max_length=200)

    owner = models.ForeignKey('auth.User', related_name='shapefiles')

    def delete(self, *args, **kwargs):
        self.dbf.delete()
        self.shp.delete()
        self.shx.delete()
        self.prj.delete()
        super(ShapeFile, self).delete(*args, **kwargs)


class TripleStore(models.Model):

    format_file = models.CharField(max_length=9, choices=TGEO_STORE_FORMATS, null=True)
    target_store = models.CharField(max_length=200,
                                    default=TGEO_PARAMS['target_store'], null=True)
    feature_string = models.CharField(max_length=200, blank=True, null=True)
    attribute = models.CharField(max_length=200, blank=True, null=True)
    type_wkt = models.CharField(max_length=12, choices=TGEO_WKT_OBJECTS, null=True, blank=True)
    name = models.CharField(max_length=200, default=TGEO_PARAMS['name'],
                            blank=True, null=True)
    class_store = models.CharField(max_length=200, default=TGEO_PARAMS['class'],
                                   blank=True, null=True)
    ns_prefix = models.CharField(max_length=200, blank=True, null=True)
    ns_URI = models.CharField(max_length=200, default=TGEO_PARAMS['ns_uri'],
                              blank=True, null=True)
    ontology_NS_prefix = models.CharField(
        max_length=200, default=TGEO_PARAMS['ontology_ns_prefix'], blank=True, null=True)
    ontology_NS = models.CharField(max_length=200,
                                   default=TGEO_PARAMS['ontology_ns'],
                                   blank=True, null=True)
    default_lang = models.CharField(max_length=2, choices=TGEO_LANGUAGES,
                                    blank=True, null=True)
    ignore = models.CharField(max_length=200, blank=True, null=True)
    source_RS = models.CharField(max_length=200, blank=True, null=True)
    target_RS = models.CharField(max_length=200, blank=True, null=True)
    input_file = models.CharField(max_length=400, blank=True, null=True)

    #output_file = models.CharField(max_length=400, blank=True)
    output_file = models.FileField(upload_to=settings.UPLOAD_TRIPLE_STORE,
                                   max_length=200, blank=True, null=True)

    shp = models.ManyToManyField(ShapeFile)

    owner = models.ForeignKey('auth.User', related_name='triplestores')

    def delete(self, *args, **kwargs):
        self.output_file.delete()
        super(TripleStore, self).delete(*args, **kwargs)


class UserDataLoadedEvents(models.Model):
    """
    This model contains every data loaded event.

    Contains associated message create by triplegeo/strabon,
    data loaded result and date.
    """
    user = models.ForeignKey('auth.User', related_name='user_data_loaded')
    message = models.TextField()
    loaded = models.BooleanField()
    created = models.DateTimeField()


class NodeToken(models.Model):
    """
    The node.js app server token authorization model.
    """
    key = models.CharField(max_length=40, primary_key=True)
    user = models.ForeignKey('auth.User', related_name='node_token')
    created = models.DateTimeField(auto_now_add=True)

    def __generate_key(self):
        return binascii.hexlify(os.urandom(20))

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.__generate_key()
        return super(NodeToken, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.key
