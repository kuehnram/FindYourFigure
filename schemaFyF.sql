DROP TABLE IF EXISTS texts;
DROP TABLE IF EXISTS annotations;
DROP TABLE IF EXISTS rhetorical_figures;

CREATE TABLE texts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text VARCHAR(255) NOT NULL,
    context VARCHAR(255),
    author VARCHAR (255),
    source VARCHAR (255),
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text_id INTEGER NOT NULL,
    figure_id INTEGER NOT NULL,
    verified BOOLEAN,
    FOREIGN KEY (text_id) REFERENCES texts(id),
    FOREIGN KEY (figure_id) REFERENCES rhetorical_figures(figure_id)
);

CREATE TABLE rhetorical_figures (
    figure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL
);

