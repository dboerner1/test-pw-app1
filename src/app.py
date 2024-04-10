# Import packages
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

crs = [
'#48AFF4','#5DDA93',
'#B582D9','#F9B26C',
'#6797E0','#E76A87',
'#1CCEC5','#F4D35D',
'#F391D4','#9CA4B4',
'#9AD3F9','#8BDFB0',
'#FACA9B','#CCA6D9',
'#9FB5D6','#F598AE',
'#8DE2DE','#F9E494',
'#F4C2E4','#BFC4CF']

# sample company: Asana (381043)
company = 'Asana'
transitions = pd.read_csv(Path(__file__).parent.parent/'data'/'pw_sample_transitions.csv')
transitions = transitions[transitions['COMPANY']=='Asana, Inc.']

positions = pd.read_csv(Path(__file__).parent.parent/'data'/'pw_sample_positions.csv')
positions = positions[positions['ultimate_parent_rcid']==381043]
education = pd.read_csv(Path(__file__).parent.parent/'data'/'pw_sample_education.csv')
prestige_ref = pd.read_csv(Path(__file__).parent.parent/'data'/'pw_prestige_percentiles.csv')
# limiting options to roles the company has at least 20 employees in
selections = list((transitions.groupby('CATEGORY')['N'].sum()[transitions.groupby('CATEGORY')['N'].sum()>=20]).index)

# Format title
def format_title(title, subtitle=None,font_size=25, subtitle_font_size=15):
    title =  f'<span style="font-size: {font_size}px;margin-bottom:50px;font-family:Roboto Medium;color:#2D426A">{title}</span>'
    if not subtitle:
        return title
    subtitle = f'<span style="font-size: {subtitle_font_size}px;font-family:Roboto;color:#899499">{subtitle}</span>'
    return f'{title}<br><br>{subtitle}'

# Initialize the app
app = Dash(__name__)
server = app.server

# App layout
app.layout = html.Div([
    html.Div([
        dcc.Dropdown(options=['All']+selections, value=list(selections[:1]), clearable=True, id='role-dropdown', multi=True, placeholder='All'),
        dcc.Graph(id='spectrum')],
        style={'width': '100%', 'display': 'inline-block'}),
    html.Div([
        dcc.Graph(id='company-inflows-bar')],
        style={'width': '49%', 'display': 'inline-block'}),
    html.Div([
        dcc.Graph(id='school-inflows-bar')],
        style={'width': '49%', 'float': 'right', 'display': 'inline-block'})
    ])

# Add controls to build the interaction
@callback(
    Output(component_id='spectrum', component_property='figure'),
    Output(component_id='company-inflows-bar', component_property='figure'),
    Output(component_id='school-inflows-bar', component_property='figure'),
    Input(component_id='role-dropdown', component_property='value')
)
def update_graph(roles_chosen):
    all_roles = False
    if 'All' in roles_chosen or len(roles_chosen)==0:
        all_roles = True
        spectrum_data = positions
    else:
        spectrum_data = positions[positions['role_k150'].isin(roles_chosen)]

    raw_prestige = np.sum(spectrum_data['weight_v2']*spectrum_data['prestige_v2'])/np.sum(spectrum_data['weight_v2'])

    tmp = prestige_ref.copy()
    tmp['tmp_col'] = np.abs(tmp['PRESTIGE']-raw_prestige)
    percentile = int(round(tmp[tmp['tmp_col']==(tmp['tmp_col'].min())]['PERCENTILE'].values[0]*100,0))

    formatted_percentile = '{:.0f}%'.format(percentile)
    spectrum = go.Figure(go.Heatmap(
        z=[list(range(101))],
        x=list(range(101)),
        y=[''],
        colorscale='Spectral',
        opacity=0.8,
        showscale=False,
        hoverinfo='skip'
    ))

    spectrum.add_shape(type="line",
                       x0=percentile, y0=-0.7,
                       x1=percentile, y1=0.7,
                       line=dict(color="Gray", width=5)
                       )
    
    spectrum.add_annotation(x=percentile, y=0.8,
                    text=f" {formatted_percentile}",
                    #    hovertext=f"Salary growth score is <b>{formatted_percentile}</b>" ,
                    font_size=16,
                    showarrow=False,
                    yshift=10)
    spectrum.update_yaxes(showticklabels=False)

    # Layout
    spectrum.update_layout(
        xaxis=dict(
            visible=False,
            title=""),
        yaxis=dict(title=None),
        
        title=dict(
            text=format_title(
                f'Average prestige: '+('Overall' if all_roles else 'selected roles')),
            yanchor="top",
            y=0.72,
            xanchor="left",
            x=0.02,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel = dict(
            bgcolor="white",
            bordercolor = "#2D426A",
            font = dict(size=12, family='Roboto Mono', color="#2D426A")
        )
    )
    if all_roles:
        transitions_data = transitions.groupby('SOURCE_COMPANY')['N'].sum().sort_values(ascending=False)[:5].sort_values(ascending=True).reset_index()
    else:
        transitions_data = (transitions[transitions['CATEGORY'].isin(roles_chosen)].groupby('SOURCE_COMPANY')['N'].
                            sum().sort_values(ascending=False)[:5].sort_values(ascending=True).reset_index())

    companies = go.Figure()
    trace = go.Bar(y = transitions_data['SOURCE_COMPANY']+' ',
                   x = transitions_data['N'],
                   marker_color = [crs[9]]*(len(transitions_data)-1)+[crs[0]],
                   orientation='h')
    companies.add_trace(trace)
    companies.update_layout(
        barmode='group',
        yaxis=dict(zeroline=False, showgrid=False,
                   gridcolor='#EAECF0', gridwidth=1,
                   tickfont=dict(family="Roboto", size=16, color="#2D426A")),
        xaxis=dict(zeroline=True, zerolinecolor='#EAECF0', zerolinewidth=1,
                   showgrid = False, gridcolor='#EAECF0', gridwidth=1, tickformat='.f', showticklabels = False, 
                   tickfont=dict(family="Roboto", size=16, color="#2D426A")),
        showlegend=False,
        title = dict(text = format_title('Top source companies'), yanchor='top', y=0.92, xanchor='left', x=0.02),
        plot_bgcolor = 'rgba(0,0,0,0)',
        hoverlabel=dict(
            bgcolor='white',
            bordercolor = "#2D426A",
            font = dict(size=12, family="Roboto Mono", color='#2D426A'))
    )

    if all_roles:
        alumni = positions['user_id'].unique()
    else:
        alumni = positions[positions['role_k150'].isin(roles_chosen)]['user_id'].unique()
    
    education_data = (education[education['user_id'].isin(alumni)].groupby('parent_school_name')['education_id'].
                      count().sort_values(ascending=False)[:5].sort_values(ascending=True).reset_index())
    
    schools = go.Figure()
    trace = go.Bar(y=education_data['parent_school_name'].apply(lambda x: x.title().replace(' Of', ' of').replace(' And', ' and'))+' ',
                   x=education_data['education_id'],
                   marker_color = [crs[9]]*(len(education_data)-1)+[crs[0]],
                   orientation='h')
    schools.add_trace(trace)
    schools.update_layout(
        barmode='group',
        yaxis=dict(zeroline=False, showgrid=False,
                   gridcolor='#EAECF0', gridwidth=1,
                   tickfont=dict(family="Roboto", size=16, color="#2D426A")),
        xaxis=dict(zeroline=True, zerolinecolor='#EAECF0', zerolinewidth=1,
                   showgrid = False, gridcolor='#EAECF0', gridwidth=1, tickformat='.f', showticklabels = False, 
                   tickfont=dict(family="Roboto", size=16, color="#2D426A")),
        showlegend=False,
        title = dict(text = format_title('Top alma maters'), yanchor='top', y=0.92, xanchor='left', x=0.02),
        plot_bgcolor = 'rgba(0,0,0,0)',
        hoverlabel=dict(
            bgcolor='white',
            bordercolor = "#2D426A",
            font = dict(size=12, family="Roboto Mono", color='#2D426A'))
    )

    return spectrum, companies, schools


# Run the app
if __name__ == '__main__':
    app.run(debug=True)