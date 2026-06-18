from django.templatetags.static import static


def admin_stylesheet(_request) -> str:
    return static("admin/css/unfold-neuralterrena.css")


def admin_logo(_request) -> dict[str, str]:
    logo = static("images/brand/NT-logo-color-horizontal.png")
    return {
        "light": logo,
        "dark": logo,
    }


def admin_icon(_request) -> str:
    return static("images/brand/NT-iso-color-on-white.png")


def admin_favicon_svg(_request) -> str:
    return static("images/favicons/favicon.svg")


def admin_favicon_96(_request) -> str:
    return static("images/favicons/favicon-96x96.png")


def admin_favicon_apple(_request) -> str:
    return static("images/favicons/apple-touch-icon.png")
