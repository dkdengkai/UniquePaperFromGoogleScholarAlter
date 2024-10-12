import os
import time
import base64
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from markdown_strings import header, table, code_block

# set the proxy of yourself computer, xxxx is the proxy port
os.environ["http_proxy"] = "http://127.0.0.1:xxxx"
os.environ["https_proxy"] = "http://127.0.0.1:xxxx"

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
      creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
      else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
      # Save the credentials for the next run
      with open('token.json', 'w') as token:
        token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def get_unread_messages(service):
    # print(type(service))
    # results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD']).execute()
    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])

    Dicts = {'TitleKey':[], 'value':[]}
    if not messages:
      print('No unread messages found.')
    else:
      cout = 0
      for message in messages:
        google_scholar_sender = 0
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        sender  = ''
        # Get value of 'payload' from dictionary 'msg'
        payload = msg['payload']
        headers = payload['headers']

        for d in headers:
          if d['name'] == 'From':
            sender   = d['value']
            if "Google Scholar Alerts" in sender or "Google 学术搜索快讯" in sender:
              google_scholar_sender = 1
        if google_scholar_sender:
          cout += 1
          # The Body of the message is in Encrypted format. So, we have to decode it.
          # Get the data and decode it with base 64 decoder.
          data         = payload['body']['data']
          data         = data.replace("-","+").replace("_","/")
          decoded_data = base64.b64decode(data)

          # Now, the data obtained is in html. So, we will parse 
          # it with BeautifulSoup library
          soup = BeautifulSoup(decoded_data , "html.parser")

          Titles   = soup.find_all("a",   class_="gse_alrt_title")
          Authors  = soup.find_all('div', style =lambda value: value and '006621' in value)
          ABS      = soup.find_all("div", class_="gse_alrt_sni")
          Contents = zip(Titles, Authors, ABS)
          for (title, author, abs_)in Contents:
            if title.text not in Dicts['TitleKey']:
              Dicts['TitleKey'].append(title.text)
              Dicts['value'].append(str(title)+"\n<font color=#006621>"+author.text+"</font>\n"+abs_.text)
    
    # location of markdown file for saving the content
    savepath = "E:/DESKTOP/GoogleScholar/"
    if not os.path.exists(savepath):
      os.mkdir(savepath)
    # filename of markdown file with time
    timestr  = time.strftime('%Y%m%d', time.localtime())
    filename = f"{savepath}{timestr}_google_scholar_.md"
    # if file is not exists, then creat it
    if not os.path.exists(filename):
      open(filename, "w").close()

    print(f'Unread messages:{cout} ----- Unique paper:{len(Dicts["TitleKey"])}\n\n\n')
    # write the dict "Dicts" into markdown file
    with open(filename, 'w', encoding="utf8") as file:
      file.write(f'Unread messages:{cout}\nUnique paper:{len(Dicts["TitleKey"])}\n\n\n')
      for value in Dicts['value']:
        file.write(f'{value}\n\n\n')

def main():
    service = get_gmail_service()
    get_unread_messages(service)

if __name__ == '__main__':
    main()