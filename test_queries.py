from SPARQLWrapper import SPARQLWrapper, CSV, JSON
import message_ as spq
import pandas as pd
import re
import time
import csv


endpoint = 'http://localhost:8890/sparql'

# Configure the SPARQL endpoint
sparql = SPARQLWrapper(endpoint)

# Configure the SPARQL endpoint and desired return format
sparql.setReturnFormat(JSON)


def query_tester(graph_1 = 'http://localhost:8890/35', graph_2 = 'http://localhost:8890/dims', ont = 'http://localhost:8890/pediaowl'):
    sparql.setQuery(spq.q_density(graph= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    
    sparql.setQuery(spq.q_cluster(graph= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    
    sparql.setQuery(spq.q_voc_uni(graph= graph_1))
    print(sparql.query().convert()["results"]["bindings"])
    
    sparql.setQuery(spq.q_knowledge_degree(graph= graph_1))
    print(sparql.query().convert()["results"]["bindings"])
    
    sparql.setQuery(spq.q_growth(graph1= graph_1, graph2= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    
    sparql.setQuery(spq.q_change_ratio(graph1= graph_1, graph2= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    
    sparql.setQuery(spq.q_add_change_ratio(graph1= graph_1, graph2= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    
    sparql.setQuery(spq.q_rem_change_ratio(graph1= graph_1, graph2= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    
    sparql.setQuery(spq.q_add_vocab_dyn(graph1= graph_1, graph2= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    
    sparql.setQuery(spq.q_rem_vocab_dyn(graph1= graph_1, graph2= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    
    sparql.setQuery(spq.q_icr(graph= graph_1, ont= ont))
    print(sparql.query().convert()["results"]["bindings"])
    
    sparql.setQuery(spq.q_ipr(graph= graph_1, ont= ont))
    print(sparql.query().convert()["results"]["bindings"])
    
    sparql.setQuery(spq.q_imi(ont= ont))
    print(sparql.query().convert()["results"]["bindings"])

query_tester()