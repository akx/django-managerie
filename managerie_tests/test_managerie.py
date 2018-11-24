import pytest


@pytest.mark.django_db
def test_managerie(admin_client):
    assert 'Commands' in admin_client.get('/admin/').content.decode()
    csup_content = admin_client.get('/admin/managerie/auth/createsuperuser/').content.decode()
    assert 'Used to create a superuser.' in csup_content
    assert 'Verbosity' in csup_content
    assert 'Username' in csup_content
    assert 'Database' in csup_content
