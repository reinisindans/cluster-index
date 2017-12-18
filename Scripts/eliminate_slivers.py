
from qgis.core import *



#Set the group where the script is to be found
##Pikobytes=group
##sliver_eliminator=name

#Set input layers
##grid=vector polygon
##min_area=number 100


#Set output layers

##land=output vector polygon

print 'Inputs and outputs defined' 

#Get the layers 
original=processing.getObject(grid)
land = QgsVectorLayer(original.source(), original.name(), original.providerType())

print 'Layers gotten'

#Enable editing of Layers

land.startEditing()

#Set the identifier Field
_NAME_FIELD = 'REGION'


#Feature dictionaries of both layers
land_feature_dict = {f.id(): f for f in land.getFeatures()}


print 'Dictionaries created'


#Create spatial indexes 

print 'QgsSpatialIndex'

land_index = QgsSpatialIndex()


print 'QgsSpatialIndex created'

#Create populate spatial indexes

for f in land_feature_dict.values():
    land_index.insertFeature(f)


 
print 'QgsSpatialIndexes populated' 
    
#Get minimum area Feature

#Defining the value to sort after

def getArea(f):
    return f.geometry().area()
    
print 'Getting min area feature'     

# Find smallest feature
min_land_feature= min(land_feature_dict.values(),key=getArea)
# Get area of smallest feature
min_land_feature_area=min_land_feature.geometry().area()

min_land_feature_id = [key for key, value in land_feature_dict.iteritems() if value == min_land_feature]
min_land_feature_id=min_land_feature_id[0]
 
print "Found min area feature %s" %min_land_feature_id
print "Min Area= %f" %min_land_feature_area
print "Chosen minimal area of features %s" %min_area

# Loop through all features and find features that touch each feature
while min_land_feature_area < min_area:
    

    #getting the corresponding feature:
    f=land_feature_dict[min_land_feature_id]
    print 'Working on %s' % f[_NAME_FIELD]
    
    geom = f.geometry()
        
    # Find all features that intersect the bounding box of the current feature.
    # We use spatial index to find the features intersecting the bounding box
    # of the current feature. This will narrow down the features that we need
    # to check neighboring features.
    
    intersecting_ids = land_index.intersects(geom.boundingBox())
    
    # Initalize neighbors list 
    
    neighbors = []
    
    for intersecting_id in intersecting_ids:
        
        # Look up the feature from the dictionary
        
        intersecting_f = land_feature_dict[intersecting_id]

        # For our purpose we consider a feature as 'neighbor' if it touches or
        # intersects a feature. We use the 'disjoint' predicate to satisfy
        # these conditions. So if a feature is not disjoint, it is a neighbor.
        
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #HERE ALSO THE ALGORITHM TO SELCT THE RIGHT NEIGHBOR!!!!
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
        if (f != intersecting_f and
            not intersecting_f.geometry().disjoint(geom)):
            neighbors.append(intersecting_f)
            print "found neighbor %s" %intersecting_f[_NAME_FIELD]
            
    #Find if there are any neighbors from the same original region, rearrange in new neighbor list
    selected_neighbors=[]
    for neighbor_feature in neighbors:
        if (neighbor_feature!=None and neighbor_feature[_NAME_FIELD]==f[_NAME_FIELD]):
            print "This feature is from the same original feature %s" %neighbor_feature[_NAME_FIELD]
            selected_neighbors.append(neighbor_feature)
            print "Neighbor feature appended"
    # If there are no neighboring features from same original Polygons, 
    
                
    if (selected_neighbors==[]):
        print "There were no neighboring regions from the same original REGION!"
        selected_neighbors=neighbors
        print "All neighbor features appended"
    
    if (selected_neighbors==[]):
        print "There were NO neighbors at all!!! WTF?"
        land.deleteFeature(f.id())
        land.updateExtents()
        land_index.deleteFeature(f)
        land_feature_dict.pop(f.id(),None)
        
        #Recalculate minimal area! 
        # Find smallest feature
        min_land_feature= min(land_feature_dict.values(),key=getArea)
        # Get area of smallest feature
        min_land_feature_area=min_land_feature.geometry().area()

        min_land_feature_id = [key for key, value in land_feature_dict.     iteritems() if value == min_land_feature]
        min_land_feature_id=min_land_feature_id[0]
 
        print "Found min area feature %s" %min_land_feature_id
        print "Min Area= %f" %min_land_feature_area
        continue 
    
    #creating lines 
    lines=[]
    for selected_neighbor in selected_neighbors:
        lines.append(f.geometry().intersection(selected_neighbor.geometry()))
        print "Creating line from %s" %selected_neighbor[_NAME_FIELD]
        print "line length %f" %f.geometry().intersection(selected_neighbor.geometry()).length()
    
    
    #Get the longest border
    
    def getLength(line):
        return line.length()
        
    max_border=max(lines,key=getLength)
    print "Maximum line is %f" %max_border.length()
    
    # Get the correstponding feature 
    
    print "Size of lines= %i; size of neighbors= %i" %(len(lines), len(selected_neighbors))
     
    for i in range(0,len(lines)):
        print i
        
        if (lines[i]==max_border):
            neighbor_feature=selected_neighbors[i]
            
            print "Neighbor found!! Neighbor ID: %s ; Neighbor Name: %s; Border Length: %f" %(neighbor_feature.id(), neighbor_feature[_NAME_FIELD], lines[i].length())

    # Merging the features!!! 
    print "Preparing to merge features"
    #Combining geometries
    merged_geometry=neighbor_feature.geometry().combine(geom)
    #Creating new feature
    new_feature=QgsFeature(land.pendingFields())
    #Setting geometry
    new_feature.setGeometry(merged_geometry)
    #Adding Attributes
    new_feature.setAttribute(_NAME_FIELD, neighbor_feature[_NAME_FIELD])
    
    #Add New feature to Layer
    land.addFeature(new_feature)
    land.updateExtents()
    
    print "Merged Feature ID: %s ; Name: %s; Area: %f" %(new_feature.id(), new_feature[_NAME_FIELD], new_feature.geometry().area())
    #Delete Features from layer itself! 
    land.deleteFeature(f.id())
    land.updateExtents()
    land.deleteFeature(neighbor_feature.id())
    land.updateExtents()
    
    #Update Dictionary!! 
    #Delete both used features from dictionary
    print "Updating dictionary"
    land_feature_dict.pop(f.id(),None)
    land_feature_dict.pop(neighbor_feature.id(),None)
    #Add the new Feature to dictionary!
    land_feature_dict.update({new_feature.id(): new_feature})
    
    #Update SpatialIndex! 
    print "Updating spatial Index"
    land_index.deleteFeature(f)
    land_index.deleteFeature(neighbor_feature)
    land_index.insertFeature(new_feature)
  
  #Recalculate minimal area! 
    # Find smallest feature
    min_land_feature= min(land_feature_dict.values(),key=getArea)
    # Get area of smallest feature
    min_land_feature_area=min_land_feature.geometry().area()

    min_land_feature_id = [key for key, value in land_feature_dict.iteritems() if value == min_land_feature]
    min_land_feature_id=min_land_feature_id[0]
 
    print "Found min area feature %s" %min_land_feature_id
    print "Min Area= %f" %min_land_feature_area
    
    print "Feature count: %i" %land.featureCount()
    

land.commitChanges()


print 'Processing complete.'
