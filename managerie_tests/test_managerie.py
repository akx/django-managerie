import json
from html import unescape

import pytest
from django.utils.crypto import get_random_string


@pytest.mark.django_db
def test_managerie(admin_client):
    assert "Commands" in admin_client.get("/admin/").content.decode()
    csup_content = admin_client.get("/admin/managerie/auth/createsuperuser/").content.decode()
    assert "Used to create a superuser." in csup_content
    assert "Verbosity" in csup_content
    assert "Username" in csup_content
    assert "Database" in csup_content
    all_commands_content = admin_client.get("/admin/managerie/").content.decode()
    assert "Mg Test Command" in all_commands_content
    assert "mg_test_command" in all_commands_content
    assert "Mg Disabled Command" not in all_commands_content
    assert "mg_disabled_command" not in all_commands_content


@pytest.mark.django_db
def test_mg_test_command(admin_client, admin_user):
    url = "/admin/managerie/managerie_test_app/mg_test_command/"
    assert "wololo" in admin_client.get(url).content.decode()
    string = get_random_string(42)
    content = admin_client.post(
        url,
        {
            "true_option": "1",
            "false_option": "1",
            "string_option": string,
        },
    ).content.decode()
    assert "Command executed successfully." in content
    data = json.loads(unescape(content[content.index("XXX:") + 4 : content.index(":XXX")]))
    assert data["string_option"] == string
    assert admin_user.username
    assert data["username"] == admin_user.username


@pytest.mark.django_db
def test_mg_disabled_command(admin_client):
    url = "/admin/managerie/managerie_test_app/mg_disabled_command/"
    assert "Not Found" in admin_client.get(url).content.decode()


@pytest.mark.django_db
def test_staff_no_access(staff_client):
    # Test there's no access to these commands for staff users
    for command in ("mg_disabled_command", "mg_test_command"):
        url = f"/admin/managerie/managerie_test_app/{command}/"
        assert "Not Found" in staff_client.get(url).content.decode()


@pytest.mark.django_db
def test_staff_custom_access(staff_client):
    # Test there's access to mg_unprivileged_command for staff users
    url = "/admin/managerie/managerie_test_app/mg_unprivileged_command/"
    assert "Unprivileged" in staff_client.get(url).content.decode()
    content = staff_client.post(url, {}).content.decode()
    assert "Command executed successfully." in content


@pytest.mark.django_db
def test_outsider_no_access(client):
    # Test there's no access to these commands for outsiders
    for command in (
        "mg_disabled_command",
        "mg_test_command",
        "mg_unprivileged_command",
    ):
        url = f"/admin/managerie/managerie_test_app/{command}/"
        resp = client.get(url)
        assert resp.status_code == 302  # Redirect to login
