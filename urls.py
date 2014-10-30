from django.conf.urls import patterns, url, include
from rest_framework.urlpatterns import format_suffix_patterns
from oaks_rest_api import views

urlpatterns = patterns('',
    url(r'^oauth2/', include('provider.oauth2.urls', namespace='oauth2')),
    url(r'^v1/geo/api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),

    url(r'^v1/geo/data/$', views.Data.as_view()),


    url(r'^v1/geo/data/shapes/$', views.ShapeList.as_view()),
    url(r'^v1/geo/data/shapes/(?P<pk>[0-9]+)/$', views.ShapeDetail.as_view()),

    url(r'^v1/geo/data/triple-stores/$', views.TripleStoreList.as_view()),
    url(r'^v1/geo/data/triple-stores/(?P<pk>[0-9]+)/$',
        views.TripleStoreDetail.as_view()),

    url(r'^v1/geo/data/(?P<name>[a-z0-9-_]+)/$', views.DownloadFile.as_view()),

    url(r'^v1/geo/shape-convert/$', views.ShapeConvert.as_view()),

    url(r'^v1/geo/gitlog/$', views.GitLog.as_view()),

    url(r'^v1/geo/users/$', views.UserList.as_view()),
    url(r'^v1/geo/users/(?P<pk>[0-9]+)/$', views.UserDetail.as_view()),

    url(r'^v1/geo/current-user/$', views.CurrentUser.as_view())


)

urlpatterns = format_suffix_patterns(urlpatterns)
