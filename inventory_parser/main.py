import sys
import re
import os
import json
from datetime import datetime
import calendar
import codecs

def readNextLine(f):
    line = f.readline()
    #print(line.strip())
    while ('(digitaal)' in line or '(digital)' in line or len(line) < 2) and line != "":
        line = f.readline()
        #print(line.strip())
    #remove line endings
    return line.strip()

filenames = []

dir = os.path.dirname(os.path.realpath(__file__))

for file in os.listdir(dir):
    if file.endswith(".txt"):
        filename= os.path.join(dir, file)
        print(filename)
        filenames.append(filename)

gemeentes = dict()
entries = 0

re_date = re.compile('../../.... - ../../....*')
re_index = re.compile('...._..._....._..._.*')
re_type = re.compile('(PAROCHIEREGISTERS|REGISTRES PAROISSIAUX|PFARRREGISTER)\..?')
re_paroch = re.compile('(.+)(, paroisse |, parochie |, Pfarre )(.+)$|(.+)(, )(.+ - .+)$')


for filename in filenames:
    #print ("Reading Filen" + filename)

    with open(filename, encoding="utf8") as f:

        line = f.readline().strip()
        bloknr = line

        i = 1
        start = False
        while start is False:
            i = i + 1
            line = f.readline()
            if 'Naam archiefblok' in line or 'Nom du bloc' in line:
                naam_archiefblok = f.readline().strip()
                line = f.readline().strip()
                if 'riode' not in line:
                    naam_archiefblok = naam_archiefblok + ' ' + line
                naam_archiefblok = naam_archiefblok.replace('Parochieregisters', '')
                naam_archiefblok = naam_archiefblok.replace('Registres paroissiaux', '')
                naam_archiefblok = naam_archiefblok.replace('Pfarrregister', '')
                naam_archiefblok = naam_archiefblok.replace('.', '')
                naam_archiefblok = naam_archiefblok.split('(')[0]

                print(filename + ' ' + naam_archiefblok)
            if 'Beschrijving van de series en archiefbestanddelen' in line:
                start = True
            if 'Description des séries et des éléments' in line:
                start = True


            #print(line)

        gemeente = ''
        parochie = ''
        aktetype = ''

        while line != "":

            i = i+1
            #print(line)
            m = re_paroch.match(line)
            #if m != None:
            #    print(m.groups())
            if m:
                if m.groups()[3] is None:
                    gemeente = m.groups()[0]
                    parochie = m.groups()[2]
                else:
                    gemeente = m.groups()[3]
                    parochie = m.groups()[5]

                line = readNextLine(f)
                if 'Parochieregisters' in gemeente:
                     raise Exception("Something is rotten")
                if naam_archiefblok not in gemeentes.keys():
                    gemeentes[naam_archiefblok] = dict()
                if gemeente not in gemeentes[naam_archiefblok].keys():
                    gemeentes[naam_archiefblok][gemeente] = dict()
                if parochie not in gemeentes[naam_archiefblok][gemeente].keys():
                    gemeentes[naam_archiefblok][gemeente][parochie] = list()

            if re_type.match(line):
                line1 = line
                line = readNextLine(f)
                if (line.isupper() and not '.' in line and not re_index.match(line)):
                    aktetype = (line1 + ' ' + line)
                    line = readNextLine(f)
                else:
                    aktetype = (line1)

            if re_index.match(line):
                inventarisnr = line
                while not re_date.match(line):
                    line = readNextLine(f)

                dates = line.split(' - ')

                def sanitizeDate(date):
                    date = date.replace('?', '9')
                    date = date.replace('.', '9')
                    [day, month, year] = date.split('/')

                    if len(year) > 4:
                        year = year[0:3]
                    if len(year) == 3:
                        year = year + '9'

                    if int( day) == 0:
                        day = '01'
                    if int (month) == 0:
                        month = '01'
                    if int (year) == 0:
                        year = '0001'
                    if int(month) > 12:
                        month = '12'
                    maxday = calendar.monthrange(int(year), int(month))[-1]
                    if int(day) > maxday:
                        day = maxday
                    return str(day) + '/' + month + '/' + year

                dates[0] = sanitizeDate(dates[0])
                dates[1] = sanitizeDate(dates[1])

                startdate = datetime.strptime(dates[0], '%d/%m/%Y')
                enddate = datetime.strptime(dates[1], '%d/%m/%Y')

                aktetype = aktetype.split('. ')[-1].capitalize()
                url = "https://search.arch.be/nl/zoeken-naar-archieven/zoekresultaat/ead/zoekresultaat/eadid/"+ bloknr+"/sunitid/"+""+inventarisnr
                entry = {'bloknr': bloknr, 'aktetype':aktetype, 'inventarisnr': inventarisnr, 'dates':line, 'startdate':dates[0], 'enddate':dates[1], 'url':url}
                gemeentes[naam_archiefblok][gemeente][parochie].append(entry)
                entries = entries + 1

            line = readNextLine(f)


j = json.dumps(gemeentes, indent=4, sort_keys=True)
jsonFile = open('links.json', 'w')
print(j, file=jsonFile)
jsonFile.close()

output = codecs.open('parochieregisters.py', 'w',  "utf-8")
print('gemeentes = ' + str(gemeentes), file=output)

output.close()

print('Found ' + str(entries) + ' links')

sys.exit()