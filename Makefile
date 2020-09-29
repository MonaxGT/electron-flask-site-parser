build-python:
	pyinstaller backend/app.py --distpath appdist
	rm -rf build/
	rm -rf app.spec

build_electron:
	./node_modules/.bin/electron-packager . --overwrite \
	--ignore="backend" \
	--ignore=".venv" \
	--ignore=".vscode" \
	--ignore="Makefile" \
	--ignore="requirements.txt"
