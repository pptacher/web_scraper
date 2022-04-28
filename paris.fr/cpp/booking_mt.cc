#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <string>
#include <vector>
#include <cassert>
#include <cstdlib>
#include <ctime>
#include <curl/curl.h>
#include <re2.h>
//#include <chrono>
#include <thread>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <mutex>

using std::string;

std::mutex output_mutex, hash_table_mutex;

std::unordered_map<string, string> hmap;
std::unordered_set<string> hash_table;

//  libcurl write callback function
static int writer(char *data, size_t size, size_t nmemb, std::string *writerData)
{
  if(writerData == NULL)
    return 0;

  writerData->append(data, size*nmemb);

  return size * nmemb;
}

void book(){
  CURL *curl = NULL;
  CURLcode code;



  char errorBuffer[CURL_ERROR_SIZE];
  std::string buffer;

  curl = curl_easy_init();

  //curl_easy_setopt(curl, CURLOPT_VERBOSE, 1L);
  //curl_easy_setopt(curl, CURLOPT_HEADER, 1L);
  //curl_easy_setopt(curl, CURLOPT_NOPROGRESS, 0L);

  if(curl == NULL) {
    fprintf(stderr, "Failed to create CURL connection\n");
    exit(EXIT_FAILURE);
  }

  std::srand(std::hash<std::thread::id>{}(std::this_thread::get_id())+std::time(NULL));
  string rdstring;
  const char alphanum[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  for (size_t i = 0; i < 16; i++) {
    rdstring.push_back(alphanum[std::rand()/((RAND_MAX + 1u)/62)]);
  }

  while( true ){

  curl_easy_setopt(curl, CURLOPT_ERRORBUFFER, errorBuffer);
  curl_easy_setopt(curl, CURLOPT_URL, "https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointmentsearch&view=search&category=titres");
  curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 0L);
  curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writer);
  curl_easy_setopt(curl, CURLOPT_WRITEDATA, &buffer);
  //curl_easy_setopt(curl, CURLOPT_HTTPAUTH, CURLAUTH_BASIC);
  //curl_easy_setopt(curl, CURLOPT_USERPWD, "james:bond");
  curl_easy_setopt(curl, CURLOPT_USERAGENT, "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148");

  curl_easy_setopt(curl, CURLOPT_COOKIEJAR, ("/tmp/cookies" + rdstring + ".txt").c_str());
  code = curl_easy_perform(curl);
  if(code != CURLE_OK) {
    fprintf(stderr, "Failed to get url [%s]\n", errorBuffer);
    exit(EXIT_FAILURE);
  }

  const char* jsonObj = "{ \"username\" : \"username\" , \"password\" : \"password\" }";
  //sprintf(jsonObj, "\"name\" : \"%s\", \"age\" : \"%s\"", name, age);
  struct curl_slist *list = NULL;
  list = curl_slist_append(list, "Content-Type: application/json");
  list = curl_slist_append(list, "charset: utf-8");

  curl_easy_setopt(curl, CURLOPT_HTTPHEADER, list);
  curl_easy_setopt(curl, CURLOPT_POSTFIELDS, jsonObj);

  int i(0);

  do  {
    i = (i+1)%20;
    buffer = "";
    code = curl_easy_perform(curl);
    if(code != CURLE_OK) {
      fprintf(stderr, "Failed to get url [%s]\n", errorBuffer);
      exit(EXIT_FAILURE);
    }
    //std::cout << "\r\e[1mPolling the server\e[0m " << std::setw(20) << std::left << std::string(20,' ');
    //std::cout << "\r\e[1mPolling the server\e[0m " << std::setw(i) << std::left << std::string(i,'.')  << std::flush;


    //std::this_thread::sleep_for(std::chrono::milliseconds(1000));

  } while (RE2::PartialMatch(buffer,"(Merci de renouveler votre demande dans quelques minutes)|"
                                    "(Tous les rendez-vous ont)|"
                                    "(Veuillez en choisir un autre.)|"
                                    "(Aucun rendez-vous n'est actuellement disponible.)|"
                                    "(Ville de Paris pour cette semaine ont tous)|"
                                    "Le 3975 n’est pas en mesure de vous proposer des rendez-vous|"
                                    "Les  5 600|"
                                    "Maintenance|"
                                    "Le 3975 n’est pas en mesure de vous proposer des rendez-vous|"
                                    "Les  5 500" ));

  //printf("%s\n", buffer.c_str());
  long response_code;
  curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);

  if (response_code != 200) {
    continue;
  }

  string link, date;
  RE2::PartialMatch(buffer, R"(<\s*a\s.*href=\"([[:ascii:]]*)\".*id=\".*appointment_first_slot\"\s*>([[:alnum:]\s:]*)</a>)",&link, &date);
  {
    std::lock_guard g(hash_table_mutex);
    auto it = hash_table.find(date);
    if ( it != hash_table.end() )  {
      continue;
    }
    else{
      hash_table.insert(date);
    }
  }
  buffer.clear();

  auto it = link.find("step3");
  link.erase(it,5);

  string id3;
  RE2::PartialMatch(link, R"(id_form=(\d{2}))", &id3);

  curl_easy_setopt(curl, CURLOPT_URL, link.c_str());
  code = curl_easy_perform(curl);
  if(code != CURLE_OK) {
    fprintf(stderr, "Failed to get '%s' [%s]\n", link.c_str(), errorBuffer);
    exit(EXIT_FAILURE);
  }

  string id1, id2;
  RE2::PartialMatch(buffer, R"(<\s*input\s.*id=\"(attribute\d{2}).*size=\"10")",&id1);
  RE2::PartialMatch(buffer, R"(<\s*input\s.*id=\"(attribute\d{2}).*size=\"5")",&id2);

  string name, domain;
  RE2::FullMatch(hmap["email"],"(.*)@(.*)", &name, &domain);
  string email = name + '+' + rdstring + '@' + domain;

  curl_mime* multipart = curl_mime_init(curl);
  curl_mimepart* part = curl_mime_addpart(multipart);
  curl_mime_name(part, "page");
  curl_mime_data(part, "appointment", CURL_ZERO_TERMINATED);

  part = curl_mime_addpart(multipart);
  curl_mime_name(part, "action");
  curl_mime_data(part, "doValidateForm", CURL_ZERO_TERMINATED);

  part = curl_mime_addpart(multipart);
  curl_mime_name(part, "id_form");
  curl_mime_data(part, id3.c_str(), CURL_ZERO_TERMINATED);

  part = curl_mime_addpart(multipart);
  curl_mime_name(part, "date_of_display");
  curl_mime_data(part, "2022-04-02", CURL_ZERO_TERMINATED);

  part = curl_mime_addpart(multipart);
  curl_mime_name(part, "session");
  curl_mime_data(part, "session", CURL_ZERO_TERMINATED);

  part = curl_mime_addpart(multipart);
  curl_mime_name(part, "anchor");
  curl_mime_data(part, "step4", CURL_ZERO_TERMINATED);

  part = curl_mime_addpart(multipart);
  curl_mime_name(part, "lastname");
  curl_mime_data(part, hmap["lastname"].c_str(), CURL_ZERO_TERMINATED);

  part = curl_mime_addpart(multipart);
  curl_mime_name(part, "firstname");
  curl_mime_data(part, hmap["firstname"].c_str(), CURL_ZERO_TERMINATED);

  part = curl_mime_addpart(multipart);
  curl_mime_name(part, "email");
  curl_mime_data(part, email.c_str(), CURL_ZERO_TERMINATED);

  part = curl_mime_addpart(multipart);
  curl_mime_name(part, "emailConfirm");
  curl_mime_data(part, email.c_str(), CURL_ZERO_TERMINATED);

  part = curl_mime_addpart(multipart);
  curl_mime_name(part, id1.c_str());
  curl_mime_data(part, hmap["phone"].c_str(), CURL_ZERO_TERMINATED);

  part = curl_mime_addpart(multipart);
  curl_mime_name(part, id2.c_str());
  curl_mime_data(part, hmap["postalcode"].c_str(), CURL_ZERO_TERMINATED);

  part = curl_mime_addpart(multipart);
  curl_mime_name(part, "save");
  curl_mime_data(part, "", CURL_ZERO_TERMINATED);

  buffer.clear();
  curl_slist_free_all(list);
  curl_easy_setopt(curl, CURLOPT_HTTPHEADER, NULL);
  curl_easy_setopt(curl, CURLOPT_MIMEPOST, multipart);
  curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L); // the server weirdly redirects to url#step4.
  curl_easy_setopt(curl, CURLOPT_URL, "https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointment&view=displayRecapAppointment&anchor=");

  curl_easy_perform(curl);

  curl_mime_free(multipart);
  curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 0L);

  curl_easy_setopt(curl, CURLOPT_HTTPHEADER, NULL);

  while (true) {
    char filename[] = "/tmp/fileXXXXXX";
    mktemp(filename);
    strcat(filename, ".jpg");
    FILE* fp = fopen(filename, "wb");

    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, fwrite);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, fp);
    curl_easy_setopt(curl, CURLOPT_URL, "https://teleservices.paris.fr/rdvtitres/JCaptchaImage");

    curl_easy_perform(curl);

    fclose(fp);
    string captcha;
    char command[60];
    strcpy(command, "open ");
    strcat(command, filename);

    {
      std::lock_guard guard(output_mutex);
      std::system(command);
      std::cout << std::this_thread::get_id() << '\t' << date << ' ' << filename << '\n' << '\t' << "Enter Captcha (:q to discard): ";
      std::cin >> captcha;
    }

    remove(filename);
    if(captcha == ":q") {
      break;
    }


    multipart = curl_mime_init(curl);
    part = curl_mime_addpart(multipart);
    curl_mime_name(part, "page");
    curl_mime_data(part, "appointment", CURL_ZERO_TERMINATED);

    part = curl_mime_addpart(multipart);
    curl_mime_name(part, "action");
    curl_mime_data(part, "doMakeAppointment", CURL_ZERO_TERMINATED);

    part = curl_mime_addpart(multipart);
    curl_mime_name(part, "lastname");
    curl_mime_data(part, hmap["lastname"].c_str(), CURL_ZERO_TERMINATED);

    part = curl_mime_addpart(multipart);
    curl_mime_name(part, "firstname");
    curl_mime_data(part, hmap["firstname"].c_str(), CURL_ZERO_TERMINATED);

    part = curl_mime_addpart(multipart);
    curl_mime_name(part, "email");
    curl_mime_data(part, email.c_str(), CURL_ZERO_TERMINATED);

    part = curl_mime_addpart(multipart);
    curl_mime_name(part, "anchor");
    curl_mime_data(part, "step5", CURL_ZERO_TERMINATED);

    part = curl_mime_addpart(multipart);
    curl_mime_name(part, "j_captcha_response");
    curl_mime_data(part, captcha.c_str(), CURL_ZERO_TERMINATED);

    part = curl_mime_addpart(multipart);
    curl_mime_name(part, "jcaptchahoneypot");
    curl_mime_data(part, "", CURL_ZERO_TERMINATED);

    part = curl_mime_addpart(multipart);
    curl_mime_name(part, "validate");
    curl_mime_data(part, "validate", CURL_ZERO_TERMINATED);

    buffer.clear();
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, NULL);
    curl_easy_setopt(curl, CURLOPT_MIMEPOST, multipart);
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writer);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &buffer);
    char url1[150];
    sprintf(url1, "https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointment&view=getAppointmentCreated&id_form=%s&anchor=", id3.c_str());
    curl_easy_setopt(curl, CURLOPT_URL, url1);

    CURLcode res = curl_easy_perform(curl);

    //printf("%s\n", buffer.c_str());

    if ( res == CURLE_OK ) {
      long response_code;
      char* url = NULL;
      curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
      curl_easy_getinfo(curl, CURLINFO_EFFECTIVE_URL, &url);

      if (response_code == 200 && RE2::PartialMatch(url, "getAppointmentCreated")) {
        break;
      }

    }

  }

  }

  curl_easy_cleanup(curl);

}


int main(int argc, char *argv[])
{

  std::ifstream file;
  file.open("../data.txt");
  string line;

  if(file.is_open()){
    while(std::getline(file, line)) {
      std::istringstream iss(line);
      string key, value;

      iss >> key;
      iss >> value;
      hmap[key] = value;
    }
  }
  else{
    fprintf(stderr, "Failed to open file \'data.txt\'.\n");
    exit(EXIT_FAILURE);
  }

  curl_global_init(CURL_GLOBAL_DEFAULT);

  unsigned int nt = argc>1 ? std::min((uint)atoi(argv[1]), std::thread::hardware_concurrency()):std::thread::hardware_concurrency();
  std::vector<std::thread> threads;

  for (uint j=0; j<nt; ++j) {
    threads.push_back(std::thread(book));
  }

  std::cout << "Runnning with " << nt << " threads." << std::endl;

  book();

  for (auto& th : threads) {
    th.join();
  }

  threads.clear();

  curl_global_cleanup();

  return EXIT_SUCCESS;

}
