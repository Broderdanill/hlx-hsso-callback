# hlx-hsso-callback
This is a add-on for BMC Helix Single Sign-On that via the HSSO callback functionality can create a request in AR Server. By doing so the possibility to automate users permissions is possible.

# Step-by-Step to install
1. Configure SAML-authentication in HSSO
2. Build and Setup this Container in your environment
3. Import "hlx-hsso-callback.def" in your AR Environment
4. Set up correct username and password in the secret (this must be a user that has permissions to create submit in form hlx-hsso-callback)
5. Set Webhook Callback URL in HSSO for the Realm (to point at the hlx-hsso-callback service)
6. Test and verify that the claims are created in the AR form "hlx-hsso-callback"
7. Build your own workflow to create users and build permissions for the user on the form "hlx-hsso-callback".
The provided application here only shows that we can recieve a submit with user information from SAML claims.
What you do with this is up to you :)


-----------------------------------------------------------------------------------


# Build image
podman build -t hlx-hsso-callback .

# Test-Run the container (update urls aso)
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

