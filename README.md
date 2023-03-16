# The Sol Den Bot (The Referee)

## Installation

Clone the repo:
```bash
git clone https://github.com/quellen-sol/tsdbot2.git
```

Start up virtual environment. Pipenv recommended:
```bash
python3 -m pipenv shell
```

Install Dependencies:
```bash
pip3 install -r requirements.txt
```

Create a bot and token from the Discord Developers dashboard and use that for local testing (See [.env.example](.env.example))

## Running locally

Build with docker:
```bash
./build.sh
```

Run
```bash
./run.sh
```

It may also be possible to just run [main.py](main.py)

```bash
python3 main.py
```