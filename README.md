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

# Gastrostomy prediction

**Goal** : 
build a model to predict the time to dietary consistency change

**Select features according to previous studies** :    
- Age(ordered categorical data by 5yrs), Gender, onset_site(Bulbar/Non-bulbar), onset_delta(months), diag_delta(months), diag_minus_onset(months) 
- ALSFRS (total score, item scores), FVC, Creatinine, Weight
- References https://www.tandfonline.com/doi/abs/10.3109/17482960802566824?journalCode=iafd19, https://www.nature.com/articles/nbt.3051
- calculate mean values over the first 3 months for ALSFRS, FVC, Creatinine     
- calculate slope values over the first 3 months for the time-resolved features (ALSFRS/FVC/Creatinine/Weight, per month)            
- exclude cases with missing values in onset_delta because of a large proportion of missing values (same cases with missing values in diag_delta, diag_minus_onset, 99.9% similar cases in onset_site)
- exclude cases with missing values in mean_ALSFRS_q beacause all 10 sub scores had same large proportion of missing values 

**Imputation** :
- Missing data nullity matrix
<img src="https://user-images.githubusercontent.com/79128639/135747347-39fef080-14d1-43df-9a00-a46ef2b6401d.PNG" width="60%">


- Missing data nullity matrix after excluding cases with missing values in onset_delta, mean_ALSFRS_Q
<img src="https://user-images.githubusercontent.com/79128639/135713545-8b813052-d727-4eec-8f13-c73ee36f45b9.png" width="60%">

- Missing data proportion circle graph
<img src="https://user-images.githubusercontent.com/79128639/135709837-3121e213-d58c-4f83-a766-ac52259289cc.png" width="60%">

- Imputation using iterativeImputer in scikit-learn

**Stepwise forward selection & Create meta-feature** : 
- Age, onset_delta, mean_FVC, ALSFRS_total_slope, mean_Q1_Speech, mean_Q2_Salivation, mean_Q3_Swallowing, mean_Q7_Turning_in_Bed, slope_Q3_Swallowing, slope_Q6_Dressing_and_Hygiene, Creatinine_slope, weight_slope was selected through Stepwise forward selection
- Due to high multicollinearity, meta feature 'mean_Q1_2_3_mouth' was added and 'mean_Q1_Speech'/'mean_Q2_Salivation'/'mean_Q3_Swallowing' were removed. 
- Due to high multicollinearity of ALSFRS_total_slope/slope_Q6_Dressing_and_Hygiene, 'slope_Q6_Dressing_and_Hygiene' was removed.

**Algorithm** :          
- Accelerated failure time (parametric)
- Cox proportional hazard model (semi-parametric)
- Random survival forests (machine-learning)

**Results** :       
- Demonstrations; Printing prediction curve on test set
![image](https://user-images.githubusercontent.com/79128639/135747819-7e608aac-27b5-4425-a372-32389f0b5bb6.png)     
     
- Evaluating model performance; C-index in Repeated 5-fold cross validation
![C-index](https://user-images.githubusercontent.com/79128639/135747430-93d02c66-7ffe-4feb-8def-ffd85ec411fe.PNG)
models show C-index around 0.84


- Group Stratification
![group stratification](https://user-images.githubusercontent.com/79128639/135747846-858af067-a9e7-4fb8-89a1-06ed7d239582.PNG)
Prediction matches well with Kaplan Meier in Rapid and Intermediate group but not much in slow group

![group stratification2](https://user-images.githubusercontent.com/79128639/135747505-73614925-48de-4fbe-a23f-c1ee73470925.PNG)
Thick colored lines are interquartile range between 25 to 75 % probability time to event. And the dots in the middle are the 50% probability times    

# Extra analysis; Survival impact of delayed gastrostomy    
- Using the cox model made, the predicted median time to gastrostomy('_Predicted gastrostomy_') for individual patients was obtained.  
- Time-diffenrence defined as _'Actual gastrostomy time' minus 'Predicted gastrostomy'_   
- Patient data with status = 1(occurred) on the actual gastrostomy were only used.   
- Patients whose survival report was cut earlier than the actual gastrostomy or the predicted gastrostomy were excluded.               
     
<img src="https://user-images.githubusercontent.com/79128639/135748533-36c2b299-0c6e-4286-b844-a97bdcdbb367.png" width="60%">          
Data with bigger time difference, with its actual gastrostomy more delayed from predicted gastrostomy, tends to have worse survival              
     
     
<img src="https://user-images.githubusercontent.com/79128639/135748495-9a1eae6f-9c8f-4940-8561-21985fe05758.png" width="60%">
Based on time difference distribution, patients were categorized into Early/Medium/Late classes, by 25% and 75% percentile criterion        
     
     
<img src="https://user-images.githubusercontent.com/79128639/135748560-fe7ade4c-371b-4023-8517-3a968dfc0612.png" width="60%">
Early group showed better survival than the Late group. logrank test result (p-value=0.001)       
     
Also the plot above suggests a time-dependent effect of time difference         
