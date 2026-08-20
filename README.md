# Event Registration System

A Django event registration and attendance system with event management, member registration, QR check-in, support requests, and an in-app help chatbot.

## Setup

1. Create or activate a Python virtual environment.
2. Install the project dependencies available in the environment:

   ```powershell
   .\env\Scripts\Activate.ps1
   ```

3. Apply migrations and start Django:

   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

Open `http://127.0.0.1:8000/` in a browser.

## QR check-in

QR codes use `SITE_URL` from `config/settings.py`. For scanning with a phone, set it to the computer's LAN address, for example:

```python
SITE_URL = "http://192.168.1.20:8000"
```

The phone and computer must be on the same network, and the chosen host must be allowed by the local firewall.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
