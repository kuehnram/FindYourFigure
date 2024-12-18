"""
Add Internationalization
https://medium.com/@nicolas_84494/flask-create-a-multilingual-web-application-with-language-specific-urls-5d994344f5fd
https://phrase.com/blog/posts/flask-app-tutorial-i18n/

Put SPARQL queries in a separate file
"""
import language_tool_python

import http
import random
import sqlite3
from typing import List

import rdflib
from flask import Flask, render_template, request, url_for, redirect, flash, Response
from werkzeug.exceptions import abort

import db

import openai
from llama_index.core import (
    ServiceContext,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.node_parser import HierarchicalNodeParser
from llama_index.core.node_parser import get_leaf_nodes
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.indices.postprocessor import SentenceTransformerRerank
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.openai import OpenAI
from llama_index.core import (
    ServiceContext,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
openai.api_key = "INSERT_YOUR_API_KEY_HERE"



import langdetect # for language detection of user input
# Spellchecker for user input
tool = language_tool_python.LanguageTool('de')

g = rdflib.Graph()
# g.parse('./grhootNewSmall.owl', format='application/rdf+xml')
g.parse('./grhoot_reified.owl', format='application/rdf+xml')

#webprotege = rdflib.Namespace('http://webprotege.stanford.edu/')
gr = rdflib.Namespace('https://ramonakuehn.de/grhoot.owl/')
rdfs = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema/')
owl = rdflib.Namespace('http://www.w3.org/2002/07/owl/')
g.bind("owl", owl)
g.bind("rdfs", rdfs)
g.bind("gr", gr)
#g.bind("webprotege", webprotege)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

get_all_figure_labels_query = """SELECT ?label
                    WHERE {
                      ?subclass rdf:type owl:Class ;
                                rdfs:subClassOf gr:RhetorischeFigur ;
                                rdfs:label ?label
                                Filter (LANG(?label) = 'de')
                        }
                        """



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
    TODO: check in table annotations that example is not yet connected with another figure or has
    the least annotations yet.
    """
    print("example Button")
    connection = db.get_db_connection()
    cursor = connection.cursor()

    # Get the total number of entries in the table
    cursor.execute("SELECT COUNT(*) FROM texts WHERE is_harmful <> 1")
    total_entries = cursor.fetchone()[0]

    # Generate a random offset within the total number of entries
    random_offset = random.randint(0, total_entries - 1)

    # Retrieve a random entry using LIMIT and OFFSET, prevent harmful texts
    cursor.execute("SELECT * FROM texts WHERE is_harmful <> 1 LIMIT 1 OFFSET ?", (random_offset,))
    random_entry = cursor.fetchone()

    # Close the connection
    connection.close()
    # Now 'random_entry' contains the randomly retrieved entry
    if random_entry is None:
        abort(http.HTTPStatus.INTERNAL_SERVER_ERROR, f"No examples found")
    return random_entry


def get_automerging_query_engine(
    automerging_index,
    similarity_top_k,
    rerank_top_n,
):
    base_retriever = automerging_index.as_retriever(similarity_top_k=similarity_top_k)
    retriever = AutoMergingRetriever(
        base_retriever, automerging_index.storage_context, verbose=True
    )
    rerank = SentenceTransformerRerank(
        top_n=rerank_top_n, model="BAAI/bge-reranker-large"
    )
    auto_merging_engine = RetrieverQueryEngine.from_args(
        retriever, node_postprocessors=[rerank]
    )

    return auto_merging_engine



@app.route('/llm', methods=['POST', 'GET'])
def ask_llm():
    text = ""
    author = ""
    source = ""
    context = ""
    text_id = None
    question = ""

    if request.method == 'POST':
        if "get_example_button" in request.form:
            example = get_example_data()
            text = example.get("text", "").strip()
            author = example.get("author", "").strip()
            source = example.get("source", "").strip()
            context = example.get("context", "").strip()
            text_id = example.get("id", "").strip()
        else:
            text = request.form.get('text', "").strip()
            author = request.form.get('author', "").strip()
            source = request.form.get('source', "").strip()
            context = request.form.get('context', "").strip()
            text_id = request.form.get('text_id', "").strip()

        question = request.form.get('prompttext', "").strip()

    message = ("Please insert the OpenAI API key in the app.py to use this functionality. In the live-version of"
               "the website, we will of course include a key.")

    embed_model = "local:BAAI/bge-m3"
    llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)

    merging_context = ServiceContext.from_defaults(
        llm=llm,
        embed_model=embed_model,
    )
    save_dir = "./merging_index_grhoot"

    index = load_index_from_storage(
        StorageContext.from_defaults(persist_dir=save_dir),
        service_context=merging_context)

    automerging_query_engine = get_automerging_query_engine(index, similarity_top_k=6, rerank_top_n=3)
    auto_merging_response = automerging_query_engine.query(question) + " Bitte antworte nur auf Deutsch!"
    llm_response = auto_merging_response

    return render_template("llm.html",
                           text=text,
                           text_id=text_id,
                           context=context,
                           author=author,
                           source=source,
                           llm_response=llm_response)

@app.route('/annotation-save', methods=['POST', 'GET'])
def annotation_save():
    if request.method == "POST":
        figure_names: List[str] = request.form.getlist('figure_names')
        text_id: int = int(request.form.get('text_id'))
        figure_ids = [db.get_figure_id_by_name(figure_name.strip()) for figure_name in figure_names]

        db.link_text_with_figures(text_id, figure_ids)

        return render_template("annotation-save.html")
    else:
        return Response("<a href='/fyfpage'>Bitte hier Daten eingeben.</a>", status=http.HTTPStatus.BAD_REQUEST)




def query_builder_result(ling_element, ling_area, ling_form, operation, operation_position, nothing):
    ling_elem_block = f"""
           SELECT ?label
           WHERE {{
             ?class rdf:type owl:Class ;
                   rdfs:label ?label ;
                   rdfs:subClassOf [
                     rdf:type owl:Restriction ;
                     owl:onProperty gr:betroffenesElement ;
                     owl:someValuesFrom gr:{ling_element} ;
                   ] .
           Filter (LANG(?label) = 'de')
           }}"""

    ling_area_block = f"""
    SELECT ?label
           WHERE {{
             ?class rdf:type owl:Class ;
                   rdfs:label ?label ;
       rdfs:subClassOf [
                     rdf:type owl:Restriction ;
                     owl:onProperty gr:liegtImBereich ;
                     owl:someValuesFrom gr:{ling_area} ;
                   ];
                    Filter (LANG(?label) = 'de')
                    }}"""

    operation_block = f"""
    SELECT ?label
           WHERE {{
             ?class rdf:type owl:Class ;
                   rdfs:label ?label ;
       rdfs:subClassOf [
                     rdf:type owl:Restriction ;
                     owl:onProperty gr:hatOperation ;
                     owl:someValuesFrom gr:{operation} ;
                   ];
                    Filter (LANG(?label) = 'de')}}"""

    operation_position_block = f"""
        SELECT ?label
           WHERE {{
             ?class rdf:type owl:Class ;
                   rdfs:label ?label ;
       rdfs:subClassOf [
                             rdf:type owl:Restriction ;
                             owl:onProperty gr:istInPosition ;
                             owl:someValuesFrom gr:{operation_position} ;
                           ]; 
                           Filter (LANG(?label) = 'de')
                           }} """

    ling_form_block = f"""
        SELECT ?label
           WHERE {{
             ?class rdf:type owl:Class ;
                   rdfs:label ?label ;
       rdfs:subClassOf [
                     rdf:type owl:Restriction ;
                     owl:onProperty gr:hatOperationsform ;
                     owl:someValuesFrom gr:{ling_form} ;
                   ];  
                   Filter (LANG(?label) = 'de')}} """


    # Query only where it is not "Keins davon/Weiß nicht", set "Keins davon" to all figures
    all_figures = []
    result = g.query(get_all_figure_labels_query)
    for res in result:
        all_figures.append(str(res['label']))
    #print(all_figures)


    result_ling_area = parse_figure_name(g.query(ling_area_block)) if ling_area != nothing else ""
    result_ling_elem = parse_figure_name(g.query(ling_elem_block)) if ling_element != nothing else ""
    result_ling_form = parse_figure_name(g.query(ling_form_block)) if ling_form != nothing else ""
    result_operation = parse_figure_name(g.query(operation_block)) if operation != nothing else ""
    result_position = parse_figure_name(g.query(operation_position_block)) if operation_position != nothing else ""

    #resultlist = list(set(result_ling_area) & set(result_ling_elem) & set(result_ling_form) & set(result_operation) & set(result_position))

    # remove empty sets and form intersection to find matching rhetorical figures
    non_empty_sets = [result_set for result_set in [
        result_ling_elem, result_ling_form, result_operation, result_position, result_ling_area
    ] if result_set]

    if non_empty_sets:
        resultlist = list(set.intersection(*map(set, non_empty_sets)))
    else:
        resultlist = all_figures
    print("here is ze resultlist:")
    print(resultlist)
    return resultlist



@app.route('/fyfpage', methods=('POST', "GET"))
def fyfpage():
    """
    Build first the options for the dropdowns from where the users can choose matching properties.
    Based on those properties, build a query for the ontology.
    """
    # data = [{'name': 'red'}, {'name': 'green'}, {'name': 'blue'}]
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
                    rdfs:subClassOf gr:LinguistischeForm ;
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
            text = example["text"]
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
        operation = request.form['operation']
        operation_position = request.form['operation_position']
        # convert to CamelCase => classnames in ontology
        operation_position = operation_position.title().replace(" ", "") if operation_position != nothing else nothing
        ling_element = request.form['ling_element']
        ling_form = request.form['ling_form']
        ling_form = ling_form.title().replace(" ", "") if ling_form != nothing else nothing
        ling_area = request.form['ling_area']

        # ling_elem_block = f"""rdfs:subClassOf [
        #               rdf:type owl:Restriction ;
        #               owl:onProperty gr:betroffenesElement ;
        #               owl:someValuesFrom gr:{ling_element} ;
        #             ]; """
        # ling_area_block = f"""rdfs:subClassOf [
        #               rdf:type owl:Restriction ;
        #               owl:onProperty gr:liegtImBereich ;
        #               owl:someValuesFrom gr:{ling_area} ;
        #             ]; """
        #
        # operation_block = f"""rdfs:subClassOf [
        #               rdf:type owl:Restriction ;
        #               owl:onProperty gr:hatOperation ;
        #               owl:someValuesFrom gr:{operation} ;
        #             ]; """
        #
        # operation_position_block = f"""rdfs:subClassOf [
        #                       rdf:type owl:Restriction ;
        #                       owl:onProperty gr:istInPosition ;
        #                       owl:someValuesFrom gr:{operation_position} ;
        #                     ]; """
        #
        # ling_form_block = f"""rdfs:subClassOf [
        #               rdf:type owl:Restriction ;
        #               owl:onProperty gr:hatOperationsform ;
        #               owl:someValuesFrom gr:{ling_form} ;
        #             ]; """
        #
        # figure_query = f"""
        #     SELECT ?label
        #     WHERE {{
        #       ?class rdf:type owl:Class ;
        #             rdfs:label ?label ;
        #             {ling_elem_block if ling_element != nothing else ""}
        #             {ling_area_block if ling_area != nothing else ""}
        #             {operation_block if operation != nothing else ""}
        #             {operation_position_block if operation_position != nothing else ""}
        #             {ling_form_block if ling_form != nothing else ""}
        #             FILTER (LANG(?label) = 'de').
        #     }}
        #     """
        # print(figure_query)
        #
        # test_query = f"""
        #       SELECT ?label
        #       WHERE {{
        #         ?class rdf:type owl:Class ;
        #               rdfs:label ?label ;
        #               rdfs:subClassOf [
        #                 rdf:type owl:Restriction ;
        #                 owl:onProperty gr:betroffenesElement ;
        #                 owl:someValuesFrom gr:Wortelement ;
        #               ] ;
        #               rdfs:subClassOf [
        #                 rdf:type owl:Restriction ;
        #                 owl:onProperty gr:hatOperationsform ;
        #                 owl:someValuesFrom gr:SelbeForm ;
        #                ]
        #        FILTER (LANG(?label) = 'de').
        #       }}
        #            """

        readonly = any([has_value(form_value) for form_value in [text, text_id, context, author, source]])

        figure_infos = []
        if not text:
            flash('Bitte gib einen Text ein!')
        if "send" in request.form:
            # Only save the new text if it does not yet have an ID
            if text_id is None or text_id.strip() == "":
                new_text_id = db.save_new_text(text, context, author, source)
                text_id = new_text_id

            result = query_builder_result(ling_element, ling_area, ling_form, operation, operation_position, nothing)

            print(f"here are the results: {result}")

            for figure_name in result:
                figure_info = {"figure_name": figure_name, "definitions": get_figure_definition(figure_name),
                               "examples": get_examples(figure_name)}
                figure_infos.append(figure_info)
        if text:
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
                        owl:onProperty gr:hatDefinition ;
                        owl:hasValue ?value ;
                     ] .    }}
                    """
    def_query_result = g.query(def_query)
    for result in def_query_result:
        value_uri = result['value'].toPython()
        def_text_query = f""" SELECT ?definitionText
                 WHERE {{
                      <{value_uri}> gr:hatDefinitionsText ?definitionText .
                     }}
                """

        def_text_result = g.query(def_text_query)
        for def_text in def_text_result:
            definition_entry = {'text': "",
                                'author': ""}
            label_literal = def_text['definitionText']
            definition_entry['text'] = label_literal.value

            # add author of a definition
            def_author_query = f""" SELECT ?definitionAutor
                 WHERE {{
                      <{value_uri}> gr:istAutor ?definitionAutor .
                     }}
                """
            def_author_result = g.query(def_author_query)
            for def_author in def_author_result:
                label_literal = def_author['definitionAutor']
                definition_entry['author'] = label_literal.value

            # add source of a definition
            def_source_query = f"""
                        SELECT ?definitionSource
                        WHERE {{
                        <{value_uri}> gr:istQuelle ?definitionSource .
                            }}
                        """
            for def_source in g.query(def_source_query):
                label_literal = def_source['definitionSource']
                definition_entry['source'] = label_literal.value
            definitions.append(definition_entry)

    return definitions


def get_examples(figure_name):
    figure_name = figure_name.replace(" ", "") # remove spaces from figure names (e.g., "Etymolog. Figur")
    examples = []
    example_query = f""" SELECT ?instance ?author ?source ?example
                        WHERE {{
                          ?instance rdf:type gr:{figure_name} .
                          OPTIONAL {{ ?instance gr:istAutor ?author . }}
                          OPTIONAL {{ ?instance gr:istQuelle ?source . }}
                          OPTIONAL {{ ?instance gr:istBeispiel ?example . }}
                            }}
                        """
    print(f"figure name in examples: {figure_name}")
    example_query_result = g.query(example_query)
    for res in example_query_result:
        example_entry = {
            # 'instance': res['instance'].n3(),
            'example_text': res["example"].value,  # example text is mandatory
            'example_source': res["source"].value if res["source"] else None,
            'example_author': res["author"].value if res["author"] else None
        }
        print(f"example entry {example_entry}")
        examples.append(example_entry)

    return examples


@app.route("/figure_information", methods=['POST', 'GET'])
def figure_information():

    figure_data = query_list_elements(query=get_all_figure_labels_query, key_name="figure", no_idea=False)

    if request.method == 'POST':
        figure = request.form['figure']
        figure_detail_infos = []
        figure_detail_info = {"figure_name": figure, "definitions": get_figure_definition(figure),
                              "examples": get_examples(figure)}
                                #"position": "Anfang", "rhetoricalClass": "Betonungsfigur"}  # etc...
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


# check is user input has
# 1. resonable length
# 2. is German
# 3. is not harmful
def is_invalid_input(text):
    # 1. Check reasonable text length
    if len(text) < 10 or len(text) > 1000:
        return True

    # 2. Check language
    lang = langdetect.detect(text)
    if lang != 'de':  # Assuming 'en' is the expected language
        return True

    # 3. hate speech

    return False


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
            conn.execute('INSERT INTO texts (text, context, author, source, is_invalid) VALUES (?, ?, ?, ?, ?)',
                         (text, context, author, source, is_invalid_input(text)))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('create.html')


def get_figure_label() -> list:
    result = g.query(get_all_figure_labels_query)
    data = []
    for row in result:
        value_element = row[0]
        data.append(value_element)
    return data




if __name__ == '__main__':
    app.run()
