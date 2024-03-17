import sqlite3

import rdflib

import app

figure_labels = app.get_figure_label()

connection = sqlite3.connect("database.db")

with open("schemaFyF.sql") as f:
    connection.executescript(f.read())

cursor = connection.cursor()

# cursor.execute("INSERT INTO texts (text, context, author, source) VALUES (?)",
#                ('Veni, vidi, vici', '', 'Caesar', '')
#                )
cursor.execute(
    "INSERT INTO texts (text, context, author, source) VALUES ('Veni, vidi, vici', '', 'Caesar', '')"
)


for figure in figure_labels:
    cursor.execute(
        f"INSERT INTO rhetorical_figures (name) VALUES ('{figure}')"
    )  # (figure,) as a tuple?

cursor.execute(
    "INSERT INTO annotations (text_id, figure_id, verified) VALUES (1,1, TRUE)"
)

# cur.execute(f"INSERT INTO rhetorical_figures (name) VALUES (?)",
#             ('First Post', 'Content for the first post')
#             )
#


connection.commit()
connection.close()
