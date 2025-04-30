# hlx-hsso-callback
This is a add-on for BMC Helix Single Sign-On that via the HSSO callback functionality can create a request in AR Server. By doing so the possibility to automate users permissions is possible.


----------------------------------------------------------------------------------

# Step 1 - Configure SAML-authentication for Realm i Helix Single Sign-On
You need to have a SAML-integration before going further (maybe this container will work for several integrations aswell but not tested)

# Step 2 - Build image
Build as you normally do in your environment, for example:
  podman build -t hlx-hsso-callback .

# Step 3 - Install Innovation Studio application
Install Innovation Studio application from zip-file ./is-app/broderdanill.hlx-hsso-callback-<version>.zip in your environment

# Step 4 - Deploy container application
Deploy kubernetes application in your environment, following is included (may need to be changed in your environment):
  configmap.yaml - This includes "fields_config.json" that handles claims that will be sent via POST to IS-app from container
  deployment.yaml - The deployment using the image created
  secret.yaml - Secrets with username/password that are used to authenticate with Helix Innovation Suite REST API (this must be a user that has permissions to create submit in form "broderdanill.hlx-hsso-callback:hlx-hsso-callback")
  service.yaml - The service that will be called from Helix SSO onAuth Callback

# Step 5 - Configure Helix Single Sign-On
Set "onAuth Webhook Callback URL" in HSSO for the Realm (to point at the hlx-hsso-callback service in kubernetes/openshift)
Also verify that you have configured the claims with same name and amount as in the configmap.yaml

# Step 6 - Run test
Try to login to the realm now using the SAML-integration. If configured correctly the following will happen:
  1. Helix SSO authenticates with SAML and recieves claims
  2. onAuth webhook will be called from Helix SSO and will send to webhook in our container hlx-hsso-callback (look at the logs in the container, has debug logging default)
  3. The hlx-hsso-callback container will make a POST request to the form specified in env-variable "BMC_WEBHOOK_URL"
  4. Look in the IS-application and you should have recieved data and with fields containing the claims

# Step 7 - Build/Rebuild
If you have come this far you can now build your own functionality on how to create a user and user group list from configuration mapping for example "groups" from claims to you AR Groups
The onAuth call will be handeled before user beeing logged in, so when this workflow is done and given "http status 200" the user will be logged in with the groups you deisre


# Bonus / Nice to know about
If you want to hinder users not in specific group(s) to even access Helix at all you can use the env-variable in deployment "ALLOWED_GROUPS" to set which groups that are allowed to access. If you set the variable empty then all groups are allowed and you need to handle them all in your application in Innovation Studio.


----------------------------------------------------------------------------------

# Other or old documentation



Test-Run the container (update urls aso)
podman run -v $(pwd)/fields_config.json:/config/fields_config.json:ro -e FIELDS_CONFIG_PATH=/config/fields_config.json -e BMC_USERNAME=youruser -e BMC_PASSWORD=yourpass -e BMC_LOGIN_URL=https://test.com -e BMC_WEBHOOK_URL=https://test.com -p 5000:5000 hlx-hsso-callback


Example of claims from Helix SSO
{'groups': [], 'realm': 'realm-namn', 'login': 'user123', 'tenant': 'tenant-value'}


SAML Assertion example
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

