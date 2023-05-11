import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

#-------------------------------------------------------------------------------------------------------

#! First all the plots for the structure and content analysis can be made with the following function


def get_data(file_path):
    data = pd.read_csv(file_path)
    
    dbpedia_data = data[data['File'].str.contains('dbpedia')].drop(columns= ['Unnamed: 0'])
    wiki_data = data[data['File'].str.contains('wiki')].drop(columns= ['Unnamed: 0'])
    
    return [dbpedia_data, wiki_data]
    

legend_mapping = {
                    'KD': 'Knowledge Degree', 'VocUni': 'Vocabulary Uniqueness', 
                    'Vdyn': 'Vocabulary Dynamicity', 'AddVdyn': 'Addition Vdyn', 
                    'RemVdyn': 'Removal Vdyn', 'ChangeRatio': 'Change Ratio', 
                    'AddCR': 'Addition Change Ratio', 
                    'RemCR': 'Removal Change Ratio', 'Growth': 'Growth',
                    'Density': 'Density'
                }

def plot_parameters_over_versions(df, parameters, markers, title, output_file_name, 
                                    legend_mapping= legend_mapping, 
                                    y_label='Ratio', save_image= False,
                                    show_plot= False):

    for parameter, marker in zip(parameters, markers):
        legend_name = legend_mapping[parameter] if legend_mapping is not None else parameter
        plt.plot(df['Version'], df[parameter], marker=marker, linestyle='-', label=legend_name)

    plt.xlabel('Version')
    plt.ylabel(y_label)
    plt.title(title)
    plt.legend()
    plt.grid(axis='both', color='0.85')
    plt.xticks(np.arange(0, len(df[parameter])+1, 1))
    if save_image: plt.savefig(output_file_name, dpi=300, bbox_inches='tight')
    if show_plot: plt.show()

    
#-------------------------------------------------------------------------------------------------------

#! The quality plots can be constructed with the following functions

#First we have the plots for the quality measures (ICR, IPR and IMI)

def quality_plots(file_path):
    
    df = pd.read_csv(file_path)
    
    #Plot 1
    plt.plot('ICR', data = df, marker = '*')
    plt.plot('IPR', data = df, marker = 'd')
    
    plt.xlabel("Version")
    plt.ylabel("Ratio")
    
    plt.legend(loc = 'upper right')
    plt.title('Instantiated Class and Property Ratio for DBpedia')
    
    plt.grid(axis='both', color='0.85')
    plt.xticks(np.arange(0, len(df['ICR'])+1, 1))
    
    plt.show()
    
    #Plot 2
    
    plt.plot('IMI', data = df, color = 'red', marker = 'X')
    plt.xlabel("Version")
    plt.ylabel("Ratio")
    plt.title('Inverse Multiple Inhertiance for DBpedia')
    plt.grid(axis='both', color='0.85')
    plt.xticks(np.arange(0, len(df['IMI'])+1, 1))
    

#Then we want to plot the growth of the ontology and the ratio of external ontologies used
#Therefore, we need to take in the data and clean it first

def ont_prepare(path):
    
    df = pd.read_csv(path, delimiter=';')

    df['external'] = df['len(Graph - Ont check)']/df['Graph set lenght']
    df = df.drop(['Graph - Ont check', 'Ont - Graph check', 'len(Ont - Graph check)'], axis = 1)
    df = df.rename(columns = {'len(Graph - Ont check)' : 'ex_set', 'Graph set lenght' : 'graph_set', 'Ont set lenght' : 'ont_set' })
    df['inst_ont'] = df['graph_set']-df['ex_set']
    df['ont_diff'] = df['ont_set']-df['inst_ont']

    df = df.sort_values(by = 'Version')
    
    return df

#Then, we can plot the growth of the classes or the properties with the following function

def ont_growth(file_path, title_name): 
    
    df = ont_prepare(file_path)
    
    x1 = np.array(df['Version'])
    y1 = np.array(df['ont_set'])
    y3 = np.array(df['ont_diff'])
    y4 = np.array(df['inst_ont'])

    plt.plot(x1,y1, marker = "X")
    plt.plot(x1,y4, marker = "d")
    plt.bar(x1,y3, fill = False)

    plt.xlabel("Version")
    plt.ylabel("# of classes")

    labels = ['Ontology', f'Instantiated from ontology', 'Difference']

    plt.legend(loc = 'upper left', labels = labels)
    plt.title(f'Ontology and graph {title_name} growth for DBpedia')

    plt.grid(axis='both', color='0.85')

    plt.xticks(np.arange(0, len(df['external'])+1, 1))
    plt.show()
    

#To get the external use ratio, we can use the next function

def external_ratio(class_path, property_path): 
    
    df_icr = ont_prepare(class_path)
    df_ipr = ont_prepare(property_path)
    
    x1 = np.array(df_icr['Version'])
    y1 = np.array(df_icr['external'])
    x2 = np.array(df_ipr['Version'])
    y2 = np.array(df_ipr['external'])

    plt.plot(x1,y1, marker = "X")
    plt.plot(x2,y2, marker = "d")

    plt.xlabel("Version")
    plt.ylabel("Ratio")

    labels = ['External Class Ratio', 'External Property Ratio']

    plt.legend(loc = 'upper left', labels = labels)
    plt.title('External Class and Property Ratio for DBpedia')

    plt.grid(axis='both', color='0.85')

    plt.xticks(np.arange(0, len(df_icr['external'])+1, 1))
    plt.show()

#Gathering all of that into one single function is done here:

def ontology_plots(class_path, property_path): 
    
    ont_growth(class_path, 'class')
    ont_growth(property_path, 'property')
    
    external_ratio(class_path, property_path)
    
# -----------------------------------------------------------------------
#! This section is for the entity analysis

def top_trends(file_path, file_path2, company, type, loc= 'upper left', defined= False):
    df = pd.read_csv(file_path)
    basics = pd.read_csv(file_path2)
    
    if defined:
        if company.lower() == 'dbpedia':
            df = df[df['File'].str.contains('dbpedia')]
            basics = basics[basics['File'].str.contains('dbpedia')]
        elif company.lower() == 'wikidata':
            df = df[df['File'].str.contains('wiki')]
            basics = basics[basics['File'].str.contains('wiki')]
        else:
            print('Incorrect company input')
    
    triples = list(basics.Triples)
    
    df['ratio'] = df.apply(lambda row: row.Count / triples[row.Version], axis= 1)
    
    x = np.array(df['Version'].unique())
    
    
    y1 = np.array(df.loc[df['Rank'] == 1, 'ratio'])
    y2 = np.array(df.loc[df['Rank'] == 2, 'ratio'])
    y3 = np.array(df.loc[df['Rank'] == 3, 'ratio'])
    
    try:
        plt.plot(x, y1, marker = ".")
        plt.plot(x, y2, marker = "P")
        plt.plot(x, y3, marker = "d")
    except ValueError:
        print(f'Please make sure that there are atleast 3 unique {type}')
    
    plt.xlabel("Version")
    plt.ylabel("Ratio of appearances")

    labels = ['Most common', '2. most common', '3. most common']

    plt.legend(loc=  loc, labels = labels)
    plt.title(f'Trend in most common {type} for {company}')

    plt.grid(axis='both', color='0.85')

    plt.xticks(np.arange(0, len(df['Version'].unique())+1, 1))
    