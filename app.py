# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px

import pandas as pd
import numpy as np


#%% Functions
def get_random(var,n=10000):
    return np.random.uniform(*var+[n])

def update_df(surface_area = 900,
              height = 10,
              num_faculty = 1,
              num_students = 10,
              duration = 75,
              num_class_periods = 26,
              num_classes_taken = 4,
              breathing_rate_faculty = [1,1.2],
              breathing_rate_student = [0.7,0.9],
              ventilation_w_outside_air = [2,4],
              decay_rate_of_virus = [0,0.63],
              deposition_to_surface = [0.3,1.5],
              additional_control_measures = [0,0],
              quanta_emission_rate_faculty = [100,300],
              quanta_emission_rate_student = [10,30],
              exhalation_mask_efficiency = [0.5,0.7],
              inhalation_mask_efficiency = [0.3,0.5],
              background_infection_rate = [0.0019,0.0038]):
    #Create dataframe of 10,000 runs
    num_runs = 10000
    df = pd.DataFrame(index=np.arange(num_runs))
    df['VENT']  = get_random(ventilation_w_outside_air,num_runs)
    df['DECAY'] = get_random(decay_rate_of_virus,num_runs)
    df['DEP']   = get_random(deposition_to_surface,num_runs)
    df['OTHER'] = get_random(additional_control_measures,num_runs)
    df['L']     = df['VENT'] + df['DECAY'] + df['DEP']
    df['L*DUR'] = df['L'] * duration / 60
    df['VOL']   = surface_area * height*0.305**3
    df['EFFOUT'] = get_random(exhalation_mask_efficiency,num_runs)
    df['EMMF']  = get_random(quanta_emission_rate_faculty,num_runs)
    df['EMMS']  = get_random(quanta_emission_rate_student,num_runs)
    df['INFRATE'] = get_random(background_infection_rate,num_runs)
    df['CONCF'] = (df['EMMF']*
                   (1-df['EFFOUT'])/
                   (df['L']*df['VOL'])*
                   (1-1/df['L*DUR']*(1-np.exp(-df['L*DUR'])))*
                   df['INFRATE'])*num_faculty
    df['CONCS'] = (df['EMMS']*
                   (1-df['EFFOUT'])/
                   (df['L']*df['VOL'])*
                   (1-1/df['L*DUR']*(1-np.exp(-df['L*DUR'])))*
                   df['INFRATE'])*num_students
    df['EFFIN'] = get_random(inhalation_mask_efficiency,num_runs)
    df['BRF']   = get_random(breathing_rate_faculty,num_runs)
    df['BRS']   = get_random(breathing_rate_student,num_runs)
    df['INS_F'] = df['CONCF'] * df['BRS'] * duration/60 * (1-df['EFFIN'])
    df['INF_S'] = df['CONCS'] * df['BRF'] * duration/60 * (1-df['EFFIN'])
    df['INS_S'] = df['CONCS'] * df['BRS'] * duration/60 * (1-df['EFFIN']) * (num_students-1)/num_students
    df['PS_F']  = 1 - np.exp(-df['INS_F']) #<--Per class infection rate for faculty
    df['PF_S']  = 1 - np.exp(-df['INF_S'])
    df['PS_S']  = 1 - np.exp(-df['INS_S'])
    #FACULTY INFECTION PROBABILITIES
    df['nPS_F'] = 1 - df['PF_S']           #<--Faculty not infected probability per class
    df['nPS_Fsemester'] = df['nPS_F']**num_class_periods
    df['PS_Fsemester']  = 1 - df['nPS_Fsemester'] #<--Faculty infection probability per semester
    #STUDENT INFECTION PROBABILITIES
    df['PS_FS'] = df['PS_F']+df['PS_S']    #<--Per class infection rate for student
    df['nPS_FS'] = 1 - df['PS_FS']         #<--Per class non-infection rate for student  
    df['nPS'] = df['nPS_FS']**(num_classes_taken*num_class_periods)
    df['PS_Ssemester'] = 1 - df['nPS']
    return(df)

def update_figure(df):
    #Update the dataframe
    fig = px.histogram(df,x='PS_Fsemester',nbins=40,
                       title='Distribution of Faculty Probabilities (Semester)')
    fig.update_xaxes(title_text = 'Probability of infection (%)')
    fig.update_layout(xaxis_tickformat = ".2%")
    #fig = px.scatter(df,x='L',y='L*DUR')
    fig.update_layout(transition_duration=500)
    return(fig)

def summarize_output(df):
    #Create markdown from values
    fac_mean = df['PS_Fsemester'].mean()
    fac_quants = [df['PS_Fsemester'].quantile(x) for x in (0.05,0.25,0.5,0.75,0.9)]
    stu_mean = df['PS_Ssemester'].mean()
    stu_quants = [df['PS_Ssemester'].quantile(x) for x in (0.05,0.25,0.5,0.75,0.9)]
    #Create Markdown
    md_text=f'''
### Output: Probabilies for semester accounting for community infection rates   
| Average Infection Probability for Faculty Member for semester | {fac_mean:0.2%} |
| --- | --- |
| 5th percentile: | {fac_quants[0]:0.2%} |
| 25th percentile: | {fac_quants[1]:0.2%} |
| 50th percentile: | {fac_quants[2]:0.2%} |
| 75th percentile: | {fac_quants[3]:0.2%} |
| 95th percentile: | {fac_quants[4]:0.2%} |
| --- | --- |
| **Average Infection Probability for Student for semester**       | **{stu_mean:0.2%}** |
| 5th percentile: | {stu_quants[0]:0.2%} |
| 25th percentile: | {stu_quants[1]:0.2%} |
| 50th percentile: | {stu_quants[2]:0.2%} |
| 75th percentile: | {stu_quants[3]:0.2%} |
| 95th percentile: | {stu_quants[4]:0.2%} |
'''
    return md_text

#%%Read in the static data
df = update_df()
fig = update_figure(df)
md_results = summarize_output(df)
#df = pd.read_csv('static.csv')

#%% Page construction
#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__)#, external_stylesheets=external_stylesheets)
server = app.server 

#Construct the web site
app.layout = html.Div([
    html.Table([
        html.Tr([
            html.Th("Variable"), html.Th("Value")]),
        html.Tr([
            html.Td("Surface area"), 
            html.Td(dcc.Input(id='surface',value=900,type='number'))]),
        html.Tr([
            html.Td("Height"), 
            html.Td(dcc.Input(id='height',value=10,type='number'))]),
        html.Tr([
            html.Td("# of students"), 
            html.Td(dcc.Input(id='num_students',value=10,type='number'))]),
        html.Tr([
            html.Td("Class duration"), 
            html.Td(dcc.Input(id='class_duration',value=75,type='number'))]),
        html.Tr([
            html.Td("# of class periods"), 
            html.Td(dcc.Input(id='class_periods',value=26,type='number'))]),
        html.Tr([
            html.Td("# of classes taken/student"), 
            html.Td(dcc.Input(id='classes_taken',value=4,type='number'))])
            ]),
              
    html.Button(id='submit-button-state',n_clicks=0,children='Submit'),
    html.Div([
        dcc.Markdown(id='faculty_results')]),
    dcc.Graph(id='faculty_histogram')
])

@app.callback([Output('faculty_results','children'),
               Output('faculty_histogram','figure')],
              [Input('submit-button-state','n_clicks')],
              [State('surface','value'),
               State('height','value'),
               State('num_students','value'),
               State('class_duration','value'),
               State('class_periods','value'),
               State('classes_taken','value')]
)
def update_page(input_value,sa,ht,nstudents,cduration,cperiods,ctaken):
    #Recompute the monte carlo run
    df = update_df(surface_area=sa,
                   height=ht,
                   num_students=nstudents,
                   duration=cduration,
                   num_class_periods=cperiods,
                   num_classes_taken=ctaken
                   )
    #Get Values
    md_results = summarize_output(df)
    #Create histogram
    fig = update_figure(df)
    #return f'Pexp Faculty (Semester): {mean_val:0.2%}',fig
    return md_results,fig
    



if __name__ == '__main__':
    app.run_server(debug=True)
