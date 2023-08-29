"""




Add Internationalization
https://medium.com/@nicolas_84494/flask-create-a-multilingual-web-application-with-language-specific-urls-5d994344f5fd
https://phrase.com/blog/posts/flask-app-tutorial-i18n/

"""
import re
from flask import Flask, render_template, request, url_for, redirect, flash
import sqlite3
from werkzeug.exceptions import abort
import rdflib

g = rdflib.Graph()
g.parse('C:/Users/kuehn21/PycharmProjects/GrhootRestructured/grhoot.owl', format='application/rdf+xml')
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


# Get all elements from a cetain category from the ontology as options in the dropdown menu
def query_list_elements(query: str, key_name: str) -> list:
    result = g.query(query)
    data = []
    for row in result:
        value_element = row[0]
        data.append({key_name: str(value_element)})
    # add "nothing/ i don't know as option
    data.append({key_name: "Keins davon/Weiß nicht"})
    return data


# Build first the options for the dropdowns from where the users can choose matching properties.
# Based on those properties, build a query for the ontology.
# Todo Return the matching figures + definition + examples to the users.
@app.route('/fyfpage', methods=('POST', "GET"))
def fyfpage():
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
    ling_pos_data = query_list_elements(query=ling_pos_query, key_name="lingPos")

    ling_operation_query = """
    SELECT ?subclassLabel
    WHERE {
      ?subclass rdf:type owl:Class ;
                rdfs:subClassOf gr:LinguistischeOperation ;
                rdfs:label ?subclassLabel .
    }
    """
    ling_operation_data = query_list_elements(query=ling_operation_query, key_name="lingOp")

    ling_element_query = """
    SELECT ?subclassLabel
    WHERE {
      ?subclass rdf:type owl:Class ;
                rdfs:subClassOf gr:LinguistischesElement ;
                rdfs:label ?subclassLabel .
    }
    """
    ling_element_data = query_list_elements(query=ling_element_query, key_name="lingElem")

    ling_form_query = """
        SELECT ?subclassLabel
        WHERE {
          ?subclass rdf:type owl:Class ;
                    rdfs:subClassOf webprotege:LinguistischeForm ;
                    rdfs:label ?subclassLabel .
        }
        """
    ling_form_data = query_list_elements(query=ling_form_query, key_name="lingForm")

    ling_area_query = """
     SELECT ?subclassLabel
        WHERE {
          ?subclass rdf:type owl:Class ;
                    rdfs:subClassOf gr:LinguistischerUmfang ;
                    rdfs:label ?subclassLabel .
        }
     """
    ling_area_data = query_list_elements(query=ling_area_query, key_name="lingArea")

    if request.method == 'POST':
        nothing = "Keins davon/Weiß nicht"
        author = request.form['author']
        source = request.form['source']
        text = request.form['text']
        operation = request.form['operation']
        operation_position = request.form['operation_position']
        # convert to CamelCase => classnames in ontology
        operation_position = operation_position.title().replace(" ", "") if operation_position != nothing else nothing
        ling_element = request.form['ling_element']
        ling_form = request.form['ling_form']
        ling_form = ling_form.title().replace(" ", "") if ling_form != nothing else nothing
        ling_area = request.form['ling_area']

        test = f"""
        SELECT ?label
        WHERE {{
          ?class rdf:type owl:Class ;
                rdfs:label ?label ;
                rdfs:subClassOf [
                  rdf:type owl:Restriction ;
                  owl:onProperty webprotege:betroffenensElement ;
                  owl:someValuesFrom webprotege:{ling_element} ;
                ]
                .
        }}
        """

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
                   .
            }}
            """
        print(figure_query)
        result = g.query(figure_query)
        figure_list = []

        # < owl: onProperty
        # rdf: resource = "http://webprotege.stanford.edu/hatDefinition" / >
        # < owl: hasValue
        # rdf: resource = "http://webprotege.stanford.edu/DefinitionAnapher1" / >
        for row in result:
            row = re.search(r"('.*?')", str(row)).group(1)
            def_query = f""" SELECT ?value
                             WHERE {{
                                ?class rdf:type owl:Class ;
                                rdfs:label {row}@de  ;
                                rdfs:subClassOf [
                                owl:onProperty webprotege:hatDefinition ;
                                owl:hasValue ?value ;
                             ] .    }}
                            """
            def_query_result = g.query(def_query)
            for definition in def_query_result:
                pass # todo get definitions

            print(row)  # ANAPHORA!
        if not text:
            flash('Bitte gib einen Text ein!')
        else:
            return render_template('fyfpage.html', ling_element_data=ling_element_data,
                                   operation_data=ling_operation_data,
                                   position_data=ling_pos_data, ling_form_data=ling_form_data,
                                   ling_area_data=ling_area_data, ergebnis="Folgende Figuren wurden gefunden:",
                                   result=result)

    # conn = get_db_connection()
    # posts = conn.execute('SELECT * FROM posts').fetchall()
    # conn.close()
    return render_template('fyfpage.html', ling_element_data=ling_element_data, operation_data=ling_operation_data,
                           position_data=ling_pos_data, ling_form_data=ling_form_data, ling_area_data=ling_area_data)


@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    return render_template('post.html', post=post)


def get_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    conn.close()
    if post is None:
        abort(404)
    return post


@app.route('/function')
def function():
    return render_template("function.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/create', methods=('POST', "GET"))
def create():
    if request.method == 'POST':
        author = request.form['author']
        source = request.form['source']
        text = request.form['text']
        if not text:
            flash('A text is required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO examples (example_text, example_author, example_source) VALUES (?, ?, ?)',
                         (text, author, source))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('create.html')


@app.route("/<int:id>/edit", methods=("GET", "POST"))
def edit(id):
    post = get_post(id)
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        if not title:
            flash("Title is required!")
        else:
            conn = get_db_connection()
            conn.execute("UPDATE posts SET title = ?, content = ? WHERE id = ?", title, content, id)
            conn.commit()
            conn.close()
            return redirect(url_for("index"))
    return render_template("edit.html", post=post)


@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    post = get_post(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted!'.format(post['title']))
    return redirect(url_for('index'))


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == '__main__':
    app.run()
