# book an appointment for id renewal.
You live in Paris and need to have your ID card or passport issued. You will have to go to the site [paris.fr](https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointmenttitresearch#). Currently, due to high demand (as claimed by the relevant authorities), it can be very hard to get an appointment in city hall to start the ID issuing process (cf. this article [bfm](https://www.bfmtv.com/paris/carte-d-identite-passeport-embouteillage-a-paris-et-en-ile-de-france-pour-obtenir-un-rendez-vous_AV-202203300255.html)). This program, relying on C library curl to make http requests, can help you get any appointment as soon as it becomes available, within usually just a couple of minutes if you are lucky enough.

## Usage

0. Clone the repository.

1. Fill in the file data.txt with your personal information.

2. Go to the cpp directory and

```
mkdir build
cd build
```

3. Configure with

```
cmake ..
```

4. Build executable

```
make
```

5. Launch the binary with

```
./booking.bin
```
For the multithreaded version,

```
./booking_mt.bin n
```
where n is an integer representing the number of threads. If not given in argument, the number of threads is determined at runtime. If you want to be able to book several appointments simultaneously, using only 1 email address, your email provider must support aliases like john+1234@gmail.com (eg. google, outlook).

6. When an availability is posted on the site and waiting for you to book, solve the captcha which appears in the terminal.

5. Done.


Retry if you get an error. You should better sign out from your paris.fr account if you have one, because that may change the flow of the booking. There are more availabilities during business hours.

## Requirements

- [libcurl](https://curl.se) for http communications.

- [Google re2](https://github.com/google/re2) for parsing web page using regular expressions.

- macOS with c++ compiler.

Tested on Macbook pro 16" 2021 with MacOS Monterey 12.0.1, c++ compiler: AppleClang 13.0.0.
