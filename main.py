import poplib

import yaml

import settings


def get_emails(config_path: str = settings.CONFIG_PATH):
    config = yaml.load(open(config_path), Loader=yaml.FullLoader)
    for user_cfg in config['users']:
        server = poplib.POP3(user_cfg['pop3'])
        server.user(user_cfg['username'])
        server.pass_(user_cfg['password'])
        num_emails = len(server.list()[1])
        for email_id in range(1, num_emails + 1):
            email_content = server.retr(email_id)[1]
            yield email_content
            server.dele(email_id)
        server.quit()


for email in get_emails():
    print(email)
