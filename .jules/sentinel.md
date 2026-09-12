## 2025-02-27 - [IDOR in UserDetailView]
**Vulnerability:** IDOR (Insecure Direct Object Reference) in `UserDetailView` where a user could view the profile of any other user by navigating to `/users/<id>/`.
**Learning:** `get_queryset()` was not restricted to `self.request.user.id`, allowing unauthorized access to any user profile via the view. Also, the `users` app URLs were inadvertently omitted from `config/urls.py`, so testing this behavior caused unexpected `NoReverseMatch` errors when attempting to verify success URLs.
**Prevention:** Always override `get_queryset()` in views that handle sensitive objects, ensuring `.filter(id=self.request.user.id)` (or equivalent filtering) is applied to prevent users from interacting with objects that do not belong to them. Ensure app URLs are registered correctly in the project root URLs so tests can properly reverse view names.

## 2025-02-27 - [Python 3 syntax errors masquerading as multiple exception catchers]
**Vulnerability:** Application DoS due to SyntaxError in `except ExceptionA, ExceptionB:`
**Learning:** Python 3 requires multiple exception types to be parenthesized in except clauses. Code attempting to catch `(A, B)` was instead throwing a fatal compile-time error. This broke critical authentication layers (`JWTTenantMiddleware` and `PasswordResetConfirmSerializer`), blocking runtime execution entirely.
**Prevention:** Always use ruff and pytest to verify that code compiles cleanly. Use parenthesized tuples for multiple exception catchers `except (TypeError, ValueError):` to avoid fatal compilation faults.
