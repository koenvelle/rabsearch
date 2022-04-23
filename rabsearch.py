# LICENSE :
# This work is shared under the Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
# created by Koen VELLE, Roeselare, Belgium
# https://github.com/koenvelle/rabsearch
#
#
# You are free to:
# Share — copy and redistribute the material in any medium or format
# Adapt — remix, transform, and build upon the material
# The licensor cannot revoke these freedoms as long as you follow the license terms.


#fixme : search without 'gemeente' results in crash in map creation and search thread.


from geopy.geocoders import Nominatim
import sys
import roles
from citylocs import citylocs, city_names
from geopy import distance
import time

import PySimpleGUI as sg
import webbrowser
import requests
import re
import threading
from parochieregisters import gemeentes as parochieregisters

import folium

city_names.insert(0, '')

sg.theme('SystemDefaultForReal')

geolocator = Nominatim(user_agent="genealocsearch", timeout = 10)
city_loc = geolocator.geocode("beveren aan de ijzer" + ", Belgium")
if city_loc != None:
    print("beveren aan de ijzer", city_loc.latitude, ":", city_loc.longitude)

eerste_pers_voor = sg.InputText(size=(20), key='pers1_voornaam')
eerste_pers_achter = sg.InputText(size=(20), key='pers1_achternaam')
eerste_pers_rol = sg.DropDown(size=20, key = 'pers1_rol', values=[ x[1] for x in roles.person_roles], default_value=roles.person_roles[0][1])

eerste_persoon_beroep = sg.InputText(size=(20), key='pers1_beroep')

zw_m = sg.Checkbox('M', key = 'zw_m')
zw_v = sg.Checkbox('V', key = 'zw_v')
zw_o = sg.Checkbox('Niet vermeld', key = 'zw_o')

tweede_pers_voor = sg.InputText(size=(20), key='pers2_voornaam')
tweede_pers_achter =  sg.InputText(size=(20), key='pers2_achternaam')
tweede_pers_rol = sg.DropDown(size=20, key = 'pers2_rol', values=[ x[1] for x in roles.person_roles], default_value=roles.person_roles[0][1])
akteperiode = sg.InputText(size=(20), key='akteperiode')
aktegemeente_zoek = sg.InputText(size=(46), key='aktegemeente_zoek', enable_events=True)
check_results = sg.Button("Zoek aantal resultaten per gemeente", key='tel_resultaten', enable_events=True,tooltip="Zoek het aantel personen per gemeente die voldoen aan de opgegeven criteria (kan even duren)")
abort_search = sg.Button("Stop...", key='stop_tellen', enable_events=True,tooltip="Breek het zoeken voortijdig af", disabled=True)
aktegemeente_dropdown = sg.DropDown(values=city_names, enable_events=True,
                                    key = 'aktegemeente_kies', default_value='', readonly=True)
progress_bar = sg.ProgressBar(max_value = 100, size = (44, 10), key='progress', visible=False)
radius_slider = sg.Slider(range=(0,50), orientation='horizontal', size=(50,10), key="radius", enable_events=True , default_value=10)
gemeentelijst = sg.Listbox(values=[], size=(82, 30), key='gemeentelijst', enable_events=True, tooltip="Klik op de gewenste gemeente om de resultaten te zien")

kaart = sg.Button("Kaart", disabled = True, enable_events=True, key="kaart")

zoek = sg.Button('Zoek', key='zoek', tooltip="Toon de resultaten voor de opgegeven aktegemeente")

inputs = [radius_slider, gemeentelijst, eerste_persoon_beroep, eerste_pers_voor, eerste_pers_achter, eerste_pers_rol,
          tweede_pers_achter, tweede_pers_voor, tweede_pers_rol, zw_o, zw_v, zw_m, aktegemeente_dropdown, akteperiode,
          check_results, aktegemeente_zoek]

person1_column = [
        [sg.Text("Persoon 1", size=15, text_color='black', font='bold')],
        [sg.Text("Achternaam", size=15),  eerste_pers_achter],
        [sg.Text("Voornaam", size=15), eerste_pers_voor],
        [sg.Text("Rol", size=15), eerste_pers_rol],
        [sg.Text("Beroep", size=15), eerste_persoon_beroep],
        [sg.Text("Geslacht", size=15), zw_m, zw_v, zw_o]
]
person2_column = [
        [sg.Text("Persoon 2", size=15, text_color='black', font='bold')],
        [sg.Text("Achternaam", size=15), tweede_pers_achter],
        [sg.Text("Voornaam", size=15), tweede_pers_voor],
        [sg.Text("Rol", size=15), tweede_pers_rol],
        [sg.Text("")],
        [sg.Text("")]
]
aktegemeente_row = [
        [sg.Text("Aktegemeente", text_color='black', font='bold')],
        [sg.Text("Periode", size=15), akteperiode],
        [sg.Text("Gemeente", size=15), aktegemeente_zoek],
        [sg.Text("", size=15),aktegemeente_dropdown],
        [zoek],
]
buurgemeente_row= [
        [sg.Text("Zoeken in omgeving", size=25, text_color='black', font='bold')],
        [sg.Text("Afstand(km)", size=15), radius_slider],

        [check_results, abort_search, kaart],
        [progress_bar],
        [gemeentelijst]
]
layout_personen = [
    [ sg.Column(
        [[
        sg.Column(person1_column),
        sg.VerticalSeparator(),
        sg.Column(person2_column)
        ]]
        , justification='left')

    ],
    [sg.HorizontalSeparator()],
    [sg.Column(aktegemeente_row, justification = 'left')],
    [sg.HorizontalSeparator()],
    [sg.Column(buurgemeente_row, justification = 'left')],
]

gemeentelijst_unsorted = list(parochieregisters.keys())
gemeentelijst_sorted = sorted(gemeentelijst_unsorted)

print(list(gemeentelijst_unsorted)[0:100])
print(list(gemeentelijst_sorted)[0:100])
PR_gemeentelijst = sg.DropDown(values=gemeentelijst_sorted, size=60, key='parochieregisters_gemeente', enable_events=True)
PR_parochielijst = sg.DropDown(values=['kies eerst een gemeente'], size=60, key='parochieregisters_parochie', enable_events=True, disabled=True)
PR_typelijst = sg.DropDown(values=['kies eerst een gemeente en een parochie'], size=60, key='parochieregisters_type', disabled=True, enable_events=True )
PR_jaar_van = sg.InputText(key='PR_jaar_van', size = 5, visible = False)
PR_jaar_tot = sg.InputText(key='PR_jaar_tot', size = 5, visible = False)
PR_links = sg.Listbox(values=[], key='parochieregisters_links',size=(90,50), enable_events=True)

layout_registers = [
    [sg.Text("Gemeente", size=15), PR_gemeentelijst],
    [sg.Text("Parochie", size=15), PR_parochielijst],
    [sg.Text("Type", size=15), PR_typelijst],
    [sg.Text("Jaartal", size=15, visible=False), PR_jaar_van, sg.Text("-", visible=False), PR_jaar_tot],
    [sg.HorizontalSeparator()],
    [PR_links],
]

tabgrp = [
    [sg.TabGroup(
        [
        [sg.Tab('Personen Zoeken', layout_personen,title_color='Blue', element_justification='left')],
        [sg.Tab('Parochieregisters', layout_registers,title_color='Blue', element_justification='left')]
        ],
        selected_title_color="green"
    ),
    [sg.Text("Koen Velle (koen.velle@gmail.com)")],
    [sg.Text("'Standing on the shoulders of Giants' (de vrijwilligers van het RAB)")]
    ]
]




window = sg.Window(title="RAB Person Query Generator", layout=tabgrp , margins=(20, 20), element_justification='c', finalize=True, resizable=True, location=(0,0))

eerste_pers_rol.bind("<FocusOut>", "eerste_pers_rol_FocusOut")
eerste_pers_rol.bind("<ButtonRelease>", "eerste_pers_rol_FocusIn")
eerste_pers_rol.bind("<KeyRelease>", "eerste_pers_rol_predict")
eerste_pers_rol.bind("<Return>", "eerste_pers_rol_enter")

tweede_pers_rol.bind("<FocusOut>", "tweede_pers_rol_FocusOut")
tweede_pers_rol.bind("<ButtonRelease>", "tweede_pers_rol_FocusIn")
tweede_pers_rol.bind("<KeyRelease>", "tweede_pers_rol_predict")

aktegemeente_dropdown.bind(bind_string="<KeyRelease>", key_modifier="", propagate=True)

def getCityLoc(src):
    return citylocs[next((i for i, v in enumerate(citylocs) if v[0] == src))]


def updateList(src, radius):
    matches = []
    if (src!= '' and (src in city_names)):
        naam, (src_latitude, src_longitude) = getCityLoc(src)

        distances = []

        for dest, (dest_latitude, dest_longitude) in citylocs:
            d = distance.distance((src_latitude, src_longitude), (dest_latitude, dest_longitude))
            distances.append((round(d.km, 2), dest))

        distances.sort()

        for d in distances:
            if d[0] <= radius:
                matches.append(d[1])#, str(d[0])+'km')

    gemeentelijst.update(matches)

def autocomplete_dropdown(value):

    def predict_text(input, lista):
        pattern = ('(^|\()'+re.escape(str(input).upper()) + '.*')
        return [w for w in lista if re.search(pattern, w)]

    prediction_list = predict_text(value, city_names)
    aktegemeente_dropdown.update(prediction_list[0] if len(prediction_list) > 0 else 'geen match', values=prediction_list)
    aktegemeente_zoek.update(value=value.upper())

    return aktegemeente_zoek.get()

def createURL(values, gemeente):
    vn1 = values['pers1_voornaam']
    an1 = values['pers1_achternaam']
    vn2 = values['pers2_voornaam']
    an2 = values['pers2_achternaam']
    beroep1 = values['pers1_beroep']
    rol1 = values['pers1_rol']
    rol2 = values['pers2_rol']
    periode = values['akteperiode']
    zw_m = '1' if values['zw_m'] else '0'
    zw_v = '1' if values['zw_v'] else '0'
    zw_o = '1' if values['zw_o'] else '0'

    if vn1 != '':
        vn1 = "q/persoon_voornaam_t_0/" + vn1 + '/'
    if an1 != '':
        an1 = "q/persoon_achternaam_t_0/" + an1 + '/'
    if beroep1 != '':
        beroep1 =  "q/persoon_beroep_s_0/"+beroep1+"/"
    if vn2 != '':
        vn2 = "q/persoon_voornaam_t_1/" + vn2 + '/'
    if an2 != '':
        an2 = "q/persoon_achternaam_t_1/" + an2 + '/'
    if rol1 != '':
        rol1 = str([id for (id, type) in roles.person_roles if type == rol1][0])
        rol1 = "q/persoon_rol_s_0/" + rol1 + '/'
    if rol2 != '':
        rol2 = str([id for (id, type) in roles.person_roles if type == rol2][0])
        rol2 = "q/persoon_rol_s_1/" + rol2 + '/'
    if gemeente != '':
        gemeente = "&aktegemeente=" + gemeente
    if '(' in gemeente:
        gemeente = gemeente.split('(')[0]
    if periode != '':
        periode = "&akteperiode=" + periode


    url = "https://search.arch.be/nl/zoeken-naar-personen/zoekresultaat/" + an1 + vn1 + rol1 + an2 + vn2 \
          + rol2 + "q/zoekwijze/s/" + beroep1 + "?M="+ zw_m +"&V="+ zw_v +"&O="+ zw_o +"&persoon_0_periode_geen=0" \
          + gemeente + periode
    return url

def disableInputs(value):
    for item in inputs:
        item.update(disabled=value)
    abort_search.update(disabled=(value==False))


class ResultsScavenger(threading.Thread):

    def __init__(self, values, gemeentes, results, match_indexes):
        self.__window = window
        self.__done = False
        self.__values = values
        self.__gemeentes = gemeentes
        self.__results = results
        self.__match_indexes = match_indexes
        self.__stop_requested = False
        threading.Thread.__init__(self)

    def collectResults(self, values, gemeentes, results, match_indexes):

        i = 0
        hit_map_locations = []
        for item in (gemeentes):

            url = createURL(values, item)

            if (self.__stop_requested == False):
                # Don't overload server....
                time.sleep(.5)
                r = requests.get(url)

                lines = str(r.content).split('\n')
                pattern = re.compile('.*Resultaten\s(\d+\s)-\s(\d+\s)van\s(\d+\s).*')

                for line in lines:
                    match = pattern.match(line)
                    if match != None:
                        hit_count = match.groups()[2]
                        results.append(item + ' (aantal : ' + hit_count + ')')
                        match_indexes.append(i)
                        name, (lat, lon) = getCityLoc(item)
                        hit_map_locations.append([name, lat, lon, hit_count, url])
                    else:
                        results.append(item + ' (aantal : 0)')

                i = i + 1
                window.write_event_value("progress", i)

        x, centre = getCityLoc(gemeentes[0])
        generateHitMap(centre, hit_map_locations, self.__values['radius'])
        window.write_event_value("done", 1)
        self.__stop_requested = False

    def run(self):
        self.__done = False
        self.collectResults(self.__values, self.__gemeentes, self.__results, self.__match_indexes)
        self.__done = True
        sys.exit()

    def done(self):
        return self.__done

    def clear(self):
        self.__done = False
        self.__stop_requested = False

    def completion(self):
        return ( (len(self.__results)*100) / len(self.__gemeentes) )

    def stop(self):
        self.__stop_requested = True



def generateHitMap(centre, locations, radius):

    m = folium.Map(location=centre, zoom_start=10)
    circle = folium.Circle(location=centre, radius=radius * 1000)
    circle.add_to(m)

    if (len(locations)):

        for location in locations:

            marker = folium.Marker(
                [location[1], location[2]],
                popup="<a href="+location[4]+"> Aantal hits: "+location[3]+"</a>",
                tooltip = location[0]+ " hits: "+location[3]
            )
            marker.add_to(m)

    m.save("rabsearch_hits.html")

def openHitMap():
    webbrowser.open("rabsearch_hits.html", autoraise=True)

def restoreRolesList(widget, value=None):
    default_roles_list = [x[1] for x in roles.person_roles]
    if value is None:
        value = default_roles_list[0]
    widget.update(values=default_roles_list, value=value)

def persRolDropDownHandler(widget, event, value):
    print('handler' + event)
    if event.endswith('predict'):
        pattern = re.compile('.*'+re.escape(value.lower())+'.*')
        matches = []
        for (id, role) in roles.person_roles:
            match = pattern.match(role.lower())
            if (match) :
                matches.append(role)
        if len(matches) == 1:
            restoreRolesList(widget, matches[0])
        else :
            widget.update(values=matches, value=value)

    elif event.endswith('FocusOut'):
        if len(widget.Values) > 0 :
            if (value not in widget.Values):
                print("restoring defaults")
                # whe have matches, and there is currently no complete valid value entered
                if window.find_element_with_focus() is not None:
                    print(" dropdown activated")
                    #have we opened the dropdown ?V
                    restoreRolesList(widget, widget.Values[0])
            else :
                # whe have matches, and there is currently a valid value entered
                print("boo")
                #we can attempt to restore the default list here, but somehow this messes up
                #the selected value...
        else :
            # no match on focus out
            restoreRolesList(widget)
            print("0 values")
            if window.find_element_with_focus() is None:
                widget.widget.event_generate('<Button>')
                print(" dropdown activated")


    elif event.endswith('FocusIn'):
        widget.Widget.select_range(0, 'end')

    elif event.endswith('enter'):
        widget.widget.tk_focusNext().focus()
        return ("break")

global rs
rs = None

def updatePRTypes(gemeente, parochie):
    types = list()
    for entry in parochieregisters[gemeente][parochie]:
        print(entry)
        types.append(entry['aktetype'])
    sortedtypes = sorted(list(set(types)))
    PR_typelijst.update(values=sortedtypes, value=sortedtypes[0], disabled=False)
    updatePRResults(gemeente, parochie, list(set(types))[0], PR_jaar_van.get() )

def updatePRResults(gemeente, parochie, type, jaar_van):
    allresults = parochieregisters[gemeente][parochie]

    global PRMatches
    PRMatches = []

    for i in allresults:
        if type == i['aktetype']:
            if jaar_van != '':
                print('fixme')
            else:
                PRMatches.append(i)

    i = 0
    PR_links_values=[]
    for match in PRMatches:
        PR_links_values.append(str(i).ljust(5) + ': ' + match['dates'] + ': ' + match['aktetype'])
        i = i + 1

    PR_links.update(values=PR_links_values)

def getScansURL(eadid, src_url):
    r = requests.get(src_url)
    time.sleep(.5)
    lines = (r.content.decode('utf-8')).split('\n')
    for index, elem in enumerate(lines):
        if '/inventarisnr/' in elem:
            inv_re = re.compile('.+/inventarisnr/(.+?)/.*')
            invnr = inv_re.match(elem)[1]
            break
    tgt_url = 'https://search.arch.be/nl/zoeken-naar-archieven/zoekresultaat/inventaris/rabscans/eadid/' +\
              eadid+'/inventarisnr/'+invnr+'/level/file'
    return tgt_url

while True:

    event, values = window.read()
    print(event, values)
    gemeente = values['parochieregisters_gemeente']
    parochie = values['parochieregisters_parochie']

    if event == 'parochieregisters_gemeente':
        parochies = list(parochieregisters[gemeente].keys())
        PR_parochielijst.update(disabled=False, values=parochies, value=parochies[0])
        updatePRTypes(gemeente, parochies[0])

    if event == 'parochieregisters_parochie':
        parochies = list(parochieregisters[gemeente].keys())
        updatePRTypes(gemeente, parochie)

    if event == 'parochieregisters_type':
        updatePRResults(gemeente, parochie, values['parochieregisters_type'], values['PR_jaar_van'])

    if event == 'parochieregisters_jaar_van':
        updatePRResults(gemeente, parochie, values['parochieregisters_type'], values['PR_jaar_van'])

    if event == 'parochieregisters_links':
        #fixme if valid value
        print(PRMatches)
        linkindex = int(values['parochieregisters_links'][0].split(':')[0])

        url = PRMatches[linkindex]['url']
        webbrowser.open_new_tab(getScansURL(PRMatches[linkindex]['bloknr'], PRMatches[linkindex]['url']))

    if event == "Exit" or event == sg.WIN_CLOSED:
        sys.exit()
        break

    if event.startswith('pers1_rol'):
        value = values['pers1_rol'].capitalize()
        persRolDropDownHandler(eerste_pers_rol, event, value)

    if event.startswith('pers2_rol'):
        value = values['pers2_rol'].capitalize()
        persRolDropDownHandler(tweede_pers_rol, event, value)

    if event == 'kaart':
        openHitMap()
    if event == 'done':
        disableInputs(False)
        print ("update gemeentelijst")
        gemeentelijst.update(results)

        print ("update kaart")
        if len(match_indexes):
            kaart.update(disabled=False)
        for i in match_indexes:
            gemeentelijst.Widget.itemconfigure(i, bg='lightgreen', fg='black')  # set options for item in listbox
        print ("kaart geupdate")
        rs.clear()
        print ("rs cleared")

    elif event == 'progress':
        progress_bar.update(current_count=rs.completion(), visible=True)

    elif event == "stop_tellen":
        kaart.update(disabled=True)
        rs.stop()

    elif event == "Exit" or event == sg.WIN_CLOSED:
        break
    elif event == "aktegemeente_zoek":
        gem = autocomplete_dropdown(values['aktegemeente_zoek'])
        updateList(gem, values['radius'])
    elif event == "aktegemeente_kies":
        aktegemeente_zoek.update(values['aktegemeente_kies'])
        updateList(values['aktegemeente_kies'], values['radius'])
    elif event == "radius":
        updateList(values['aktegemeente_zoek'], values['radius'])
    elif event== "tel_resultaten":
        kaart.update(disabled=True)
        gem = autocomplete_dropdown(values['aktegemeente_zoek'])
        updateList(gem, values['radius'])
        results = []
        match_indexes = []
        disableInputs(True)
        progress_bar.update(0, visible=False)
        rs = ResultsScavenger(values, gemeentelijst.get_list_values(), results, match_indexes)
        rs.start()

    elif event == "gemeentelijst" or event == "zoek":
        aktegemeente = values['aktegemeente_zoek'] if event == 'zoek' else values['gemeentelijst'][0] if len(values['gemeentelijst']) else ''
        aktegemeente = aktegemeente.split('(aantal')
        url = createURL(values, aktegemeente[0])
        webbrowser.open_new_tab(url)

sys.exit()



source = "nieuwkerke".upper()
naam, (src_latitude, src_longitude)= getCityLoc(source)

print("Afstand tot ", naam, "(",src_latitude, src_longitude,")")

distances=[]

for dest, (dest_latitude, dest_longitude) in citylocs:
    d = distance.distance((src_latitude, src_longitude), (dest_latitude,dest_longitude))
    distances.append((round(d.km, 2), dest))


distances.sort()

for i in range(1,20):
    target_distance, target_name = distances[i]
    print( target_name, target_distance, "km")

exit()
# Initialize Nominatim API
geolocator = Nominatim(user_agent="genealocsearch", timeout = 10)

location1 = geolocator.geocode("Woumen")

print("The latitude of the location is: ", location1.latitude)
print("The longitude of the location is: ", location1.longitude)

distances = []

unique_city_names = list(dict.fromkeys(city_names))
city_count = len(unique_city_names)



i = 0
for city in unique_city_names :
    i = i+1
    city_loc = geolocator.geocode(city+", Belgium")

    if city_loc != None:
        time.sleep(1)
        print(city, ":", city_loc.latitude, ":", city_loc.longitude)
        #dist = distance.distance((location1.latitude, location1.longitude), (city_loc.latitude, city_loc.longitude))
        #distances.append((dist.km, city))
        #print(int(i/ city_count * 10000)/100, " ", city, " ", dist.km)


#distances.sort()
#print(distances)



# See PyCharm help at https://www.jetbrains.com/help/pycharm/

