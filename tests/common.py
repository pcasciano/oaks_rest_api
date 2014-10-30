from django.contrib.auth.models import User

def setup_user():
    test_user = User.objects.create_user('test', email='testuser@test.com',
                                         password='test')
    test_user.save()
    user = User.objects.get(username='test')
    return user
