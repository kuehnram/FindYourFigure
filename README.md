Find your Figure! This is a Webapp to find the name of a rhetorical figure hidden in a text. For now, it is only availably in German.
As a human, you are very good in spotting "deviations" from the normal sentence structure, e.g., see repeating words, or if they are reversed, etc. But no one can remember those fancy Latin or Greek names for rhetorical figures! 

```fyfpage.html```: This page helps you to find the right name after you indicate the properties you spotted in a text/sentence.
You can enter a self-chosen example or select one from the database.
You can also use the power of a large language model together with RAG that helps you to find the name of the figure when you describe it in natural language.

```create.html```: If you want to submit just text without determining the figure, this is your way to go. Text is mandatory, contextn, author and source are not necessarily required, but nice to have.

```figure_info.html```: Here you can learn about rhetorical figures in general.

**Technical Details**

The website uses the Python Flask framework and a SQLite databse
The database is based on ```schemaFyF.sql``` and contains three tables:

```texts```: Users can submit text, context (sentences before the actual text/sentence), author, and source

```rhetorical_figures```: a static list of rhetorical figures and their id's

```annotations```: links text ids with rhetorical figure ids. In addition, it has a verified field such that a trained linguist can verify the annotation
