# ---------------------------------------------------------------------------
# esri2open.py
# Created on: March 11, 2013
# Created by: Michael Byrne
# Federal Communications Commission
# exports the feature classes for any feature class to
# a csv file, JSON file or geoJSON file 
# also adding edits from sgillies and Shaun Walbridge
# updates include using the python json.dumps method and indentation issues
# edits made 3/19/2013
# ---------------------------------------------------------------------------

import arcpy
import json
import sys
import os


input_fc = sys.argv[1]
output_folder = sys.argv[2]
output_filetype = sys.argv[3]
output_delim = sys.argv[4]

def writeCSV(myOF):
    """Function wrtiteCSV - for each row, writes out each field w/ a delimiter.
       Right now does not deal w/ geometry, blob, or rasters.
       Has one argument; the name of the output file.

    """
    myFile = open(myOF, 'a')
    for row in arcpy.SearchCursor(input_fc):
        myStr = ""
        for myF in arcpy.ListFields(input_fc):
             if myF.type == "String":
                 myStr = myStr + str(row.getValue(myF.name).encode('utf-8')).strip() + output_delim
             if myF.typein ["Float", "Double", "Short", "Integer", "OID"]:
                 myStr = myStr + str(row.getValue(myF.name)) + output_delim 
             if (myF.type == "Date"):
                 myStr = myStr + str(row.getValue(myF.name)).strip() + output_delim
             # TODO: need to deal , blob, and raster
        myLen = len(myStr) - 1
        myStr = myStr[:myLen]
        myFile.write(myStr +  "\n")
    myFile.close()
    del myLen, myStr, myF, myFile, myOF
    del row
    return()

def writeJSON(myOF):
    """Function wrtiteJSON - for each row, writes out a JSON Object.
       Right now does not deal w/ multi-part points.
       Has one argument;  the name of the output file.

    """
    myFile = open(myOF, 'a')
    cnt = 1
    for row in arcpy.SearchCursor(input_fc):
        myFcnt = 1
        #the next line initializes the variable myGeomStr so that it is available
        #this code sets the geometry object for geoJson at the end of the line
        #the attributes or properties
        myGeomStr = ""  
        myStr = '{"type": "Feature", "id": ' + str(cnt) + ', "properties": '
        properties = {}
        for myF in arcpy.ListFields(input_fc):
            fCnt = int(len(arcpy.ListFields(input_fc)))    
            #if you are a shape field, so something special w/ it
            if myF.name == "Shape": 
                if output_filetype == "GeoJSON": # avoid globals!
                    myField = "geometry"
                    myGeomStr = myGeomStr + writeGeom(row.getValue(myF.name)) + "}"

            else: #otherwise, just write up the attribues as "properties"
                key = myF.name.lower()
                val = row.getValue(myF.name)
                if val is None:
                    # skip this field
                    continue 
                if myF.type == "String":
                    properties[key] = val.strip()
                if myF.type in ("Float", "Double", "Short", "Integer", "OID"):
                    properties[key] = val
                # TODO: Convert these to ISO 8601 datetime strings.
                if (myF.type == "Date"):
                    properties[key] = '"%s"' % val.strip()
            # TODO: Need to deal , blob, and raster at some point
        myStr += json.dumps(properties)
        #if its not the last row, then add a comma
        if cnt < theCnt :
            #if if the oType is a geoJson file, append the geomStr
            if output_filetype == "GeoJSON":  
                myFile.write(myStr + ", " + myGeomStr + "," + "\n")
            #if the oType is Json, don't append the geomStr
            else:
                myFile.write(myStr +  "}, \n") #"} " + "}," +
        #if it is the last row then just add the ending brackets
        else:   
            #if if the oType is a geoJson file, append the geomStr
            if output_filetype == "GeoJSON":  
                myFile.write(myStr + ", " + myGeomStr + " \n")
            #if the oType is Json, don't append the geomStr
            else:
                myFile.write(myStr + "} \n")
        cnt = cnt + 1
    myFile.write("]}" + "\n")
    myFile.close()

def writeGeom(myGeom):
    """Function writeGeom - writes out the geometry object to text.
       Has one argument; first is for the geometry object itself,
       myStr gets concatenated and returned.
    """
    myGeomStr = '"geometry": { "type": '
    if myGeom.isMultipart == 0:  #then it is simple geometry
        if myGeom.type == "point": #then write out the simple point attributes
            myGeomStr = myGeomStr + '"Point", "coordinates": ['
            myGeomStr = myGeomStr + str(myGeom.getPart().X) + ", " 
            myGeomStr = myGeomStr + str(myGeom.getPart().Y) + "] "
        #then write out the simple polygon features;  
        #currently not supportinginside rings
        if myGeom.type == "polygon": 
            #initialize the coordinates object
            myGeomStr = myGeomStr + '"Polygon", "coordinates": [['
            #set up a geometry part counting variable
            partnum = 0
            for part in myGeom:
                for pnt in myGeom.getPart(partnum):
                    myGeomStr = myGeomStr + "[" + str(pnt.X) + ", "\
                              + str(pnt.Y) + "],"
                partnum = partnum + 1
            myLen = len(myGeomStr) - 1
            myGeomStr = myGeomStr[:myLen] + "]] "
            del myLen, partnum, part, pnt
        if myGeom.type == "polyline": #then write out the simple line features
            myGeomStr = myGeomStr + '"LineString", "coordinates": ['
            partnum = 0
            for part in myGeom:
                for pnt in myGeom.getPart(partnum):
                    myGeomStr = myGeomStr + "[" + str(pnt.X) + ", "\
                              + str(pnt.Y) + "],"
                partnum = partnum + 1
            myLen = len(myGeomStr) - 1
            myGeomStr = myGeomStr[:myLen] + "] "
            del myLen, partnum, part, pnt    

    if myGeom.isMultipart == 1: #then it is multipart geometry
        if myGeom.type == "multipoint":
            #initialize the coordinates object for the geoJson file
            myGeomStr = myGeomStr + '"MultiPoint", "coordinates": ['
            partnum = 0
            partcount = myGeom.partCount
            while partnum < partcount:
                pnt = myGeom.getPart(partnum)
                myGeomStr = myGeomStr + "[" + str(pnt.X) + ", " 
                myGeomStr = myGeomStr + str(pnt.Y) + "],"
                partnum = partnum + 1
            myLen = len(myGeomStr) - 1
            myGeomStr = myGeomStr[:myLen] + "]"
            del partnum, partcount, pnt

        if myGeom.type == "polygon": 
            #initialize the coordinates object for the geoJson file
            myGeomStr = myGeomStr + '"MultiPolygon", "coordinates": [[['
            #set up a geometry part counting variable
            partnum = 0
            partcount = myGeom.partCount
            while partnum < int(partcount):
                part = myGeom.getPart(partnum)
                pnt = part.next()
                pntcnt = 0
                while pnt:
                    myGeomStr = myGeomStr + "[" + str(pnt.X) + ", "\
                              + str(pnt.Y) + "],"
                    pnt = part.next()
                    pntcnt = pntcnt + 1
                    if not pnt:
                        pnt = part.next()
                        if pnt:
                            arcpy.AddMessage("    interior ring found")
                myLen = len(myGeomStr) - 1
                myGeomStr = myGeomStr[:myLen] + "]],[["
                partnum = partnum + 1
            myLen = len(myGeomStr) - 3 
            myGeomStr = myGeomStr[:myLen] + "]"
            del partnum, partcount, part, pnt, pntcnt    

        if myGeom.type == "polyline": 
            #initialize the coordinates object for the geoJson file
            myGeomStr = myGeomStr + '"MultiLineString", "coordinates": [['
            #set up a geometry part counting variable
            partnum = 0
            partcount = myGeom.partCount
            while partnum < int(partcount):
                part = myGeom.getPart(partnum)
                pnt = part.next()
                pntcnt = 0
                while pnt:
                    myGeomStr = myGeomStr + "[" + str(pnt.X) + ", "\
                              + str(pnt.Y) + "],"
                    pnt = part.next()
                    pntcnt = pntcnt + 1
                    if not pnt:
                        pnt = part.next()
                        if pnt:
                            arcpy.AddMessage("    interior ring found")
                myLen = len(myGeomStr) - 1
                myGeomStr = myGeomStr[:myLen] + "],["
                partnum = partnum + 1
            myLen = len(myGeomStr) - 2
            myGeomStr = myGeomStr[:myLen] + "]"
            del partnum, partcount, part, pnt, pntcnt
    myGeomStr = myGeomStr + " } "
    del myGeom 
    return(myGeomStr)

def prepJSonFile (myOF):
    """Function prepJSonFile preps the file for writing to a JSON file type.
       Has one argument, the output file.

    """
    myFile = open(output_folder, 'w')
    myFile.write("{" + "\n")
    myStr = '"type": "FeatureCollection",'
    myFile.write(myStr + "\n")
    myStr = '"features": ['
    myFile.write(myStr + "\n")
    myFile.close()
    del myOF, myStr, myFile
    return()

def prepCSVFile (myOF):
    """Function prepCSVFile preps the file for writing to a CSV file type.
       If the field is a geometry, blob, or raster, it does not write them out

    """
    myStr = ""
    for myF in arcpy.ListFields(input_fc):  #only create data for field types that make sense
        if myF.type in ["String", "Float", "Double", "Short", "Integer", "OID", "Date"]:
           myStr = myStr + myF.name + output_delim
    myLen = len(myStr) - 1
    myStr = myStr[:myLen]
    myFile = open(myOF, 'w')
    myFile.write(myStr + "\n")
    myFile.close()            
    del myOF, myStr, myLen, myFile 
    return()

if __name__ == "__main__":
    try:
        if output_delim == None:
            output_delim = "|"
        #get the file prefix by truncating the featureclass
        output_folder = output_folder + "/" + str(os.path.splitext(os.path.basename(input_fc))[0])\
              + "." + output_filetype.lower()
        arcpy.AddMessage(output_folder)
        theCnt = int(arcpy.GetCount_management(input_fc).getOutput(0))

        arcpy.AddMessage("Writing out " + str(theCnt) + " records ")
        arcpy.AddMessage("     from feature class " + input_fc)
        arcpy.AddMessage("     to the file " + output_folder)
        arcpy.AddMessage("     as a " + output_filetype + " file")
        #if the output type is csv, write a csv
        if output_filetype == "CSV":
            prepCSVFile(output_folder)
            writeCSV(output_folder)
        #if the output type is json, or geojson, write a json file
        if output_filetype in ["JSON", "GeoJSON"]:
            prepJSonFile(output_folder)
            writeJSON(output_folder)
    except:
        arcpy.AddMessage("Something bad happened")
