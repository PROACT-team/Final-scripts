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

**Goal** : 
build a model to predict the time to dietary consistency change

**Features** :    
- Age(ordered categorical data by 5yrs), Gender, onset_site(Bulbar/Non-bulbar), onset_delta(months), diag_delta(months), diag_minus_onset(meta feature, months) 
- ALSFRS (total score, item scores), FVC, Creatinine, Weight     
- calculate mean values over the first 3 months for ALSFRS, FVC, Creatinine     
- calculate slope values over the first 3 months for the time-resolved features (ALSFRS/FVC/Creatinine/Weight, per month)            
- exclude cases with missing values in onset_delta because of a large proportion of missing values (same cases with missing values in diag_delta, onset_site)    

**Stepwise selection** : 
- Age, onset_delta, mean_FVC, ALSFRS_total_slope, mean_Q1_Speech, mean_Q2_Salivation, mean_Q3_Swallowing, mean_Q7_Turning_in_Bed, slope_Q3_Swallowing, slope_Q6_Dressing_and_Hygiene, Creatinine_slope, weight_slope
- Due to high multicollinearity, meta feature 'mean_Q1_2_3_mouth' was added and 'mean_Q1_Speech'/'mean_Q2_Salivation'/'mean_Q3_Swallowing' were removed

**Algorithm** :          
- Accelerated failure time (parametric)
- Cox proportional hazard model (semi-parametric)
- Random survival forests (machine-learning)

**Results** :       
- Demonstrations; Printing prediction curve on test set
![그림1](https://user-images.githubusercontent.com/78291206/133879890-4ac2c178-b60e-4212-a863-67676fdf6973.png) 
     
     
- Evaluating model performance; C-index in Repeated 5-fold cross validation
![image](https://user-images.githubusercontent.com/78291206/133880313-392f1e65-8574-4328-9966-d4c11d8cb4de.png)    
models show C-index around 0.84


- Group Stratification
![그림4](https://user-images.githubusercontent.com/78291206/133880998-375964b4-c582-4871-9f39-cf74854e0516.png)
![image](https://user-images.githubusercontent.com/78291206/133881471-06ed8067-f25c-4790-9ebf-0460cedc1ed7.png)
