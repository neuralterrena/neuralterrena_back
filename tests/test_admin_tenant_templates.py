from django.template.loader import render_to_string
from django.test import RequestFactory


def test_admin_app_list_preserves_unfold_navigation_for_shared_apps() -> None:
    request = RequestFactory().get("/admin/")
    request.tenant = type("Tenant", (), {"schema_name": "public"})()

    app_list = [
        {
            "app_label": "users",
            "app_url": "/admin/users/",
            "name": "Users",
            "models": [
                {
                    "object_name": "User",
                    "name": "Users",
                    "admin_url": "/admin/users/user/",
                    "add_url": "/admin/users/user/add/",
                    "view_only": False,
                    "hidden": False,
                },
            ],
        },
    ]

    html = render_to_string(
        "admin/app_list.html",
        {
            "app_list": app_list,
            "show_changelinks": True,
        },
        request=request,
    )

    assert "Shared app" in html
    assert 'id="nav-sidebar-apps"' in html
    assert "/admin/users/user/" in html
    assert "hover:text-primary-600" in html


def test_admin_app_list_marks_tenant_only_apps_unavailable_in_public_schema() -> None:
    request = RequestFactory().get("/admin/")
    request.tenant = type("Tenant", (), {"schema_name": "public"})()

    app_list = [
        {
            "app_label": "rest_framework",
            "app_url": "/admin/rest_framework/",
            "name": "REST framework",
            "models": [],
        },
    ]

    html = render_to_string(
        "admin/app_list.html",
        {
            "app_list": app_list,
            "show_changelinks": True,
        },
        request=request,
    )

    assert "Unavailable" in html
    assert "Not available for global schema" in html
