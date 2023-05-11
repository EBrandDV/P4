'''
This file contains all the queries and functions that will be sent to our Virtuoso database
'''

#! Imports
from SPARQLWrapper import SPARQLWrapper, CSV, JSON
import csv
import numpy as np
import pandas as pd



#-----------------------------------------------------------------------------

#! Must be run first to get the graph lists

def graph_retr(wrapper):
    
    # Set the SPARQL query to retrieve graph URIs starting with "http://example.com/"
    wrapper.setQuery('''
        SELECT DISTINCT ?g
        WHERE {
            GRAPH ?g {
                ?s ?p ?o .
            }
        }
    ''')

    # Execute the query and convert the result to JSON
    result = wrapper.query().convert()

    # Extract the list of graph URIs from the JSON result
    graph_uris = [binding['g']['value'] for binding in result['results']['bindings']]

    wiki_list = []
    db_list = []  

    # Print the list of graph URIs
    print("Graphs starting with 'http://example.com/':")
    for uri in graph_uris:
        if 'http://example.com/wiki_' in uri:
            wiki_list.append(uri)
        elif 'http://example.com/dbpedia_' in uri:
            db_list.append(uri)

    return [db_list, wiki_list]



#-----------------------------------------------------------------------------

#! Now we want to combine all the queries so we get the results
def query_retriever(wrapper, query, name):
    
    wrapper.setQuery(query)
    res = wrapper.query().convert()

    res = res['results']['bindings'][0][f'{name}']['value']

    res = float(res)
    
    return res

#-------------------------------------------------------------------------

#! Create a csv file with basic information about all graphs

def data_info(wrapper, graph_list):
    info_dict ={'File':[],
                'Subjects': [], 
                'Predicates':[],
                'Objects': [],
                'Triples': [] }

    for graph in graph_list:
        
        #Get number of distinct subjects, predicates and objects
        wrapper.setQuery(f'''
            SELECT
                (COUNT(DISTINCT ?s) as ?numSubjects)
                (COUNT(DISTINCT ?p) as ?numPredicates)
                (COUNT(DISTINCT ?o) as ?numObjects)
            FROM NAMED <{graph}>
            WHERE {{
            GRAPH <{graph}> {{
                ?s ?p ?o .
                }}
            }}
        ''')

        results = wrapper.query().convert()

        for result in results['results']['bindings']:
            numSubjects = result['numSubjects']['value']
            numPredicates = result['numPredicates']['value']
            numObjects = result['numObjects']['value']
        
        #Get number of triples
        wrapper.setQuery(f'''
            SELECT count(*)
            FROM NAMED <{graph}>
            WHERE {{
            GRAPH <{graph}> {{
                ?s ?p ?o .
                }}
            }}
        ''')

        res = wrapper.query().convert()

        triples = res['results']['bindings'][0]['callret-0']['value']

        #Inserting values into the dictionary
        info_dict['File'].append(graph)
        info_dict['Subjects'].append(numSubjects)
        info_dict['Predicates'].append(numPredicates)
        info_dict['Objects'].append(numObjects)
        info_dict['Triples'].append(triples)

        print(f'{graph} completed')
    
    #Create a csv file with the data
    with open('basics.csv', 'w') as b:
        writer = csv.writer(b)
        writer.writerow(info_dict.keys())
        writer.writerows(zip(*info_dict.values()))



#----------------------------------------------------------------------------

#! This section is dedicated to functions that return query text

def q_density(graph):
    q_dens = f'''
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            
        select (xsd:double(?E) / xsd:double(?V * (?V - 1)) as ?density)
        FROM NAMED <{graph}>
        where {{ GRAPH <{graph}>
                {{
                select (?us + ?uo + ?litcount as ?V)
                where {{
                            {{select (count(distinct(?s)) as ?us) where {{?s ?p ?o}}}}
                            {{select (count(distinct(?o)) as ?uo) where {{?s ?p ?o filter(!isLiteral(?o))}} }}
                            {{select (count(?o) as ?litcount) where {{?s ?p ?o filter(isLiteral(?o))}} }}
                    }}
                    }}
                {{
                select (count(*) as ?E) where {{ graph <{graph}> {{?s ?p ?o}}}}
                }}
            }}
            ''' 

    return q_dens

def q_cluster(graph):
    
    q_clust = f''' 
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT (xsd:float(?triangles) / xsd:float(?triples) as ?clustering_coefficient)
        FROM NAMED <{graph}>
        WHERE {{
        {{ 
        SELECT (count(?X) as ?triangles)
            WHERE {{ GRAPH <{graph}> {{
                {{ 
                    ?X ?a ?Y .
                    ?Y ?b ?Z .
                    ?Z ?c ?X
                    FILTER (STR(?X) < STR(?Y))
                    FILTER (STR(?Y) < STR(?Z))
                }} UNION {{
                    ?X ?a ?Y .
                    ?Y ?b ?Z .
                    ?Z ?c ?X
                    FILTER (STR(?Y) > STR(?Z))
                    FILTER (STR(?Z) > STR(?X))
                }} UNION {{
                    ?X ?a ?Y .
                    ?Y ?b ?Z .
                    ?X ?c ?Z
                }}
            }}
        }}
        }}
        {{
        SELECT (count(*) as ?triples) 
            WHERE{{ GRAPH <{graph}> {{
                ?s ?p ?o .
            }}
        }}
        }}
        }}
    '''
    
    return q_clust

def q_voc_uni(graph):

    q_voc_u = f''' 
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT ((xsd:float(?vocab)/xsd:float(?triples)) as ?unique)
        FROM NAMED <{graph}>
        WHERE {{

        #Enumerator
            {{
            SELECT (count(DISTINCT ?entity) as ?vocab)
            WHERE{{ GRAPH <{graph}> {{
                {{?entity ?p ?o}}
                UNION
                {{?s ?entity ?o}}
                UNION
                {{?s ?p ?entity}}
                    }}
                }}
            }}

        #Denominator
            {{
            SELECT (count(*) as ?triples)
            WHERE {{ GRAPH <{graph}> {{
                {{?s ?p ?o}}
                    }}
                }}
            }}
        }}
    '''
    
    return q_voc_u

def q_knowledge_degree(graph):
    
    q_know_deg = f''' 
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        select (xsd:float(?outdegreesum) / xsd:float(?V) as ?knowledgedegree)
        from named <{graph}>
        where {{ GRAPH <{graph}> {{
                {{
                select (sum(?outdegree) as ?outdegreesum) 
                where
                    {{
                        {{
                        select ?s (count(?s) as ?outdegree) 
                        where {{ 
                            ?s ?p ?o . 
                            }}
                        group by ?s
                        }}
                    }}
                }}
                {{
                select (count(distinct(?nodes)) as ?V) 
                where 
                    {{
                        {{
                        select (?s as ?nodes) 
                        where {{
                            ?s ?p ?o
                            }}
                        }} 
                    union 
                        {{
                        select (?o as ?nodes) 
                        where {{
                            ?s ?p ?o filter(!isLiteral(?o))
                            }}
                        }}
                    }}
                }}
            }}
        }}
    '''
    
    return q_know_deg

def q_growth(graph1, graph2):
    
    q_grow = f''' 
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT (xsd:float(?next)/xsd:float(?previous) as ?growthratio)
        FROM NAMED <{graph1}>
        FROM NAMED <{graph2}>
        WHERE {{ 

            #Begin subquery 1
                {{
                SELECT (count(*) as ?previous)
                WHERE {{GRAPH <{graph1}>
                        {{?s ?p ?o}}
                    }} # End Where 1
                }} #End first subquery

            #Begin subquery 2
                {{
                SELECT (count(*) as ?next)
                WHERE {{GRAPH <{graph2}>
                        {{?s ?p ?o}}
                    }} # End Where 2
                }} #End second subquery
            }} #End Full Query 
    '''
    
    return q_grow

def q_cluster2(graph):
    triangle = f'''
        SELECT (count(*) as ?triangles)
        from named <{graph}>
            WHERE{{ 
                {{select distinct(?X) ?Y ?Z 
                    where {{ graph <{graph}> {{
                        ?X ?a ?Y .
                        ?Y ?b ?Z .
                        ?Z ?c ?X .
                        filter(?X != ?Y && ?X != ?Z && ?Y != ?Z)
                        }}
                    }}
                }}
            }}
        '''
    
    triplet = f'''
        SELECT (count(*) as ?connectedTriplets)
        from named <{graph}>
            WHERE{{ 
                {{select distinct(?X) ?Y ?Z 
                    where {{ graph <{graph}> {{
                        ?X ?a ?Y .
                        ?Y ?b ?Z .
                        filter(!isLiteral(?Z))
                        filter(?X != ?Y && ?X != ?Z && ?Y != ?Z)
                    }}
                }}
            }}
        }}
        '''
    
    return triangle, triplet

def q_change_ratio(graph1, graph2):
    
    q_cr = f''' 
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ((xsd:float(?enumerator)/xsd:float(?denominator)) as ?changeratio)
FROM NAMED <{graph1}>
FROM NAMED <{graph2}>
WHERE{{

#Query 1 - Enumerator
 {{
  SELECT ((?additions + ?removals) as ?enumerator)
  WHERE{{

  #Query 1.1
   {{SELECT (count(*) as ?removals)
    WHERE{{
     {{SELECT *
      WHERE{{GRAPH <{graph1}>
       {{?s ?p ?o}}
      }}
     }}
     MINUS
     {{SELECT *
      WHERE{{GRAPH <{graph2}>
       {{?s ?p ?o}}
      }}
     }}
    }}
   }}

  #Query 1.2
   {{SELECT (count(*) as ?additions)
    WHERE{{
     {{SELECT *
      WHERE{{GRAPH <{graph2}>
       {{?s ?p ?o}}
      }}
     }}
     MINUS
     {{SELECT *
      WHERE{{GRAPH <{graph1}>
       {{?s ?p ?o}}
      }}
     }}
    }}
   }}
  }}
 }}

#Query 2 - Denominator
 {{
 SELECT (count( DISTINCT *) as ?denominator)
 WHERE {{
   #Query 2.1
   {{SELECT *
    WHERE {{GRAPH <{graph1}>
     {{?s ?p ?o}}
    }} 
   }} #End Query 2.1
   UNION
   #Query 2.2
   {{SELECT *
    WHERE {{GRAPH <{graph2}>
     {{?s ?p ?o}}
    }} #End Where 2.2
   }} #End Query 2.2
  }} #End Where Query 2
 }} #End Query 2
}} #End Full Query
    '''
    
    return q_cr

def q_add_change_ratio(graph1, graph2):
    
    q_ps_cr =  f''' 
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ((xsd:float(?additions)/xsd:float(?denominator)) as ?addratio)
FROM NAMED <{graph1}>
FROM NAMED <{graph2}>
WHERE{{

#Query 1 - Enumerator
{{SELECT (count(*) as ?additions)
 WHERE{{
    {{SELECT *
    WHERE{{GRAPH <{graph2}>
        {{?s ?p ?o}}
      }} # End WHERE 1.1.1
     }} #End 1.1.1
     MINUS
     {{SELECT *
      WHERE{{GRAPH <{graph1}>
       {{?s ?p ?o}}
      }} #End WHERE 1.1.2
     }} #End 1.1.2
    }} #End WHERE 1.1
   }} #End 1.1

#Query 2 - Denominator
 {{
  SELECT (count(*) as ?denominator)
  WHERE {{GRAPH <{graph1}>
  {{?s ?p ?o}}
    }} #End Where 2
 }} #End Query 2
}} #End Full Query
    
    '''
    
    return q_ps_cr

def q_rem_change_ratio(graph1, graph2):
    
    rem_cr = f''' 
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ((xsd:float(?removals)/xsd:float(?denominator)) as ?removeratio)
FROM NAMED <{graph1}>
FROM NAMED <{graph2}>
WHERE{{

#Query 1 - Enumerator
{{SELECT (count(*) as ?removals)
 WHERE{{
    {{SELECT *
    WHERE{{GRAPH <{graph1}>
        {{?s ?p ?o}}
      }} # End WHERE 1.1.1
     }} #End 1.1.1
     MINUS
     {{SELECT *
      WHERE{{GRAPH <{graph2}>
       {{?s ?p ?o}}
      }} #End WHERE 1.1.2
     }} #End 1.1.2
    }} #End WHERE 1.1
   }} #End 1.1

#Query 2 - Denominator
 {{
  SELECT (count(*) as ?denominator)
  WHERE {{GRAPH <{graph1}>
  {{?s ?p ?o}}
    }} #End Where 2
 }} #End Query 2
}} #End Full Query 
    '''
    
    return rem_cr

def query_set(graph, offset = 0):
    q_vocab = f'''
    SELECT (?entity as ?vocab_set)
      WHERE{{
      {{SELECT DISTINCT ?entity
        WHERE{{GRAPH <{graph}> {{
        {{?entity ?p ?o}}
        UNION
        {{?s ?entity ?o}}
        UNION
        {{?s ?p ?entity}}
            }}
          }} OFFSET {offset} LIMIT 1048576
        }}
       }}'''
    
    return q_vocab

def vocab_set(wrapper, graph):

    incr = 0
    voc_set = set()

    while incr % 1048576 == 0:
            q_vocab = query_set(graph, offset= incr)

            wrapper.setQuery(q_vocab)
            res = wrapper.query().convert()

            for ans in res['results']['bindings']:
                voc_set.add(ans['vocab_set']['value'])
                incr +=1

    return voc_set

def vocab_union(wrapper, graph1, graph2):

  q_denom = f'''
 SELECT (count( DISTINCT *) as ?denominator)
 WHERE {{
   #Query 2.1
   {{SELECT DISTINCT ?entity
      WHERE{{GRAPH <{graph1}> {{
       {{?entity ?p ?o}}
       UNION
       {{?s ?entity ?o}}
       UNION
       {{?s ?p ?entity}}
      }}
    }} 
   }} #End Query 2.1
   UNION
   #Query 2.2
   {{SELECT DISTINCT ?entity
      WHERE{{GRAPH <{graph2}> {{
       {{?entity ?p ?o}}
       UNION
       {{?s ?entity ?o}}
       UNION
       {{?s ?p ?entity}}
     }}
    }} #End Where 2.2
   }} #End Query 2.2
  }} #End Where Query 2
  '''
  denom = query_retriever(wrapper, q_denom, 'denominator')
  
  return denom  

def vocab_dyna(wrapper, graph1, graph2):
    print('Starting queries')

    old_set = vocab_set(wrapper, graph1)
    new_set = vocab_set(wrapper, graph2)

    old_vocab = len(old_set - new_set)
    new_vocab = len(new_set - old_set)

    enum = old_vocab + new_vocab
    print(f'Enumerator: {enum}')

    denom = vocab_union(wrapper, graph1, graph2)
    print(f'Denominator: {denom}')

    vdyn = enum/denom
    add_vdyn = new_vocab/denom
    rem_vdyn = old_vocab/denom

    print(f'Vdyn: {vdyn}')

    final = [vdyn, add_vdyn, rem_vdyn]

    return final

def q_icr(graph, ont):
    
    q_icr = f'''
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT (xsd:float(?enum)/xsd:float(?denom) as ?icr)
FROM NAMED <{graph}>
FROM NAMED <{ont}>
WHERE {{
 {{
  SELECT (COUNT(DISTINCT ?class) as ?enum)
  WHERE {{GRAPH <{graph}> {{
    ?s rdf:type ?class .
    FILTER(isUri(?class) && STRSTARTS(STR(?class), STR(dbo:)))
   }}
  }}
 }} # End subq1
 
 {{
  SELECT (count(DISTINCT ?s) as ?denom)
  WHERE{{ GRAPH <{ont}> {{?s ?p ?o
    
     {{?s rdf:type owl:Class}} 
     UNION
     {{?s rdf:type rdfs:Class}} 
    }}    
   }} 
  }} #End sub2
}}
'''
    return q_icr

def q_icr_check(graph, ont, request):

    if request == 'g':
        q_icr = f'''
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>


        SELECT DISTINCT (?class as ?graph_classes)
        FROM NAMED <{graph}>
            WHERE {{GRAPH <{graph}> {{
                ?s rdf:type ?class .
                }}
            }}
        '''
        return q_icr
    
    if request == 'o':
        q_icr = f'''
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT DISTINCT (?s as ?owl_classes)
            FROM NAMED <{ont}>
                WHERE{{ GRAPH <{ont}> {{?s ?p ?o
                    {{?s rdf:type owl:Class}} 
                    UNION
                    {{?s rdf:type rdfs:Class}} 
                    }}    
                }}
        '''
        return q_icr

def icr_set(wrapper, graph, ont):

    if ont == None:
        return None, None, None, None

    graph_set = set()
    owl_set = set()

    q_icr = q_icr_check(graph, ont, request= 'g')

    wrapper.setQuery(q_icr)
    res = wrapper.query().convert()

    for ans in res['results']['bindings']:
        graph_set.add(ans['graph_classes']['value'])
    
    q_icr = q_icr_check(graph, ont, request= 'o')

    wrapper.setQuery(q_icr)
    res = wrapper.query().convert()
    
    for ans in res['results']['bindings']:
        owl_set.add(ans['owl_classes']['value'])

    return (graph_set - owl_set), (owl_set - graph_set), len(graph_set), len(owl_set)

def q_ipr(graph, ont):

    q_ipr = f'''
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX dbo: <http://dbpedia.org/ontology/>

        SELECT (xsd:float(?enum)/xsd:float(?denom) as ?ipr)
        FROM NAMED <{graph}>
        FROM NAMED <{ont}>
        WHERE {{
            {{
            SELECT (COUNT(DISTINCT ?property) AS ?enum)
            WHERE {{ GRAPH <{graph}> {{
                ?subject ?property ?object .
                FILTER(isUri(?property) && STRSTARTS(STR(?property), STR(dbo:)))
                }}
            }}
            }} # End subq1
            {{
            SELECT (count(*) as ?denom)
            WHERE {{ GRAPH <{ont}> {{
                {{
                ?property rdf:type owl:ObjectProperty .
                }} UNION {{
                ?property rdf:type owl:DatatypeProperty .
                }} UNION {{
                ?property rdf:type owl:FunctionalProperty .
                }} 
                }}
            }}  
            }} #End sub2
        }}
        '''
    return q_ipr

def q_ipr_check(graph, ont, request):

    if request == 'g':
        q_ipr = f'''
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT DISTINCT(?property AS ?graph_properties)
            FROM NAMED <{graph}>
            WHERE {{ GRAPH <{graph}> {{
                ?subject ?property ?object .
                }}
            }}
            '''
    if request == 'o':
        q_ipr = f'''
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            
            SELECT distinct(?property as ?owl_properties)
            FROM NAMED <{ont}>
            WHERE {{ GRAPH <{ont}> {{
                {{
                ?property rdf:type owl:ObjectProperty .
                }} UNION {{
                ?property rdf:type owl:DatatypeProperty .
                }} UNION {{
                ?property rdf:type owl:FunctionalProperty .
                }} 
                }}
            }}  
            '''
    return q_ipr

def ipr_set(wrapper, graph, ont):

    if ont == None:
        return None, None, None, None

    graph_set = set()
    owl_set = set()

    q_ipr = q_ipr_check(graph, ont, request= 'g')

    wrapper.setQuery(q_ipr)
    res = wrapper.query().convert()

    for ans in res['results']['bindings']:
        graph_set.add(ans['graph_properties']['value'])
    
    q_ipr = q_ipr_check(graph, ont, request= 'o')

    wrapper.setQuery(q_ipr)
    res = wrapper.query().convert()
    
    for ans in res['results']['bindings']:
        owl_set.add(ans['owl_properties']['value'])

    return (graph_set - owl_set), (owl_set - graph_set), len(graph_set), len(owl_set)

def q_imi(ont):
    
    q_imi =  f'''
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>


    SELECT (xsd:float(?superSum)/xsd:float(?classCount) as ?imi)
    FROM NAMED <{ont}>
    WHERE {{
    #Query 1
    {{
    SELECT (count(*) as ?superSum)
    WHERE{{GRAPH <{ont}>
    {{?s rdfs:subClassOf ?o }}
    }}
    }}

    #Query 2
    {{
    SELECT (count( DISTINCT ?s) as ?classCount)
    WHERE{{ GRAPH <{ont}> {{?s ?p ?o
        
        {{?s rdf:type owl:Class}} 
    UNION
    {{?s rdf:type rdfs:Class}} 
    }}    
    }} 
    }}

    }} #End Full Query
    '''
    return q_imi

def structure_and_content(wrapper, graph_list):
    
    struct_cont_dict = {'File': [],
                        'Version': [],
                        'Density': [],
                        'CC': [],
                        'KD': [],
                        'VocUni': [],
                        'Vdyn': [],
                        'AddVdyn': [],
                        'RemVdyn': [],
                        'ChangeRatio': [],
                        'AddCR': [],
                        'RemCR': [],
                        'Growth': []
                        }
    
    for list in graph_list:
        v_num = 0
        
        #Go through all the graphs
        #REQUIRES AN ORDERED LIST!
        for i in range(len(list)):
            
            #Get information for each single graph
            density = query_retriever(wrapper, q_density(list[i]), 'density')
            
            #clustering = query_retriever(wrapper, q_cluster(list[i]), 'clustering_coefficient')
            clustering = 0
            
            knowledge_degree = query_retriever(wrapper, q_knowledge_degree(list[i]), 'knowledgedegree')
            
            vocabulary_uniqueness = query_retriever(wrapper, q_voc_uni(list[i]), 'unique')

            #Do comparions of the graphs
            if v_num == 0:
                vocabulary_dynamicity = 0
                add_voc = 0
                rem_voc = 0
                change_ratio = 0
                add_cr = 0
                rem_cr = 0
                growth = 0 
            else:
                print(f'Doing comparisons of {list[i-1]} and  {list[i]}')
                voc_res = vocab_dyna(wrapper, list[i-1], list[i])
                vocabulary_dynamicity = voc_res[0] 
                add_voc = voc_res[1]
                rem_voc = voc_res[2]
                change_ratio = query_retriever(wrapper, q_change_ratio(list[i-1], list[i]), 'changeratio')
                add_cr = query_retriever(wrapper, q_add_change_ratio(list[i-1], list[i]), 'addratio')
                rem_cr = query_retriever(wrapper, q_rem_change_ratio(list[i-1], list[i]), 'removeratio')
                growth = query_retriever(wrapper, q_growth(list[i-1], list[i]), 'growthratio')
            
            #Insert information into the  dictionary
            struct_cont_dict['File'].append(list[i])
            struct_cont_dict['Version'].append(v_num)
            struct_cont_dict['Density'].append(density)
            struct_cont_dict['CC'].append(clustering)
            struct_cont_dict['KD'].append(knowledge_degree)
            struct_cont_dict['VocUni'].append(vocabulary_uniqueness)
            struct_cont_dict['Vdyn'].append(vocabulary_dynamicity) 
            struct_cont_dict['AddVdyn'].append(add_voc) 
            struct_cont_dict['RemVdyn'].append(rem_voc) 
            struct_cont_dict['ChangeRatio'].append(change_ratio) 
            struct_cont_dict['AddCR'].append(add_cr) 
            struct_cont_dict['RemCR'].append(rem_cr) 
            struct_cont_dict['Growth'].append(growth)            
        
            v_num += 1
            
            print(struct_cont_dict)
    
            #Consider not writing every time
            with open('structure_and_content.csv', 'w') as sc:
                writer = csv.writer(sc) #requires import csv
                writer.writerow(struct_cont_dict.keys())
                writer.writerows(zip(*struct_cont_dict.values()))
        
    return struct_cont_dict

def quality(wrapper, graph_list, ont_list):
    
    qual_dict = {'File': [],
                'Version': [],
                'ICR': [],
                'IPR': [],
                'IMI': []}
    
    v_num = 0
    
    for i in range(len(graph_list)):
        if ont_list[i] == None:
            pass
        else: 
        icr = query_retriever(wrapper, q_icr(graph_list[i], ont_list[i]), 'icr')
        ipr = query_retriever(wrapper, q_ipr(graph_list[i], ont_list[i]), 'ipr')
        imi = 1/query_retriever(wrapper, q_imi(ont_list[i]), 'imi')
        
        #Insert information into the  dictionary
        qual_dict['File'].append(graph_list[i])
        qual_dict['Version'].append(v_num)
        qual_dict['ICR'].append(icr)
        qual_dict['IPR'].append(ipr)
        qual_dict['IMI'].append(imi)
        
        v_num +=1
        
        print(qual_dict)
        
    with open('quality.csv', 'w') as q:
        writer = csv.writer(q) #requires import csv
        writer.writerow(qual_dict.keys())
        writer.writerows(zip(*qual_dict.values()))  
        
    return qual_dict      

def ipcr_csv(wrapper, graph_list, version_list, ont_list, name):
    print(name)
    if name != 'ipr' and name != 'icr':
        print('name can only be icr or ipr')
        return

    set_dict = {'Graph': [],
                'Version': [],
                'Graph - Ont check': [],
                'len(Graph - Ont check)': [],
                'Ont - Graph check': [],
                'len(Ont - Graph check)': [],
                'Graph set lenght': [],
                'Ont set lenght': []
                }
    
    for i in range(len(graph_list)):
        if name == 'ipr':
            graph_ont_diff, ont_graph_diff, graph_len, ont_len = ipr_set(wrapper, graph_list[i], ont_list[i])
        if name == 'icr':
            graph_ont_diff, ont_graph_diff, graph_len, ont_len = icr_set(wrapper, graph_list[i], ont_list[i])

        set_dict['Graph'].append(graph_list[i])
        set_dict['Version'].append(version_list[i])
        set_dict['Graph - Ont check'].append(graph_ont_diff)
        set_dict['len(Graph - Ont check)'].append(len(graph_ont_diff))
        set_dict['Ont - Graph check'].append(ont_graph_diff)
        set_dict['len(Ont - Graph check)'].append(len(ont_graph_diff))
        set_dict['Graph set lenght'].append(graph_len)
        set_dict['Ont set lenght'].append(ont_len)
    
    df = pd.DataFrame(set_dict)
    df.to_csv(f'{name}.csv', index= False, header= True, sep = ';')

def top_entities(entity, wrapper, graph_list, file_name):

    common_dict = {'File':[], 
                    'Version':[],
                    'Rank':[],
                    'Name':[],
                    'Count':[]
                    } 

    for names in graph_list:
        v_num = 0


        for graph in names:

            top = 1

            query = f'''select ?{entity} (count(?{entity}) as ?count)
                        from named <{graph}>
                        where {{ GRAPH <{graph}>
                        {{?s ?p ?o}}
                        }}
                        ORDER BY desc (?count) limit 10
                        '''
            
            wrapper.setQuery(query)
            res = wrapper.query().convert()

            for l in res['results']['bindings']:
                common_dict['File'].append(graph)
                common_dict['Version'].append(v_num)
                common_dict['Rank'].append(top)
                top +=1
                common_dict['Name'].append(l[entity]['value'])
                common_dict['Count'].append(l['count']['value'])
            

            v_num += 1

            #Consider not writing every time
            with open(file_name, 'w') as sc:
                writer = csv.writer(sc) #requires import csv
                writer.writerow(common_dict.keys())
                writer.writerows(zip(*common_dict.values()))
    
    return common_dict


if __name__ == '__main__':
    endpoint = 'http://localhost:8890/sparql'

    # Configure the SPARQL endpoint
    sparql = SPARQLWrapper(endpoint)

    # Configure the SPARQL endpoint and desired return format
    sparql.setReturnFormat(JSON)
    
    def query_tester(graph_1 = 'http://localhost:8890/35', graph_2 = 'http://localhost:8890/dims', ont = 'http://localhost:8890/pediaowl'):
        print('q_density')
        sparql.setQuery(q_density(graph= graph_2))
        print(sparql.query().convert()["results"]["bindings"])
        print('q_cluster')
        sparql.setQuery(q_cluster(graph= graph_2))
        print(sparql.query().convert()["results"]["bindings"])
        print('q_voc_uni')
        sparql.setQuery(q_voc_uni(graph= graph_1))
        print(sparql.query().convert()["results"]["bindings"])
        print('q_knowledge_degree')
        sparql.setQuery(q_knowledge_degree(graph= graph_1))
        print(sparql.query().convert()["results"]["bindings"])
        print('q_growth')
        sparql.setQuery(q_growth(graph1= graph_1, graph2= graph_2))
        print(sparql.query().convert()["results"]["bindings"])
        print('q_change_ratio')
        sparql.setQuery(q_change_ratio(graph1= graph_1, graph2= graph_2))
        print(sparql.query().convert()["results"]["bindings"])
        print('q_add_change_ratio')
        sparql.setQuery(q_add_change_ratio(graph1= graph_1, graph2= graph_2))
        print(sparql.query().convert()["results"]["bindings"])
        print('q_rem_change_ratio')
        sparql.setQuery(q_rem_change_ratio(graph1= graph_1, graph2= graph_2))
        print(sparql.query().convert()["results"]["bindings"])
        print('query_set')
        sparql.setQuery(query_set(graph= graph_1))
        print(sparql.query().convert()["results"]["bindings"])
        
        print('vocab_set')
        print(vocab_set(wrapper= sparql, graph= graph_1))
        print('vocab_union')
        print(vocab_union(wrapper= sparql, graph1= graph_1, graph2= graph_2))
        print('vocab_dyna')
        print(vocab_dyna(wrapper= sparql, graph1= graph_1, graph2= graph_2))
        
        print('q_icr')
        sparql.setQuery(q_icr(graph= graph_1, ont= ont))
        print(sparql.query().convert()["results"]["bindings"])
        print('q_ipr')
        sparql.setQuery(q_ipr(graph= graph_1, ont= ont))
        print(sparql.query().convert()["results"]["bindings"])
        print('q_imi')
        sparql.setQuery(q_imi(ont= ont))
        print(sparql.query().convert()["results"]["bindings"])
    
    #query_tester()
    sparql.setQuery(q_icr(graph= 'http://localhost:8890/35', ont= 'http://localhost:8890/pediaowl'))
    print(sparql.query().convert()["results"]["bindings"])
    #print(icr_set(wrapper= sparql, graph= 'http://localhost:8890/35', ont= 'http://localhost:8890/pediaowl'))
    if False:
        triangle, triplet = q_cluster2(graph= 'http://localhost:8890/dims2')
        sparql.setQuery(triangle)
        cc_triangle = sparql.query().convert()["results"]["bindings"][0]['triangles']['value']
        sparql.setQuery(triplet)
        cc_triplet = sparql.query().convert()["results"]["bindings"][0]['connectedTriplets']['value']
        print(int(cc_triangle)/int(cc_triplet), cc_triangle, cc_triplet)
