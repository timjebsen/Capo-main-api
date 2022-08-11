#! /bin/sh
echo "Setting up env and installing:"
python3 -m venv venv
. venv/bin/activate
python3 --version
cd dist
ls | xargs pip3 install --force-reinstall
cd ..
pip3 install aiohttp aiohttp_cors
pip3 install gunicorn
pip3 install -r requirements.txt
gunicorn -w 4 'capo_main_api:production()' -b 0.0.0.0:8008 --worker-class aiohttp.GunicornWebWorker


