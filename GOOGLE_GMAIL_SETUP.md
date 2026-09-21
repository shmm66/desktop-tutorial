# Google Login + Gmail setup

1. In Google Cloud Console create an OAuth client of type **Desktop app**.
2. Enable the Gmail API.
3. Configure the OAuth consent screen and use the narrow Gmail scope requested by the app: \`https://www.googleapis.com/auth/gmail.send\`.
4. Download the OAuth JSON and keep it private.
5. In Trader Planner Pro open **Settings → Google Account → Choose credentials.json** and select that file.
6. Click **Continue with Google** and complete the browser sign-in.
7. The Journal page can then generate a graphical PDF/PNG statement and send it to the signed-in Gmail address.

The app stores the OAuth token locally under %USERPROFILE%\TraderPlannerPro\google_token.json.
No Gmail password is stored by the application.

Google classifies \`gmail.send\` as a sensitive scope, so public distribution may require OAuth app verification depending on the application's deployment and audience.
