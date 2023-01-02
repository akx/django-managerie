import pytest


@pytest.fixture()
def staff_user(db: None, django_user_model, django_username_field: str):
    UserModel = django_user_model
    username_field = django_username_field
    username = "staff@example.com" if username_field == "email" else "staff"
    try:
        user = UserModel._default_manager.get_by_natural_key(username)
    except UserModel.DoesNotExist:
        user_data = {
            "password": "staff",
            username_field: username,
            "is_staff": True,
            "email": "staff@example.com",
        }
        user = UserModel._default_manager.create_user(**user_data)
    return user


@pytest.fixture()
def staff_client(db: None, staff_user):
    """A Django test client logged in as a staff user."""
    from django.test.client import Client

    client = Client()
    client.force_login(staff_user)
    return client
