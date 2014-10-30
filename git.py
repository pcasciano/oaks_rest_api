from geogigpy import geogig
from geogigpy.repo import Repository
from django.conf import settings
from django_oaks_rest_api.models import ShapeFile
import os


class Git:
    """
    TODO::write some docs
    """
    def __init__(self, owner):
        self.geogig_dir = settings.GEOGIG_REPO+'/'+str(owner.id)

        if not os.path.exists(self.geogig_dir):
            #create repo
            self.repo = Repository(self.geogig_dir, init=True)
            self.repo.config(geogig.USER_NAME, owner.username)
            self.repo.config(geogig.USER_EMAIL, owner.email)
        else:
            #use existing repo
            self.repo = Repository(self.geogig_dir, init=False)

    def push(self, shp=None, commit_msg=None):
        """
        import (may take some time!) and commit uploaded shape file in repo
        """
        self.repo.importshp(shp)
        self.repo.add()
        self.repo.commit(message=commit_msg)

    def log(self):
        """
        log
        """
        log = self.repo.log()
        list_info = []
        for l in log:
            info = {
                'id': l.id,
                'date': l.committerprettydate(),
                'msg': l.message
            }
            list_info.append(info)

        return list_info
