# Goals
- To develop individualized prediction models for gastrostomy in ALS patients

**Target Variables**
- Time to dietary consistency change (ALSFRS_Q3_Swallowing score dropping to 2.0, among patients whose initial FVC is more than 50%)

**Python scripts**  
https://github.com/PROACT-team/Final-scripts

**data files** 
https://drive.google.com/drive/u/0/folders/1Axu5zX-2oADEc2cxG-GbxA1I0rWkFrzc

# Preparations  

## Data source

PRO-ACT database (raw data)
https://nctu.partners.org/proact  

Preprocessed csv files
https://www.dropbox.com/sh/3lmi5ii3sgyi7o3/AACeVLTGtSDXSKIaX6P7Hxj2a?dl=0
(local) /Users/hong/Dropbox/ALSmaster/PROACT  

## Scripts   
**1_preprocessing.py**
Extracting features and target variables & Data imputation

**2_feature_selection.py**  
Stepwise selection & Checking multicollinearity
     
**3_fitting_and_evaluation.py**     
Prediction & Testing

**4_effect_of_delayed_gastrostomy.py** 
to investigate the relationship between time-difference and survival
time-diffenrence defined as _'Actual gastrostomy time' minus 'Predicted gastrostomy'_

# Imputation
## Missing data: proportion and pattern  
Imputation using iterativeImputer in scikit-learn

# Gastrostomy prediction

Goal: build a model to predict the time to dietary consistency change

Features:    
- Age(ordered categorical data by 5yrs), Gender, onset_site(Bulbar/Non-bulbar), onset_delta(months), diag_delta(months), diag_minus_onset(meta feature, months)
- ALSFRS (total score, item scores), FVC, Creatinine, Weight
- calculate mean values over the first 3 months for ALSFRS, FVC, Creatinine
- calculate slope values over the first 3 months for the time-resolved features (ALSFRS/FVC/Creatinine/Weight, points per month)  
- ALSFRS bulbar dimension score did not include Q2_salivation because of the symptomatic treatments available           
- exclude cases with missing values in onset_delta because of a large proportion of missing values (same cases with missing values in diag_delta, onset_site)    

Stepwise selection: 

Algorithm: Accelerated failure time(parametric), cox proportional hazard model(semi-parametric), random survival forests(machine-learning)

Results:  
Correlation plot between observed vs. predicted slope values    
![scatter_plot_slope_obs_pred](/images/cor_lm_rf.png)     

Comparisons of model performance: MAE, RMSE, Rsquared
![model_comparison](/images/model_comparisons.png)   

found no significance in paired t-test w/ bonferroni correction  
but there was a significant difference in Rsquared in raw p-value
