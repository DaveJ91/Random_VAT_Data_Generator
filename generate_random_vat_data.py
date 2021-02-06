from random import random,gauss, randint
import random
import string
import numpy as np
from faker import Faker
import pandas as pd
import datetime
import calendar

faker=Faker()

country_iso_codes=['IE', 'GB', 'ES', 'IT', 'PT', 'PL', 'FR', 'DE', 'NL', 'CZ', 'BE', 'AT', 'CH', 'SE', 'FI']

domestic_input_tax_codes = {
    'I1':(0.23, '23% Input VAT'),
    'I2':(0.15, '16% Input VAT'),
    'I3': (0.5, '5% Input VAT'),
    'I4': (0.0, '0% Input VAT')
}

domestic_output_tax_codes = {
    'O1': (.23, '23% Output VAT'),
    'O2': (.15, '15% Output VAT'),
    'O3': (.5, '5% Output VAT'),
    'O4': (0, '0% Output VAT')
}

ic_tax_codes = {
    'F1': (0, 'IC_Sale'),
    'F9': (0, 'IC_Purchase')
}

# generate a VAT ID in format IE12345678A
def generate_vat_id(country_iso):
    number=country_iso
    for i in range(8):
        number += str(randint(0,9))
    number += random.choice(string.ascii_letters).capitalize()
    return number

# Generate transaction (date in datetime object format)
def generate_transaction(trans_type,country_iso, trans_value_mean, trans_value_std, start, end):
    Trans_Date = faker.date_time_between(start_date=start, end_date=end)
    if trans_type == 'domestic_sale' or 'domestic_purchase':
        country_iso_vat = country_iso
    else:
        country_iso_codes.remove(country_iso)
        country_iso_vat = random.choices(country_iso_codes)[0]
    VAT_ID = generate_vat_id(country_iso_vat)
    Company = faker.company()
    Tax_Base_Amount= round(abs(gauss(trans_value_mean,trans_value_std)),2)
    
    
    if trans_type == 'domestic_sale':
        tax_codes = domestic_output_tax_codes
        Tax_Code = random.choices(list(tax_codes.keys()), weights=(60,20,10,10))[0]
    if trans_type == 'domestic_purchase':
        tax_codes = domestic_input_tax_codes
        Tax_Code = random.choices(list(tax_codes.keys()), weights=(60,20,10,10))[0]
    if trans_type == 'ic_sale':
        Tax_Code = 'F1'
    if trans_type == 'ic_purchase':
        Tax_Code = 'F9'
    if trans_type == 'domestic_sale' or trans_type == 'domestic_purchase':
        Tax_Rate = tax_codes[Tax_Code][0]
    else:
        Tax_Rate = 0.0
        
    Tax = Tax_Base_Amount * Tax_Rate
    return[Trans_Date,VAT_ID, Company, Tax_Base_Amount, Tax_Code, Tax_Rate, Tax]

# Generate monthy transactions
def generate_monthly_transactions(trans_type,country_iso,trans_value_mean, trans_value_std,monthly_vol_mean, monthly_vol_std,month,year):
    start = datetime.date(year,month,1)
    end = datetime.date(year, month, calendar.monthrange(year, month)[1])
    monthly_transactions_volume = int(abs(gauss(monthly_vol_mean,monthly_vol_std)))
    transactions_dict = {}
    
    for i in range(monthly_transactions_volume):
        transactions_dict[i] = generate_transaction(trans_type,country_iso,trans_value_mean, trans_value_std,start, end)
        
    transactions_df = pd.DataFrame.from_dict(transactions_dict, orient='index')
    pd.options.display.float_format = '€{:,.2f}'.format

    transactions_df.columns = ['trans_date', 'vat_id', 'company', 'tax_base', 'tax_code', 'tax_rate', 'tax']
    
    return transactions_df

        
# Generate annual domestic transactions (done by month so there's more variance each month)
def generate_annual_transactions(trans_type,country_iso,trans_value_mean, trans_value_std,monthly_vol_mean, monthly_vol_std,year):
    df = generate_monthly_transactions(trans_type,country_iso,trans_value_mean, trans_value_std ,monthly_vol_mean, monthly_vol_std,1,year)
    for i in range(2,13):
        new_month = generate_monthly_transactions(trans_type,country_iso,trans_value_mean, trans_value_std,monthly_vol_mean, monthly_vol_std,i,year)
        df = pd.concat([df,new_month])
        df = df.sort_values(by='trans_date')
        print(f"Month {i} completed")
    print(f"{trans_type} completed")
    return df

def generate_sample_dataset():
    domestic_sales = generate_annual_transactions('domestic_sale',"GB",1000,200,5000,300,2019)
    domestic_purchases = generate_annual_transactions('domestic_purchase',"GB",300,100,3000,300,2019)
    ic_sales = generate_annual_transactions('ic_sale',"GB",300,100,3000,300,2019)
    ic_purchases = generate_annual_transactions('ic_purchase',"GB",300,100,3000,300,2019)

    df = pd.concat([domestic_sales,domestic_purchases,ic_sales,ic_purchases])
    df = df.drop(['tax_rate'], axis=1)

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    df['Month']  = df.trans_date.dt.month
    df['Month'] = df['Month'].apply(lambda x: calendar.month_abbr[x])
    df['Month'] = pd.Categorical(df['Month'], categories=months, ordered=True)


    df['Year'] = df.trans_date.dt.year
    df['Year'] = df.Year.astype(str)

    return df