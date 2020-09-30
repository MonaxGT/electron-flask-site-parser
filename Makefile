build: build-python build-electron

build-python:
	pyinstaller backend/app.py --distpath appdist --noconfirm
	mkdir appdist/app/search_engine_scraper
	cp .venv/lib/python3.8/site-packages/search_engine_scraper/proxies.txt \
		appdist/app/search_engine_scraper/proxies.txt
	cp .venv/lib/python3.8/site-packages/search_engine_scraper/user_agents.txt \
		appdist/app/search_engine_scraper/user_agents.txt
	rm -rf build/
	rm -rf app.spec

build-electron:
	./node_modules/.bin/electron-packager . --overwrite \
	--ignore="backend" \
	--ignore=".venv" \
	--ignore=".vscode" \
	--ignore="Makefile" \
	--ignore="requirements.txt" \
	--ignore=".gitignore"
