import re

from unidecode import unidecode

def slugify(s):
	return re.sub(r'\W+', '-', unidecode(s).lower())
