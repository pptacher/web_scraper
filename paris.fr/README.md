# book an appointment for id renewal.
You live in Paris and need to have your ID card or passport issued. You will have to go to the site [paris.fr](https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointmenttitresearch#). Currently, due to high demand (as claimed by the relevant authorities), it can be very hard to get an appointment in city hall to start the ID issuing process (cf. this article [bfm](https://www.bfmtv.com/paris/carte-d-identite-passeport-embouteillage-a-paris-et-en-ile-de-france-pour-obtenir-un-rendez-vous_AV-202203300255.html)). This simple python script, relying on Python standard library urllib to make http requests, can help you get any appointment as soon as it becomes available, within usually just a couple of minutes if you are lucky enough.

## Usage

### using Browser automation.

0. In terminal, activate safari automation with (cf. [Apple doc](https://developer.apple.com/documentation/webkit/testing_with_webdriver_in_safari))

```
safaridriver --enable
```

1. Fill in the file data.json with your personal information.

2. Launch the script:

```
python3 python_request.py
```

3. When an availability is posted on the site and waiting for you to book, you should receive a macOS notification and iMessage on your phone.

4. Solve the captcha on the webpage opened in safari browser.

5. Done.

Retry if you get an error.

### pure urllib version, using POST requests and no browser.

0. Fill in the file data.json with your personal information.

1. Launch the script:

```
python3 python_request_nb.py
```

2. When an availability is posted on the site and waiting for you to book, you should receive a macOS notification and iMessage on your phone.

3. Solve the displayed captcha in the terminal.

4. Done.

Retry if you get an error. You should better sign out from your paris.fr account if you have one, because that may change the flow of the booking. There are more availabilities during business hours.

## Requirements

- [python3](https://www.python.org) with selenium and BeautifulSoup packages.

- macOS with safari.

Tested on Macbook pro 16" 2021 with MacOS Monterey 12.0.1, Python 3.9.10.
