// Vorlage. Die echte config.js wird von der Pipeline (oder publish-frontend.ps1)
// aus den Stack-Outputs erzeugt. redirectUri wird NICHT gesetzt: das Frontend
// nimmt zur Laufzeit window.location.origin.
window.APP_CONFIG = {
  apiEndpoint: "https://DEINE-API.execute-api.us-east-1.amazonaws.com",
  userPoolId: "us-east-1_XXXXXXXXX",
  userPoolClientId: "XXXXXXXXXXXXXXXXXXXXXXXXXX",
  cognitoDomain: "https://netlab-scheduler-XXXX.auth.us-east-1.amazoncognito.com"
};
