# gema

![Logo Gema](./logo-gema.svg)

gema stands for **GobCan Email Alarm**

> This tool lets you receive Telegram notification when you receive an incoming email to Gobierno de Canarias.

## Setup

1. Create a Python virtualenv (>=3.10)
2. `pip install -r requirements.txt`
3. Add custom values in `.env` file for the following params:
   - `TELEGRAM_BOT_TOKEN`
4. Add users' config in `config.yaml`:

```yaml
users:
  - name: Sergio Delgado Quintero
    inbox: hello@gobiernodecanarias.org
    pop3:
      username: user@example.com
      password: thepassword
      addr: pop3.example.com
    telegram_id: your_telegram_id
```

## Usage

1. Launch application:

```console
$ python main.py
```

> You can change loglevel using: `-linfo` `-ldebug` `-lerror`

2. Disable notifications:

```console
$ python main.py --no-notify
```

3. Disable deleting emails after dispatching:

```console
$ python main.py --no-delete
```
