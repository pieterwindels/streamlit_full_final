import streamlit as st
import pandas as pd
import json
import plotly.figure_factory as ff
import plotly.express as px
import pdfkit
import seaborn as sns
import numpy as np
import datetime
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
import smtplib


#LOAD THE DATAFRAME AND CLEAN IT UP
@st.cache_data
def load_data():
    df = pd.read_csv('df_3_months.csv')
    df_comp = pd.read_csv('df_6_months.csv')
    
    return (df, df_comp)

#LOAD THE LIST OF MUNICIPALITIES AND ARRONDISSEMENTS TO CHOSE FROME
@st.cache_data
def gemeente():
    with open('belgium-postal-codesn.json', 'r') as file:
        data = json.load(file)

    #create list of municipalities to chose from:
    gemeenten, arrondissementen = [], []
    for item in data:
      if item['mun_name_nl'] is not None:
        gemeenten.append(item['mun_name_nl'])
      if item['mun_name_fr'] is not None:
        gemeenten.append(item['mun_name_fr'])
      if item['mun_name_de'] is not None:
        gemeenten.append(item['mun_name_de'])
      if item['arr_name_nl'] is not None:
        arrondissementen.append(item['arr_name_nl'])
      if item['arr_name_fr'] is not None:
        arrondissementen.append(item['arr_name_fr'])
      if item['arr_name_de'] is not None:
        arrondissementen.append(item['arr_name_de'])

    i=0
    while i<len(arrondissementen):
      arrondissementen[i]=arrondissementen[i]+' (arrondissement)'
      i+=1

    set_finaal = set(arrondissementen).union(set(gemeenten))
  
    return set_finaal

#DOWNLOAD SELECTED TABLE AS PDF
@st.cache_data
def convert_df(df):
    options = {'orientation': 'landscape',
              'encoding': "UTF-8"}
        
    return pdfkit.from_string(df.to_html(index=False, escape=False), options=options)

#DOWNLOAD REPORT AS PDF
#@st.cache_data
def convert_report():

    env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
    template = env.get_template("template.html")
    
    options = {'orientation': 'landscape',
              'encoding': "UTF-8"}

    html = template.render(
        student='ik',
        course='course',
        grade='100',
        date='503')

    return pdfkit.from_string(html, False)
         
#page setup
st.set_page_config(
    page_title="IMMO2SMART PORTAL",
    page_icon="house",
    layout="wide")
    
#RUN THE TWO METHODS DF and MUNICIPALITIES LIST
df, df_comp = load_data()
selector = gemeente()
    
#HEADER OF THE APP
st.title('Welcome to our Immo2Smart real estate app!')
st.caption('''This is a demo version to get you inspired with the functionalities. Final results will have **DEMO** values. If interested in the full version, just leave your email below!
Any other questions: immo2smart@gmail.com''')

st.header('I want full access to the app!')
user_email = st.text_input("Please enter your email address")

if st.button("Contact me for full access"):
    try:
        # Set up the SMTP server and login to your email account
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        #server.starttls()
        server.login("devpwindels@gmail.com", "eskuahufhdrwiwzb")

        # Create the email message
        message = "Subject: New Email from Streamlit App\n\n" + "Email: " + user_email

        # Send the email
        server.sendmail("devpwindels@gmail.com", "immo2smart@gmail.com", message)

        # Close the SMTP server connection
        server.quit()

        # Display a success message to the user
        st.success("Email sent successfully! We will be in touch with you soon!")
    except Exception as e:
        # Display an error message if there is an issue sending the email
        st.error("Email could not be sent. Something went wrong, please send an email to immo2smart@gmail.com")

st.divider()

#THE BOX TO SELECT WHAT SHOULD BE VISUALIZED
with st.form('invulformulier'):
        
    st.header('What are the characteristics of the property?')
        
    choice_type=st.radio('What is the property type?', ['House for sale HK', 'Appartement for sale AK', 'Appartement for rent AH', 'House for rent HH'])
        
    gemeente=st.selectbox('What is the location of the property?', selector, index=None, placeholder='Please select the main municipality or arrondissement...')
        
    choice_opp=st.slider('Wat is the habitable surface (m²)?', 25.0, 450.0, step=25.0, value=(25.0, 450.0))                                                   
        
    nieuwbouw_of_bestaand=st.radio('Is the property already built or newly constructed?', ['existing', 'new construction'])
    
    customerName = st.radio('Is the property put on the market by an agency or by the owner?' , ['agency', 'by owner'])
       
    submitted = st.form_submit_button("Search")
    
#CREATE A SELECTION DATAFRAME
if submitted:

    if gemeente != None:
     
        #filter 1 selecteert het type pand
        filter1 = df['type']==choice_type[-2:]
        filter1_comp = df_comp['type']==choice_type[-2:]
    
        #filter 2 selecteert de postcodes van de panden
        #link the chosen muni to a list of postal codes:
        postal_codes = []
        with open("belgium-postal-codesn.json", "r") as file:
            data1 = json.load(file)
    
        for item in data1:
            if '(arrondissement)' in gemeente:
                if item['arr_name_nl'] == gemeente.replace(' (arrondissement)', ''):
                    postal_codes.append(int(item['postcode']))
                elif item['arr_name_fr'] == gemeente.replace(' (arrondissement)', ''):
                    postal_codes.append(int(item['postcode']))
                elif item['arr_name_de'] == gemeente.replace(' (arrondissement)', ''):
                    postal_codes.append(int(item['postcode'])) 
            else:
              if item['mun_name_nl'] == gemeente:
                postal_codes.append(int(item['postcode']))
              elif item['mun_name_fr'] == gemeente:
                postal_codes.append(int(item['postcode']))
              elif item['mun_name_de'] == gemeente:
                postal_codes.append(int(item['postcode']))
              
        filter2 = df['property-location-postalCode'].isin(postal_codes)
        filter2_comp = df_comp['property-location-postalCode'].isin(postal_codes)
    
        #filter 3 selecteert de bewoonbare opp van het pand
        filter3 = df['property-netHabitableSurface'].between(choice_opp[0], choice_opp[1], inclusive='both')
        filter3_comp = df_comp['property-netHabitableSurface'].between(choice_opp[0], choice_opp[1], inclusive='both')
    
        #filter 4 selecteert of het bestaand of nieuwbouw is
        if nieuwbouw_of_bestaand=='new construction':
            filter4 = (df['flags-secondary']=="['new_real_estate_project']")|(df['flags-secondary']=="['new_construction']")
            filter4_comp = (df_comp['flags-secondary']=="['new_real_estate_project']")|(df_comp['flags-secondary']=="['new_construction']")
        else:
            filter4 = (df['flags-secondary']=="['new_price']")|(df['flags-secondary']=="['biddit_sale']")|(df['flags-secondary']=="['notary_sale']")|(df['flags-secondary']=="['new_price', 'notary_sale']")|(df['flags-secondary'].isnull())
            filter4_comp = (df_comp['flags-secondary']=="['new_price']")|(df_comp['flags-secondary']=="['biddit_sale']")|(df_comp['flags-secondary']=="['notary_sale']")|(df_comp['flags-secondary']=="['new_price', 'notary_sale']")|(df_comp['flags-secondary'].isnull())
        
        #filter 5 selecteert of het pand is aangeboden door eigenaar of door immokantoor
        if customerName == 'by owner':
            filter5 = df['customerName']=='PRIVATE'
            filter5_comp = df_comp['customerName']=='PRIVATE'
        else:
            filter5 = df['customerName']!='PRIVATE'
            filter5_comp = df_comp['customerName']!='PRIVATE'
    
        df_sel=df[filter1&filter2&filter3&filter4&filter5]
        df_sel_comp=df_comp[filter1_comp&filter2_comp&filter3_comp&filter4_comp&filter5_comp]
    
        #HERE WE CREATE THE DEMO DF_SEL WITH RANDOM MISSING VALUES -TO BE DELETED IN PAYING VERSION!
        sampled_df_sel = df_sel.sample(frac=0.4)
        df_sel.loc[sampled_df_sel.index, ['property-location-street', 'property-location-number', 'date']] = '**DEMO**'
        
        #SET SOME VARIABLES DEPENDING ON THE SELECTED PROPERTIES
        
        if choice_type[-2:] == 'HK':
            pand='houses'
            transactie = 'for sale'
        elif choice_type[-2:] == 'AK':
            pand='appartements'
            transactie = 'for sale'
        elif choice_type[-2:] == 'AH':
            pand='appartements'
            transactie = 'for rent'
        else:
            pand='houses'
            transactie = 'for rent'
            
        #VISUALIZE THE LIST VIEW OF THE SELECTED PROPERTIES
        st.header(f'List view of all {pand} {transactie} that have come on the market in {gemeente} in the last 3 months!')

        day = datetime.date.today()
        delta = datetime.timedelta(days=90)
        day_90 = day - delta
    
        if choice_type[-2:] == 'HK' or choice_type[-2:] == 'AK':
            new_column_names = {'property-location-locality':'locality',
                                'property-location-street':'street',
                                'property-location-number':'street number',
                                'property-netHabitableSurface':'habitable surface m²',
                                'price-mainValue':'price €',
                                'price-oldValue':'old price €',
                                'price_m2':'price € per m²'}
            
            df_sel = df_sel.rename(columns=new_column_names)
            df_sel_comp = df_sel_comp.rename(columns=new_column_names)
            
            st.dataframe (df_sel[['locality', 
                                 'street',
                                 'street number', 
                                 'habitable surface m²', 
                                 'price €', 
                                 'old price €', 
                                 'price € per m²', 
                                 'price_reduction%', 
                                 'date']],
                          column_config={'old price €': st.column_config.NumberColumn
                                         (help='Was there a price reduction for the property?'),
                                         'date': st.column_config.DateColumn
                                         (help='Listing date of property')
                                        },
                          hide_index=True)
    
            #download tabel als pdf
            
            pdf = convert_df(df_sel[['date',
                                     'locality',
                                     'street',
                                     'street number',
                                     'habitable surface m²', 
                                     'price €',
                                     'old price €',
                                     'price € per m²',
                                     'price_reduction%']])
        
            st.download_button(label="Download list as PDF",
                               data=pdf,
                               file_name=f'smart_immo_{pand}_{transactie}_{gemeente}_{day}.pdf',
                               mime='application/pdf'
                              )
    
        
        else:
            new_column_names = {'property-location-locality':'locality',
                                'property-location-street':'street',
                                'property-location-number':'street number',
                                'property-netHabitableSurface':'habitable surface m²',
                                'price-mainValue':'monthly price €',
                                'price-oldValue':'old price €',
                                'price_m2':'monthly price € per m²',
                                'price-additionalValue':'extra costs €'}
    
            df_sel = df_sel.rename(columns=new_column_names)
            df_sel_comp = df_sel_comp.rename(columns=new_column_names)
            
            st.dataframe(df_sel[['locality', 
                                 'street',
                                 'street number', 
                                 'habitable surface m²', 
                                 'monthly price €',
                                 'extra costs €',
                                 'old price €', 
                                 'monthly price € per m²', 
                                 'price_reduction%', 
                                 'date']],
                         column_config={'extra costs €':st.column_config.NumberColumn
                                        (help='Costs to cover for heat, garage, ....'),
                                        'old price €': st.column_config.NumberColumn
                                        (help='Was there a price reduction for the property?'),
                                        'date': st.column_config.DateColumn
                                        (help='Listing date of property'),
                                       },
                         hide_index=True)
            
            #download tabel als pdf
            
            pdf = convert_df(df_sel[['date',
                                     'locality',
                                     'street',
                                     'street number',
                                     'habitable surface m²', 
                                     'monthly price €',
                                     'old price €',
                                     'monthly price € per m²',
                                     'extra costs €',
                                     'price_reduction%']])
        
            st.download_button(label="Download data as PDF",
                               data=pdf,
                               file_name='example.pdf',
                               mime='application/pdf'
                              )
            
        st.divider()

        #VISUALIZE THE SELECTED PROPERTIES ON A MAP
        
        st.header(f'Map view of all {pand} {transactie} that have come on the market in {gemeente} in the last 3 months!')
    
        if choice_type[-2:] == 'HK' or choice_type[-2:] == 'AK':
    
            fig2 = px.scatter_mapbox(df_sel,
                                     lat="lat", 
                                     lon="lon", 
                                     hover_data={'price € per m²':True, 'lat':False, 'lon':False},
                                     hover_name='street', 
                                     size='price €',
                                     color='price € per m²',
                                     color_continuous_scale='Inferno',
                                     #color_discrete_sequence=["red"],
                                     #labels={'property-location-street':'street',
                                     #        'property-location-number':'street nr',
                                    #       'price-mainValue':'price €',
                                      #       'price_m2':'price € per m²'},
                                     zoom=8, 
                                     height=300,
                                     center={'lat':df_sel['lat'].mean(), 'lon':df_sel['lon'].mean()}
                                    )
            fig2.update_layout(mapbox_style="open-street-map")
            fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            fig2.update_layout(mapbox_bounds={"west": 2, "east": 7, "south": 49, "north": 52})
            fig2.update_layout(
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=16,
                    font_family="Rockwell"
                )
            )
            st.plotly_chart(fig2, use_container_width=True)
    
        else:
    
            fig2 = px.scatter_mapbox(df_sel,
                                     lat="lat", 
                                     lon="lon", 
                                     hover_data={'monthly price € per m²':True, 'lat':False, 'lon':False},
                                     hover_name='street', 
                                     size='monthly price €',
                                     color='monthly price € per m²',
                                     color_continuous_scale='Inferno',
                                     #color_discrete_sequence=["red"],
                                     #labels={'property-location-street':'street',
                                     #        'property-location-number':'street nr',
                                    #       'price-mainValue':'price €',
                                      #       'price_m2':'price € per m²'},
                                     zoom=8, 
                                     height=300,
                                     center={'lat':df_sel['lat'].mean(), 'lon':df_sel['lon'].mean()}
                                    )
            fig2.update_layout(mapbox_style="open-street-map")
            fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            fig2.update_layout(mapbox_bounds={"west": 2, "east": 7, "south": 49, "north": 52})
            fig2.update_layout(
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=16,
                    font_family="Rockwell"
                )
            )
            st.plotly_chart(fig2, use_container_width=True)
            
    
        st.divider()

        #PROVIDE A SUMMARY METRICS OVERVIEW OF THE SELECTED PROPERTIES
        
        st.header(f'Summary price information for all {pand} {transactie} that were on the market in {gemeente} in the last 3 months! Comparison with data from previous 6 months.')
    
        if choice_type[-2:] == 'HK' or choice_type[-2:] == 'AK':

            if df_sel.empty:

                st.write('No properties were selected')

            else:
        
                col1, col2, col3, col4 = st.columns(4)
                col1.metric('Number of properties on market', df_sel['price €'].count(), delta=int(df_sel['price €'].count()-df_sel_comp['price €'].count()))
                col2.metric('Mean sale price €', int(df_sel['price €'].mean().round()), delta=int(df_sel['price €'].mean()-df_sel_comp['price €'].mean()))
                col3.metric('Mean sale price € per m²', int(df_sel['price € per m²'].mean().round()), delta=int(df_sel['price € per m²'].mean()-df_sel_comp['price € per m²'].mean()))
                col4.metric('25% of properties are priced lower than', int(df_sel['price €'].quantile(q=0.25)), delta=int(df_sel['price €'].quantile(q=0.25)-df_sel_comp['price €'].quantile(q=0.25)))
                
                col5, col6, col7 = st.columns(3)
                col5.metric('25% of properties are priced higher than', int(df_sel['price €'].quantile(q=0.75)), delta=int(df_sel['price €'].quantile(q=0.75)-df_sel_comp['price €'].quantile(q=0.75)))
                col6.metric('Number of properties with reduced price', df_sel['old price €'].count(), delta=int(df_sel['old price €'].count()-df_sel_comp['old price €'].count()))
                try:
                    col7.metric('Average price reduction in %', df_sel['price_reduction%'].mean(numeric_only=True).round(), delta=df_sel['price_reduction%'].mean(numeric_only=True).round()-df_sel_comp['price_reduction%'].mean(numeric_only=True).round())
                except:
                    col7.metric('Average price reduction in %', 'None')
        else:

            if df_sel.empty:

                st.write('No properties were selected')

    
            else:
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric('Number of properties on market', df_sel['monthly price €'].count(), delta=int(df_sel['monthly price €'].count()-df_sel_comp['monthly price €'].count()))
                col2.metric('Mean monthly rental price €', int(df_sel['monthly price €'].mean().round()), delta=int(df_sel['monthly price €'].mean()-df_sel_comp['monthly price €'].mean()))
                col3.metric('Mean monthly rental price € per m²', int(df_sel['monthly price € per m²'].mean().round()), delta=int(df_sel['monthly price € per m²'].mean()-df_sel_comp['monthly price € per m²'].mean()))
                col4.metric('25% of properties are priced lower than', int(df_sel['monthly price €'].quantile(q=0.25)), delta=int(df_sel['monthly price €'].quantile(q=0.25)-df_sel_comp['monthly price €'].quantile(q=0.25)))
                
                col5, col6, col7 = st.columns(3)
                col5.metric('25% of properties are priced higher than', int(df_sel['monthly price €'].quantile(q=0.75)), delta=int(df_sel['monthly price €'].quantile(q=0.75)-df_sel_comp['monthly price €'].quantile(q=0.75)))
                col6.metric('Number of properties with reduced price', df_sel['old price €'].count(), delta=int(df_sel['old price €'].count()-df_sel_comp['old price €'].count()))
                try: 
                    col7.metric('Average price reduction in %', df_sel['price_reduction%'].mean(numeric_only=True).round(), delta=df_sel['price_reduction%'].mean(numeric_only=True).round()-df_sel_comp['price_reduction%'].mean(numeric_only=True).round())
                except:
                    col7.metric('Average price reduction in %', 'None')
        
        st.divider()

        #PROVIDE THE OPTION TO DOWNLOAD A FULL REPORT OF THE INFO PROVIDED
        
        st.header('Do you want to download a summary report of these data?')

        st.write('Not available in demo version!')

        #download report als pdf  

        st.divider()
      
    else:
        st.error('You forgot to select a municipality or arrondissement!')
