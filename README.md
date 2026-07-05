# bYolk

Nest Egg -> Egg Yolk + Broke = bYolk

## Frameworks and Technologies used:

- Django
- DaisyUI
- Docker/Podman

## Installation instructions

#### Linux

#### Fedora

1. Download and install Docker - Instructions can be found here: https://docs.docker.com/desktop/setup/install/linux/fedora/
2. Clone the repository, or download as a zip and extract
```bash
git clone https://git.silverbricc.com/JamesMakela/bYolk.git
```

3. Navigate to the directory in your terminal
4. Copy the `.env.example` to `.env`
```bash
cp .env.example .env
```

5. Open and edit the `.env` file in your text editor
	1. Set the db password to a password of your choosing
	2. Set the django secret key
		- You can generate this with the below:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

6. If you are running in production mode, you will need to set the `CSRF_TRUSTED_ORIGINS` and `ALLOWED_HOSTS` in the `.env` file
7. Ensure NPM is installed - instructions here: https://nodejs.org/en/download
8.  Run with `./start-dev.sh`, or `./start.sh` if running in production mode
9. Access the application at either `127.0.0.1:8000` or the URL you have set up if running in production

#### NixOS

1. Ensure you have direnv installed: https://wiki.nixos.org/wiki/Direnv
2. Clone the repository, or download as a zip and extract
3. Navigate to the directory in your terminal
4. Copy the `.env.example` to `.env`
```bash
cp .env.example .env
```

5. Open and edit the `.env` file in your text editor as above
	- You may want to set the `CONTAINER_RUNTIME` in the `.env` file to podman, or change the `shell.nix` to use docker if you prefer
6. In your terminal type direnv allow
7. Run with `./start-dev.sh`, or `./start.sh` if running in production mode
8. Access the application at either `127.0.0.1:8000` or the URL you have set up if running in production

### Windows

- Instructions to come later
