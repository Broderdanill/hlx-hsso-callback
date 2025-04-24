# hlx-hsso-callback
Callback for Helix SSO to grep groups (claims) from SAML and creates/updates user i AR Server

# Build image
podman build -t hlx-hsso-callback .

# Run (update urls aso)
podman run -v $(pwd)/fields_config.json:/config/fields_config.json:ro -e FIELDS_CONFIG_PATH=/config/fields_config.json -e BMC_USERNAME=youruser -e BMC_PASSWORD=yourpass -e BMC_LOGIN_URL=https://test.com -e BMC_WEBHOOK_URL=https://test.com -p 5000:5000 hlx-hsso-callback

# Example of claims from Helix SSO
{'groups': [], 'realm': 'realm-namn', 'login': 'user123', 'tenant': 'tenant-value'}

# SAML Assertion example
{
  "saml_assertion": {
    "issuer": "https://helix-sso.bmc.com",
    "subject": "johndoe",
    "attributes": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "johndoe@example.com",
      "roles": ["admin", "user"]
    },
    "authn_context": {
      "auth_method": "PasswordProtectedTransport",
      "auth_level": "high"
    },
    "audience": "your-application.com"
  }
}

