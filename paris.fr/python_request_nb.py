import os
import re
import uuid
import sys, traceback, time, datetime
import random, string
import io
import gzip

import http.client
import mimetypes
import json

from urllib.request import urlopen, Request
from urllib.parse import urlparse, parse_qs, urlencode

from bs4 import BeautifulSoup

#format data for http POST requests.
def encode_multipart_formdata(fields):
    boundary = '------WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    CRLF = '\r\n'
    L = []
    for key, value in fields.items():
        L.append('--' + boundary)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    L.append('--' + boundary + '--')
    L.append('')
    body = CRLF.join(L).encode('utf-8')
    content_type = f'multipart/form-data; boundary={boundary}'
    return content_type, body

# convert cookies in html response message to json format as described in RFC6265. TO DO: handle multiple cookies.
def parse_dict_cookies(cookies):
    result = {}
    for index, item in enumerate(cookies.split(';')):
        if index == 0:
            name, value = item.split('=', 1)
            result['name'] = name
            result['value'] = value
            continue
        item = item.strip()
        if not item:
            continue
        if '=' not in item:
            result[item] = True
            continue
        name, value = item.split('=', 1)
        result[name] = value
    return result

def processing_flush(n, index=10):
    sys.stdout.write(f"\r\033[1mPolling the server\033[0m %s" % (index * " "))
    sys.stdout.write(f"\r\033[1mPolling the server\033[0m %s" % ((n % index)* "."))
    sys.stdout.flush()

with open("data.json", "r") as file:
    data = json.load(file)

url = "https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointmentsearch&view=search&category=titres"

phony_data = {
    "name" : "username",
    "password" : "password"
}

while True:

    jsonData = json.dumps(phony_data).encode('utf-8')
    req = Request(url, data=jsonData, headers={
                    'content-type': 'application/json'
                    })
    with urlopen(req) as response:
        html = response.read().decode('utf-8')
        cookies = response.getheader("Set-Cookie")

    cookie1, cookie2 = cookies.split(',',1)
    parsed_cookies = [parse_dict_cookies(cookie1),parse_dict_cookies(cookie2)]
    poll_period = 0.0 #time before sending new http request for availability to server in seconds.
    i = 0

    #Check for warning in the webpage that no appointment are available.
    while "Merci de renouveler votre demande dans quelques minutes" in html or \
                        "Tous les rendez-vous ont" in  html or \
                        "Veuillez en choisir un autre." in html or \
                        "Aucun rendez-vous n'est actuellement disponible." in  html or \
                        "Ville de Paris pour cette semaine ont tous" in html or \
                        "Le 3975 n’est pas en mesure de vous proposer des rendez-vous" in  html or \
                        "Les  5 600" in html or \
                        "Maintenance" in html or \
                        "Le 3975 n’est pas en mesure de vous proposer des rendez-vous" in  html or \
                        "Les  5 500" in html:
        processing_flush(i)
        time.sleep(poll_period)
        req = Request(url, data=jsonData, headers={
                        "content-type" : "application/json",
                        "Cookie" : cookies,
                        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
                        })
        html = urlopen(req).read().decode('utf-8')
        i = i + 1

    print('\n')

    parsed_html = BeautifulSoup(html,features="lxml")
    a_element = parsed_html.find('a', id=re.compile("appointment_first_slot$"))
    date_time = a_element.text
    day = re.match('\d{2} *',date_time).group(0)
    o = urlparse(a_element['href'])
    dict = parse_qs(o.query)
    dict.pop('anchor',None)
    dict['anchor'] = ''
    url1 = o._replace(query=urlencode(dict,doseq=True)).geturl() + "#step3"

    list = cookies.split(',',1)
    list1 = list[0].split(';',1)
    list2 = list[1].split(';',1)


    req = Request(url1, data=jsonData, headers={
                            "content-type" : "application/json",
                            "Cookie" :list1[0]+';'+list2[0],
                            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
                            })

    with urlopen(req) as response:
        html = response.read().decode('utf-8')

    #TO DO: handle exceptions here.
    parsed_html = BeautifulSoup(html,features="lxml")
    a_element = parsed_html.find('input', attrs={"size": "10", "id":re.compile(r'attribute\d{2}$')})
    a1 = a_element['id']
    a_element = parsed_html.find('input', attrs={"size": "5", "id":re.compile(r'attribute\d{2}$')})
    a2 = a_element['id']

    fields = {
        "page" : "appointment",
        "action" : "doValidateForm",
        "id_form" : parse_qs(o.query)['id_form'][0],
        "date_of_display" : f"2022-04-{day}",
        "session": "session",
        "anchor" : "step4",
        "lastname" : data["last_name"],
        "firstname" : data["first_name"],
        "email" : data["email"],
        "emailConfirm" : data["email"],
        a1 : data["phone"],
        a2 : data["postal_code"],
        "save" : ""
    }
    content_type, body = encode_multipart_formdata(fields)
    req = Request("https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointment&view=displayRecapAppointment&anchor=#step4", data=body, headers={
                            "content-type" : content_type,
                            "Cookie" :list1[0]+';'+list2[0],
                            'content-length': str(len(body)),
                            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
                            } , method = 'POST')
    with urlopen(req) as response:
        html = response.read().decode('utf-8')


    parsed_html = BeautifulSoup(html,features="lxml")
    img_element = parsed_html.find('input', id="j_captcha_response")

    if img_element is not None:
        break

    h_element = parsed_html.find('div', class_="alert alert-danger")
    if h_element is not None:
        print('\033[93m' + h_element.text + '\033[0m')

    #quit()
    print(f"\033[1mRetrying...\033[0m")

title = "Success"
message = "Slot available."

command = f'''
osascript -e 'display notification "{message}" with title "{title}"'
'''
os.system(command)

message = f'''
Book available slot on {date_time}.
'''
command = f'''
osascript sendMessage.scpt {data["phone"]} "{message}"
'''
os.system(command)

while True:

    req = Request("https://teleservices.paris.fr/rdvtitres/JCaptchaImage", headers={
                            "Cookie" :list1[0]+';'+list2[0],
                            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
                            })

    with urlopen(req) as p:
        filename = '/tmp/' + str(uuid.uuid4())+'.jpg'
        with open(filename, mode="wb") as file:
            file.write(p.read())

    command = f'''
    open {filename}
    '''
    os.system(command)

    #TO DO: let user get another captcha.
    captcha = input("Enter captcha:")

    fields = {
        "page" : "appointment",
        "action" : "doMakeAppointment",
        "lastname" : data["last_name"],
        "firstname" : data["first_name"],
        "email" : data["email"],
        "anchor" : "step5",
        "j_captcha_response" : captcha,
        "jcaptchahoneypot": "",
        "validate" : "validate"
    }

    content_type, body = encode_multipart_formdata(fields)#id_appointment ?
    req = Request(f"https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointment&view=getAppointmentCreated&id_form={parse_qs(o.query)['id_form'][0]}&anchor=#step5",
                data=body,
                headers={
                            "content-type" : content_type,
                            "Cookie" :list1[0]+';'+list2[0],
                            'content-length': str(len(body)),
                            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
                },
                method = 'POST')

    dict = {}
    with urlopen(req) as response:
        o = urlparse(response.url)
        dict = parse_qs(o.query)

    html = response.read().decode('utf-8')
    parsed_html = BeautifulSoup(html,features="lxml")

    command = f'''
    rm {filename}
    '''
    os.system(command)

    if dict.get('view') == ['getAppointmentCreated']:
        break

    h_element = parsed_html.find('div', class_="alert alert-danger")
    if h_element is not None:
        print('\033[93m' + h_element.text + '\033[0m')
