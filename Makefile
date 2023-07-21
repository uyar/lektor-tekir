SRC = lektor_tekir
DOMAIN = lektor_tekir
POTFILE = $(DOMAIN).pot
TRANSLATIONS = $(SRC)/translations

i18n-extract:
	pybabel extract -F babel.cfg -o $(POTFILE) $(SRC)

i18n-update:
	pybabel update -i $(POTFILE) -D $(DOMAIN) -d $(TRANSLATIONS)

i18n-compile:
	pybabel compile -D $(DOMAIN) -d $(TRANSLATIONS)

i18n-init:
	pybabel init -i $(POTFILE) -D $(DOMAIN) -d $(TRANSLATIONS) -l $(lang)
