import os
import pickle
import pandas as pd
import networkx as nx
from flask import Flask, session, request, jsonify, render_template

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

G = nx.read_gpickle("G.pickle")
attributes = pickle.load(open("attributes.pickle", "rb"))
most_popular = pickle.load(open("most_popular.pickle", "rb"))

app = Flask(__name__)
app.config['SECRET_KEY'] = "f84f6176aa4cb7fccac55381b1f9005d97a8f6bd"


def get_connected_games(G, node_id):
    """Get the ids of the games and the number of connections it
    Args:
        G: NetworkX Graph
        node_id: root node
    Returns:
        counts: Dictionary with game id and number of connections
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
def index():
    return render_template('home.html')

@app.route("/details/<game_id>")
def details(game_id):
    game_id = int(game_id)
    game = attributes[game_id]
    #return jsonify(attributes[game_id])
    return render_template("details.html", game=game)

@app.route("/api/recomendations/<game_id>")
def recomendations(game_id):
    node_id = "game_" + str(game_id)
    connected_games = get_connected_games(G, node_id)
    #connected_games = pd.DataFrame([connected_games])
    connected_games = sorted(((value, key) for (key,value) in connected_games.items()), reverse=True)
    ## Get viewed from session
    ## sum rows viewed
    ## sort by weight
    ## pick top 5 records not viewed

    return jsonify(connected_games)

if __name__ == '__main__':
    app.run()