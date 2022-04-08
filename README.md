django-managerie
================

:lightbulb: Expose Django management commands as forms in the admin

Requirements
------------

* Django 3.2+ (this project tracks Django's end-of-life policy)
* Python 3.6+

Installation
------------

Install the package as you would any Python package, then add `django_managerie` to your `INSTALLED_APPS`.

### Automatic patching

This is the easiest way to get up and running. You can have Managerie patch the admin site's dashboard view to include pseudo-models with the name "Commands" for all apps where management commands are available, and while it's at it, it'll also include URLs of its own.

Hook up Managerie to your admin site (e.g. in `urls.py`, where you have `admin.autodiscover()`), like so:

```python
from django.contrib import admin
from django_managerie import Managerie
# ...
managerie = Managerie(admin_site=admin.site)
managerie.patch()
```

### No patching

This is likely safer (in the presence of slightly less tolerant 3rd party apps that mangle the admin, for instance), but you can't enjoy the luxury of the Commands buttons in the admin dashboard.

```python
from django.contrib import admin
from django.conf.urls import include, url
from django_managerie import Managerie
# ...
managerie = Managerie(admin_site=admin.site)
# ...
urlpatterns = [
    # ...
    # ... url(r'^admin/', include(admin.site.urls)), ...
    url(r'^admin/', include(managerie.urls)),  # Add this!
]
```


Usage
-----

If you allowed Managerie to patch your admin, superusers can now see `Commands` "objects" in the admin dashboard.
If you didn't patch the admin, you can access a list of all commands through `/admin/managerie/` (or wherever your
admin is mounted).

If you click through to a command, you'll see the arguments of the command laid out as a form.
Fill the form, then hit "Execute Command", and you're done! :sparkles:

### Accessing the Django request from a managerie'd command

Managerie sets `_managerie_request` on the command instance to the current Django request.
You can use it to access the request, for instance, to get the current user.

TODO
----

* More `argparse` action support
* Multiple-argument support (`nargs`)
