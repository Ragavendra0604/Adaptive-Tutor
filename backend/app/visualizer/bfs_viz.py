import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO

def visualize_bfs(graph_adj, start_node):
    G = nx.Graph()
    for u, vs in graph_adj.items():
        for v in vs:
            G.add_edge(u, v)
    pos = nx.spring_layout(G)
    plt.figure(figsize=(6,4))
    nx.draw(G, pos, with_labels=True, node_size=600)
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return buf
