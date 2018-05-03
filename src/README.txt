Instructions for running the program:


The Python script rl2857_datachallenge.py can be run as follows:


$ python3 rl2857_datachallenge.py


Requirements: In order to run the program, the following Python modules need to be installed:
1. NetworkX, for creating the graphs
2. Geopy (1.11.0), to calculate the distance between two coordinate pairs.
   1. The module can be installed using the command: pip install geopy


Algorithm Description:


The program goes through the following steps:
1. Classification: In this step, the file containing anonymous check-in information (checkins_train_anon.txt) is read into a dictionary, and the coordinate information corresponding to each node is parsed to classify whether the label is A or B.
   1. Relevant function: get_node_attributes()
   2. If the coordinates are located within a 10 mile city radius (New York, Rio or London), then the node is classified as A.
      1. Relevant function: if_location_within_city_radius()
   1. If it’s outside, or if it’s missing this information, the node is classified as B.
   2. In addition to the check-in information, the step also stores the check-in timestamps and the distance to each city for each node.
1. Graph creation: In this step, the file containing edge relationships between the nodes (edges_train_anon.txt) is read to create a graph of 35646 nodes.
2. Setting Graph Attributes: The information obtained from step (1) is then used to graph’s attributes using NetworkX’s set_node_attributes() method.
3. Choosing the seed set: Since the choice of seed set is critical to how the behavior is propagated across the social network, different combinations of seed sets containing nodes labeled A and B were considered.
   1. Seed sets containing top 100 nodes all labeled A, referring to people with most connections and are located in one of the three cities, were found to have a profit of close to 16,427, implying a slight improvement over baseline, but wasn’t yielding a consistent result when compared to taking a combination of nodes labeled A and B for New York and London.
   2. It was observed that choosing a (20,80) combination of nodes, i.e. 20 nodes labeled A and 80 labeled B, for New York and a (30,70) combination of nodes for London yields better results (a profit of 16667 and 16490 respectively), proving that for influence to spread better across the social network, just taking into account the geographic cluster isn’t enough and that taking into possibly far-away contacts (in terms of likes and comments) can have wider consequences for cascades.
   3. For Rio, like a combination of (42,58) yielded a profit of 16568.
1. Finding influence using independent cascades: Given the graph and the initial seed set, the algorithm navigates across the graph until all nodes have been exhausted to estimate the number of nodes influenced. 
   1. Relevant function: find_influence_top_100()
   2. It does this by performing a breadth first search of nodes as they are influenced at time t, so that nodes are added at time t are visited before nodes that are added in the next time step (t+1).
   3. The BFS algorithm starts with the seed set, finding all its neighbours and for each of them, perform the following checks:
      1. If the neighbour’s label is “A”, then add the node to the set of nodes that is sure to buy the product and promote to all its friends.
      2. If the neighbour’s label is “B”, then it estimates the probability and if it’s less than or equal to 0.3, then the node is added to the nodes to be explored. Else the cascade ends there.
   1. The search thus proceeds in this fashion until there are no more nodes to be explored.