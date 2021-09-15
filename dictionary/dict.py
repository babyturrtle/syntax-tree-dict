from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
import nltk
# import svgling
from striprtf.striprtf import rtf_to_text
from stat_parser.parser import Parser
from .auth import login_required
from .db import get_db

bp = Blueprint("dict", __name__)

parser = Parser()
UPLOAD_FOLDER = '/files'
ALLOWED_EXTENSIONS = {'rtf'}


""" 
Fragment functions 
"""


def allowed_file(filename):
    """ Check if the file extension is correct. """

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_text(text_id):
    """ Get a text from dictionary by id. """

    text = (
        get_db()
        .execute(
            "SELECT DISTINCT text.id, text.name, text.body, text.user_id"
            " FROM text"
            " WHERE text.id = ?",
            (text_id,),
        ).fetchone()
    )

    if text is None:
        abort(404, "Text id {0} doesn't exist.".format(text_id))

    return text


def get_text_id(text_name):
    """ Get a text id from dictionary by name. """

    text_id = (
        get_db()
        .execute(
            "SELECT DISTINCT text.id"
            " FROM text"
            " WHERE text.name = ?",
            (text_name,),
        ).fetchone()
    )

    if text_id is None:
        abort(404, "Text id {0} doesn't exist.".format(text_name))

    return text_id


def get_sen_ids(text_id):
    """ Get sentences id's from dictionary by text id. """

    sen_ids = (
        get_db()
        .execute(
            "SELECT DISTINCT sentence.id"
            " FROM text"
            " JOIN sentence ON text.id = sentence.text_id "
            " WHERE text.id = ?",
            (text_id,),
        ).fetchall()
    )

    if sen_ids is None:
        abort(404, "Text id {0} doesn't exist.".format(text_id))

    return sen_ids


def get_sentence(sen_id):
    """ Get a sentence from dictionary by id. """

    sentence = (
        get_db()
        .execute(
            "SELECT sentence.id, sentence.name, sentence.tree, sentence.text_id, sentence.user_id"
            " FROM sentence"
            " WHERE sentence.id = ?",
            (sen_id,),
        ).fetchone()
    )

    if sentence is None:
        abort(404, "Sentence id {0} doesn't exist.".format(sen_id))

    return sentence


'''
def get_tree(sentence):
    """ Get syntax tree of sentence. """

    tokens = nltk.regexp_tokenize(sentence, sentence_re)
    tagged_tokens = nltk.tag.pos_tag(tokens)
    tree = chunker.parse(tagged_tokens)

    return tree
'''

'''
def tree_to_image(tree, text_name, sen_id):
    cf = CanvasFrame()
    t = Tree.fromstring(tree)
    tc = TreeWidget(cf.canvas(), t)
    cf.add_widget(tc, 10, 10)
    ps_name = text_name + '_' + str(sen_id) + '.ps'
    png_name = text_name + '_' + str(sen_id) + '.png'
    cf.print_to_file(ps_name)
    cf.destroy()
    os.system('convert ' + ps_name + ' ' + png_name)
    return png_name
'''

""" 
View functions 
"""

''' 
        file.save(os.path.join(bp.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('uploaded_file', filename=filename))
'''


@bp.route("/")
def index():
    """ View the names of the texts in the dictionary. """

    db = get_db()
    texts = db.execute(
        "SELECT text.id, text.name FROM text ORDER BY text.name "
    ).fetchall()

    return render_template("dictionary/dictionary.html", texts=texts)


@bp.route("/<int:text_id>/")
def view_text(text_id):
    """ View the sentence and its tree by the sentence id. """

    text = get_text(text_id)
    sen_ids = get_sen_ids(text_id)
    sentences = []

    for sen_id in sen_ids:
        for sent in sen_id:
            sentence = get_sentence(sent)
            sentences.append(sentence)

    return render_template("dictionary/text.html", text=text, sentences=sentences)


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """
        Upload a rtf text file and add the text,
        its sentences and their syntax trees to the database.
    """

    if request.method == 'POST':
        text_name = request.form["text"]
        error = None

        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if not text_name:
            error = "Text name is required."
        if error is not None:
            flash(error)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(filename)
            with open(filename) as f:
                as_string = f.read()
            file_text = rtf_to_text(as_string)
            # with open(filename) as f:
            #   file_text = f.read()
            sentences = nltk.tokenize.sent_tokenize(file_text)

            db = get_db()
            db.execute(
                "INSERT OR IGNORE INTO text (name, body, user_id) VALUES (?, ?, ?)",
                (text_name, file_text, g.user["id"]),
            )
            db.commit()
            text_id_list = get_text_id(text_name)
            for i in text_id_list:
                text_id = i
            for sentence in sentences:
                # tree = get_tree(sentence)
                tree = parser.parse(sentence)
                db.execute(
                    "INSERT OR IGNORE INTO sentence (name, tree, text_id, user_id) VALUES (?, ?, ?, ?)",
                    (sentence, str(tree), text_id, g.user["id"]),
                )
                db.commit()

        return redirect(url_for("dict.index"))

    return render_template("dictionary/upload_file.html")
