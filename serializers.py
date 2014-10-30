from rest_framework import serializers
from oaks_rest_api.models import ShapeFile, TripleStore
from django.core.validators import URLValidator
from django.contrib.auth.models import User

class ShapeFileSerializer(serializers.ModelSerializer):
    """
    shape file serializer
    """
    owner = serializers.Field(source='owner.username')

    class Meta:
        model = ShapeFile
        exclude = ('owner',)

    def validate(self, attrs):
        """
        validates shape file

        checking mimetypes and file names
        """
        """
        if not attrs['shp'].content_type == 'application/x-esri-shape':
            raise serializers.ValidationError("shp not valid.")
        if not attrs['shx'].content_type == 'application/x-esri-shape-index':
            raise serializers.ValidationError("shx not valid.")
        if not attrs['dbf'].content_type == 'application/x-dbf':
            raise serializers.ValidationError("dbf not valid.")
        """
        #validate shapefile name
        shp_name = attrs['shp'].name.split('.')[0]
        dbf_name = attrs['dbf'].name.split('.')[0]
        shx_name = attrs['shx'].name.split('.')[0]
        if not shp_name == dbf_name == shx_name:
            raise serializers.ValidationError('shape file not valid.')
        return attrs


class TripleStoreSerializer(serializers.ModelSerializer):
    shp = serializers.PrimaryKeyRelatedField(many=True)
    owner = serializers.Field(source='owner.username')

    class Meta:
        model = TripleStore
        exclude = ('owner', 'input_file', 'output_file')


    def __validate_uri(self, param, param_name):
        """
        validates uri param
        """
        url_validation = URLValidator()
        try:
            url_validation(param)
        except serializers.ValidationError, e:
            raise serializers.ValidationError(
                param_name+
                ' is not well-formed! Only absolute URIrefs can be included.')

    def validate(self, attrs):
        """
        validates uri params for rdf output format
        """
        if attrs['format_file'] == 'rdf':
            self.__validate_uri(attrs['ns_URI'], 'ns_URI')
            self.__validate_uri(attrs['ontology_NS'], 'ontology_NS')

        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    used by authentication system
    """
    shapefiles = serializers.PrimaryKeyRelatedField(many=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'shapefiles')
