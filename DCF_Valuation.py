#import all the packages we need
import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import numpy as np
import yfinance as yf
import pickle
import matplotlib.pyplot as plt
import streamlit as st
import plotly
import plotly.express as px
import time
import datetime
from datetime import datetime
#___________________________________________________Function Defines___________________________________________________________________#
#Function Defines
def date2qtr(x):
    QTR=(x.month-1)//3+1
    QTR="Q"+str(QTR)
    return QTR

def date2year(x):
    return x.year

@st.cache
def DCF(earnings, discount_rate, growth_rate1, growth_years ,growth_rate2, total_years):
    value=0
    last_Earnings=earnings
    #if thegrowth years are 0 then use the perpetual growth rate
    if(growth_years==0):
        if(discount_rate<=growth_rate1):
            value=np.inf
        else:
            value=earnings/(discount_rate-growth_rate1)
    #use the 2 peice growth model
    else:
        #sum the disconted cash flow for the # of years for the first griwth rate
        value=earnings
        for i in range(1, growth_years+1):
            last_Earnings=last_Earnings*(1+growth_rate1)
            value=value+last_Earnings/(1+discount_rate)**(i)
        #if total years are 0 then we use a perpetual terminal value
        if(total_years==0 or total_years <=growth_years):
            TV=last_Earnings*(1+growth_rate1)/(discount_rate-growth_rate2)
            value=value+TV/(1+discount_rate)**(growth_years+1)
        else:
            for i in range(growth_years+1, total_years+1):
                last_Earnings=last_Earnings*(1+growth_rate2)
                value=value+last_Earnings/(1+discount_rate)**(i)
    return value
#force the layout to be wide
st.set_page_config(layout="wide")
#__________________________________Load the Data set, filter on ticker________________________________________________________________#
companyDF=pd.read_csv(r'C:\Users\cwesterb\Stock Data 11-22-2021\complete_data.csv')
#companyDF=pd.read_csv(r'complete_financial_information_2011.csv')
company_list=companyDF.drop_duplicates(subset='Ticker')

#grab the complete list oc companies
company_list=company_list['Ticker'].values

#title for the Applicaiton
#st.title('Discounted Cash Flow Valuation')
#2 Columns
cols = st.columns(2)
#slect box for picking the company
sim_date = cols[0].date_input('"Current Date" For Simulation')
#slect box for picking the company
company_ticker = cols[0].selectbox('Ticker:',company_list)
#grab the data for the select company
financialDF = companyDF[companyDF['Ticker'] == company_ticker]

#columns we want for DCF
DCF_columns=["Ticker","Year","QTR","Report Date", "Shares (Diluted)", "Revenue",
                         "Pretax Income (Loss)",'Net Income (Common)', 'Stock Price','Stock pct Increase', 
                         'Op. Invested Capital','Fin. Invested Capital','Invested Capital','Owner Earnings','Free Cash Flow',
                         'Net Worth','Market Cap','PE','PB','PB (Tangible)','Faustmann Ratio','ROIC','Profit Margin',
                         'ROA','ROE']

#filter to the columns we need
financialDF=financialDF[DCF_columns]

#remove data after the simulation date
financialDF["Report Date"] = pd.to_datetime(financialDF["Report Date"], format="%m/%d/%Y")
financialDF=financialDF[financialDF["Report Date"] <= pd.to_datetime(sim_date, format="%Y/%m/%d")]
#create the annual version of the data frame
annualDF=pd.DataFrame()
#these are the columns where we want the most recent value
latest_columns=["Ticker","Year","Report Date","Shares (Diluted)",'Stock Price','Net Worth','Market Cap']
#these are the columns where we want to add the qtrs together
add_columns=["Revenue", "Pretax Income (Loss)",'Net Income (Common)','Owner Earnings','Free Cash Flow']
#these are the columns where we want to average the values from the quaters
average_columns=['PE','PB','PB (Tangible)','Faustmann Ratio','ROIC','Profit Margin',
                         'ROA','ROE']

#populate the annual daaframe
#check that we have enough data to try and create annual numbers
if(len(financialDF)>4):
    temp=financialDF.drop_duplicates(subset='Year')
    #grab the number of years to cycle through
    year_list=temp['Year']
    for year in year_list:
        #Grab this years data
        temp=financialDF[financialDF['Year']==year]
        #grab latest columns
        latestDF=temp[latest_columns]
        #grab the last row
        latestDF=latestDF.iloc[-1:]
        latestDF=latestDF.reset_index(drop=True)
        addDF=temp[add_columns]
        addDF=pd.DataFrame(addDF.sum(axis=0)*4/len(temp))
        addDF=addDF.T
        averageDF=temp[average_columns]
        averageDF=pd.DataFrame(averageDF.sum(axis=0)/len(temp))
        averageDF=averageDF.T
        #if it is the first time then we need to create the dataframe
        if(annualDF.empty):
            annualDF=pd.concat([latestDF, addDF, averageDF], axis=1)
        else:
            annualDF=annualDF.append(pd.concat([latestDF, addDF, averageDF], axis=1), ignore_index = True)
#focus on the earnings
EPS=annualDF["Owner Earnings"].values/annualDF["Shares (Diluted)"].values
EPS_change=(EPS-np.roll(EPS,1))/np.roll(EPS,1)*100
EPS_change[0]=0
EPSDF=pd.DataFrame(annualDF["Year"])
EPSDF["EPS"]=pd.DataFrame(EPS)
EPSDF["EPS %"]=pd.DataFrame(EPS_change)
EPSDF['Sales per Share']=pd.DataFrame(annualDF['Revenue'].values/annualDF["Shares (Diluted)"].values)
annualDF["EPS"]=EPSDF["EPS"]
annualDF["EPS %"]=EPSDF["EPS %"]
annualDF['Sales per Share']=EPSDF['Sales per Share']
displayDF=EPSDF.sort_values(by=['Year'], ascending=False)

#put the Simplified data frame in the 
cols[0].dataframe(data=displayDF, height=175)
LatestDF=EPSDF.iloc[-1:]
#@st.cache
Earnings=cols[0].text_input("Year 1 Earnings", 0)
Drate = cols[0].text_input("Disconut Rate",value=0.07)
Growth1 = cols[0].text_input("Early Growth Rate",value=0.03)
GrowthYears = cols[0].text_input("Years of Growth (0 assumes perpetual Early Growth Rate)",value=0)
Growth2 = cols[0].text_input("Terminal Growth Rate",value=0.03)
TotalYears =  cols[0].text_input("Years of Growth (0 assumes Terminal Value from Terminal Growth Rate)",value=0)

headings=annualDF.columns
item1 = cols[1].selectbox('Plot1:',headings, index=21)
item2 = cols[1].selectbox('Plot2:',headings, index=1)

#displayDF=filtered_data.sort_values(by=['QTR'], ascending=False, kind='mergesort')
#filtered_data=filtered_data.sort_values(by=['Year'], ascending=False, kind='mergesort')

#__________________________________Grab the data for plotting________________________________________________________________#


plot2DF=pd.DataFrame(annualDF[item1])
plot2DF['Year']=annualDF['Year'].values
if(item2 !='Year'):
    plot_series=[item1, item2]
    plot2DF[item2]=annualDF[item2]
else:
    plot_series=[item1]
fig2 = px.line(plot2DF,x="Year", y=plot_series)
cols[1].plotly_chart(fig2, use_container_width=True)
#__________________________________Data below the plot________________________________________________________________#
#The Discounted Cash Flow Valuation
valuation=DCF(float(Earnings), float(Drate), float(Growth1), int(GrowthYears), float(Growth2), int(TotalYears))
current_price=yf.Ticker(company_ticker).history(start=sim_date)
#cols[1].text(current_price)
current_price=current_price["Close"].values
current_price=current_price[0]
current_price_format = "{:.2f}".format(current_price)
valuation_format = "{:.2f}".format(valuation)
cols[1].subheader("Valuation: "+str(valuation_format)+ "\tCurrent Price: "+str(current_price_format))

MS_format=(valuation/current_price-1)*100
MS_format = "{:.2f}".format(MS_format)
cols[1].subheader("Margin of Safety: "+str(MS_format)+"%")
if(len(EPSDF)>3):
    eps=EPSDF['EPS'].values
    eps3Growth=((eps[len(eps)-1]/eps[len(eps)-4])**(1/3)-1)    
    #eps3Growth="{:.2f}".format(eps3Growth)
    #cols[1].text("EPS 3 Year % Growth: "+ str(eps3Growth) + "%")
else:
    eps3Growth=0
    #eps3Growth="{:.0f}".format(eps3Growth)
if(len(EPSDF)>5):
    eps=EPSDF['EPS'].values
    eps5Growth=((eps[len(eps)-1]/eps[len(eps)-6])**(1/5)-1)
    #eps5Growth="{:.2f}".format(eps5Growth)
    #cols[1].text("EPS 5 Year % Growth: "+ str( eps5Growth)+"%")
else:
    eps5Growth=0
    #eps5Growth="{:.0f}".format(eps5Growth)
LatestDF=annualDF.iloc[-1:]
LatestDF["EPS 3Y Growth"]=eps3Growth
LatestDF["EPS 5Y Growth"]=eps5Growth
LatestDF=LatestDF[["EPS 3Y Growth", "EPS 5Y Growth", 'Faustmann Ratio', 'ROIC', 'ROE', 'PE', "PB"]]

LatestDF=LatestDF.style.format({"EPS 3Y Growth":'{:.2%}'})
LatestDF=LatestDF.format({"EPS 5Y Growth":'{:.2%}'})
LatestDF=LatestDF.format({"Faustmann Ratio":'{:.2f}'})
LatestDF=LatestDF.format({"ROIC":'{:.2%}'})
LatestDF=LatestDF.format({"ROE":'{:.2%}'})
LatestDF=LatestDF.format({"PE":'{:.2f}'})
LatestDF=LatestDF.format({"PB":'{:.2f}'})

cols[1].dataframe(data=LatestDF, height=100)
