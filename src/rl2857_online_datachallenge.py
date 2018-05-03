import logging
import requests
from operator import itemgetter
# import pickle

# set the console logging format
FORMAT = '%(asctime)-15s %(message)s'
DATEFMT = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(format=FORMAT, datefmt=DATEFMT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# budget
budget = 500

# degree threshold
degree_threshold = 100

# clustering coefficient threshold
cc_threshold = 0.2


# function to add nodes to the final seed set
def appendToSeedSet(seed_s, nodes, num):

    for n in nodes:
        if n[0] not in seed_s and len(seed_s) < 250:
            seed_s.append(n[0])

    return seed_s


if __name__ == "__main__":

    logger.info("Started execution...")

    logger.info("Fetching nodes from the online network...")

    key_headers = {"uni": "rl2857", "pass": "16"}
    api_key_response = requests.get("http://167.99.225.109:5000/api/getKey", headers=key_headers)
    # key_headers = {"uni": "rl2857"}
    # api_key_response = requests.get("http://159.89.95.64:5000/api/getKey", headers=key_headers)
    APIkey = api_key_response.text

    logger.info(APIkey)

    node_headers = {"uni": "rl2857", "key": APIkey}

    graph = {}

    # Make 499 API calls to get the random nodes
    for i in range(499):
        # node_response = requests.get("http://159.89.95.64:5000/api/nodes/getRandomNode", headers=node_headers)
        node_response = requests.get("http://167.99.225.109:5000/api/nodes/getRandomNode", headers=node_headers)
        node_info = node_response.json()
        node_id = node_info['nodeid']

        graph[node_id] = [node_info['neighbors'], node_info['label'], node_info['degree'], node_info['clusteringCoef']]

    # with open("nodes.pkl", "wb") as f:
    #     pickle.dump(graph, f)
    #
    # with open("nodes.pkl", "rb") as f:
    #     graph = pickle.load(f)

    # Construct a master list of nodes containing their properties
    node_list_dict = {}
    for key, value in graph.items():
        node_list_dict[key] = [key, value[1], value[2], value[3]]
        neighbors_dict = value[0]
        for n_key, n_value in neighbors_dict.items():
            if n_key not in node_list_dict:
                node_list_dict[n_key] = [n_key, n_value['label'], n_value['degree'], n_value['clusteringCoef']]

    node_list = node_list_dict.values()

    logger.info("Total number of nodes: " + str(len(node_list)))

    logger.info("Creating the seed set...")

    # Construct an interim seed set based on labels A and B for the nodes
    interim_a_seed_set = []
    interim_b_seed_set = []

    for node in node_list:
        nodeid = node[0]
        label = node[1]
        degree = int(node[2])
        clustering_coeff = node[3]

        if clustering_coeff == "undefined":
            clustering_coeff = 1.0
        else:
            clustering_coeff = float(clustering_coeff)

        # Add a node of label A to the interim seed set if its clustering coefficient is less than 0.2
        # Add a node of label A to the interim seed set if its degree is more than 100
        if label == 'A' and (clustering_coeff <= cc_threshold or degree >= degree_threshold) \
                and nodeid not in interim_a_seed_set:
            interim_a_seed_set.append([nodeid, degree, clustering_coeff])
        if label == 'B' and degree >= degree_threshold and nodeid not in interim_b_seed_set:
            interim_b_seed_set.append([nodeid, degree, clustering_coeff])

    # Sort the respective lists based on clustering coefficient and degree
    interim_a_seed_set = sorted(interim_a_seed_set, key=itemgetter(2))
    interim_b_seed_set = sorted(interim_b_seed_set, key=itemgetter(1), reverse=True)

    # Get a combination of these two seed sets to get the final seed set
    interim_seed_set = interim_a_seed_set[0:75] + interim_b_seed_set[0:175]

    logger.info("Total number of interim nodes: " + str(len(interim_seed_set)))

    number_elts_needed = 0

    # If size of seed set is less than 250, add more of nodes labeled B
    if len(interim_seed_set) < 250 and len(interim_b_seed_set) > 175:
        current_len = len(interim_seed_set)
        number_elts_needed = 250 - current_len
        last_index = 175 + number_elts_needed

        interim_seed_set = interim_seed_set + interim_b_seed_set[175:last_index]

    logger.info("Total number of interim nodes after updates: " + str(len(interim_seed_set)))

    seed_set = [row[0] for row in interim_seed_set]

    # If the final seed set size is still less than 250, add nodes not prevviously added randomly
    if len(seed_set) < 250:
        seed_set = appendToSeedSet(seed_set, node_list, number_elts_needed)

    logger.info("Final number of nodes in seed set after updates: " + str(len(seed_set)))

    logger.info("Writing the seed set to file...")
    seed_file = open("seedset.txt", "w")
    for item in seed_set:
        seed_file.write("%s\\n\n" % item)