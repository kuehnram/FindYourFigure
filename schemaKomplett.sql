DROP TABLE IF EXISTS posts;

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
    linguistic_operation_id INTEGER FOREIGN KEY REFERENCES linguistic_operations(ling_op_id),
    form_id INTEGER FOREIGN KEY REFERENCES operation_forms(op_form_id),
    rhet_group_id INTEGER FOREIGN KEY REFERENCES rhetorical_groups(rhet_group_id)
);

CREATE TABLE linguistic_operations (
    ling_op_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ling_operation VARCHAR(255)
);

CREATE TABLE definitions (
  definition_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  definition_text VARCHAR(255) NOT NULL,
  definition_author VARCHAR(255),
  definition_source VARCHAR(255)
);

CREATE TABLE linguistic_objects (
    ling_object_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    ling_object VARCHAR(255)
);


CREATE TABLE linguistic_elements (
    ling_element_id INTEGER PRIMARY KEY AUTOINCREMENT ,
    ling_element VARCHAR(255)
);

CREATE TABLE linguistic_operations (
    ling_op_id INTEGER PRIMARY KEY AUTOINCREMENT ,
    ling_op VARCHAR(255)
);

CREATE TABLE operation_forms (
    op_form_id INTEGER PRIMARY KEY AUTOINCREMENT ,
    op_form VARCHAR(255)
);

CREATE TABLE linguistic_positions (
    ling_pos_id INTEGER PRIMARY KEY AUTOINCREMENT ,
    ling_pos VARCHAR(255)
);

CREATE TABLE  rhetorical_groups (
    rhet_group_id INTEGER PRIMARY KEY AUTOINCREMENT ,
    rhet_group VARCHAR(255)
);

CREATE TABLE linguistic_groups (
    ling_group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ling_group VARCHAR(255)
);

CREATE TABLE has_definition (
    PRIMARY KEY (def_id, rhet_figure_id),
    def_id FOREIGN KEY REFERENCES definitions(definition_id),
    rhet_figure_id FOREIGN KEY REFERENCES  rhetorical_figures(rhet_figure_id)
);

CREATE TABLE is_in_object(
    PRIMARY KEY (ling_object_id, rhet_figure_id),
    ling_object_id FOREIGN KEY  REFERENCES linguistic_objects(ling_object_id),
    rhet_figure_id FOREIGN KEY REFERENCES  rhetorical_figures(rhet_figure_id)
);

CREATE TABLE has_example (
    PRIMARY KEY (example_id, rhet_figure_id),
    example_id FOREIGN KEY REFERENCES examples(example_id),
    rhet_figure_id FOREIGN KEY REFERENCES rhetorical_figures(rhet_figure_id)
);

CREATE TABLE operation_affects (
    PRIMARY KEY (ling_element_id, rhet_figure_id),
    ling_element_id FOREIGN KEY REFERENCES linguistic_elements(ling_element_id),
    rhet_figure_id FOREIGN KEY REFERENCES rhetorical_figures(rhet_figure_id)
);

CREATE TABLE is_in_position (
    PRIMARY KEY (rhet_figure_id, ling_pos_id),
    rhet_figure_id FOREIGN KEY REFERENCES rhetorical_figures(rhet_figure_id),
    ling_pos_id FOREIGN KEY REFERENCES linguistic_positions(ling_pos_id)
);

CREATE TABLE is_linguistic_group (
    PRIMARY KEY (ling_group_id, rhet_figure_id),
    ling_group_id FOREIGN KEY references linguistic_groups(ling_group_id),
    rhet_figure_id FOREIGN KEY REFERENCES rhetorical_figures(rhet_figure_id)
);

CREATE TABLE is_in_area (
    PRIMARY KEY (ling_scope_id, rhet_figure_id),
    ling_scope_id FOREIGN KEY REFERENCES linguistic_scopes(ling_scope_id),
    rhet_figure_id FOREIGN KEY REFERENCES rhetorical_figures(rhet_figure_id)
);

CREATE TABLE linguistic_scopes (
    ling_scope_id INTEGER PRIMARY KEY AUTOINCREMENT ,
    ling_scope VARCHAR(255)
);

CREATE TABLE rhetorical_functions (
    rhet_func_id INTEGER PRIMARY KEY AUTOINCREMENT,
    function VARCHAR(255)
);

CREATE TABLE has_function (
    PRIMARY KEY (rhet_func_id, rhet_figure_id),
    rhet_func_id FOREIGN KEY REFERENCES rhetorical_functions(rhet_func_id),
    rhet_figure_id FOREIGN KEY REFERENCES rhetorical_figures(rhet_figure_id)
);

CREATE TABLE alternative_spelling(
    alt_spelling_id INTEGER PRIMARY KEY AUTOINCREMENT ,
    rhet_figure_id FOREIGN KEY REFERENCES rhetorical_figures(rhet_figure_id),
    spelling VARCHAR(255),
    language VARCHAR(255)
);