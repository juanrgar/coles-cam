#!/usr/bin/env python3

import csv
import mechanicalsoup
import re
import requests
import sqlite3

EP_URL = "https://gestiona3.madrid.org/wpad_pub/run/j/MostrarConsultaGeneral.icm"
CSV_FILENAME = "_coles.csv"

SOLICITUDES_BASE_DATA = {'callCount': '1', 'c0-scriptName': 'GraficasDWRAccion', 'c0-methodName': 'obtenerGrafica', 'c0-id': '3829_1650964201631', 'c0-e1': 'string:28007103', 'c0-e2': 'string:12', 'c0-e3': 'string:3', 'c0-e4': 'string:1', 'c0-e5': 'string:0', 'c0-param0': 'Object:{cdCentro:reference:c0-e1, cdnivelEducativo:reference:c0-e2, cdGrafica:reference:c0-e3, tipoGrafica:reference:c0-e4, tipoSolicitud:reference:c0-e5}', 'xml': 'true'}
SOLICITUDES_URL = 'https://gestiona3.madrid.org/wpad_pub/dwr/exec/GraficasDWRAccion.obtenerGrafica.dwr'

def apply_schema():
    conn = sqlite3.connect('coles_cam.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS COLEGIOS")
    c.execute("""CREATE TABLE COLEGIOS (
            Area_Territorial VARCHAR(255) NOT NULL,
            Codigo_Centro INTEGER NOT NULL PRIMARY KEY,
            Tipo_De_Centro VARCHAR(25),
            Centro TEXT,
            Domicilio TEXT,
            Municipio TEXT,
            Distrito_Municipal TEXT,
            Codigo_Postal CHAR(5),
            Telefono CHAR(9),
            Fax CHAR(9),
            Email VARCHAR(255),
            Email2 VARCHAR(255),
            Titularidad TEXT
        ); """)

    c.execute("DROP TABLE IF EXISTS PROCESO_ADMISION")
    c.execute("""CREATE TABLE PROCESO_ADMISION (
            Codigo_Centro INTEGER,
            Etapa VARCHAR(255),
            Estado VARCHAR(255),
            Periodo VARCHAR(255),
            Cantidad INTEGER
        ); """)

    conn.close()

def insert_into_db(c, r):
    # Make sure we have the right number of arguments.
    # Some entries contain various email addresses separated with the same csv
    # delimiter.
    if len(r) == 14:
        if ("@" in r[10] ) and ("@" in r[11]) and ("@" in r[12]):
            # Merge two email addresses
            r[11] += ("," + r[12].strip())
            r.pop(12)

    # Name could have single quotes.
    r[3] = r[3].replace("'", "''")
    print(r[3])

    r = [e.strip() for e in r]

    c.execute(f'''INSERT INTO COLEGIOS
              VALUES ("%s",%s,"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s");''' % tuple(r));
    print(r[1])

def get_common_data(browser):
#    downlaod_full_listing(browser)

    with open(CSV_FILENAME, "r") as f:
        csvf = csv.reader(f, delimiter=';')
        # Skip first line.
        next(csvf)
        # Get header.
        header = next(csvf)

        # Connect to DB
        conn = sqlite3.connect('coles_cam.db')
        c = conn.cursor()

        for row in csvf:
            # CSV lines end with a delimiter for some reason.
            row.pop(-1)

            insert_into_db(c, row)

        conn.commit()
        conn.close()

def get_schools_info(browser):
    conn = sqlite3.connect("coles_cam.db")
    c = conn.cursor()

    c.execute("SELECT Codigo_Centro FROM COLEGIOS ORDER BY Codigo_Centro;")
    rows = c.fetchall()

    for r in rows:
        code = r[0]
        get_school_info(browser, code)

    conn.close()

def get_school_info(browser, code):
    conn = sqlite3.connect("coles_cam.db")
    c = conn.cursor()
    response = browser.open(EP_URL)
    form = response.soup.find("form", {"id": "formBusquedaSencilla"})
    form.find("input", {"name": "cdCentro"})["value"] = str(code)
    form["action"] = "MostrarFichaCentro.icm"
    response = browser.submit(form, browser.url)
    niveds = response.soup.find_all("input", id=re.compile("nivEd.*grafica3"))
    print("Niveles educativos " + str(niveds))
    for niv in niveds:
        label = response.soup.find_all("label", {"for": niv["id"]})
        req = SOLICITUDES_BASE_DATA.copy()
        m = re.match("nivEd([0-9]+)", niv["id"])
        req["c0-e2"] = "string:" + m.group(1)
        req["c0-e1"] = "string:" + str(code)
        res = requests.post(SOLICITUDES_URL, req)
        snippet = res.text
        snippet = snippet.replace("var ", "")
        snippet = snippet.replace("false", "False")
        snippet = snippet.replace("true", "True")
        snippet = snippet.replace("null", "None")
        lines = snippet.split("\n")
        lines.pop(-1)
        lines.pop(-1)
        snippet = "\n".join(lines)
        snippet = re.sub(r"\.(\w+)=", r'["\1"]=', snippet)
        snippet = snippet.replace(";", "\n")
        snippet = re.sub(r"\[\d+\]=(.*)", r".append(\1)", snippet)
        gvar = dict()
        lvar = dict()
        ret = exec(snippet, None, lvar)
        for series in lvar["s0"]["listaSeries"]:
            for i in range(len(series["serieX"])):
                c.execute(f'''INSERT INTO PROCESO_ADMISION
                              VALUES (%s,"%s","%s","%s",%s);''' % (code, label[0].text, series["nombreSerie"], series["serieX"][i], series["serieY"][i]));

    conn.commit()
    conn.close()
#            break

#            forms = page.soup.select("form")
#
#            form = forms[0]
#            input = form.find("input", {"id": "basica.strCodNomMuni"})
#            input["value"] = "concepcionistas"
#            school_page = browser.submit(form, page.url)
#            url = school_page.url
#
#            pcuerpo = school_page.soup.find("form", {"id": "formResultadoLista"})
#            tab = pcuerpo.select("table")[0]
#            cod = tab.select("tr")[3].select("td")[0].text.strip()
#            print(cod)
#
#            form = page.soup.find("form", {"id": "formBusquedaSencilla"})
#            input = form.find("input", {"name": "cdCentro"})
#            form["action"] = "MostrarFichaCentro.icm"
#            school_page = browser.submit(form, url)
#            print(form)
#            print(school_page.soup)
#            print(school_page.url)
#            print(type(cod))


def download_full_listing(browser):
    browser.open(EP_URL)

    # First, we have to do a search with an empty string; that would return all
    # entries.
    browser.select_form('form[id="formBusquedaSencilla"]')
    browser["basica.strCodNomMuni"] = " "
    response = browser.submit_selected()

    # A list with all identifiers is returned here.  We have to copy that to the
    # next form.
    params = response.soup.find("input", {"name" : "codCentrosExp"})["value"]
    browser.select_form('form[id="frmExportarResultado"]')
    browser["codCentrosExp"] = params
    response = browser.submit_selected()

    # This page overrides the location.href property to point to the csv file to
    # download, but we have to that by hand here.
    target = response.soup.find("input", {"name": "TEXTO"})["value"]
    new_url = browser.url
    new_url = '/'.join(new_url.split('/')[:-1]) + '/' + target
    response = browser.open(new_url)

    # Finally, save the content to a file.
    with open(CSV_FILENAME, 'w') as f:
        f.write(response.content.decode("iso8859_15"))


def main():
    # apply_schema()
    browser = mechanicalsoup.StatefulBrowser()
    # get_common_data(browser)
    # get_schools_info(browser)
    get_school_info(browser, "28007103")
    # get_school_info(browser, "28080712")

#    browser = mechanicalsoup.StatefulBrowser()
#    page = browser.get(url)
#    forms = page.soup.select("form")
#
#    form = forms[0]
#    input = form.find("input", {"id": "basica.strCodNomMuni"})
#    input["value"] = "concepcionistas"
#    school_page = browser.submit(form, page.url)
#    url = school_page.url
#
#    pcuerpo = school_page.soup.find("form", {"id": "formResultadoLista"})
#    tab = pcuerpo.select("table")[0]
#    cod = tab.select("tr")[3].select("td")[0].text.strip()
#    print(cod)
#
#    form = page.soup.find("form", {"id": "formBusquedaSencilla"})
#    input = form.find("input", {"name": "cdCentro"})
#    form["action"] = "MostrarFichaCentro.icm"
#    school_page = browser.submit(form, url)
#    print(form)
#    print(school_page.soup)
#    print(school_page.url)
#    print(type(cod))


if __name__ == "__main__":
    main()
