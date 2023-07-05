SRC = lektor_tekir
POTFILE = messages.pot
TRANSLATIONS = $(SRC)/translations

i18n-extract:
	pybabel extract -F babel.cfg -o $(POTFILE) $(SRC)

i18n-update:
	pybabel update -i $(POTFILE) -d $(TRANSLATIONS)

i18n-compile:
	pybabel compile -d $(TRANSLATIONS)

i18n-init:
	pybabel init -i $(POTFILE) -d $(TRANSLATIONS) -l $(lang)
