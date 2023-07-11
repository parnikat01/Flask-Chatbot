from flask import Flask, redirect, render_template, request, redirect, session, abort, send_file
import requests
from flask_sqlalchemy import SQLAlchemy
import yaml
from collections import defaultdict
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import os
import pathlib
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from zipfile import ZipFile

app = Flask(__name__)
english_bot = ChatBot("Chatterbot", storage_adapter="chatterbot.storage.SQLStorageAdapter")
trainer = ChatterBotCorpusTrainer(english_bot)
trainer.train("chatterbot.corpus.english")
trainer.train("D:\Flask-ChatBot-Creator\data\data.yml")

# Google Auth
app.secret_key = "ABDP@123"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GOOGLE_CLIENT_ID = "107668336904-gga3mks6pspvjjs8dmdc8grv2i9odm3s.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email",
            "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect("/protected_area")


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper


@app.route("/protected_area")
@login_is_required
def protected_area():
    # return f"Hello {session['name']}! <br/> <a href='/logout'><button>Logout</button></a>"
    return render_template("index.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# Google Auth end

# Download
@app.route("/download")
def download_file():
    p = "requirements.txt"
    return send_file(p, as_attachment=True)


@app.route("/downloadcode")
def download_code():
    p = "code.txt"
    return send_file(p, as_attachment=True)


@app.route("/downloaddata")
def download_data():
    p = "./data/data.yml"
    return send_file(p, as_attachment=True)


# Download end

# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///QA.db"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://ybncbfmogryini:330fe15eda5addf40a557045e7c603f29b072129a64fdeb0279c3ff454a0db61@ec2-44-199-143-43.compute-1.amazonaws.com:5432/d8p9gvm3tr6hj2"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

e = {'categories': ['conversations']}
d = {}
keys = 'conversations'
c = {}
values = []
d[keys] = values


class QA(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    ques = db.Column(db.String(200), nullable=False)
    ans = db.Column(db.String(200), nullable=False)

    def __repr__(self) -> str:
        return f"{self.ques} - {self.ans}"


@app.route("/")
def index():
    return render_template("Home.html")  # to send context to html file


@app.route("/qa", methods=['GET', 'POST'])
def hello_world():
    if request.method == 'POST':
        question = request.form['ques']
        answer = request.form['ans']
        qa = QA(ques=question, ans=answer)
        db.session.add(qa)
        db.session.commit()

        array = [question, answer]

        letsCheck = []
        letsCheck.append(array)
        values.append(array)
        c = e.update(d)

        def write_yaml(data):
            # """ A function to write YAML file"""
            # with open('toyaml.yml', 'a') as f:
            #     yaml.dump_all(data, f, default_flow_style=False)
            with open(r'data\data.yml', 'a') as file:
                documents = yaml.dump(data, file, default_flow_style=False)

        if __name__ == "__main__":
            # read the config yaml
            my_config = letsCheck

            # write A python object to a file
            write_yaml(my_config)

    showQA = QA.query.all()
    # print(showQA)
    return render_template("index.html", showQA=showQA)


@app.route("/update/<int:sno>", methods=['GET', 'POST'])
def update(sno):
    if request.method == 'POST':
        question = request.form['ques']
        answer = request.form['ans']
        udpQA = QA.query.filter_by(sno=sno).first()
        udpQA.ques = question
        udpQA.ans = answer
        db.session.add(udpQA)
        db.session.commit()
        return redirect("/qa")
    udpQA = QA.query.filter_by(sno=sno).first()
    # print(udpQA)
    return render_template("update.html", udpQA=udpQA)


@app.route("/delete/<int:sno>")
def delete(sno):
    delQA = QA.query.filter_by(sno=sno).first()
    db.session.delete(delQA)
    db.session.commit()
    return redirect("/qa")


@app.route("/get")
def get_bot_response():
    userText = request.args.get("msg")  # to get data from input, we write js in index.html
    return str(english_bot.get_response(userText))


@app.route("/deployment")
def guidance():
    return render_template("Deployment.html")


if __name__ == "__main__":
    app.run(debug=True)
