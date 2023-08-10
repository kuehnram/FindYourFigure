DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS examples;
DROP TABLE IF EXISTS rhetorical_figures;
DROP TABLE IF EXISTS contains_figure;

CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    content TEXT NOT NULL
);


CREATE TABLE examples (
    example_id INTEGER PRIMARY KEY AUTOINCREMENT,
    example_text VARCHAR(255) NOT NULL,
    example_author VARCHAR(255),
    example_source VARCHAR(255)
);

CREATE TABLE rhetorical_figures (
    rhet_figure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255)
);

CREATE TABLE contains_figure (
    example_id INTEGER,
    rhet_figure_id INTEGER,
    human_verified BOOLEAN,
    algorithm_verified BOOLEAN,
    PRIMARY KEY (example_id, rhet_figure_id),
    FOREIGN KEY (example_id) REFERENCES examples(example_id),
    FOREIGN KEY (rhet_figure_id) REFERENCES rhetorical_figures(rhet_figure_id)

);
