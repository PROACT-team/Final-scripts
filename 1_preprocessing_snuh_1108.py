# -*- coding: utf-8 -*-
"""1_Preprocessing_snuh_1108.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1YgVpX8pq8D3AQauCMqa448hDyWxCehYK
"""

# Load packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from google.colab import drive
drive.mount('/content/drive')

# Read datasets needed
from google.colab import files 
uploaded = files.upload()

# import raw data
import io
static = pd.read_csv(io.BytesIO(uploaded['snuh_dx.csv']))
creatinine = pd.read_csv(io.BytesIO(uploaded['snuh_cr.csv']))
weight = pd.read_csv(io.BytesIO(uploaded['snuh_wt.csv']))
alsfrs_R_raw = pd.read_csv(io.BytesIO(uploaded['snuh_alsfrs.csv']))
fvc = pd.read_csv(io.BytesIO(uploaded['snuh_fvc_20211025.csv']))
gastro = pd.read_csv(io.BytesIO(uploaded['snuh_gastro.csv']))

"""# 1. Extracting feature variables

## 1-1. Static features

### (1) Age/Gender (Demographics)
"""

static.columns

static = static.drop(columns = ['Hosp_ID', 'Dx'])
static.columns = ['SubjectID', 'Gender', 'Age', 'Date_onset', 'Date_dx',
       'Date_enrollment', 'Onset_region']
static = static.sort_values(by=['SubjectID'], axis=0).reset_index().drop(columns='index')
static

sns.histplot(static['Age'])

static['Age'].describe() # min = 20, max = 84

# Convert 'Age' into ordered-categorical data (categorize in  5 years)
age_min = 15 

def cat_age(age, age_min):
  return (age - age_min) // 5

static['Age'] = static.apply(lambda x: cat_age(x['Age'], age_min), axis = 1)
sns.histplot(static['Age'])

# Female = 0, Male = 1
static = static.replace({'Gender':{"F":0, "M":1}})
static #228 data

"""### (2) diag_delta/onset_delta/diag_minus_onset/onset_site (ALS history)"""

# Calculate onset_delta, diag_delta, diag_minus_onset in months 
static['onset_delta'] = (pd.to_datetime(static['Date_onset'])- pd.to_datetime(static['Date_enrollment'])) / np.timedelta64(1,'D') * 12/365
static['diag_delta'] = (pd.to_datetime(static['Date_dx'])- pd.to_datetime(static['Date_enrollment'])) / np.timedelta64(1,'D') * 12/365
static['diag_minus_onset'] = static['diag_delta']-static['onset_delta'] #define 'diag_minus_onset' as time difference between onset and diagnosis

# Save Data_enrollment (for feature delata calculation in time-resolved feature) 
date_enroll = static[['SubjectID', 'Date_enrollment']]
static.drop(columns = ['Date_onset','Date_enrollment','Date_dx'], inplace = True)

# Bubar_onset = 1, non-Bulbar_onset = 0
static.rename(columns = {'Onset_region':'onset_site'}, inplace = True)
static = static.replace({'onset_site':{"LS":0, "B":1, "C":0, "BL":1}})

static #228 data

static[static['diag_minus_onset']<0]

static = static.query('diag_minus_onset >= 0')
static

"""## 1-2. Time-resolved features

### (0) Define function
"""

# Define function returning df with calculated feature delta for time-resolved feautures 
def cal_feature_delta(df, date_enroll):
  df1 = pd.merge(df, date_enroll)
  df1['feature_delta'] = (pd.to_datetime(df1['Date_visit'])- pd.to_datetime(df1['Date_enrollment'])) / np.timedelta64(1,'D') * 12/365
  df1 = df1.sort_values(by=['SubjectID', 'feature_delta'], axis=0).reset_index().drop(columns='index')
  df1.drop(columns = ['Date_visit','Date_enrollment'], inplace = True)
  return df1

# Define function drawing histplot of first, second delta of each SubjectID 
def hisplot_first_second_delta(df):
  df_delta = df[['SubjectID', 'feature_delta']]
  df1 = df_delta.groupby('SubjectID').nth(0)
  df1.columns = ['first delta'] 
  plt.figure(figsize=(15,5))
  plt.subplot(121)
  sns.histplot(df1)

  df2 = df_delta.groupby('SubjectID').nth(1)
  df2.columns = ['second delta'] 
  plt.subplot(122)
  sns.histplot(df2)

# Define function calculating mean
def cal_mean(df):
  df_mean = df.groupby('SubjectID').agg('mean')
  df_mean.reset_index(inplace=True) # reset 'SubjectiD' as column
  
  mean_df = pd.DataFrame(df_mean['SubjectID'])
  feature_list = list(df.drop(columns = ['SubjectID', 'feature_delta']).columns)

  for feature in feature_list:
    mean_df['mean_'+feature] = df_mean[feature]

  return mean_df

# Define function calculating slope
def cal_slope(df):
  df_first_last = df.groupby('SubjectID').agg(['first', 'last'])
  df_first_last.reset_index(inplace=True) # reset 'SubjectiD' as column
  df_first_last['interval'] = df_first_last[('feature_delta','last')] - df_first_last[('feature_delta','first')]
  df_first_last = df_first_last[df_first_last['interval']!=0] # exclude data that is observed only once

  slope_df = pd.DataFrame(df_first_last['SubjectID'])
  feature_list = list(df.drop(columns = ['SubjectID', 'feature_delta']).columns)

  for feature in feature_list:
    slope_df['slope_'+feature] = df_first_last.apply(lambda x: (x[(feature,'last')]-x[(feature, 'first')])/x[('interval','')] if x[('interval','')] >= 1.0 else np.nan, axis = 1)
    # data with time interval less than 1 month is regarded as missing data, otherwise calculate slope with data of (last, first) feature delta

  return slope_df

# Define function calculating for time-resolved features
def cal_time_resolved(df):
  # Filter first 3 month data
  df_3mo = df.query('(feature_delta <= 3.0) and (feature_delta >= 0)')

  # Calculate mean
  mean_df = cal_mean(df_3mo)

  # Calculate slope
  slope_df = cal_slope(df_3mo)
  
  # Merge mean & slope data
  df_summary =  mean_df.merge(slope_df, on = 'SubjectID', how='outer')

  return df_summary

"""### (1) alsfrs_r (total/3 dimension/q)"""

alsfrs_R_raw1 = alsfrs_R_raw.drop(columns = ['Hosp_ID', 'gastrostomy'])

# Add alsfrs-3dimension scores 
alsfrs_R_raw1['bulbar'] = alsfrs_R_raw1['Q1']+alsfrs_R_raw1['Q3']
alsfrs_R_raw1['motor'] = alsfrs_R_raw1['Q4']+alsfrs_R_raw1['Q5']+alsfrs_R_raw1['Q6']+alsfrs_R_raw1['Q7']+alsfrs_R_raw1['Q8']+alsfrs_R_raw1['Q9']
alsfrs_R_raw1['respiratory'] = alsfrs_R_raw1['Q10']+alsfrs_R_raw1['Q11']+alsfrs_R_raw1['Q12']

# Reset column name
alsfrs_R_raw1.columns = ['SubjectID', 'Date_visit', 'ALSFRS_R_Total', 'Q1_Speech',
       'Q2_Salivation', 'Q3_Swallowing', 'Q4_Handwriting', 'Q5_Cutting',
       'Q6_Dressing_and_Hygiene', 'Q7_Turning_in_Bed', 'Q8_Walking',
       'Q9_Climbing_Stairs', 'R1_Dyspnea', 'R2_Orthopnea',
       'R3_Respiratory_Insufficiency', 'bulbar', 'motor', 'respiratory']

# Calculate feature delta 
alsfrs_R_raw1 = cal_feature_delta(alsfrs_R_raw1, date_enroll) 

# Calculate summary
alsfrs_R_summary = cal_time_resolved(alsfrs_R_raw1)
alsfrs_R_summary #222 data

hisplot_first_second_delta(alsfrs_R_raw1)

"""### (2) FVC"""

fvc1 = fvc.drop(columns = 'Hosp_ID')

# Reset column name
fvc1.columns = ['SubjectID', 'Date_visit', 'fvc']

# Calculate feature delta 
fvc1 = cal_feature_delta(fvc1, date_enroll) 

# Calculate summary
fvc_summary = cal_time_resolved(fvc1)
fvc_summary # 107 data

hisplot_first_second_delta(fvc1)

"""### (3) Creatinine"""

creatinine

# Delete data with string value '#VALUE!' and convert dtype to float
creatinine = creatinine[creatinine['Cr'] != '#VALUE!']
creatinine['Cr'] = creatinine['Cr'].astype(float)
creatinine['Cr'] = creatinine['Cr'] * 100
creatinine # 3 deleted

creatinine1 = creatinine.drop(columns = 'Hosp_ID')

# Reset column name
creatinine1.columns = ['SubjectID', 'Date_visit', 'Creatinine']

# Calculate feature delta 
creatinine1 = cal_feature_delta(creatinine1, date_enroll) 

# Calculate summary
creatinine_summary = cal_time_resolved(creatinine1)
creatinine_summary # 129 data

hisplot_first_second_delta(creatinine1)

"""### (4) Weight"""

weight1 = weight.drop(columns = 'Hosp_ID')

# Reset column name
weight1.columns = ['SubjectID', 'Date_visit', 'weight']

# Calculate feature delta 
weight1 = cal_feature_delta(weight1, date_enroll) 

# Calculate summary
weight_summary = cal_time_resolved(weight1)
weight_summary # 215 data

hisplot_first_second_delta(weight1)

"""## 1-3. Merging all features"""

features_without_alsfrs = pd.DataFrame(columns=['SubjectID'])
feature_list = [static, fvc_summary, creatinine_summary, weight_summary]
for i in feature_list :
    df = i
    features_without_alsfrs = features_without_alsfrs.merge(df, on='SubjectID', how='outer')
features_without_alsfrs.query('diag_minus_onset >=0', inplace=True) 
features_without_alsfrs #228 data -> 224 data

# features_with_alsfrs_R
features_with_alsfrs_R = features_without_alsfrs.merge(alsfrs_R_summary, on='SubjectID', how = 'inner')
features_with_alsfrs_R #222 data->218 data

"""## 1-4. Check NaN proportion

### (1) Check NaN proportion in features for train/test data
"""

def report_nulls(df):
    '''
    Show a fast report of the DF.
    '''
    rows = df.shape[0]
    columns = df.shape[1]
    null_cols = 0
    list_of_nulls_cols = []
    list_of_nulls_cols_pcn = []
    list_of_nulls_cols_over60 = []
    for col in list(df.columns):
        null_values_rows = df[col].isnull().sum()
        null_rows_pcn = round(((null_values_rows)/rows)*100, 2)
        col_type = df[col].dtype
        if null_values_rows > 0:
            print("The column {} has {} null values. It is {}% of total rows.".format(col, null_values_rows, null_rows_pcn))
            print("The column {} is of type {}.\n".format(col, col_type))
            null_cols += 1
            list_of_nulls_cols.append(col)
            list_of_nulls_cols_pcn.append(null_rows_pcn)
            if null_rows_pcn > 60:
                list_of_nulls_cols_over60.append(col)
    null_cols_pcn = round((null_cols/columns)*100, 2)
    print("The DataFrame has {} columns with null values. It is {}% of total columns.".format(null_cols, null_cols_pcn))
    plt.plot(list_of_nulls_cols, list_of_nulls_cols_pcn)
    return list_of_nulls_cols_over60

report_nulls(features_with_alsfrs_R) # {onset_delta / diag_delta / diag_minus_onset}-> 54.77%  {onset_site}-> 54.78%  {mean_alsfrs_q} -> 33.93%  {slope_alsfrs_q} -> 42.55%  of Total 9848 data

features_with_alsfrs_R.isnull().sum()

#Create df for showing NaN pattern
feature_nan_pattern1 = features_with_alsfrs_R[['Age', 'Gender', 'diag_delta', 'onset_delta', 'onset_site',
       'diag_minus_onset', 'mean_Q1_Speech','slope_Q1_Speech', 'mean_fvc', 'slope_fvc', 'mean_Creatinine',
       'slope_Creatinine', 'mean_weight','slope_weight']]
feature_nan_pattern1.columns = ['Age', 'Gender', 'diag_delta', 'onset_delta', 'onset_site',
       'diag_minus_onset', 'mean_ALSFRS','slope_ALSFRS', 'mean_fvc', 'slope_fvc', 'mean_Creatinine',
       'slope_Creatinine', 'mean_weight','slope_weight']

# Nullity matrix
import missingno as msno
msno.matrix(feature_nan_pattern1)

# Exclude 'slope_fvc' in feature list because it's NaN proportion is over 50% & it can be replaced by alsfrs respiratory score
features_snuh = features_with_alsfrs_R.drop(columns = ['slope_fvc', 'slope_Creatinine'])

features_snuh.to_csv('/content/drive/MyDrive/Colab Notebooks/????????? ??????????????????/PACTALS/1108featurewithnans_snuh.csv')

"""## 1-5. Train/Test split & Data imputation **This part is unchanged from 1016 preprocess!

### (1) Data for train/test
"""

# Split Train/Test in 8:2
from sklearn.model_selection import train_test_split
features_for_train, features_for_test = train_test_split(features_for_train_test, train_size=0.8, test_size=0.2, random_state=11)

from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn import linear_model

# Train data Imputation with IterativeImputer
X_train = features_for_train
columns = X_train.columns
imputer = IterativeImputer(sample_posterior = True, random_state=11)
ar = imputer.fit_transform(X_train)
X_train_imputed = pd.DataFrame(ar, columns = columns)
X_train_imputed

# Test data Imputation with IterativeImputer
X_test = features_for_test
columns = X_test.columns
imputer = IterativeImputer(sample_posterior = True, random_state=11)
ar = imputer.fit_transform(X_test)
X_test_imputed = pd.DataFrame(ar, columns = columns)
X_test_imputed

X_train_imputed.to_csv('/content/drive/MyDrive/Colab Notebooks/data/1016/1016_X_train_imputed.csv')

X_test_imputed.to_csv('/content/drive/MyDrive/Colab Notebooks/data/1016/1016_X_test_imputed.csv')

"""### (2) Data for test2"""

# Test2 data Imputation with IterativeImputer
X_test2 = features_for_test2
columns = X_test2.columns
imputer = IterativeImputer(sample_posterior = True, random_state=11)
ar = imputer.fit_transform(X_test2)
X_test2_imputed = pd.DataFrame(ar, columns = columns)
X_test2_imputed

X_test2_imputed.to_csv('/content/drive/MyDrive/Colab Notebooks/data/1016/1016_X_test2_imputed.csv')

"""# 2. Extracting target variables

## 2-1. Optimal target (Q3 becoming 1.0)
"""

# FVC ?????? ??????

"""### (1) Subtracting [initial Q3 score <=1 ]"""

alsfrs_Sw = alsfrs_R_raw1[['SubjectID', 'Q3_Swallowing', 'feature_delta']]
alsfrs_Sw = alsfrs_Sw[alsfrs_Sw['feature_delta']>=0]
alsfrs_Sw

alsfrs_Sw_grouped = alsfrs_Sw.groupby('SubjectID').agg(['first', 'last'])
alsfrs_Sw_grouped = alsfrs_Sw_grouped.reset_index()
alsfrs_Sw_grouped = alsfrs_Sw_grouped[alsfrs_Sw_grouped[('feature_delta', 'last')]!= alsfrs_Sw_grouped[('feature_delta', 'first')]] # more than 2 observation needed (score chagnes from above 2 to 2)
alsfrs_filtered_extent = list(alsfrs_Sw_grouped[alsfrs_Sw_grouped[('Q3_Swallowing','first')]>1.0].reset_index()['SubjectID']) # initial ALSFRS Q3 > 1

# Subtract [first ALSFRS Q3 <=1.0] & [ALSFRS Q3 observed only once]
alsfrs_Sw_filtered = alsfrs_Sw.query("SubjectID == {0}".format(alsfrs_filtered_extent))
alsfrs_Sw_filtered

"""### (2) Time of [Q3 score == 1.0]"""

# Find the first time of [ALSFRS_Q3 <= 1.0]
Optimal_event = alsfrs_Sw_filtered[alsfrs_Sw_filtered['Q3_Swallowing']<=1].groupby('SubjectID').agg(['first']).reset_index()

# Coding [ALSFRS-Q3<=1] event as '1'
Optimal_event_1 = Optimal_event[[(    'SubjectID',      ''), ('feature_delta', 'first')]]
Optimal_event_1.columns = ['SubjectID', 'time_opt']

Optimal_event_1_sublist = list(Optimal_event['SubjectID'])

Optimal_event_1['status_opt'] = 1
print("There are",len(Optimal_event_1['SubjectID'].unique()), "subjects whose status_opt = 1")

# Otherwise '0'
Optimal_event_0 = alsfrs_Sw_filtered[~alsfrs_Sw_filtered['SubjectID'].isin(Optimal_event_1_sublist)]
Optimal_event_0 = Optimal_event_0.groupby('SubjectID').agg(['last']).reset_index().drop(columns=('Q3_Swallowing', 'last'))
Optimal_event_0.columns = ['SubjectID', 'time_opt']
Optimal_event_0['status_opt'] = 0
print("There are",len(Optimal_event_0['SubjectID'].unique()), "subjects whose status_opt = 0")
 # There are 29 subjects whose status_opt = 1
 # There are 196 subjects whose status_opt = 0

alsfrs_Sw_coded = pd.concat([Optimal_event_1, Optimal_event_0]).sort_values(by='SubjectID', axis=0)
alsfrs_Sw_coded = alsfrs_Sw_coded.reset_index()
alsfrs_Sw_coded.drop(columns='index', inplace=True)

Optimal_Gas = alsfrs_Sw_coded.copy()
sub_list = list(Optimal_Gas['SubjectID'])
Optimal_Gas #225 data

Optimal_Gas.to_csv('/content/drive/MyDrive/Colab Notebooks/data/1101/1101_optimal_target_snuh.csv')

# Be aware that 'time_opt' is month scaled

"""## 2-2. Real target

### (0) Time of gastrostomy event
"""

gastro1 = gastro.drop(columns = ['Hosp_ID', 'Event'])

# Reset column name
gastro1.columns = ['SubjectID', 'Date_visit']

# Calculate feature delta 
gastro1 = cal_feature_delta(gastro1, date_enroll) 

gastro1.columns = ['SubjectID', 'time_real']
gastro1['status_real'] = 1
gastro1

gastro1.to_csv('/content/drive/MyDrive/Colab Notebooks/data/1101/1101_real_target_snuh_status1.csv')

"""### (1) Time of [ALSFRS Q5_b != NaN] **This part is unchanged from 1016 preprocess!"""

gastro = alsfrs_raw[['SubjectID', 'Gastrostomy', 'feature_delta']].sort_values(by=['SubjectID', 'feature_delta'], axis=0).reset_index().drop(columns='index')
gastro.replace({'Gastrostomy':{False:np.nan}}, inplace=True)
gastro

gastro.isnull().sum()

# Check censored data
def checking_censored(x):
  
  if x.isnull().sum() == 0:
    return "Left censored"
  elif x.notnull().sum() == 0:
    return "Right censored"
  else:
    return "Normal"

aggs_by_col = {'Gastrostomy': [checking_censored], 'feature_delta': ['last']}
gastro_a = gastro.groupby('SubjectID', as_index=False).agg(aggs_by_col)
gastro_a

#Subtract Left censored data

gastro_a.columns = ['SubjectID', 'checking_censored', 'last_feature_delta']
gastro_a = gastro_a[gastro_a['checking_censored'] != 'Left censored']
full_extent = list(gastro_a['SubjectID'])
Right_censored_extent = list(gastro_a[gastro_a['checking_censored'] == 'Right censored']['SubjectID'])
Normal_extent = list(gastro_a[gastro_a['checking_censored'] == 'Normal']['SubjectID'])

print("Total number is " + str(len(full_extent))) # Total number is 3515
print("There are " + str(len(Right_censored_extent)) + " right censored data") # There are 2700 right censored data
print("There are " + str(len(Normal_extent)) + " normal data") # There are 815 normal data

# Create gastro_event_0
gastro_event_0 = gastro_a[gastro_a['checking_censored'] == 'Right censored']
gastro_event_0 = gastro_event_0.replace({'checking_censored':{'Right censored': 0}})
gastro_event_0.columns = ['SubjectID', 'status', 'time']
gastro_event_0 = gastro_event_0[gastro_event_0['time'] != 0] # time != 0 
gastro_event_0 #2686 data

# Create gastro_event_1
gastro_b = gastro.copy()
gastro_b.query("SubjectID == {0}".format(Normal_extent), inplace=True)
gastro_b = gastro_b.dropna(axis=0)
gastro_event_1 = pd.DataFrame(gastro_b.groupby('SubjectID')['feature_delta'].agg('first')).reset_index()
gastro_event_1.columns = ['SubjectID', 'time']
gastro_event_1['status'] = 1
gastro_event_1 = gastro_event_1[gastro_event_1['time'] != 0] # time != 0 
gastro_event_1 #597 data

gastro_fin = pd.concat([gastro_event_1, gastro_event_0]).sort_values(by='SubjectID', axis=0)
gastro_fin = gastro_fin.reset_index().drop(columns = 'index')
gastro_fin.columns = ['SubjectID', 'time_real', 'status_real']
Real_Gas = gastro_fin.copy()
Real_Gas # 3283 data

Real_Gas.to_csv('/content/drive/MyDrive/Colab Notebooks/data/1016/1016_real_target.csv')

"""## 2-3. Comparing proportion of censored data in Optimal gas/ Real gas / Survival"""

event_distribution = pd.DataFrame(Optimal_Gas[['status_opt']].value_counts()).reset_index()
event_distribution.columns = ['status_o', 'count']
event_distribution['status_o'] = event_distribution['status_o'].astype('bool')
event_distribution = event_distribution.replace({'status_o': {False:'0 (censored)', True:'1 (occured)'}})
print(event_distribution)

event_distribution_2 = pd.DataFrame(surv[['status']].value_counts()).reset_index()
event_distribution_2.columns = ['status_surv', 'count']
event_distribution_2['status_surv'] = event_distribution_2['status_surv'].astype('bool')
event_distribution_2 = event_distribution_2.replace({'status_surv': {False:'0 (censored)', True:'1 (occured)'}})
print(event_distribution_2)

event_distribution_3 = pd.DataFrame(Real_Gas[['status_real']].value_counts()).reset_index()
event_distribution_3.columns = ['status_real', 'count']
event_distribution_3['status_real'] = event_distribution_3['status_real'].astype('bool')
event_distribution_3 = event_distribution_3.replace({'status_real': {False:'0 (censored)', True:'1 (occured)'}})
print(event_distribution_3)

A_1 = event_distribution.iloc[0]['count']
B_1 = event_distribution.iloc[1]['count']
per_0 = str(round((A_1/(A_1+B_1))*100,2))+"%"
per_1 = str(round((B_1/(A_1+B_1))*100,2))+'%'

A = event_distribution_2.iloc[0]['count']
B = event_distribution_2.iloc[1]['count']
perc_0 = str(round((A/(A+B))*100,2))+"%"
perc_1 = str(round((B/(A+B))*100,2))+'%'

A_2 = event_distribution_3.iloc[0]['count']
B_2 = event_distribution_3.iloc[1]['count']
pe_0 = str(round((A_2/(A_2+B_2))*100,2))+"%"
pe_1 = str(round((B_2/(A_2+B_2))*100,2))+'%'


#        status_o  count
# 0  0 (censored)   3000
# 1   1 (occured)    796
#     status_surv  count
# 0  0 (censored)   6005
# 1   1 (occured)   3075
#     status_real  count
# 0  0 (censored)   2686
# 1   1 (occured)    597

plt.figure(figsize=(15, 6))

plt.subplot(131)
plt.bar(event_distribution['status_o'], height=event_distribution['count'], color=['green', 'orange'])
plt.ylim([0,7000])
plt.title('Event Distribution (Optimal Gastrostomy)')
plt.text(-0.12,1600,per_0)
plt.text(0.85,700,per_1)

plt.subplot(132)
plt.bar(event_distribution_2['status_surv'], height=event_distribution_2['count'], color=['green', 'orange'])
plt.ylim([0,7000])
plt.title('Event Distribution (Survival)')
plt.text(-0.15,1500,perc_0)
plt.text(0.85,550,perc_1)

plt.subplot(133)
plt.bar(event_distribution_3['status_real'], height=event_distribution_3['count'], color=['green', 'orange'])
plt.ylim([0,7000])
plt.title('Event Distribution (Real Gastrostomy)')
plt.text(-0.15,1500,pe_0)
plt.text(0.85,300,pe_1)

plt.show()

# ??????????????? ???????????? ???????????? censored data??? ????????? ??????????????? ?????? ?????????.