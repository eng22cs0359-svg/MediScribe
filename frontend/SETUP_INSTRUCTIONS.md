# MediScribe Email Configuration Setup

## Installation Required

Before running the application, install the required package:

```bash
pip install python-dotenv
```

## Email Configuration

1. Open the `.env` file in `ScanPlus/frontend/.env`
2. Replace `YOUR_GMAIL_ADDRESS_HERE` with your actual Gmail address
3. The app password is already configured: `mbdrlptvjgofzhkm`

Example:
```
email=youremail@gmail.com
pass=mbdrlptvjgofzhkm
```

## Important Notes

- The `.env` file is already added to `.gitignore` and will NOT be committed to git
- Keep your email credentials secure and never share them
- The app password provided is a Gmail App Password (not your regular Gmail password)
- Email reminders will be sent automatically when prescriptions are scanned with an email address

## Verification

After setup, the application will:
- Load email credentials from the `.env` file automatically
- Send prescription reminders via email when configured
- Display a warning if email is not configured but reminders are requested
