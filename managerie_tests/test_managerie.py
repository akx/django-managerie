import pytest


@pytest.mark.django_db
def test_managerie(admin_client):
    assert 'Commands' in admin_client.get('/admin/').content.decode()
    chpw_content = admin_client.get('/admin/managerie/auth/changepassword/').content.decode()
    assert 'password for django.contrib.auth.' in chpw_content
    assert 'Verbosity' in chpw_content
    assert 'Username' in chpw_content
    assert 'Database' in chpw_content
