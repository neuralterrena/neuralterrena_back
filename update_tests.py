import re

with open("neuralterrena/users/tests/test_adapters.py", "r") as f:
    content = f.read()

# Replace manual settings override with pytest-django settings fixture modification

content = content.replace(
    "def test_social_account_adapter_is_open_for_signup(rf):",
    "def test_social_account_adapter_is_open_for_signup(rf, settings):",
)
content = content.replace(
    "def test_account_adapter_is_open_for_signup(rf):",
    "def test_account_adapter_is_open_for_signup(rf, settings):",
)

with open("neuralterrena/users/tests/test_adapters.py", "w") as f:
    f.write(content)
