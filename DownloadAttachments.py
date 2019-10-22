
# coding: utf-8

# In[ ]:


# Version 1.2

import logging, os, re, datetime, json
from IPython.display import display
from arcgis.gis import GIS

''' ********************** SCRIPT CONFIGURATION START ********************** '''
#Define working directory
path = r'\\shares\sfs_0165_1\ZGIS\RESEARCH\02_PROJECTS\03_Para_26\TCS00047_citizenMorph\04_Work\WP5\Export_files_CM\citizenMorph'
os.chdir(path)

#Get images from German (DE) or English (EN) survey?
language = 'EN'

#What is the ID of the Feature Layer you want to download attachments from?
#Where do you want your attachments stored?
if language == 'DE':
    FeatureLayerId = '97a5a105d3b546c78a94e2d85bbce834'
    SaveAttachmentsTo = '../ScriptDownloads_DE'
else:
    FeatureLayerId = 'cf4004ce88cd4061bf91d9f0456ddfec'
    SaveAttachmentsTo = '../ScriptDownloads_EN'

SaveLogsTo = 'Logging'

#What are your ArcGIS Enterprise/ArcGIS Online credentials? This is case sensitive.
with open('credentials.json') as f:
    data = json.load(f)
    PortalUserName = data['username']
    PortalPassword = data['password']
    
PortalUrl = 'https://zgis.maps.arcgis.com'

#How do you want your attachments stored? Options are GroupedFolder and IndividualFolder
#GroupedFolder - Attachments from every feature in each layer is stored in the same folder - attachments are renamed in the format OBJECTID-ATTACHMENTID-OriginalFileName
#IndividualFolder - A new folder is created for each OBJECTID, and associated attachments are stored in that folder - attachments are renamed in the format ATTACHMENTID-OriginalFileName
AttachmentStorage = 'IndividualFolder'

#Set to False if ArcGIS Enterprise cert is not valid
PortalCertVerification = True

#Setup logging - levels are DEBUG,INFO,WARNING,ERROR,CRITICAL
logging.basicConfig(level=logging.INFO)

''' ********************** SCRIPT CONFIGURATION END ********************** '''

#https://stackoverflow.com/questions/273192/how-can-i-create-a-directory-if-it-does-not-exist
def createFolder(folderPath):
    if not os.path.exists(folderPath):
        try:
            os.makedirs(folderPath)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

def renameFile(currentAttachmentPath, newAttachmentPath):
    #Rename file - ensure new attachment path does not exist already
    if not os.path.exists(newAttachmentPath):
        os.rename(currentAttachmentPath, newAttachmentPath)
        logger.info('{} being renamed as {}'.format(currentAttachmentPath, newAttachmentPath))
    else:
        logger.warning('Not able to rename {} as {} because file already exists. Removing {}'.format(currentAttachmentPath, newAttachmentPath, currentAttachmentPath))
        os.remove(currentAttachmentPath)

#Create specified folder if it does not exist already
createFolder(SaveAttachmentsTo)
createFolder(SaveLogsTo)
        
#Logging level specified in script configuration
logger = logging.getLogger(__name__)
logFileName = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
fileHandler = logging.handlers.RotatingFileHandler('{}/{}.log'.format(SaveLogsTo, logFileName), maxBytes=100000, backupCount=5)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(relativeCreated)d \n%(filename)s %(module)s %(funcName)s %(lineno)d \n%(message)s\n')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

logger.info('Script Starting at {}'.format(str(datetime.datetime.now())))

#Connect to GIS, and get Feature Layer information
if PortalUserName == '' and PortalPassword == '':
    gis = GIS()
else:
    gis = GIS(PortalUrl, PortalUserName, PortalPassword, verify_cert=PortalCertVerification)

downloadCounter = 0
nonDownloadCounter = 0
downloadSizeCounter = 0

itemObject = gis.content.get(FeatureLayerId)
logger.info('Iterating through layers in Feature Layer "{}"'.format(itemObject.name))
display(itemObject)

#Loop through layers in Feature Layer
for i in range(len(itemObject.layers)):
    featureLayer = itemObject.layers[i]
    
    #Skip layer if attachments are not enabled
    if featureLayer.properties.hasAttachments == True:
        #Remove any characters from feature layer name that may cause problems and ensure it's unique...
        featureLayerName = '{}-{}'.format(str(i), re.sub(r'[^A-Za-z0-9]+', '', featureLayer.properties.name))
        featureLayerFolder = SaveAttachmentsTo + r'\\' + featureLayerName
        createFolder(featureLayerFolder)

        #Query to get list of object ids in layer
        featureObjectIds = featureLayer.query(where='1=1', return_ids_only=True)
        featureIds = featureLayer.query(out_fields = ['objectId','globalId'])
        layer_ids = {}
        for row in featureIds.to_dict()["features"]:
            layer_ids[row['attributes']['globalid']] = row['attributes']['objectid']
        
        #Provide some updates to user...
        logger.info('Time: {}'.format(str(datetime.datetime.now())))
        logger.info('Currently looping through feature attachments in layer {} of {}: storing in folder named "{}"'.format(str(i + 1), str(len(itemObject.layers)), featureLayerName))
        logger.info('There are {} features to iterate in this layer'.format(str(len(featureObjectIds['objectIds']))))

        #Loop through features in layer
        emptyAttachments = 0
        for j in range(len(featureObjectIds['objectIds'])):
            currentObjectId = featureObjectIds['objectIds'][j]
            currentObjectIdAttachments = featureLayer.attachments.get_list(oid=currentObjectId)

            if len(currentObjectIdAttachments) > 0:

                #Loop through feature attachments and download to appropriate folder
                for k in range(len(currentObjectIdAttachments)):
                    attachmentId = currentObjectIdAttachments[k]['id']
                    attachmentName = currentObjectIdAttachments[k]['name']
                    attachmentSize = currentObjectIdAttachments[k]['size']
                    
                    ## id_dict[attachmentGlobalId] = currentObjectId
                    
                    if AttachmentStorage == 'IndividualFolder':
                        currentFolder = featureLayerFolder + r'\\' + str(currentObjectId)
                        #Create a folder for attachments
                        createFolder(currentFolder)
                        fileName = '{}-{}'.format(attachmentId, attachmentName)
                        newAttachmentPath = '{}\\{}'.format(currentFolder, fileName)
                        if not os.path.isfile(newAttachmentPath):
                            logger.info('The size of the current attachment being downloaded is {}MB'.format((attachmentSize/1000000)))
                            currentAttachmentPath = featureLayer.attachments.download(oid=currentObjectId, attachment_id=attachmentId, save_path=currentFolder)
                            #Rename to ensure file name is unique
                            renameFile(currentAttachmentPath[0], newAttachmentPath)
                            downloadCounter += 1
                            downloadSizeCounter += attachmentSize
                        else:
                            logger.info('File {} already exists. Not downloading again!'.format(newAttachmentPath))
                            nonDownloadCounter += 1

                    elif AttachmentStorage == 'GroupedFolder':
                        fileName = '{}-{}-{}'.format(currentObjectId, attachmentId, attachmentName)
                        newAttachmentPath = '{}\\{}'.format(featureLayerFolder, fileName)
                        if not os.path.isfile(newAttachmentPath):
                            logger.info('The size of the current attachment being downloaded is {}MB'.format((attachmentSize/1000000)))
                            currentAttachmentPath = featureLayer.attachments.download(oid=currentObjectId, attachment_id=attachmentId, save_path=featureLayerFolder)
                            #Rename to ensure file name is unique
                            renameFile(currentAttachmentPath[0], newAttachmentPath)
                            downloadCounter += 1
                            downloadSizeCounter += attachmentSize
                        else:
                            logger.info('File {} already exists. Not downloading again!'.format(newAttachmentPath))
                            nonDownloadCounter += 1

                    else:
                        logger.error('AttachmentStorage option not valid: {}. Valid options are IndividualFolder and GroupedFolder'.format(AttachmentStorage))
            else:
                emptyAttachments += 1
            
        logger.info('{} of these features do not contain attachments'.format(str(emptyAttachments)))
    else:
        logger.info('Layer {} does not have attachments enabled'.format(featureLayer.properties.name))       


#Loop through tables in Feature Layer
for i in range(len(itemObject.tables)):
    featureLayer = itemObject.tables[i]
    
    #Skip layer if attachments are not enabled
    if featureLayer.properties.hasAttachments == True:
        #Remove any characters from feature layer name that may cause problems and ensure it's unique...
        featureLayerName = '{}-{}'.format(str(i), re.sub(r'[^A-Za-z0-9]+', '', featureLayer.properties.name))
        featureLayerFolder = SaveAttachmentsTo + r'\\' + featureLayerName
        createFolder(featureLayerFolder)
        
        #Query to get list of object ids in layer
        featureObjectIds = featureLayer.query(where='1=1', return_ids_only=True)
        featureIds = featureLayer.query(out_fields = ['objectId','parentGlobalId'])
        table_ids = {}
        for row in featureIds.to_dict()["features"]:
            table_ids[row['attributes']['objectid']] = row['attributes']['parentglobalid']
        
                #Provide some updates to user...
        logger.info('Time: {}'.format(str(datetime.datetime.now())))
        logger.info('Currently looping through feature attachments in layer {} of {}: storing in folder named "{}"'.format(str(i + 1), str(len(itemObject.layers)), featureLayerName))
        logger.info('There are {} features to iterate in this layer'.format(str(len(featureObjectIds['objectIds']))))
            
        #Loop through features in layer
        emptyAttachments = 0
        for j in range(len(featureObjectIds['objectIds'])):
            currentObjectId = featureObjectIds['objectIds'][j]
            currentParentGlobalId = table_ids[currentObjectId]
            currentLayerId = layer_ids[currentParentGlobalId]
            currentObjectIdAttachments = featureLayer.attachments.get_list(oid=currentObjectId)



            if len(currentObjectIdAttachments) > 0:
                
                #Loop through feature attachments and download to appropriate folder
                for k in range(len(currentObjectIdAttachments)):
                    attachmentId = currentObjectIdAttachments[k]['id']
                    attachmentName = currentObjectIdAttachments[k]['name']
                    attachmentSize = currentObjectIdAttachments[k]['size']

                     
                    if AttachmentStorage == 'IndividualFolder':
                        currentFolder = featureLayerFolder + r'\\' + str(currentLayerId)
                        #Create a folder for attachments
                        createFolder(currentFolder)
                        fileName = '{}-{}'.format(attachmentId, attachmentName)
                        newAttachmentPath = '{}\\{}'.format(currentFolder, fileName)
                        if not os.path.isfile(newAttachmentPath):
                            logger.info('The size of the current attachment being downloaded is {}MB'.format((attachmentSize/1000000)))
                            currentAttachmentPath = featureLayer.attachments.download(oid=currentObjectId, attachment_id=attachmentId, save_path=currentFolder)
                            #Rename to ensure file name is unique
                            renameFile(currentAttachmentPath[0], newAttachmentPath)
                            downloadCounter += 1
                            downloadSizeCounter += attachmentSize
                        else:
                            logger.info('File {} already exists. Not downloading again!'.format(newAttachmentPath))
                            nonDownloadCounter += 1

                    elif AttachmentStorage == 'GroupedFolder':
                        fileName = '{}-{}-{}'.format(currentLayerId, attachmentId, attachmentName)
                        newAttachmentPath = '{}\\{}'.format(featureLayerFolder, fileName)
                        if not os.path.isfile(newAttachmentPath):
                            logger.info('The size of the current attachment being downloaded is {}MB'.format((attachmentSize/1000000)))
                            currentAttachmentPath = featureLayer.attachments.download(oid=currentObjectId, attachment_id=attachmentId, save_path=featureLayerFolder)
                            #Rename to ensure file name is unique
                            renameFile(currentAttachmentPath[0], newAttachmentPath)
                            downloadCounter += 1
                            downloadSizeCounter += attachmentSize
                        else:
                            logger.info('File {} already exists. Not downloading again!'.format(newAttachmentPath))
                            nonDownloadCounter += 1

                    else:
                        logger.error('AttachmentStorage option not valid: {}. Valid options are IndividualFolder and GroupedFolder'.format(AttachmentStorage))
            else:
                emptyAttachments += 1
            
        logger.info('{} of these features do not contain attachments'.format(str(emptyAttachments)))
    else:
        logger.info('Layer {} does not have attachments enabled'.format(featureLayer.properties.name))

logger.info('Summary: {} new files have been downloaded totalling {}MB in size'.format(downloadCounter, (downloadSizeCounter/1000000)))
logger.info('Summary: {} attachments already existed so were not downloaded again'.format(nonDownloadCounter))

