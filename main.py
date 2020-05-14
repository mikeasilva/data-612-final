import os
import datetime
import pickle
import collections
import pandas as pd
import networkx as nx
from flask import Flask, session, request, jsonify, render_template, redirect

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

G = nx.read_gpickle("G.pickle")
attributes = pickle.load(open("attributes.pickle", "rb"))
most_popular = pickle.load(open("most_popular.pickle", "rb"))

app = Flask(__name__)
app.config['SECRET_KEY'] = "f84f6176aa4cb7fccac55381b1f9005d97a8f6bd"


def get_css_hash():
    """Get a Random Hash to Add to the CSS."""
    return hash(datetime.datetime.now())

def get_recommendations(G, game_id, n_recommendations = 5, return_weights = False):
    root_node = "game_" + str(game_id)
    counts = dict()
    for n in G.neighbors(root_node):
        if n == "popular":
            weight = 1
        elif "category" in n:
            weight = 2
        elif "integrates_with_"  in n:
            weight = 20
        elif "year" in n:
            weight = 1
        elif "user" in n:
            weight = 1
        else:
            weight = 2
        for node in G.neighbors(n):
            node_id = int(node.replace("game_", ""))
            if node != root_node:
                counts[node_id] = counts.get(node_id, 0) + weight
    
    recommendations = [u[1] for u in sorted(((value, key) for (key,value) in counts.items()), reverse=True)][0:n_recommendations]
    return recommendations


def add_to_front_of_history(game_id):
    """Adds a game id to the front of the session history list.
    Parameters:
        game_id: int The game id to add to the front of the history
    """
    history = session.get("history", list())
    # Remove the game id from the history if it is already there
    if game_id in history:
        history.remove(game_id)
    history.insert(0, game_id)
    # TODO limit history to ? items
    session["history"] = history


def get_connected_games(G, node_id):
    """Get the ids of the games and the number of connections it
    Parameters:
        G: NetworkX Graph
        node_id: str root node id
    Returns:
        counts: dict game id and number of connections
    """
    counts = dict()
    for u in nx.single_source_shortest_path_length(G, node_id, cutoff=1).items():
        if u[1] == 1:
            for row in nx.single_source_shortest_path_length(G, u[0], cutoff=1).items():
                if row[1] == 1:
                    if row[0] != node_id:
                        game_id = int(row[0].split("_")[1])
                        counts[game_id] = counts.get(game_id, 0) + 1
    return counts


@app.route("/")
def home():
    # Start up the user session view history
    session["history"] = session.get("history", list())
    css_hash = get_css_hash()
    top_recommendations = most_popular[0:10]
    has_history = (len(session["history"]) > 0)
    return render_template("home.html", css_hash = css_hash, top_recommendations = top_recommendations, attributes = attributes, has_history = has_history)


@app.route("/details/<game_id>")
def details(game_id):
    add_to_front_of_history(game_id)
    css_hash = get_css_hash()
    #return jsonify(session["history"])
    game_id = int(game_id)
    game = attributes[game_id]
    recommendations = get_recommendations(G, game_id, 10)
    return render_template("details.html", css_hash=css_hash, game=game, recommendations = recommendations, attributes = attributes)


@app.route("/clear-history")
def clear_history():
    session["history"] = list()
    return redirect("/")

@app.route("/img/<img_file>")
def img(img_file):
    #196 px
    game_id = img_file.split("\\.")[0]
    return str(game_id)

@app.route("/search", methods = ["GET", "POST"])
def search():
    if request.method == "GET":
        search_terms = request.args.get("search")
    else:
        search_terms = request.form["search"]

    search_terms = search_terms.split(" ")

    search_results = dict()
    for game_id, row in attributes.items():
        game_name = row["name"]
        search_in = game_name.lower()
        for search_for in search_terms:
            if search_for.lower() in search_in:
                search_results[game_name] = game_id
    # Sort by name
    search_results = collections.OrderedDict(sorted(search_results.items()))

    return render_template("search.html", search_results = search_results)

if __name__ == '__main__':
    app.run(debug=True)