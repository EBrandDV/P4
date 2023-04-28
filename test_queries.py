from SPARQLWrapper import SPARQLWrapper, CSV, JSON
import queries as spq
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
    print('q_density')
    sparql.setQuery(spq.q_density(graph= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    print('q_cluster')
    sparql.setQuery(spq.q_cluster(graph= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    print('q_voc_uni')
    sparql.setQuery(spq.q_voc_uni(graph= graph_1))
    print(sparql.query().convert()["results"]["bindings"])
    print('q_knowledge_degree')
    sparql.setQuery(spq.q_knowledge_degree(graph= graph_1))
    print(sparql.query().convert()["results"]["bindings"])
    print('q_growth')
    sparql.setQuery(spq.q_growth(graph1= graph_1, graph2= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    print('q_change_ratio')
    sparql.setQuery(spq.q_change_ratio(graph1= graph_1, graph2= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    print('q_add_change_ratio')
    sparql.setQuery(spq.q_add_change_ratio(graph1= graph_1, graph2= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    print('q_rem_change_ratio')
    sparql.setQuery(spq.q_rem_change_ratio(graph1= graph_1, graph2= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    print('query_set')
    sparql.setQuery(spq.query_set(graph= graph_1))
    print(sparql.query().convert()["results"]["bindings"])
    print('vocab_set')
    sparql.setQuery(spq.vocab_set(wrapper= sparql, graph= graph_1))
    print(sparql.query().convert()["results"]["bindings"])
    print('vocab_union')
    sparql.setQuery(spq.vocab_union(wrapper= sparql, graph1= graph_1, graph2= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    print('vocab_dyna')
    sparql.setQuery(spq.vocab_dyna(wrapper= sparql, graph1= graph_1, graph2= graph_2))
    print(sparql.query().convert()["results"]["bindings"])
    print('q_icr')
    sparql.setQuery(spq.q_icr(graph= graph_1, ont= ont))
    print(sparql.query().convert()["results"]["bindings"])
    print('q_ipr')
    sparql.setQuery(spq.q_ipr(graph= graph_1, ont= ont))
    print(sparql.query().convert()["results"]["bindings"])
    print('q_imi')
    sparql.setQuery(spq.q_imi(ont= ont))
    print(sparql.query().convert()["results"]["bindings"])

query_tester()