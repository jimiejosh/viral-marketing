import networkx as nx
import csv
import random
from geopy.distance import vincenty
import logging

# set the console logging format
FORMAT = '%(asctime)-15s %(message)s'
DATEFMT = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(format=FORMAT, datefmt=DATEFMT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# set the location coordinates
baseline_NYC = (40.730610, -73.935242)
baseline_LDN = (51.509865, -0.118092)
baseline_RDJ = (-22.970722, -43.182365)

# set 10 mile city radius threshold
threshold = 10

# budget
budget = 100

# probability of 0.3
p = 0.3

NYC_nodes = set()
LDN_nodes = set()
RDJ_nodes = set()
other_nodes = set()


# function to check if the given coordinate pair is within the city radius
def if_location_within_city_radius(baseline, latitude, longitude):
    coords = (latitude, longitude)
    dist = vincenty(baseline, coords).miles
    return dist


# function to get the attributes of each node of the graph
def get_node_attributes(checkin_d):

    new_checkin_dict = {}

    # read the checkin dictionary
    for key, val in checkin_d.items():
        checkin_ts = []
        checkin_loc_dist = []
        for details in val:
            checkin_ts.append(details[0])

            dist_ny = if_location_within_city_radius(baseline_NYC, details[1], details[2])
            if dist_ny <= threshold:
                NYC_nodes.add(key)

            dist_ldn = if_location_within_city_radius(baseline_LDN, details[1], details[2])
            if dist_ldn <= threshold:
                LDN_nodes.add(key)

            dist_rdj = if_location_within_city_radius(baseline_RDJ, details[1], details[2])
            if dist_rdj <= threshold:
                RDJ_nodes.add(key)

            else:
                other_nodes.add(key)

            checkin_loc_dist.append((dist_ny, dist_ldn, dist_rdj))

        # set the attributes for each node
        if key in NYC_nodes or key in LDN_nodes or key in RDJ_nodes:
            new_checkin_dict[key] = {"label": "A", "checkin_ts": checkin_ts, "checkin_loc": checkin_loc_dist}
        else:
            new_checkin_dict[key] = {"label": "B", "checkin_ts": checkin_ts, "checkin_loc": checkin_loc_dist}

    return new_checkin_dict


# function to find the influence using independent cascades
def find_influence_top_100(graph, seed):

    frontier_set = seed

    for node in frontier_set:

        if node in nx.nodes(graph):

            neighbors = nx.all_neighbors(G, node)

            for neighbor in neighbors:
                if neighbor not in frontier_set:
                    if len(graph.nodes[neighbor]):
                        label = graph.nodes[neighbor]["label"]
                        if label == "A":
                            frontier_set.append(neighbor)
                        elif label == "B":
                            prob = random.random()
                            if prob <= p:
                                frontier_set.append(neighbor)

    return frontier_set


if __name__ == "__main__":

    logger.info("Started execution...")

    logger.info("Reading the checkin file...")
    checkin_dict = {}

    with open("checkins_train_anon.txt") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if row[2] == '':
                row[2] = 0
            if row[3] == '':
                row[3] = 0

            if row[0] in checkin_dict:
                checkin_dict[row[0]].append([row[1], float(row[2]), float(row[3])])
            else:
                checkin_dict[row[0]] = [[row[1], float(row[2]), float(row[3])]]

    logger.info("Getting node attributes...")
    node_attrib_dict = get_node_attributes(checkin_dict)

    logger.info("Creating the graph...")
    # create the graph by reading the edges file
    fh = open("edges_train_anon.txt", 'rb')
    graph_type = nx.Graph()

    G = nx.read_edgelist(fh, comments='#', delimiter="\t", nodetype=str, create_using=graph_type)

    # set the node attributes
    nx.set_node_attributes(G, node_attrib_dict)
    logger.info("Graph created...")
    logger.info("Node attributes populated...")

    logger.info("Number of nodes labeled A in New York: " + str(len(NYC_nodes)))
    logger.info("Number of nodes labeled A in London: " + str(len(LDN_nodes)))
    logger.info("Number of nodes labeled A in Rio De Janeiro: " + str(len(RDJ_nodes)))

    # get the top nodes by degree
    node_deg_list = sorted(G.degree, key=lambda x: x[1], reverse=True)
    seed_set_list = [item[0] for item in node_deg_list]
    seed_set = seed_set_list[:budget]

    # get the top nodes by location
    # seed_set_NYC = [element for element in seed_set_list if element in list(NYC_nodes)][:budget]  # 16427
    # seed_set_LDN = [element for element in seed_set_list if element in list(LDN_nodes)][:budget]  # 16386

    seeds_NYC = [element for element in seed_set_list if element in list(NYC_nodes)][:budget]
    seeds_LDN = [element for element in seed_set_list if element in list(LDN_nodes)][:budget]
    seeds_other = [element for element in seed_set_list if element in list(other_nodes)][:budget]

    seed_set_NYC = seeds_NYC[:20] + seeds_other[:80]  # 16667
    seed_set_LDN = seeds_LDN[:30] + seeds_other[:70]  # 16490

    count = budget - len(RDJ_nodes)
    seed_set_RDJ = list(RDJ_nodes) + seeds_other[:count]  # 16568

    logger.info("Writing the seed set to file...")
    seed_file_NYC = open("NewYork.txt", "w")
    for item in seed_set_NYC:
        seed_file_NYC.write("%s\\n\n" % item)

    seed_file_LDN = open("London.txt", "w")
    for item in seed_set_LDN:
        seed_file_LDN.write("%s\\n\n" % item)

    seed_file_RDJ = open("Rio.txt", "w")
    for item in seed_set_RDJ:
        seed_file_RDJ.write("%s\\n\n" % item)

    seed_file_NYC.close()
    seed_file_LDN.close()
    seed_file_RDJ.close()

    logger.info("Finding the influence...")
    final_set_NYC = find_influence_top_100(G, seed_set_NYC)

    final_set_LDN = find_influence_top_100(G, seed_set_LDN)

    final_set_RDJ = find_influence_top_100(G, seed_set_RDJ)

    logger.info("Profit: The final set of influenced nodes for New York: " + str(len(final_set_NYC)))
    logger.info("Profit: The final set of influenced nodes for London: " + str(len(final_set_LDN)))
    logger.info("Profit: The final set of influenced nodes for Rio De Janiero: " + str(len(final_set_RDJ)))