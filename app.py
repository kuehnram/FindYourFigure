"""
Tutorial: https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3

Things to do:
Add database functionality

make it look nicer

Add Internationalization
https://medium.com/@nicolas_84494/flask-create-a-multilingual-web-application-with-language-specific-urls-5d994344f5fd
https://phrase.com/blog/posts/flask-app-tutorial-i18n/

Put SPARQL queries in a separate file
"""
import http
import random
import sqlite3
from typing import List

import rdflib
from flask import Flask, render_template, request, url_for, redirect, flash, Response
from werkzeug.exceptions import abort

import db

g = rdflib.Graph()
# g.parse('C:/Users/kuehn21/PycharmProjects/GrhootRestructured/grhoot.owl', format='application/rdf+xml')
g.parse('./grhootNewSmall.owl', format='application/rdf+xml')

webprotege = rdflib.Namespace('http://webprotege.stanford.edu/')
gr = rdflib.Namespace('https://ramonakuehn.de/grhoot.owl#')
rdfs = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#')
owl = rdflib.Namespace('http://www.w3.org/2002/07/owl#')
g.bind("owl", owl)
g.bind("rdfs", rdfs)
g.bind("gr", gr)
g.bind("webprotege", webprotege)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


@app.route('/')
def index():
    # conn = get_db_connection()
    # posts = conn.execute('SELECT * FROM posts').fetchall()
    # conn.close()
    return render_template('index.html')


def query_list_elements(query: str, key_name: str, no_idea: bool) -> list:
    """
    Get all elements from a certain category from the ontology as options in the dropdown menu how output looks for
    example: data = [{"figure": "Anapher"}, {"figure": "Epipher"}, {"figure": "Symploke"}]
    """
    result = g.query(query)
    data = []
    for row in result:
        value_element = row[0]
        data.append({key_name: str(value_element)})
    # add "nothing/ i don't know as option
    if no_idea:
        data.append({key_name: "Keins davon/Weiß nicht"})
    return data


def get_example_data() -> sqlite3.Row:
    """
    Retrieves a random examples from the database which is not yet annotated/connected with a figure via the
    table contains_figure. Think if better to check first which examples are in db then generate or create random
    numbers and test over and over if example is not annotated.
    Maybe create another table/column for it (e.g. annotated?)?
    TODO: place button right, check in table annotations that example is not yet connected with another figure or has the least annotations yet. Then display result in the textfields
    """
    print("example Button")
    connection = db.get_db_connection()
    cursor = connection.cursor()

    # Get the total number of entries in the table
    cursor.execute("SELECT COUNT(*) FROM texts")
    total_entries = cursor.fetchone()[0]

    # Generate a random offset within the total number of entries
    random_offset = random.randint(0, total_entries - 1)

    # Retrieve a random entry using LIMIT and OFFSET
    cursor.execute("SELECT * FROM texts LIMIT 1 OFFSET ?", (random_offset,))
    random_entry = cursor.fetchone()

    # Close the connection
    connection.close()
    # Now 'random_entry' contains the randomly retrieved entry
    if random_entry is None:
        abort(http.HTTPStatus.INTERNAL_SERVER_ERROR, f"No examples found")
    return random_entry


@app.route('/fyfpage', methods=('POST', "GET"))
def fyfpage():
    """
    Build first the options for the dropdowns from where the users can choose matching properties.
    Based on those properties, build a query for the ontology.
    """
    # data = [{'name': 'red'}, {'name': 'green'}, {'name': 'blue'}]
    # get all possible variables from the ontology for the dropdown menus
    result = ""
    ling_pos_query = """
    SELECT ?subclassLabel
    WHERE {
      ?subclass rdf:type owl:Class ;
                rdfs:subClassOf gr:LinguistischePosition ;
                rdfs:label ?subclassLabel .
    }
      """
    ling_pos_data = query_list_elements(query=ling_pos_query, key_name="lingPos", no_idea=True)

    ling_operation_query = """
    SELECT ?subclassLabel
    WHERE {
      ?subclass rdf:type owl:Class ;
                rdfs:subClassOf gr:LinguistischeOperation ;
                rdfs:label ?subclassLabel .
    }
    """
    ling_operation_data = query_list_elements(query=ling_operation_query, key_name="lingOp", no_idea=True)

    ling_element_query = """
    SELECT ?subclassLabel
    WHERE {
      ?subclass rdf:type owl:Class ;
                rdfs:subClassOf gr:LinguistischesElement ;
                rdfs:label ?subclassLabel .
    }
    """
    ling_element_data = query_list_elements(query=ling_element_query, key_name="lingElem", no_idea=True)

    ling_form_query = """
        SELECT ?subclassLabel
        WHERE {
          ?subclass rdf:type owl:Class ;
                    rdfs:subClassOf webprotege:LinguistischeForm ;
                    rdfs:label ?subclassLabel .
        }
        """
    ling_form_data = query_list_elements(query=ling_form_query, key_name="lingForm", no_idea=True)

    ling_area_query = """
     SELECT ?subclassLabel
        WHERE {
          ?subclass rdf:type owl:Class ;
                    rdfs:subClassOf gr:LinguistischerUmfang ;
                    rdfs:label ?subclassLabel .
        }
     """
    ling_area_data = query_list_elements(query=ling_area_query, key_name="lingArea", no_idea=True)
    if request.method == 'POST':

        if "get_example_button" in request.form:
            example = get_example_data()
            print("here comes the examples")
            print(example)
            text = example["text"]  # TODO RKU in DB alle zellen strippen
            author = example["author"]
            source = example["source"]
            context = example["context"]
            text_id = example["id"]
        else:
            text = request.form['text'].strip() if 'text' in request.form else ""
            author = request.form['author'].strip()
            source = request.form['source'].strip()
            context = request.form['context'].strip()
            text_id = request.form['text_id'] if 'text_id' in request.form else None

        nothing = "Keins davon/Weiß nicht"
        print("here are ze values")
        print(text, context, author, source)
        operation = request.form['operation']
        operation_position = request.form['operation_position']
        # convert to CamelCase => classnames in ontology
        operation_position = operation_position.title().replace(" ", "") if operation_position != nothing else nothing
        ling_element = request.form['ling_element']
        ling_form = request.form['ling_form']
        ling_form = ling_form.title().replace(" ", "") if ling_form != nothing else nothing
        ling_area = request.form['ling_area']

        ling_elem_block = f"""rdfs:subClassOf [
                      rdf:type owl:Restriction ;
                      owl:onProperty webprotege:betroffenensElement ;
                      owl:someValuesFrom webprotege:{ling_element} ;
                    ]; """
        ling_area_block = f"""rdfs:subClassOf [
                      rdf:type owl:Restriction ;
                      owl:onProperty gr:liegtImBereich ;
                      owl:someValuesFrom webprotege:{ling_area} ;
                    ]; """

        operation_block = f"""rdfs:subClassOf [
                      rdf:type owl:Restriction ;
                      owl:onProperty webprotege:hatOperation ;
                      owl:someValuesFrom webprotege:{operation} ;
                    ]; """

        operation_position_block = f"""rdfs:subClassOf [
                              rdf:type owl:Restriction ;
                              owl:onProperty gr:istInPosition ;
                              owl:someValuesFrom webprotege:{operation_position} ;
                            ]; """

        ling_form_block = f"""rdfs:subClassOf [
                      rdf:type owl:Restriction ;
                      owl:onProperty webprotege:hatOperationsform ;
                      owl:someValuesFrom webprotege:{ling_form} ;
                    ]; """

        figure_query = f"""
            SELECT ?label
            WHERE {{
              ?class rdf:type owl:Class ;
                    rdfs:label ?label ;
                    {ling_elem_block if ling_element != nothing else ""}
                    {ling_area_block if ling_area != nothing else ""}
                    {operation_block if operation != nothing else ""}
                    {operation_position_block if operation_position != nothing else ""}
                    {ling_form_block if ling_form != nothing else ""}
                    FILTER (LANG(?label) = 'de').
            }}
            """

        test_query = f"""
              SELECT ?label
              WHERE {{
                ?class rdf:type owl:Class ;
                      rdfs:label ?label ;
                      rdfs:subClassOf [
                        rdf:type owl:Restriction ;
                        owl:onProperty webprotege:betroffenensElement ;
                        owl:someValuesFrom webprotege:Wortelement ;
                      ] ;
                      rdfs:subClassOf [
                        rdf:type owl:Restriction ;
                        owl:onProperty webprotege:hatOperationsform ;
                        owl:someValuesFrom webprotege:SelbeForm ;
                       ] 
               FILTER (LANG(?label) = 'de').       
              }}
                   """

        readonly = any([has_value(form_value) for form_value in [text, text_id, context, author, source]])

        figure_infos = []
        if "send" in request.form:
            # result = g.query(figure_query) # TODO change in the end, static test_query only for testing purposes
            result = g.query(test_query)
            result = parse_figure_name(result)

            for figure_name in result:
                figure_info = {"figure_name": figure_name, "definitions": get_figure_definition(figure_name),
                               "examples": get_examples(figure_name)}
                figure_infos.append(figure_info)
        if not text:
            flash('Bitte gib einen Text ein!')
        else:
            return render_template('fyfpage.html',
                                   readonly=readonly,
                                   text=text,
                                   text_id=text_id,
                                   context=context,
                                   author=author,
                                   source=source,
                                   ling_element_data=ling_element_data,
                                   operation_data=ling_operation_data,
                                   position_data=ling_pos_data,
                                   ling_form_data=ling_form_data,
                                   ling_area_data=ling_area_data,
                                   result=figure_infos)

    return render_template('fyfpage.html', ling_element_data=ling_element_data, operation_data=ling_operation_data,
                           position_data=ling_pos_data, ling_form_data=ling_form_data, ling_area_data=ling_area_data)


def has_value(form_value: str) -> bool:
    """Checks that a given form value has an actual value (i.e. is set and does not only consist of whitespace"""
    return form_value is not None and str(form_value).strip() != ""


def parse_figure_name(result) -> list:
    figure_name_list = []
    for figure_name in result:
        label_literal = figure_name['label']
        label_value = label_literal.value
        figure_name_list.append(label_value)
    # for row in result:
    #     figure_name = re.search(r"('(.*?)')", str(row)).group(2)
    #     figure_name_list.append(figure_name)
    return figure_name_list


def get_figure_definition(figure_name: str) -> list:
    definitions = []
    def_query = f""" SELECT ?value
                     WHERE {{
                        ?class rdf:type owl:Class ;
                        rdfs:label "{figure_name}"@de  ;
                        rdfs:subClassOf [
                        owl:onProperty webprotege:hatDefinition ;
                        owl:hasValue ?value ;
                     ] .    }}
                    """
    def_query_result = g.query(def_query)
    for result in def_query_result:
        value_uri = result['value'].toPython()
        def_text_query = f""" SELECT ?definitionText
                 WHERE {{
                      <{value_uri}> webprotege:hatDefinitionsText ?definitionText .
                     }}
                """

        def_text_result = g.query(def_text_query)
        for def_text in def_text_result:
            definition_entry = {'text': "",
                                'author': ""}
            label_literal = def_text['definitionText']
            definition_entry['text'] = label_literal.value
            def_author_query = f""" SELECT ?definitionAutor
                 WHERE {{
                      <{value_uri}> webprotege:istAutor ?definitionAutor .
                     }}
                """
            def_author_result = g.query(def_author_query)
            for def_author in def_author_result:
                label_literal = def_author['definitionAutor']
                label_value = label_literal.value
                definition_entry['author'] = label_literal.value
                definitions.append(definition_entry)

    return definitions


def get_examples(figure_name):
    examples = []
    example_query = f""" SELECT ?instance ?author ?source ?example
                        WHERE {{
                          ?instance rdf:type webprotege:{figure_name} .
                          OPTIONAL {{ ?instance webprotege:istAutor ?author . }}
                          OPTIONAL {{ ?instance webprotege:istBeispielQuelle ?source . }}
                          OPTIONAL {{ ?instance gr:istBeispiel ?example . }}
                            }}
                        """
    example_query_result = g.query(example_query)
    for res in example_query_result:
        example_entry = {
            # 'instance': res['instance'].n3(),
            'example_text': res["example"].value,  # example text is mandatory
            'example_source': res["source"].value if res["source"] else None,
            'example_author': res["author"].value if res["author"] else None
        }
        examples.append(example_entry)

    return examples


@app.route("/figure_information", methods=['POST', 'GET'])
def figure_information():
    figure_label_query = """SELECT ?label
                        WHERE {
                          ?subclass rdf:type owl:Class ;
                                    rdfs:subClassOf gr:RhetorischeFigur ;
                                    rdfs:label ?label
                                    Filter (LANG(?label) = 'de')
                            }
                            """
    figure_data = query_list_elements(query=figure_label_query, key_name="figure", no_idea=False)

    if request.method == 'POST':
        figure = request.form['figure']
        figure_detail_infos = []
        figure_detail_info = {"figure_name": figure, "definitions": get_figure_definition(figure),
                              "examples": get_examples(figure), "position": "Anfang",
                              "rhetoricalClass": "Betonungsfigur"}  # etc...
        figure_detail_infos.append(figure_detail_info)
        return render_template("figure_info.html", figure_names=figure_data,
                               ergebnis="Hier sind alle Infos zu dieser Figur:",
                               figure_detail_infos=figure_detail_infos)

    return render_template("figure_info.html", figure_names=figure_data)


@app.route('/function')
def function():
    return render_template("function.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/create', methods=('POST', 'GET'))
def create():
    if request.method == 'POST':
        author = request.form['author']
        context = request.form['context']
        source = request.form['source']
        text = request.form['text']
        if not text:
            flash('Bitte gib einen Text ein!')
        else:
            conn = db.get_db_connection()
            conn.execute('INSERT INTO texts (text, context, author, source) VALUES (?, ?, ?, ?)',
                         (text, context, author, source))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('create.html')


def get_figure_label() -> list:
    figure_query = """SELECT ?label
                         WHERE {
                           ?subclass rdf:type owl:Class ;
                                     rdfs:subClassOf gr:RhetorischeFigur ;
                                     rdfs:label ?label
                                     Filter (LANG(?label) = 'de')
                             }
                             """
    result = g.query(figure_query)
    data = []
    for row in result:
        value_element = row[0]
        data.append(value_element)
    return data


if __name__ == '__main__':
    app.run()
