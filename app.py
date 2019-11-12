import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from urllib.parse import quote

import time
import pandas as pd
import re

app = dash.Dash(__name__)
app.title = "AirDePanache"

init = False

data = data = pd.read_excel("data.xls",skiprows=5,skipfooter=2)
keyword_value = None
price_range = [0, int(data["PRICE € excluding VAT"].max()+1)]
nature = None
contenance = None

app.layout = html.Div(children=[
    html.Div(id="hidden-div"),
    dcc.Input(
            id='keyword',
            debounce=True,
            placeholder="mots-clés",
            value=keyword_value,
            style={'width': 130, 'height': 30}
        ),
    html.Div(children=[
        dcc.RangeSlider(
            id='price_range_slider',
            min=price_range[0],
            max=price_range[1],
            step=0.1,
            value=price_range,
        ),
        html.Div(id='price_range_value',children="prix entre {}€ et {}€".format(price_range[0],price_range[1]))
    ],id="price_range_div",style={'width': 200}),
    dcc.Input(
            id='contenance',
            debounce=True,
            placeholder="contenance(mL)",
            style={'width': 130, 'height': 30}
        ),
    dcc.Dropdown(
        id='nature',
        options=[
            {'label': 'eau de toilette', 'value': 'EDT'},
            {'label': 'eau de cologne', 'value': 'EDC'},
            {'label': 'eau de parfum', 'value': 'EDP'},
            {'label': 'pur parfum', 'value': 'PP'},
            {'label': 'déodorant', 'value': 'DEO'},
            {'label': 'coffret', 'value': '+'},
            {'label': 'tout', 'value': ''}
        ],
        searchable=False,
        value = None,
        style={'width': 200, 'height': 35},
        clearable=False,
        placeholder="nature du produit"
    ),
    html.Div(id='product_number_div',children="{} produits conservés".format(data.shape[0])),
    html.A(children='Télécharger les données correspondantes aux critères' , id='download-chosen',download="filtered_data.csv", href="",target="_blank"),
    html.Div(children=[
        dash_table.DataTable(
        id='data_table',
        columns=[{"name": i, "id": i} for i in data.columns],
        data=data.to_dict('records'),        
        style_cell_conditional=[
            {'if': {'column_id': 'EAN'},
            'width': '130px'},
            {'if': {'column_id': 'ITEM DESCRIPTION'},
            'width': '600'},
            {'if': {'column_id': 'STOCK'},
            'width': '130px'},
            {'if': {'column_id': 'PRICE € excluding VAT'},
            'width': '130px'},
            {'if': {'column_id': 'ORDER'},
            'width': '130px'},
            {'if': {'column_id': 'VALUE € excluding VAT'},
            'width': '130px'},
            ]
        )
    ],style={'width': 1200})
])

def get_mL(s):
    p = re.compile("\ ([0-9]+)[M|m][L|l]")
    res = p.findall(s)
    if res:
        return sum([int(i) for i in res])
    else:
        return None

data["mL"] = data["ITEM DESCRIPTION"].apply(get_mL)


@app.callback([Output('data_table','data'),
               Output('price_range_value','children'),
               Output('product_number_div','children'),
               Output('download-chosen', 'href')
               ],
             [Input('keyword','value'),
              Input('price_range_slider','value'),
              Input('nature','value'),
              Input('contenance','value')])
def main_callback(keyword_input,price_range_input,nature_input,contenance_input):
    global init
    global temp_data
    global keyword_value
    global price_range
    global nature
    global contenance

    if not init:
        temp_data = data.copy()
        init = True

    elif keyword_input != keyword_value or price_range_input != price_range or nature_input != nature or contenance_input != contenance:
        temp_data = data.copy()

        if keyword_input is None or keyword_input=="":
            temp_data["MATCH_KEYWORD"] = True
        else:
            temp_data["MATCH_KEYWORD"] = temp_data['ITEM DESCRIPTION'].apply(lambda x:all([v.upper() in x.upper() for v in keyword_input.split(" ")]))

        if nature_input is None or nature_input=="":
            temp_data["MATCH_NATURE"] = True
        elif nature_input == "DEO":
            temp_data["MATCH_NATURE"] = temp_data['ITEM DESCRIPTION'].apply(lambda x:any([v in x.upper() for v in ["DEO","(D)"]]))
        else:
            temp_data["MATCH_NATURE"] = temp_data['ITEM DESCRIPTION'].apply(lambda x:nature_input in x)

        temp_data["MATCH_PRICE"] = temp_data["PRICE € excluding VAT"].apply(lambda x: price_range_input[0]<=x<=price_range_input[1])

        if contenance_input is None or contenance_input=="":
            temp_data["MATCH_CONTENANCE"] = True
        else:
            temp_data["MATCH_CONTENANCE"] = temp_data['mL'].apply(lambda x:x==int(contenance_input))

        temp_data = temp_data[(temp_data["MATCH_KEYWORD"])&(temp_data["MATCH_NATURE"])&(temp_data["MATCH_PRICE"])&(temp_data["MATCH_CONTENANCE"])].copy()

        keyword_value = keyword_input
        price_range = price_range_input
        nature = nature_input
        contenance = contenance_input


    csv_string = "data:text/csv;charset=utf-8," + quote(temp_data[["EAN","ITEM DESCRIPTION","STOCK","PRICE € excluding VAT","ORDER","VALUE € excluding VAT"]].
    to_csv(index=False,sep=";",float_format='%.15f')) 
    
    return temp_data.to_dict('records'),"prix entre {}€ et {}€".format(price_range[0],price_range[1]),"{} produits conservés".format(temp_data.shape[0]),csv_string

if __name__ == '__main__':
    # En local
    app.run_server(debug=True)