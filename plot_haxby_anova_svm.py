"""
Decoding with ANOVA + SVM: face vs house in the Haxby dataset
===============================================================
This example does a simple but efficient decoding on the Haxby dataset:
using a feature selection, followed by an SVM.
"""

#############################################################################
# Retrieve the files of the Haxby dataset
# ----------------------------------------
from nilearn import datasets

# By default the files of the Haxby dataset

haxby_dataset =  datasets.fetch_haxby()

#Print the basic information on the dataset
print ('Mask nifti image(3D) is located at : %s' % haxby_dataset.mask)
print ('Function nifti image(4D) is located at : %s' % haxby_dataset.func[0])

###############################################################################
# Load the behavioral data
#----------------------------
import numpy as np
# Load target information as string and give a numerical identifier to each
behavioral = np.recfromcsv(haxby_dataset.session_target[0],delimiter = "")
conditions = behavioral['labels']

# Restrict the analysis the faces and places
condition_mask = np.logical_or(conditions ==b'face',conditions ==b'house')
conditions =  conditions[condition_mask]

# We now have 2 conditions
print (np.unique(conditions))
session = behavioral[condition_mask]

print(session)

#############################################################################
# Prepare the fMRI data :smooth and apply the mask
#-----------------------------------------------
from nilearn.input_data import NiftiMasker
mask_filename = haxby_dataset.mask

# For decoding, Standardizing is often very important
# Note that we are also smoothing the data
masker = NiftiMasker(mask_img=mask_filename, smoothing_fwhm=4,
                     standardize=True,memory='nilearn_cache', memory_level=1)
func_filename = haxby_dataset.func[0]



X = masker.fit_transform(func_filename)

# Apply our condition_mask
X = X[condition_mask]

#decoder
#------------------------------
# Define the prediction function to be used
# Here we use a Support Vector Classification, with a linear kernel
from sklearn.svm import SVC
svc = SVC(kernel='linear')

# Define the dimension reduction to be used
# Here we use a classical univariate feature selection based on F-test
# namely Anova, we doing the full brain analysis, it is better to use
# SelectPercentile, keep 5% of voxels
# (Because it is independent of the resolution of the data)
from sklearn.feature_selection import SelectPercentile, f_classif
feature_selection = SelectPercentile(f_classif, percentile = 5)

# We have our classifier (SVC),our feature selection (SelectPercentile),and now
# We can plug them together in a *pipeline* that performs the two operations
# Successively
from sklearn.pipeline import Pipeline
anova_svc = Pipeline([('anova',feature_selection),('svc',svc)])

################################################################################
# Fit the decoder and predict
#----------------------------
anova_svc.fit(X,conditions)
y_pred = anova_svc.predict(X)

##################################################################################
# Obtain prediction scores via cross validation
#----------------------------------------------
from sklearn.cross_validation import LeaveOneLabelOut, cross_val_score

# Define the cross-validation scheme used for validation
# Here we use a LeaveOneLabelOut cross-validation on the session label
# Which corresponds to a leave-one-session-out

cv =  LeaveOneLabelOut(session)

# Computer the prediction accuracy for the different folds(i.e. session)
cv_score = cross_val_score(anova_svc,X,conditions,cv = cv)
print(cv_score)

# Return the corresponding mean prediction accuracy
classification_accuracy = cv_score.mean()

# Print the results
print ("classification accuracy: %.4f/Chance level :%f" %
       (classification_accuracy,1./len(np.unique(conditions))))

# classification accuracy :0.70370 / Chance level : 0.5000

###################################################################################
# Visualize the results
#-----------------------
# Look at the SVC's discrimination weights
coef = svc.coef_
# Reverse feature selection
coef = feature_selection.inverse_transform(coef)
# Reverse masking
weight_img = masker.inverse_transform(coef)

# Use the mean image as a background to avoid relying on anatomical data
from nilearn import image
mean_img = image.mean_img(func_filename)

# Create the figure
from nilearn.plotting import plot_stat_map,show
plot_stat_map(weight_img,mean_img,title='SVM weight')

# Save the results as NIfti file may also be important
weight_img.to_filename('haxby_face_vs_house.nii')

show()