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
from datetime import datetime

import pkg_resources
from geopy.geocoders import Nominatim
import sys
import roles
from citylocs import citylocs, city_names
from geopy import distance
import time

import PySimpleGUI
import webbrowser
import requests
import re
import threading
from parochieregisters import gemeentes as parochieregisters
from tkinter import *


import folium

version_major = 1
version_minor = 3

def get_latest_version():
    version_url = "https://koenvelle.be/rabsearch/version"
    r = requests.get(version_url)
    lines = (r.content.decode('utf-8')).split('\n')
    majmin = (int(lines[0].split('.')[0]), int(lines[0].split('.')[1]))
    return (lines[0].strip(), majmin)

def check_for_new_version( current, latest):
    if current[0] < latest[0]:
        return True
    elif current[0] == latest[0] and current[1] < latest[1]:
        return True
    return False






city_names.insert(0, '')

PySimpleGUI.theme('SystemDefaultForReal')

geolocator = Nominatim(user_agent="genealocsearch", timeout=10)
city_loc = geolocator.geocode("beveren aan de ijzer" + ", Belgium")
if city_loc is not None:
    print("beveren aan de ijzer", city_loc.latitude, ":", city_loc.longitude)

eerste_pers_voor = PySimpleGUI.InputText(size=20, key='pers1_voornaam')
eerste_pers_achter = PySimpleGUI.InputText(size=20, key='pers1_achternaam')
eerste_pers_rol = PySimpleGUI.DropDown(size=20, key='pers1_rol', values=[x[1] for x in roles.person_roles],
                                       default_value=roles.person_roles[0][1])

eerste_persoon_beroep = PySimpleGUI.InputText(size=20, key='pers1_beroep')

zw_m = PySimpleGUI.Checkbox('M', key='zw_m')
zw_v = PySimpleGUI.Checkbox('V', key='zw_v')
zw_o = PySimpleGUI.Checkbox('Niet vermeld', key='zw_o')

tweede_pers_voor = PySimpleGUI.InputText(size=20, key='pers2_voornaam')
tweede_pers_achter = PySimpleGUI.InputText(size=20, key='pers2_achternaam')
tweede_pers_rol = PySimpleGUI.DropDown(size=20, key='pers2_rol', values=[x[1] for x in roles.person_roles],
                                       default_value=roles.person_roles[0][1])

radio_zoekwijze_exact = PySimpleGUI.Radio('Exact', "ZOEKWIJZE", default=True, key='zoekwijze_exact')
radio_zoekwijze_klinkt_als = PySimpleGUI.Radio('Klinkt als', "ZOEKWIJZE", key='zoekwijze_klinkt_als',  default=False)

akteperiode = PySimpleGUI.InputText(size=20, key='akteperiode')
aktegemeente_zoek = PySimpleGUI.InputText(size=46, key='aktegemeente_zoek', enable_events=True)
check_results = PySimpleGUI.Button("Zoek aantal resultaten per gemeente", key='tel_resultaten', enable_events=True,
                                   tooltip="Zoek het aantel personen per gemeente die voldoen aan de opgegeven criteria (kan even duren)",
                                   disabled=True)
abort_search = PySimpleGUI.Button("Stop...", key='stop_tellen', enable_events=True, tooltip="Breek het zoeken voortijdig af",
                                  disabled=True)
aktegemeente_dropdown = PySimpleGUI.DropDown(values=city_names, enable_events=True,
                                             key='aktegemeente_kies', default_value='', readonly=True)
progress_bar = PySimpleGUI.ProgressBar(max_value=100, size=(44, 10), key='progress', visible=False)
radius_slider = PySimpleGUI.Slider(range=(0, 50), orientation='horizontal', size=(50, 10), key="radius", enable_events=True,
                                   default_value=10)
radius_search_results = PySimpleGUI.Listbox(values=[], size=(82, 30), key='gemeentelijst', enable_events=True,
                                            tooltip="Klik op de gewenste gemeente om de resultaten te zien")

kaart = PySimpleGUI.Button("Kaart", disabled=True, enable_events=True, key="kaart")

zoek = PySimpleGUI.Button('Zoek', key='zoek', tooltip="Toon de resultaten voor de opgegeven aktegemeente")
reset = PySimpleGUI.Button('Reset', key='reset', tooltip="Reset alle velden")

inputs = [radius_slider, eerste_persoon_beroep, eerste_pers_voor, eerste_pers_achter,
          eerste_pers_rol,
          tweede_pers_achter, tweede_pers_voor, tweede_pers_rol, zw_o, zw_v, zw_m, aktegemeente_dropdown, akteperiode,
          check_results, aktegemeente_zoek]

person1_column = [
    [PySimpleGUI.Text("Persoon 1", size=15, text_color='black', font='bold')],
    [PySimpleGUI.Text("Achternaam", size=15), eerste_pers_achter],
    [PySimpleGUI.Text("Voornaam", size=15), eerste_pers_voor],
    [PySimpleGUI.Text("Rol", size=15), eerste_pers_rol],
    [PySimpleGUI.Text("Beroep", size=15), eerste_persoon_beroep],
    [PySimpleGUI.Text("Geslacht", size=15), zw_m, zw_v, zw_o],
    [PySimpleGUI.Text("Zoekwijze", size=15), radio_zoekwijze_exact, radio_zoekwijze_klinkt_als]
    ]
person2_column = [
    [PySimpleGUI.Text("Persoon 2", size=15, text_color='black', font='bold')],
    [PySimpleGUI.Text("Achternaam", size=15), tweede_pers_achter],
    [PySimpleGUI.Text("Voornaam", size=15), tweede_pers_voor],
    [PySimpleGUI.Text("Rol", size=15), tweede_pers_rol],
    [PySimpleGUI.Text("")],
    [PySimpleGUI.Text("")]
]
zoekopties_row = [
    [PySimpleGUI.Text("Opties", size=15, text_color='black', font='bold')],
]
aktegemeente_row = [
    [PySimpleGUI.Text("Aktegemeente", text_color='black', font='bold')],
    [PySimpleGUI.Text("Gemeente", size=15), aktegemeente_zoek],
    [PySimpleGUI.Text("", size=15), aktegemeente_dropdown],
    [PySimpleGUI.Text("Periode", size=15), akteperiode],
    [zoek, reset],
]
buurgemeente_row = [
    [PySimpleGUI.Text("Zoeken in omgeving", size=25, text_color='black', font='bold')],
    [PySimpleGUI.Text("Afstand(km)", size=15), radius_slider],

    [check_results, abort_search, kaart],
    [progress_bar],
    [radius_search_results]
]
layout_personen = [
    [PySimpleGUI.Column(
        [[
            PySimpleGUI.Column(person1_column),
            PySimpleGUI.VerticalSeparator(),
            PySimpleGUI.Column(person2_column)
        ]]
        , justification='left')],
    [PySimpleGUI.HorizontalSeparator()],
    [PySimpleGUI.Column(aktegemeente_row, justification='left')],
    [PySimpleGUI.HorizontalSeparator()],
    [PySimpleGUI.Column(buurgemeente_row, justification='left')],
]

gemeentelijst_unsorted = list(parochieregisters.keys())
gemeentelijst_sorted = sorted(gemeentelijst_unsorted)

print(list(gemeentelijst_unsorted)[0:100])
print(list(gemeentelijst_sorted)[0:100])
PR_gemeentelijst = PySimpleGUI.DropDown(values=gemeentelijst_sorted, size=60, key='parochieregisters_gemeente',
                                        enable_events=True)
PR_parochielijst = PySimpleGUI.DropDown(values=['kies eerst een gemeente'], size=60, key='parochieregisters_parochie',
                                        enable_events=True, disabled=True, readonly=True)
PR_typelijst = PySimpleGUI.DropDown(values=['kies eerst een gemeente en een parochie'], size=60, key='parochieregisters_type',
                                    disabled=True, enable_events=True, readonly=True)
PR_jaar_van = PySimpleGUI.InputText(key='parochieregisters_jaar_van', size=5, visible=True, enable_events=True)
PR_jaar_tot = PySimpleGUI.InputText(key='PR_jaar_tot', size=5, visible=False)
PR_links = PySimpleGUI.Listbox(values=[], key='parochieregisters_links', size=(90, 50), enable_events=True)

layout_registers = [
    [PySimpleGUI.Text("Gemeente", size=15), PR_gemeentelijst],
    [PySimpleGUI.Text("Parochie", size=15), PR_parochielijst],
    [PySimpleGUI.Text("Type", size=15), PR_typelijst],
    [PySimpleGUI.Text("Jaartal", size=15, visible=True), PR_jaar_van, PySimpleGUI.Text("-", visible=False), PR_jaar_tot],
    [PySimpleGUI.HorizontalSeparator()],
    [PR_links],
]

update = "https://koenvelle.be/rabsearch"
if check_for_new_version((version_major, version_minor), get_latest_version()[1]):
    update = update + " ! Nieuwe versie beschikbaar !"

tabgrp = [
    [PySimpleGUI.TabGroup(
        [
            [PySimpleGUI.Tab('Personen Zoeken', layout_personen, title_color='Blue', element_justification='left')],
            [PySimpleGUI.Tab('Parochieregisters', layout_registers, title_color='Blue', element_justification='left')]
        ],
        selected_title_color="green"
    ),
        [PySimpleGUI.Text("Versie : " + str( version_major)+'.' + str(version_minor))],
        [PySimpleGUI.Text(update, text_color='red', font=('Courier New', 12, 'underline'), enable_events=True, key='koenvelle.be')],
        [PySimpleGUI.Text("Koen Velle (koen.velle@gmail.com)")],
        [PySimpleGUI.Text("'Standing on the shoulders of Giants' (de vrijwilligers van het RAB)")]
    ]
]

window = PySimpleGUI.Window(title="RAB Person Query Generator", layout=tabgrp, margins=(20, 20), element_justification='c',
                            finalize=True, resizable=True, location=(0, 0))

eerste_pers_rol.bind("<FocusOut>", "eerste_pers_rol_FocusOut")
eerste_pers_rol.bind("<ButtonRelease>", "eerste_pers_rol_FocusIn")
eerste_pers_rol.bind("<KeyRelease>", "eerste_pers_rol_predict")
eerste_pers_rol.bind("<Return>", "eerste_pers_rol_enter")

tweede_pers_rol.bind("<FocusOut>", "tweede_pers_rol_FocusOut")
tweede_pers_rol.bind("<ButtonRelease>", "tweede_pers_rol_FocusIn")
tweede_pers_rol.bind("<KeyRelease>", "tweede_pers_rol_predict")
tweede_pers_rol.bind("<Return>", "tweede_pers_rol_enter")

PR_gemeentelijst.bind("<FocusOut>", "parochieregisters_gemeente_FocusOut")
PR_gemeentelijst.bind("<ButtonRelease>", "parochieregisters_gemeente_FocusIn")
PR_gemeentelijst.bind("<KeyRelease>", "parochieregisters_gemeente_predict")
PR_gemeentelijst.bind("<Return>", "parochieregisters_gemeente_enter")

aktegemeente_dropdown.bind(bind_string="<KeyRelease>", key_modifier="", propagate=True)

resetinputs = [eerste_persoon_beroep, eerste_pers_voor, eerste_pers_achter,
          tweede_pers_achter, tweede_pers_voor, aktegemeente_dropdown, akteperiode,
          ]

def reset_all_fields():
    for item in resetinputs:
        item.update("")
    eerste_pers_rol.update("Alle rollen")
    tweede_pers_rol.update("Alle rollen")
    zw_o.update(False)
    zw_v.update(False)
    zw_m.update(False)
    radius_slider.update(10)

def get_city_location(src):
    return citylocs[next((i for i, v in enumerate(citylocs) if v[0] == src))]


def update_radius_search_results(src, radius):
    matches = []
    if src != '' and (src in city_names):
        naam, (src_latitude, src_longitude) = get_city_location(src)

        distances = []

        for dest, (dest_latitude, dest_longitude) in citylocs:
            d = distance.distance((src_latitude, src_longitude), (dest_latitude, dest_longitude))
            distances.append((round(d.km, 2), dest))

        distances.sort()

        for d in distances:
            if d[0] <= radius:
                matches.append(d[1])

    radius_search_results.update(matches)
    print('test ' + str(len(matches)))
    check_results.update(disabled=(len(matches) == 0))

def autocomplete_dropdown(value):
    def predict_text(input, lista):
        pattern = ('(^|\()' + re.escape(str(input).upper()) + '.*')
        return [w for w in lista if re.search(pattern, w)]

    prediction_list = predict_text(value, city_names)
    aktegemeente_dropdown.update(prediction_list[0] if len(prediction_list) > 0 else 'geen match',
                                 values=prediction_list)
    aktegemeente_zoek.update(value=value.upper())

    return aktegemeente_zoek.get()


def create_url(values, gemeente):
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
    zoekwijze = 's' if values['zoekwijze_exact'] is True else 'p'

    if vn1 != '':
        vn1 = "q/persoon_voornaam_t_0/" + vn1 + '/'
    if an1 != '':
        an1 = "q/persoon_achternaam_t_0/" + an1 + '/'
    if beroep1 != '':
        beroep1 = "q/persoon_beroep_s_0/" + beroep1 + "/"
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
          + rol2 + "q/zoekwijze/"+zoekwijze + "/" + beroep1 + "?M=" + zw_m + "&V=" + zw_v + "&O=" + zw_o + "&persoon_0_periode_geen=0&sort=akte_datum&direction=asc" \
          + gemeente + periode
    return url


def disable_person_inputs(disable=True):
    for item in inputs:
        item.update(disabled=disable)
    abort_search.update(disabled=(disable is False))

def update_radius_results(hits):
    radius_search_results.update(hits, disabled=False)

class ResultsScavenger(threading.Thread):

    def __init__(self, values, gemeentes, results, match_indexes):
        self.__window = window
        self.__done = False
        self.__values = values
        self.__gemeentes = gemeentes
        self.__results = results
        self.__match_indexes = match_indexes
        self.__stop_requested = False
        self.__show_all = True
        threading.Thread.__init__(self)

    def collect_results(self, values, gemeentes, results, match_indexes):

        self._progress = 0
        hit_map_locations = []
        for item in (gemeentes):

            url = create_url(values, item)

            if self.__stop_requested is False:
                # Don't overload server....
                time.sleep(.5)
                r = requests.get(url)

                lines = str(r.content).split('\n')
                pattern = re.compile(".*Resultaten\s(\d+\s)-\s(\d+\s)van\s(\d+\s).*")

                for line in lines:
                    match = pattern.match(line)
                    if match is not None:
                        hit_count = match.groups()[2]
                        results.append(item + ' (aantal : ' + hit_count + ')')
                        match_indexes.append(len(results) -1)
                        name, (lat, lon) = get_city_location(item)
                        hit_map_locations.append([name, lat, lon, hit_count, url])
                        update_radius_results(results)
                    elif self.__show_all:
                        results.append(item + ' (aantal : 0)')
                        update_radius_results(results)

                self._progress = self._progress + 1
                window.write_event_value("progress", self._progress)

        x, centre = get_city_location(gemeentes[0])
        generate_hit_map(centre, hit_map_locations, self.__values['radius'])
        window.write_event_value("done", 1)
        self.__stop_requested = False

    def run(self):
        self.__done = False
        self.collect_results(self.__values, self.__gemeentes, self.__results, self.__match_indexes)
        self.__done = True
        sys.exit()

    def done(self):
        return self.__done

    def clear(self):
        self.__done = False
        self.__stop_requested = False

    def completion(self):
        return int((self._progress * 100) / len(self.__gemeentes))

    def stop(self):
        self.__stop_requested = True

    def show_all(self, val=True):
        self.__show_all= val


def generate_hit_map(centre, locations, radius):
    m = folium.Map(location=centre, zoom_start=10)
    circle = folium.Circle(location=centre, radius=radius * 1000)
    circle.add_to(m)

    if len(locations):

        for location in locations:
            marker = folium.Marker(
                [location[1], location[2]],
                popup="<a href=" + location[4] + "> Aantal hits: " + location[3] + "</a>",
                tooltip=location[0] + " hits: " + location[3]
            )
            marker.add_to(m)

    m.save("rabsearch_hits.html")


def open_hit_map():
    webbrowser.open("rabsearch_hits.html", autoraise=True)


def restore_dropdown_list(widget, defaults, value=None):
    print ("restore dropdown list, selected value = " + str(value))
    if value is None:
        value = defaults[0]
    widget.update(values=defaults)
    widget.update(set_to_index= defaults.index(value))

def drop_down_predict(default_list, value, starts_with):
    matches = list()
    for (item) in default_list:
        if starts_with is True:
            match = item.lower().startswith(value.lower())
        else:
            match = value.lower() in (item.lower())
        if match:
            print(value.lower() + " matches " + item.lower())
            matches.append(item)
    return matches




def drop_down_handler(widget, default_list, event, value, starts_with=False):
    print("drop_down_handler : " + event + " " + value)
    global pre_prediction_value
    matches = list()
    skip_predict = False
    #fixme : delete any characters that are added if there's no potential matches
    #fixme : if length of new value is the same as before, don't change cursor pos

    if event.endswith('predict') or event.endswith('FocusOut'):
        if event.endswith('predict') and pre_prediction_value is not None :
            print ("cursor is at " + str())

            cursor_pos = widget.widget.index(INSERT)
            if cursor_pos < len(pre_prediction_value):
                #we're moving back
                skip_predict = True
                print("moving back updating to value = " + value[0:cursor_pos])
                value = value[0:cursor_pos]
                widget.update(value=value)

                pre_prediction_value = None
            else:
                value = pre_prediction_value + value[len(pre_prediction_value)]
        if not skip_predict:
            matches = drop_down_predict(default_list, value, starts_with)
        if len(matches) == 1:
            print("found match")
            if len(value) == len(matches[0]):
                pre_prediction_value = None
            else:
                pre_prediction_value = matches[0][0:len(value)]
            restore_dropdown_list(widget, default_list, matches[0])
            widget.widget.icursor(len(value))
        else:
            pre_prediction_value = None
            widget.update(values=matches, value=value)

    if event.endswith('FocusOut'):
        pre_prediction_value = None
        if len(matches) == 1:
            if value not in widget.Values:
                print("restoring defaults")
                # whe have matches, and there is currently no complete valid value entered
                if window.find_element_with_focus() is not None:
                    # if we have not opened the dropdown
                    print ("window.find_element_with_focus() is not None, setting default list and value to " + widget.Values[0])
                    restore_dropdown_list(widget, default_list, value)

        elif len(matches) == 0:
            # no match on focus out
            print("loosing focus, no possible matches, taking first of matches")
            restore_dropdown_list(widget, default_list)
            if window.find_element_with_focus() is None:
                widget.widget.event_generate('<Button>')
                print(" dropdown activated")
        else :
            # multiple matches possible on focus out
            if window.find_element_with_focus() is None:
                print("loosing focus, dropdown activated, no single match, taking first of matches")
            else:
                print("loosing focus, no single match, taking first of matches")
                widget.update(values=default_list)
                widget.update(value=matches[0])

    elif event.endswith('FocusIn'):
        pre_prediction_value = None
        widget.Widget.select_range(0, 'end')

    elif event.endswith('enter'):
        widget.widget.tk_focusNext().focus()
        return "break"


global rs


def update_pr_types(gemeente, parochie):
    types = list()
    for entry in parochieregisters[gemeente][parochie]:
        print(entry)
        types.append(entry['aktetype'])
    sortedtypes = sorted(list(set(types)))
    PR_typelijst.update(values=sortedtypes, value=sortedtypes[0], disabled=False)
    update_pr_results(gemeente, parochie, list(set(types))[0], PR_jaar_van.get())


def update_pr_results(gemeente, parochie, akte_type, jaar_van):
    allresults = parochieregisters[gemeente][parochie]

    global PRMatches
    PRMatches = []

    for i in allresults:
        if akte_type == i['aktetype']:
            if jaar_van != '':
                jaar = int(jaar_van)
                start_year = datetime.strptime(i['startdate'], '%d/%m/%Y').year
                end_year = datetime.strptime(i['enddate'], '%d/%m/%Y').year
                if start_year <= jaar <= end_year:
                    PRMatches.append(i)
            else:
                PRMatches.append(i)

    i = 0
    pr_links_values = []
    for match in PRMatches:
        pr_links_values.append(str(i).ljust(5) + ': ' + match['dates'] + ': ' + match['aktetype'])
        i = i + 1

    PR_links.update(values=pr_links_values)


def get_scans_url(eadid, src_url):
    r = requests.get(src_url)
    time.sleep(.5)
    lines = (r.content.decode('utf-8')).split('\n')
    invnr = 0
    for index, elem in enumerate(lines):
        if '/inventarisnr/' in elem:
            inv_re = re.compile('.+/inventarisnr/(.+?)/.*')
            invnr = inv_re.match(elem)[1]
            break
    tgt_url = 'https://search.arch.be/nl/zoeken-naar-archieven/zoekresultaat/inventaris/rabscans/eadid/' + \
              eadid + '/inventarisnr/' + invnr + '/level/file'
    return tgt_url

global pre_prediction_value
pre_prediction_value = None

while True:

    event, values = window.read()
    if event == "Exit" or event == PySimpleGUI.WIN_CLOSED:
        break

    print(event, values)
    gemeente = ''
    parochie = ''
    if values is not None:
        gemeente = values['parochieregisters_gemeente']
        parochie = values['parochieregisters_parochie']
    if event is None:
        event = ''
    if event == 'reset':
        reset_all_fields()
    if event.startswith('koenvelle.be'):
        webbrowser.open("https://koenvelle.be/rabsearch", autoraise=True)

    if event.startswith('parochieregisters_gemeente'):
        value = values['parochieregisters_gemeente']
        drop_down_handler(PR_gemeentelijst, list(parochieregisters.keys()), event, value, starts_with=True)
        if ((list(parochieregisters.keys())).count(PR_gemeentelijst.get()) > 0):
            print('found gemeente in keys ' + PR_gemeentelijst.get())
            parochies = list(parochieregisters[PR_gemeentelijst.get()].keys())
            PR_parochielijst.update(disabled=False, values=parochies, value=parochies[0])
            update_pr_types(PR_gemeentelijst.get(), parochies[0])

    if event== 'parochieregisters_parochie':
        parochies = list(parochieregisters[gemeente].keys())
        update_pr_types(gemeente, parochie)

    if event == 'parochieregisters_type':
        update_pr_results(gemeente, parochie, values['parochieregisters_type'], values['parochieregisters_jaar_van'])

    if event == 'parochieregisters_jaar_van':
        jaar = values['parochieregisters_jaar_van']
        numeric_filter = filter(str.isdigit, jaar)
        jaar = ("".join(numeric_filter))
        PR_jaar_van.update(value=jaar)

        update_pr_results(gemeente, parochie, values['parochieregisters_type'], jaar)

    if event == 'parochieregisters_links':
        # fixme if valid value
        linkindex = int(values['parochieregisters_links'][0].split(':')[0])

        url = PRMatches[linkindex]['url']
        webbrowser.open_new_tab(get_scans_url(PRMatches[linkindex]['bloknr'], PRMatches[linkindex]['url']))

    if event == "Exit" or event == PySimpleGUI.WIN_CLOSED:
        sys.exit()

    if event.startswith('pers1_rol'):
        value = values['pers1_rol'].capitalize()
        drop_down_handler(eerste_pers_rol, roles.role_names, event, value)

    if event.startswith('pers2_rol'):
        value = values['pers2_rol'].capitalize()
        drop_down_handler(tweede_pers_rol, roles.role_names, event, value)

    if event == 'kaart':
        open_hit_map()
    if event == 'done':
        disable_person_inputs(False)
        print("update gemeentelijst")
        radius_search_results.update(results)

        print("update kaart")
        if len(match_indexes):
            kaart.update(disabled=False)
        for i in match_indexes:
            radius_search_results.Widget.itemconfigure(i, bg='lightgreen',
                                                       fg='black')  # set options for item in listbox
        print("kaart geupdate")
        rs.clear()
        print("rs cleared")

    elif event == 'progress':
        progress_bar.update(current_count=rs.completion(), visible=True)

    elif event == "stop_tellen":
        kaart.update(disabled=True)
        rs.stop()

    elif event == "aktegemeente_zoek":
        gem = autocomplete_dropdown(values['aktegemeente_zoek'])
        update_radius_search_results(gem, values['radius'])
    elif event == "aktegemeente_kies":
        aktegemeente_zoek.update(values['aktegemeente_kies'])
        update_radius_search_results(values['aktegemeente_kies'], values['radius'])
    elif event == "radius":
        update_radius_search_results(values['aktegemeente_zoek'], values['radius'])
    elif event == "tel_resultaten":
        kaart.update(disabled=True)
        gem = autocomplete_dropdown(values['aktegemeente_zoek'])
        update_radius_search_results(gem, values['radius'])
        results = []
        match_indexes = []
        if len(radius_search_results.get_list_values()) > 0:
            disable_person_inputs(True)
            progress_bar.update(0, visible=False)
            rs = ResultsScavenger(values, radius_search_results.get_list_values(), results, match_indexes)
            rs.show_all(False)
            rs.start()

    elif event == "gemeentelijst" or event == "zoek":
        if (len(values['gemeentelijst'])):
            aktegemeente = values['aktegemeente_zoek'] if event == 'zoek' else values['gemeentelijst'][0] if len(
                values['gemeentelijst']) else ''
            aktegemeente = aktegemeente.split('(aantal')
            url = create_url(values, aktegemeente[0])
            webbrowser.open_new_tab(url)

sys.exit()

source = "nieuwkerke".upper()
naam, (src_latitude, src_longitude) = getCityLoc(source)

print("Afstand tot ", naam, "(", src_latitude, src_longitude, ")")

distances = []

for dest, (dest_latitude, dest_longitude) in citylocs:
    d = distance.distance((src_latitude, src_longitude), (dest_latitude, dest_longitude))
    distances.append((round(d.km, 2), dest))

distances.sort()

for i in range(1, 20):
    target_distance, target_name = distances[i]
    print(target_name, target_distance, "km")

exit()
# Initialize Nominatim API
geolocator = Nominatim(user_agent="genealocsearch", timeout=10)

location1 = geolocator.geocode("Woumen")

print("The latitude of the location is: ", location1.latitude)
print("The longitude of the location is: ", location1.longitude)

distances = []

unique_city_names = list(dict.fromkeys(city_names))
city_count = len(unique_city_names)

i = 0
for city in unique_city_names:
    i = i + 1
    city_loc = geolocator.geocode(city + ", Belgium")

    if city_loc is not None:
        time.sleep(1)
        print(city, ":", city_loc.latitude, ":", city_loc.longitude)
        # dist = distance.distance((location1.latitude, location1.longitude), (city_loc.latitude, city_loc.longitude))
        # distances.append((dist.km, city))
        # print(int(i/ city_count * 10000)/100, " ", city, " ", dist.km)

# distances.sort()
# print(distances)


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
