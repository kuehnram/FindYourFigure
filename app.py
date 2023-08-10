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


def query_list_elements(query: str, key_name: str) -> list:
    result = g.query(query)
    data = []
    for row in result:
        value_element = row[0]
        data.append({key_name: str(value_element)})
    data.append({key_name: "Keins davon/Weiß nicht"})
    return data


@app.route('/fyfpage', methods=('POST', "GET"))
def fyfpage():
    # data = [{'name': 'red'}, {'name': 'green'}, {'name': 'blue'}]
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

    if request.method == 'POST':
        author = request.form['author']
        source = request.form['source']
        text = request.form['text']
        operation = request.form['operation']
        operation_position = request.form['operation_position']
        ling_element = request.form['ling_element']
        ling_form = request.form['ling_form']



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
        result = g.query(test)
        print(result.bindings)
        for row in result:
            print(row)  # ANAPHORA!!!! Kreisch!

        # todo here write query with the selected items

        # if not text:
        #     flash('A text is required!')
        # else:
        return redirect(url_for('index'))

    # conn = get_db_connection()
    # posts = conn.execute('SELECT * FROM posts').fetchall()
    # conn.close()
    return render_template('fyfpage.html', ling_element_data=ling_element_data, operation_data=ling_operation_data,
                           position_data=ling_pos_data, ling_form_data=ling_form_data)


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
