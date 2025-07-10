import Keycloak from 'keycloak-js';

// Create a singleton instance using a module-level variable
// This prevents multiple instances even with React Strict Mode
const createKeycloakInstance = () => {
  return new Keycloak({
    url: process.env.REACT_APP_KEYCLOAK_URL || 'http://localhost:8080',
    realm: process.env.REACT_APP_KEYCLOAK_REALM || 'home-automation',
    clientId: process.env.REACT_APP_KEYCLOAK_CLIENT_ID || 'home-automation-frontend',
  });
};

// Store the instance globally to prevent re-initialization
if (!window.keycloakInstance) {
  window.keycloakInstance = createKeycloakInstance();
}

export default window.keycloakInstance;