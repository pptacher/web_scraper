# book an appointment for id renewal.
You live in Paris and need to have your ID card or passport issued. You will have to go to the site [paris.fr](https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointmenttitresearch#). Currently, due to high demand, it can be very hard to get a slot. This simple python script can help you get any appointment as soon as it becomes available.

## Usage

0. Activate safari automation with (cf. [Apple doc](https://developer.apple.com/documentation/webkit/testing_with_webdriver_in_safari))

```
safaridriver --enable
```

1. Fill in the file data.json with your personal information.

2. Launch the script:

```
python3 python_request.py
```

3. When an availability is posted on the site, you should receive a macOS notification and iMessage on your phone.

4. Solve the captcha on the webpage opened in safari browser.

5. Done.

Retry if you get an error.

## Requirements

- python3 with selenium and BeautifulSoup packages.

- macOS with safari.
