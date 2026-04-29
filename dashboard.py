import streamlit as st
import pandas as pd
import plotly.colors as pc
import plotly.express as px
import numpy as np   
from countrystatecity_countries import get_countries, get_country_by_code


@st.cache_data
def load_disaster():
    df = pd.read_csv("https://ourworldindata.org/explorers/natural-disasters.csv?v=1&csvType=full&useColumnShortNames=false&Disaster+Type=All+disasters&Impact=Total+affected&Timespan=Annual&Per+capita=false", 
    storage_options = {'User-Agent': 'Our World In Data data fetch/1.0'})
    df = df.rename(columns={"Number of total people affected by disasters":"Affected", "Country name":"Country"})
    df = df[df['Affected'] > 0].copy()
    df = df.sort_values('Year')
    return df

@st.cache_data
def load_mecco():
    df = pd.read_csv("mecco_dataset.csv")
    id_cols = ['Country', 'Region', 'Newspaper', 'Code']
    clean_cols = [c for c in df.columns if c not in id_cols]
    for col in clean_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    return df

@st.cache_data
def load_mecco_world():
    df = pd.read_csv("mecco_world.csv")
    id_cols = ['Region']
    clean_cols = [c for c in df.columns if c not in id_cols]
    for col in clean_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    return df

@st.cache_data
def load_tas():
    df = pd.read_excel("CRU_tas.xlsx")
    return df


@st.cache_data
def load_pr():
    df = pd.read_excel("CRU_pr.xlsx")
    return df

@st.cache_data
def get_country_mapping():
    countries = get_countries()
    iso = [c.iso2 for c in countries]
    names = [c.name for c in countries]
    return dict(zip(iso, names))


mecco_df = load_mecco()
meccow_df = load_mecco_world()
tas_df = load_tas()
pr_df = load_pr()
dis_df = load_disaster()
isodict = get_country_mapping()

config = {"width":"stretch"}

    
def plot_precipitation(df):
    pr_country = df[df['code'] == target_country]
    
    pr_data = pr_country.melt(
        id_vars=['name','code'], 
        var_name='Year', 
        value_name='Precipitation'
    )
    
    df = pr_data.sort_values('Year')
    df = df[df['Year'].astype(int) >= target_year]

    pr_fig = px.area(
        df, 
        x="Year", 
        y="Precipitation",
        title=f"Annual Precipitation Trend Of {isodict[target_country]}",
        labels={"Precipitation": "Precipitation (mm)", "Year": "Year"},
        markers=True
    )

    min_year = int(df['Year'].min())
    max_year = int(df['Year'].max())

    padding = (df['Precipitation'].max() - df['Precipitation'].min()) 

    y_min = max(0, df['Precipitation'].min() - padding)
    y_max = df['Precipitation'].max() + padding

    pr_fig.update_xaxes(range=[min_year, max_year], autorange=False)
    pr_fig.update_yaxes(range=[y_min, y_max])

    pr_fig.update_traces(
        mode='lines', 
        line=dict(dash='dash', width=2)
    )

    st.plotly_chart(pr_fig, config=config)

def plot_temp(df):
    tas_country = df[df['code'] == target_country]
    
    tf = tas_country.melt(
        id_vars=['name','code'], 
        var_name='Year', 
        value_name='Temperature'
    )

    tf['Year'] = pd.to_numeric(tf['Year'])
    tf['Temperature'] = pd.to_numeric(tf['Temperature'])
    start_temp = tf.loc[(tf['Year'] >= 1901) & (tf['Year'] <= 1931), 'Temperature'].mean()
    thres_temp = start_temp + 2.0
    safe_temp = start_temp + 1.5
    
    tf = tf.sort_values('Year')
    tf = tf[tf['Year'].astype(int) >= target_year]
    
    y_min = tf['Temperature'].min()
    y_max = thres_temp if tf['Temperature'].max() < thres_temp else tf['Temperature'].max()

    bins = np.arange(np.floor(y_min), np.ceil(y_max) + 0.5, 0.5)
    if(y_max < 10):
        c = "Blues"
    else:
        c = "Pinkyl"

    colors = pc.sample_colorscale(c, len(bins))

    fig = px.line(
        tf, 
        x='Year', 
        y='Temperature',
        title=f"Annual Temperature Trend of {isodict[target_country]}",
        labels={"Temperature": "Temperature (C)", "Year": "Year"},
        color_discrete_map={'Temperature':'#98dbef'}
    )

    fig.add_hline(
        y=thres_temp,
        line_dash="dot", 
        line_color="#FF4500", 
        opacity = 0.6,
        annotation_text="2°C Above 1900 Levels"
    )

    fig.add_hline(
        y=safe_temp,
        line_dash="dot", 
        line_color="yellow", 
        opacity = 0.6,
        annotation_text="1.5°C Above 1900 Levels"
    )

    for i in range(len(bins) - 1):
        fig.add_hrect(
            y0=bins[i], 
            y1=bins[i+1], 
            fillcolor=colors[i], 
            opacity=0.6, 
            line_width=0,
            layer="below"
        )

    fig.update_yaxes(
        range=[y_min - 0.1, y_max + 0.1],
        showgrid=False, 
        zeroline=False,
        dtick=0.5
    )

    fig.update_traces(line_shape='spline', line_smoothing=1.3)

    st.plotly_chart(fig, config=config)


def plot_heatmap(df, dfw):
    country_df = df[df['Code'].str.contains(target_country, na=False)]

    if not country_df.empty:
        df_long = country_df.melt(
            id_vars=['Country', 'Region', 'Newspaper', 'Code'], 
            var_name='Date', 
            value_name='Reports'
        )

        dfs = df_long.groupby(['Date'], as_index=False)['Reports'].sum()
        dfs[['Year', 'Month']] = dfs['Date'].str.split('.', expand=True)

        month_order = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        dfs['Month'] = pd.Categorical(dfs['Month'], categories=month_order, ordered=True)
        df = dfs[dfs['Year'].astype(int) >= target_year]

        df_final = df[['Year', 'Month', 'Reports']].copy()

        heatmap_df = df_final.pivot_table(
            index='Year', 
            columns='Month', 
            values='Reports'
        )

        fig = px.imshow(
            heatmap_df,
            labels=dict(x="Month", y="Year", color="Reports"),
            x=month_order,
            title=f"Climate News Reports of {isodict[target_country]}",
            color_continuous_scale='YlGn',
            aspect="equal"
        )

        fig.update_xaxes(
            tickmode='array',
            tickvals=month_order,
            dtick=1,            
            side='top'          
        )

        fig.update_traces(xgap=2, ygap=2)

        st.plotly_chart(fig, config=config)


    else:
        country = get_country_by_code(target_country)
        region = country.region
        subregion = country.subregion

        if(region == "Americas" and subregion == "North America"):
            region = "North America"
        elif(region == "Americas" and subregion != "North America"):
            region = "South America"

        if(subregion == "Western Asia"): 
            region = "Middle East"

    
        dfw_long = dfw.melt(
            id_vars=['Region'], 
            var_name='Date', 
            value_name='Reports'
        )

        
        df_targ =  dfw_long[dfw_long['Region'].str.contains(region, na=False)]
        df_targ[['Year', 'Month']] = df_targ['Date'].str.split('.', expand=True)

        month_order = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        df_targ['Month'] = pd.Categorical(df_targ['Month'], categories=month_order, ordered=True)
        
        df_targ = df_targ[df_targ['Year'].astype(int) >= target_year]
        df_final = df_targ[['Year', 'Month', 'Reports']].copy()
        heatmap_df = df_final.pivot_table(
            index='Year', 
            columns='Month', 
            values='Reports'
        )

        fig = px.imshow(
            heatmap_df,
            labels=dict(x="Month", y="Year", color="Reports"),
            x=month_order,
            title=f"Climate News Reports of {region}",
            color_continuous_scale='algae',
            aspect="equal"
        )

        fig.update_xaxes(
            tickmode='array',
            tickvals=month_order,
            dtick=1,            
            side='top'          
        )

        fig.update_traces(xgap=2, ygap=2)

        st.plotly_chart(fig, config=config)

        
def world_heatmap(wdf):
    mdf = wdf.melt(
        id_vars=['Region'], 
        var_name='Date', 
        value_name='Reports'
    )

    df = mdf.groupby(['Date'], as_index=False)['Reports'].sum()
    df[['Year', 'Month']] = df['Date'].str.split('.', expand=True)
    month_order = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    df['Month'] = pd.Categorical(df['Month'], categories=month_order, ordered=True)
    df = df[df['Year'].astype(int) >= target_year]

    df_final = df[['Year', 'Month', 'Reports']].copy()
    heatmap_df = df_final.pivot_table(
        index='Year', 
        columns='Month', 
        values='Reports'
    )

    fig = px.imshow(
        heatmap_df,
        labels=dict(x="Month", y="Year", color="Reports"),
        x=month_order,
        title=f"Global Climate News Reports",
        color_continuous_scale='algae',
        aspect="equal"
    )

    fig.update_xaxes(
        tickmode='array',
        tickvals=month_order,
        dtick=1,            
        side='top'          
    )

    fig.update_traces(xgap=2, ygap=2)

    st.plotly_chart(fig, config=config)

def bubble_disaster(df):
    df_year = df[df['Year'].astype(int) >= target_year]

    fig = px.scatter_geo(
        df_year, 
        locations="Country",            
        size="Affected",             
        hover_name="Country",
        color="Affected",
        animation_frame="Year",        
        title="Number of people affected by climate disasters per year",
        size_max=100,
        locationmode="country names",
        color_continuous_scale="matter"
    )

    fig.update_traces(
        marker=dict(
            sizemin=10,
            sizemode='area',
            sizeref=5000          
        )
    )

    fig.update_layout(
        height=500,         
        margin={"r":0, "t":30, "l":0, "b":0}, 
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='equirectangular' 
        )
    )
    
    st.plotly_chart(fig, config=config)


st.title("Climate Change In My Lifetime")

country_names = sorted(isodict.keys(), key=lambda x: isodict[x])

target_country = st.selectbox(
    "I was born at...",
    options=country_names, 
    format_func=lambda x: isodict[x] 
)

target_year = st.number_input(
    label="I was born in...",
    min_value=1940,      
    max_value=2026, 
    value=2000,  
    step=1,              
    format="%d" 
)


if target_country and target_year:
    
    bubble_disaster(dis_df)
    st.text("""
    Disasters include all geophysical,meteorological and climate events including 
    earthquakes, volcanic activity, landslides, drought, wildfires, storms, and flooding. 
    The total number of people affected is the sum of injured, requiring assistance and homeless.
    """)

    plot_precipitation(pr_df)

    plot_temp(tas_df)
    st.text("Temperature used is Annual Mean Surface Air Temperature")

    plot_heatmap(mecco_df, meccow_df)

    if st.toggle('Compare with Global'):
        world_heatmap(meccow_df)

    st.markdown("**Climate Headlines Around You**")
    try:
        st.image(f'flags/{target_country}.png')
    except:
        st.text("Apologies, no data available for this country.")

    st.markdown("### Sources") 
    st.markdown('''Climate Disasters: [Our World in Data](https://ourworldindata.org/natural-disasters) / EM-DAT    
    Precipitation, Temperature: [Climate Knowledge Portal](https://climateknowledgeportal.worldbank.org/download-data) / CRU   
    News Datasets: [HuggingFace](https://huggingface.co/datasets/NickyNicky/global-news-dataset) + [Kaggle](https://www.kaggle.com/datasets/fringewidth/climate-change-news)  
    News coverage: [MECCO](https://mecco.colorado.edu/form/index.html)''')




