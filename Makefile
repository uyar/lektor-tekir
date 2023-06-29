pot:
	pybabel extract -F babel.cfg -o messages.pot lektor_tekir

po:
	pybabel update -i messages.pot -d lektor_tekir/translations/

mo:
	pybabel compile -d lektor_tekir/translations/
