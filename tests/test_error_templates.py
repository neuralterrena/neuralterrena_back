from django.template.loader import render_to_string


def test_error_templates_render_without_missing_route_dependencies() -> None:
    templates = [
        "403.html",
        "403_csrf.html",
        "404.html",
        "500.html",
    ]

    for template_name in templates:
        html = render_to_string(template_name)

        assert "Neuralterrena API" in html
