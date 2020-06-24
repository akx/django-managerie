import json
from html import unescape

import pytest
from django.utils.crypto import get_random_string


@pytest.mark.django_db
def test_managerie(admin_client):
    assert 'Commands' in admin_client.get('/admin/').content.decode()
    csup_content = admin_client.get('/admin/managerie/auth/createsuperuser/').content.decode()
    assert 'Used to create a superuser.' in csup_content
    assert 'Verbosity' in csup_content
    assert 'Username' in csup_content
    assert 'Database' in csup_content
    all_commands_content = admin_client.get('/admin/managerie/').content.decode()
    assert 'Mg Test Command' in all_commands_content
    assert 'mg_test_command' in all_commands_content


@pytest.mark.django_db
def test_mg_test_command(admin_client):
    url = '/admin/managerie/managerie_test_app/mg_test_command/'
    assert 'wololo' in admin_client.get(url).content.decode()
    string = get_random_string()
    content = admin_client.post(url, {
        'true_option': '1',
        'false_option': '1',
        'string_option': string,
    }).content.decode()
    assert 'Command executed successfully.' in content
    data = json.loads(unescape(content[content.index('XXX:') + 4:content.index(':XXX')]))
    assert data['string_option'] == string
