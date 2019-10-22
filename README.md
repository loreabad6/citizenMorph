# Download citizenMorph attachments:

Based on [this repository](https://github.com/Esri/developer-support/tree/master/python/general-python/download-attachments)...

## Steps:
1. Open a Jupyter notebook and load the `DownloadAttachments.ipynb` file
2. Select if the attachments should be downloaded for the English or German survey
3. Run the script
4. (If necessary) when changes are performed to the sript, be sure to download it as a jupyter notebook and python script and save it to the WP5 folder (where the orginial file was loaded from)


Already downloaded data will ideally not be downloaded again.
Right now the attachments are stored in the citizenMorph project folder on WP5. 
The data is downloaded to the folders `ScriptDownloads_*`, which depends on the language selected.  In them there are two folders:
- `0-surveyPoint` which contains the overview picture, and
- `0-loop` which contains the photo series.

Each of these folders contain sub-folders named after the object-id of the collected data. Hence, the first submitted survey has `objectId = 1`, and its overview picture and photo series should be stored in sub-folder 1 for each parent folder. 
