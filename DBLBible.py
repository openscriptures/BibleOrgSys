#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# DBLBible.py
#
# Module handling Digital Bible Library (DBL) compilations of USX XML Bible books along with XML metadata
#
# Copyright (C) 2013-2015 Robert Hunt
# Author: Robert Hunt <Freely.Given.org@gmail.com>
# License: See gpl-3.0.txt
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Module for defining and manipulating complete or partial DBL Bible bundles.

See http://digitalbiblelibrary.org and http://digitalbiblelibrary.org/info/inside
as well as http://www.everytribeeverynation.org/library
"""

from gettext import gettext as _

LastModifiedDate = '2015-05-21' # by RJH
ShortProgName = "DigitalBibleLibrary"
ProgName = "Digital Bible Library (DBL) XML Bible handler"
ProgVersion = '0.11'
ProgNameVersion = '{} v{}'.format( ShortProgName, ProgVersion )
ProgNameVersionDate = '{} {} {}'.format( ProgNameVersion, _("last modified"), LastModifiedDate )

debuggingThisModule = False


import os, logging
from collections import OrderedDict
from xml.etree.ElementTree import ElementTree

import BibleOrgSysGlobals
from Bible import Bible
from USXFilenames import USXFilenames
from USXXMLBibleBook import USXXMLBibleBook



COMPULSORY_FILENAMES = ( 'METADATA.XML', 'LICENSE.XML', 'STYLES.XML' ) # Must all be UPPER-CASE



def t( messageString ):
    """
    Prepends the module name to a error or warning message string if we are in debug mode.
    Returns the new string.
    """
    try: nameBit, errorBit = messageString.split( ': ', 1 )
    except ValueError: nameBit, errorBit = '', messageString
    if BibleOrgSysGlobals.debugFlag or debuggingThisModule:
        nameBit = '{}{}{}: '.format( ShortProgName, '.' if nameBit else '', nameBit )
    return '{}{}'.format( nameBit, _(errorBit) )
# end of t



def DBLBibleFileCheck( givenFolderName, strictCheck=True, autoLoad=False, autoLoadBooks=False ):
    """
    Given a folder, search for DBL Bible bundles in the folder and in the next level down.

    Returns False if an error is found.

    if autoLoad is false (default)
        returns None, or the number of bundles found.

    if autoLoad is true and exactly one DBL Bible bundle is found,
        returns the loaded DBLBible object.
    """
    if BibleOrgSysGlobals.verbosityLevel > 2: print( "DBLBibleFileCheck( {}, {}, {} )".format( givenFolderName, strictCheck, autoLoad ) )
    if BibleOrgSysGlobals.debugFlag: assert( givenFolderName and isinstance( givenFolderName, str ) )
    if BibleOrgSysGlobals.debugFlag: assert( autoLoad in (True,False,) )

    # Check that the given folder is readable
    if not os.access( givenFolderName, os.R_OK ):
        logging.critical( _("DBLBibleFileCheck: Given '{}' folder is unreadable").format( givenFolderName ) )
        return False
    if not os.path.isdir( givenFolderName ):
        logging.critical( _("DBLBibleFileCheck: Given '{}' path is not a folder").format( givenFolderName ) )
        return False

    # Find all the files and folders in this folder
    if BibleOrgSysGlobals.verbosityLevel > 3: print( " DBLBibleFileCheck: Looking for files in given {}".format( givenFolderName ) )
    foundFolders, foundFiles = [], []
    for something in os.listdir( givenFolderName ):
        somepath = os.path.join( givenFolderName, something )
        if os.path.isdir( somepath ): foundFolders.append( something )
        elif os.path.isfile( somepath ): foundFiles.append( something )
    if '__MACOSX' in foundFolders:
        foundFolders.remove( '__MACOSX' )  # don't visit these directories

    # See if the compulsory files and folder are here in this given folder
    numFound = numFilesFound = numFoldersFound = 0
    for filename in foundFiles:
        if filename.upper() in COMPULSORY_FILENAMES: numFilesFound += 1
    for folderName in foundFolders:
        if folderName.upper().startswith('USX_'): numFoldersFound += 1
    if numFilesFound==len(COMPULSORY_FILENAMES) and numFoldersFound>0: numFound += 1

    ## See if there's an USXBible project here in this given folder
    #numFound = 0
    #UFns = USXFilenames( givenFolderName ) # Assuming they have standard Paratext style filenames
    #if BibleOrgSysGlobals.verbosityLevel > 2: print( UFns )
    #filenameTuples = UFns.getConfirmedFilenames()
    #if BibleOrgSysGlobals.verbosityLevel > 3: print( "Confirmed:", len(filenameTuples), filenameTuples )
    #if BibleOrgSysGlobals.verbosityLevel > 1 and filenameTuples: print( "Found {} USX files.".format( len(filenameTuples) ) )
    #if filenameTuples:
        #numFound += 1

    if numFound:
        if BibleOrgSysGlobals.verbosityLevel > 2: print( "DBLBibleFileCheck got", numFound, givenFolderName )
        if numFound == 1 and (autoLoad or autoLoadBooks):
            dB = DBLBible( givenFolderName )
            if autoLoad or autoLoadBooks:
                dB.load() # Load and process the metadata files
                if autoLoadBooks: dB.loadBooks() # Load and process the book files
            return dB
        return numFound

    # Look one level down
    numFound = 0
    foundProjects = []
    for thisFolderName in sorted( foundFolders ):
        tryFolderName = os.path.join( givenFolderName, thisFolderName+'/' )
        if not os.access( tryFolderName, os.R_OK ): # The subfolder is not readable
            logging.warning( _("DBLBibleFileCheck: '{}' subfolder is unreadable").format( tryFolderName ) )
            continue
        if BibleOrgSysGlobals.verbosityLevel > 3: print( "    DBLBibleFileCheck: Looking for files in {}".format( tryFolderName ) )
        foundSubfolders, foundSubfiles = [], []
        for something in os.listdir( tryFolderName ):
            somepath = os.path.join( givenFolderName, thisFolderName, something )
            if os.path.isdir( somepath ): foundSubfolders.append( something )
            elif os.path.isfile( somepath ): foundSubfiles.append( something )

        # See if the compulsory files and folder are here in this given folder
        numFilesFound = numFoldersFound = 0
        for filename in foundSubfiles:
            if filename.upper() in COMPULSORY_FILENAMES: numFilesFound += 1
        for folderName in foundSubfolders:
            if folderName.upper().startswith('USX_'): numFoldersFound += 1
        if numFilesFound==len(COMPULSORY_FILENAMES) and numFoldersFound>0:
            foundProjects.append( tryFolderName )
            numFound += 1

        ## See if there's an USX Bible here in this folder
        #UFns = USXFilenames( tryFolderName ) # Assuming they have standard Paratext style filenames
        #if BibleOrgSysGlobals.verbosityLevel > 2: print( UFns )
        #filenameTuples = UFns.getConfirmedFilenames()
        #if BibleOrgSysGlobals.verbosityLevel > 3: print( "Confirmed:", len(filenameTuples), filenameTuples )
        #if BibleOrgSysGlobals.verbosityLevel > 2 and filenameTuples: print( "  Found {} USX files: {}".format( len(filenameTuples), filenameTuples ) )
        #elif BibleOrgSysGlobals.verbosityLevel > 1 and filenameTuples: print( "  Found {} USX files".format( len(filenameTuples) ) )
        #if filenameTuples:
            #foundProjects.append( tryFolderName )
            #numFound += 1

    if numFound:
        if BibleOrgSysGlobals.verbosityLevel > 2: print( "DBLBibleFileCheck foundProjects", numFound, foundProjects )
        if numFound == 1 and (autoLoad or autoLoadBooks):
            dB = DBLBible( foundProjects[0] )
            if autoLoad or autoLoadBooks:
                dB.load() # Load and process the metadata files
                if autoLoadBooks: dB.loadBooks() # Load and process the book files
            return dB
        return numFound
# end of DBLBibleFileCheck



class DBLBible( Bible ):
    """
    Class to load and manipulate DBL Bible bundles.
    """
    def __init__( self, givenFolderName, givenName=None, encoding='utf-8' ):
        """
        Create the internal DBL Bible object.
        """
         # Setup and initialise the base class first
        Bible.__init__( self )
        self.objectNameString = 'DBL XML Bible object'
        self.objectTypeString = 'DBL'

        self.givenFolderName, self.givenName, self.encoding = givenFolderName, givenName, encoding # Remember our parameters

        # Now we can set our object variables
        self.name = self.givenName

        # Do a preliminary check on the readability of our folder
        if not os.access( self.givenFolderName, os.R_OK ):
            logging.error( "DBLBible: File '{}' is unreadable".format( self.givenFolderName ) )

        # Create empty containers for loading the XML metadata files
        self.DBLMetadata = self.DBLLicense = self.DBLStyles = self.DBLVersification = self.DBLLanguage = None
    # end of DBLBible.__init__


    def load( self ):
        """
        Load the XML metadata files.
        """
        if BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel > 2:
            print( t("load()") )
        if BibleOrgSysGlobals.verbosityLevel > 1: print( _("DBLBible: Loading {} from {}...").format( self.name, self.givenFolderName ) )

        # Do a preliminary check on the contents of our folder
        foundFiles, foundFolders = [], []
        for something in os.listdir( self.givenFolderName ):
            somepath = os.path.join( self.givenFolderName, something )
            if os.path.isdir( somepath ): foundFolders.append( something )
            elif os.path.isfile( somepath ): foundFiles.append( something )
            else: print( "ERROR: Not sure what '{}' is in {}!".format( somepath, self.givenFolderName ) )
        if not foundFiles:
            print( "DBLBible.load: Couldn't find any files in '{}'".format( self.givenFolderName ) )
            return # No use continuing

        self.loadDBLLicense()
        self.loadDBLMetadata()
        self.loadDBLStyles()
        self.loadDBLVersification()
        self.loadDBLLanguage()
        #print( 'DBLLicense', len(self.DBLLicense), self.DBLLicense )
        #print( 'DBLMetadata', len(self.DBLMetadata), self.DBLMetadata )
        #print( 'DBLStyles', len(self.DBLStyles), self.DBLStyles )
        #print( 'DBLVersification', len(self.DBLVersification), self.DBLVersification )
        #print( 'DBLLanguage', len(self.DBLLanguage), self.DBLLanguage )
    # end of DBLBible.load


    def loadDBLLicense( self ):
        """
        Load the metadata.xml file and parse it into the ordered dictionary self.DBLMetadata.
        """
        if BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel > 2:
            print( t("loadDBLLicense()") )

        licenseFilepath = os.path.join( self.givenFolderName, 'license.xml' )
        if BibleOrgSysGlobals.verbosityLevel > 2: print( "DBLBible.loading license data from {}...".format( licenseFilepath ) )
        self.tree = ElementTree().parse( licenseFilepath )
        assert( len ( self.tree ) ) # Fail here if we didn't load anything at all

        self.DBLLicense = OrderedDict()
        #loadErrors = []

        # Find the main container
        if self.tree.tag=='license':
            location = "DBL {} file".format( self.tree.tag )
            BibleOrgSysGlobals.checkXMLNoText( self.tree, location )
            BibleOrgSysGlobals.checkXMLNoTail( self.tree, location )

            # Process the metadata attributes first
            licenseID = None
            for attrib,value in self.tree.items():
                if attrib=='id': licenseID = value
                else: logging.warning( _("Unprocessed {} attribute ({}) in {}").format( attrib, value, location ) )
            self.DBLLicense['Id'] = licenseID

            # Now process the actual metadata
            for element in self.tree:
                sublocation = element.tag + ' ' + location
                #print( "\nProcessing {}...".format( sublocation ) )
                BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                if element.tag in ( 'dateLicense', 'dateLicenseExpiry' ):
                    BibleOrgSysGlobals.checkXMLNoSubelements( element, sublocation )
                    self.DBLLicense[element.tag] = element.text
                elif element.tag == 'publicationRights':
                    assert( element.tag not in self.DBLLicense )
                    self.DBLLicense[element.tag] = OrderedDict()
                    for subelement in element:
                        sub2location = subelement.tag + ' ' + sublocation
                        #print( "  Processing {}...".format( sub2location ) )
                        BibleOrgSysGlobals.checkXMLNoAttributes( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoSubelements( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoTail( subelement, sub2location )
                        if subelement.tag in ('allowOffline', 'allowIntroductions', 'allowFootnotes', 'allowCrossReferences', 'allowExtendedNotes' ):
                            #if BibleOrgSysGlobals.debugFlag: assert( subelement.text ) # These can be blank!
                            assert( subelement.tag not in self.DBLLicense[element.tag] )
                            self.DBLLicense[element.tag][subelement.tag] = subelement.text
                        else: logging.warning( _("Unprocessed {} subelement '{}' in {}").format( subelement.tag, subelement.text, sub2location ) )
                else:
                    logging.warning( _("Unprocessed {} element in {}").format( element.tag, sublocation ) )
                    #self.addPriorityError( 1, c, v, _("Unprocessed {} element").format( element.tag ) )
        if BibleOrgSysGlobals.verbosityLevel > 2: print( "  Loaded {} license elements.".format( len(self.DBLLicense) ) )
    # end of DBLBible.loadDBLLicense


    def loadDBLMetadata( self ):
        """
        Load the metadata.xml file and parse it into the ordered dictionary self.DBLMetadata.
        """
        if BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel > 2:
            print( t("loadDBLMetadata()") )

        mdFilepath = os.path.join( self.givenFolderName, 'metadata.xml' )
        if BibleOrgSysGlobals.verbosityLevel > 2: print( "DBLBible.loading metadata from {}...".format( mdFilepath ) )
        self.tree = ElementTree().parse( mdFilepath )
        assert( len ( self.tree ) ) # Fail here if we didn't load anything at all

        def getContents( element, location ):
            """
            Load the contents information (which is more nested/complex).
            """
            assert( element.tag == 'contents' )
            ourDict = self.DBLMetadata['contents']
            BibleOrgSysGlobals.checkXMLNoAttributes( element, location )
            BibleOrgSysGlobals.checkXMLNoText( element, location )
            BibleOrgSysGlobals.checkXMLNoTail( element, location )
            for subelement in element:
                sublocation = subelement.tag + ' ' + location
                #print( "  Processing {}...".format( sublocation ) )
                BibleOrgSysGlobals.checkXMLNoText( subelement, sublocation )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, sublocation )
                assert( subelement.tag == 'bookList' )
                bookListID = bookListIsDefault = None
                for attrib,value in subelement.items():
                    if attrib=='id': bookListID = value
                    elif attrib=='default': bookListIsDefault = value
                    else: logging.warning( _("Unprocessed {} attribute ({}) in {}").format( attrib, value, sublocation ) )
                bookListTag = subelement.tag + '-' + bookListID + (' (default)' if bookListIsDefault=='true' else '')
                assert( bookListTag not in ourDict )
                ourDict[bookListTag] = {}
                ourDict[bookListTag]['divisions'] = OrderedDict()
                for sub2element in subelement:
                    sub2location = sub2element.tag + ' ' + sublocation
                    #print( "    Processing {}...".format( sub2location ) )
                    BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2location )
                    if sub2element.tag in ('name','nameLocal','abbreviation','abbreviationLocal','description','descriptionLocal','range','tradition'):
                        if BibleOrgSysGlobals.debugFlag: assert( sub2element.text )
                        ourDict[bookListTag][sub2element.tag] = sub2element.text
                    elif sub2element.tag == 'division':
                        items = sub2element.items()
                        assert( len(items)==1 and items[0][0]=='id' )
                        divisionID = items[0][1]
                        #divisionTag = sub2element.tag + '-' + divisionID
                        ourDict[bookListTag]['divisions'][divisionID] = []
                    elif sub2element.tag == 'books':
                        BibleOrgSysGlobals.checkXMLNoAttributes( sub2element, sub2location )
                        ourDict[bookListTag] = []
                        for sub3element in sub2element:
                            sub3location = sub3element.tag + ' ' + sub2location
                            #print( "        Processing {}...".format( sub3location ) )
                            BibleOrgSysGlobals.checkXMLNoSubelements( sub3element, sub3location )
                            BibleOrgSysGlobals.checkXMLNoText( sub3element, sub3location )
                            BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3location )
                            assert( sub3element.tag == 'book' )
                            items = sub3element.items()
                            assert( len(items)==1 and items[0][0]=='code' )
                            bookCode = items[0][1]
                            ourDict[bookListTag].append( bookCode )
                    else: logging.warning( _("Unprocessed {} sub2element '{}' in {}").format( sub2element.tag, sub2element.text, sub2location ) )
                    #if 0:
                        #items = sub2element.items()
                        #for sub3element in sub2element:
                            #sub3location = sub3element.tag + ' ' + sub2location
                            #print( "      Processing {}...".format( sub3location ) )
                            #BibleOrgSysGlobals.checkXMLNoAttributes( sub3element, sub3location )
                            #BibleOrgSysGlobals.checkXMLNoText( sub3element, sub3location )
                            #BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3location )
                            #assert( sub3element.tag == 'books' ) # Don't bother saving this extra level
                            #for sub4element in sub3element:
                                #sub4location = sub4element.tag + ' ' + sub3location
                                #print( "        Processing {}...".format( sub4location ) )
                                #BibleOrgSysGlobals.checkXMLNoSubelements( sub4element, sub4location )
                                #BibleOrgSysGlobals.checkXMLNoText( sub4element, sub4location )
                                #BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4location )
                                #assert( sub4element.tag == 'book' )
                                #items = sub4element.items()
                                #assert( len(items)==1 and items[0][0]=='code' )
                                #bookCode = items[0][1]
                                #ourDict[bookListTag]['divisions'][divisionID].append( bookCode )
            #print( "Contents:", self.DBLMetadata['contents'] )
        # end of getContents

        self.DBLMetadata = OrderedDict()
        #loadErrors = []

        # Find the main container
        if self.tree.tag=='DBLMetadata':
            location = "DBL Metadata ({}) file".format( self.tree.tag )
            BibleOrgSysGlobals.checkXMLNoText( self.tree, location )
            BibleOrgSysGlobals.checkXMLNoTail( self.tree, location )

            # Process the metadata attributes first
            mdType = mdTypeVersion = mdID = mdRevision = None
            for attrib,value in self.tree.items():
                if attrib=='type': mdType = value
                elif attrib=='typeVersion': mdTypeVersion = value
                elif attrib=='id': mdID = value
                elif attrib=='revision': mdRevision = value
                else: logging.warning( _("Unprocessed {} attribute ({}) in {}").format( attrib, value, location ) )
            if BibleOrgSysGlobals.debugFlag:
                assert( mdType == "text" )
                assert( mdTypeVersion == "1.3" )
                assert( mdRevision == "1" )

            # Now process the actual metadata
            for element in self.tree:
                sublocation = element.tag + ' ' + location
                #print( "\nProcessing {}...".format( sublocation ) )
                self.DBLMetadata[element.tag] = OrderedDict()
                if element.tag == 'identification':
                    BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoText( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    for subelement in element:
                        sub2location = subelement.tag + ' ' + sublocation
                        #print( "  Processing {}...".format( sub2location ) )
                        BibleOrgSysGlobals.checkXMLNoSubelements( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoTail( subelement, sub2location )
                        if subelement.tag in ('name','nameLocal','abbreviation','abbreviationLocal','scope','description','dateCompleted','systemId','bundleProducer'):
                            thisTag = subelement.tag
                            if subelement.tag == 'systemId':
                                items = subelement.items()
                                assert( len(items)==1 and items[0][0]=='type' )
                                thisTag = thisTag + '-' + items[0][1]
                            else: BibleOrgSysGlobals.checkXMLNoAttributes( subelement, sub2location )
                            assert( subelement.text )
                            self.DBLMetadata[element.tag][thisTag] = subelement.text
                        else: logging.warning( _("Unprocessed {} subelement '{}' in {}").format( subelement.tag, subelement.text, sub2location ) )
                elif element.tag == 'confidential':
                    BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoSubelements( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    self.DBLMetadata['confidential'] = element.text
                elif element.tag == 'agencies':
                    BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoText( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    for subelement in element:
                        sub2location = subelement.tag + ' ' + sublocation
                        BibleOrgSysGlobals.checkXMLNoAttributes( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoSubelements( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoTail( subelement, sub2location )
                        if subelement.tag in ('etenPartner','creator','publisher','contributor'):
                            #if BibleOrgSysGlobals.debugFlag: assert( subelement.text ) # These can be blank!
                            self.DBLMetadata[element.tag][subelement.tag] = subelement.text
                        else: logging.warning( _("Unprocessed {} subelement '{}' in {}").format( subelement.tag, subelement.text, sub2location ) )
                elif element.tag == 'language':
                    BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoText( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    for subelement in element:
                        sub2location = subelement.tag + ' ' + sublocation
                        BibleOrgSysGlobals.checkXMLNoAttributes( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoSubelements( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoTail( subelement, sub2location )
                        if subelement.tag in ('iso','name','ldml','rod','script','scriptDirection','numerals'):
                            #if BibleOrgSysGlobals.debugFlag: assert( subelement.text ) # These can be blank!
                            self.DBLMetadata[element.tag][subelement.tag] = subelement.text
                        else: logging.warning( _("Unprocessed {} subelement '{}' in {}").format( subelement.tag, subelement.text, sub2location ) )
                elif element.tag == 'country':
                    BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoText( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    for subelement in element:
                        sub2location = subelement.tag + ' ' + sublocation
                        BibleOrgSysGlobals.checkXMLNoAttributes( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoSubelements( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoTail( subelement, sub2location )
                        if subelement.tag in ('iso','name'):
                            if BibleOrgSysGlobals.debugFlag: assert( subelement.text )
                            self.DBLMetadata[element.tag][subelement.tag] = subelement.text
                        else: logging.warning( _("Unprocessed {} subelement '{}' in {}").format( subelement.tag, subelement.text, sub2location ) )
                elif element.tag == 'type':
                    BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoText( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    for subelement in element:
                        sub2location = subelement.tag + ' ' + sublocation
                        BibleOrgSysGlobals.checkXMLNoAttributes( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoSubelements( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoTail( subelement, sub2location )
                        if subelement.tag in ('translationType','audience'):
                            #if BibleOrgSysGlobals.debugFlag: assert( subelement.text ) # These can be blank!
                            self.DBLMetadata[element.tag][subelement.tag] = subelement.text
                        else: logging.warning( _("Unprocessed {} subelement '{}' in {}").format( subelement.tag, subelement.text, sub2location ) )
                elif element.tag == 'bookNames':
                    BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoText( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    for subelement in element:
                        sub2location = subelement.tag + ' ' + sublocation
                        BibleOrgSysGlobals.checkXMLNoText( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoTail( subelement, sub2location )
                        assert( subelement.tag == 'book' )
                        items = subelement.items()
                        assert( len(items)==1 and items[0][0]=='code' )
                        bookCode = items[0][1]
                        assert( len(bookCode) == 3 )
                        self.DBLMetadata[element.tag][bookCode] = {}
                        for sub2element in subelement:
                            sub3location = sub2element.tag + ' ' + bookCode + ' ' + sub2location
                            BibleOrgSysGlobals.checkXMLNoAttributes( sub2element, sub3location )
                            BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub3location )
                            BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub3location )
                            if sub2element.tag in ('long','short','abbr'):
                                assert( sub2element.text )
                                self.DBLMetadata[element.tag][bookCode][sub2element.tag] = sub2element.text
                            else: logging.warning( _("Unprocessed {} sub2element '{}' in {}").format( sub2element.tag, sub2element.text, sub3location ) )
                elif element.tag == 'contents':
                    getContents( element, sublocation )
                elif element.tag == 'progress':
                    BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoText( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    self.DBLMetadata[element.tag] = {} # Don't need this ordered
                    for subelement in element:
                        sub2location = subelement.tag + ' ' + sublocation
                        BibleOrgSysGlobals.checkXMLNoSubelements( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoText( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoTail( subelement, sub2location )
                        assert( subelement.tag == 'book' )
                        bookCode = stage = None
                        for attrib,value in subelement.items():
                            if attrib=='code': bookCode = value
                            elif attrib=='stage': stage = value
                            logging.warning( _("Unprocessed {} attribute ({}) in {}").format( attrib, value, sub2location ) )
                        #print( bookCode, stage )
                        assert( len(bookCode) == 3 )
                        if bookCode not in self.DBLMetadata['bookNames']:
                            logging.warning( _("Bookcode {} mentioned in progress but not found in bookNames").format( bookCode ) )
                        assert( stage in ('1','2','3','4') )
                        self.DBLMetadata[element.tag][bookCode] = stage
                elif element.tag == 'contact':
                    BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoText( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    for subelement in element:
                        sub2location = subelement.tag + ' ' + sublocation
                        BibleOrgSysGlobals.checkXMLNoAttributes( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoSubelements( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoTail( subelement, sub2location )
                        if subelement.tag in ('rightsHolder','rightsHolderLocal','rightsHolderAbbreviation','rightsHolderURL','rightsHolderFacebook'):
                            #if BibleOrgSysGlobals.debugFlag: assert( subelement.text ) # These can be blank!
                            self.DBLMetadata[element.tag][subelement.tag] = subelement.text
                        else: logging.warning( _("Unprocessed {} subelement '{}' in {}").format( subelement.tag, subelement.text, sub2location ) )
                elif element.tag == 'copyright':
                    BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoText( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    for subelement in element:
                        sub2location = subelement.tag + ' ' + sublocation
                        BibleOrgSysGlobals.checkXMLNoTail( subelement, sub2location )
                        if subelement.tag in ('statement',):
                            items = subelement.items()
                            assert( len(items)==1 and items[0][0]=='contentType' )
                            contentType = items[0][1]
                            assert( contentType in ('xhtml',) )
                            if not len(subelement) and subelement.text:
                                self.DBLMetadata[element.tag][subelement.tag+'-'+contentType] = subelement.text
                            else:
                                self.DBLMetadata[element.tag][subelement.tag+'-'+contentType] = BibleOrgSysGlobals.getFlattenedXML( subelement, sub2location )
                        else: logging.warning( _("Unprocessed {} subelement '{}' in {}").format( subelement.tag, subelement.text, sub2location ) )
                elif element.tag == 'promotion':
                    BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoText( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    for subelement in element:
                        sub2location = subelement.tag + ' ' + sublocation
                        BibleOrgSysGlobals.checkXMLNoTail( subelement, sub2location )
                        if subelement.tag in ('promoVersionInfo','promoEmail'):
                            items = subelement.items()
                            assert( len(items)==1 and items[0][0]=='contentType' )
                            contentType = items[0][1]
                            assert( contentType in ('xhtml',) )
                            if not len(subelement) and subelement.text:
                                self.DBLMetadata[element.tag][subelement.tag+'-'+contentType] = subelement.text
                            else:
                                self.DBLMetadata[element.tag][subelement.tag+'-'+contentType] = BibleOrgSysGlobals.getFlattenedXML( subelement, sub2location )
                        else: logging.warning( _("Unprocessed {} subelement '{}' in {}").format( subelement.tag, subelement.text, sub2location ) )
                elif element.tag == 'archiveStatus':
                    BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoText( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    for subelement in element:
                        sub2location = subelement.tag + ' ' + sublocation
                        BibleOrgSysGlobals.checkXMLNoAttributes( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoSubelements( subelement, sub2location )
                        BibleOrgSysGlobals.checkXMLNoTail( subelement, sub2location )
                        if subelement.tag in ('archivistName','dateArchived','dateUpdated','comments'):
                            if BibleOrgSysGlobals.debugFlag: assert( subelement.text )
                            self.DBLMetadata[element.tag][subelement.tag] = subelement.text
                        else: logging.warning( _("Unprocessed {} subelement '{}' in {}").format( subelement.tag, subelement.text, sub2location ) )
                elif element.tag == 'format':
                    BibleOrgSysGlobals.checkXMLNoAttributes( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoSubelements( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    assert( element.text )
                    self.DBLMetadata[element.tag]  = element.text
                else:
                    logging.warning( _("Unprocessed {} element in {}").format( element.tag, sublocation ) )
                    #self.addPriorityError( 1, c, v, _("Unprocessed {} element").format( element.tag ) )
        #print( '\n', self.DBLMetadata )
        if BibleOrgSysGlobals.verbosityLevel > 2: print( "  Loaded {} metadata elements.".format( len(self.DBLMetadata) ) )
    # end of DBLBible.loadDBLMetadata


    def loadDBLStyles( self ):
        """
        Load the metadata.xml file and parse it into the ordered dictionary self.DBLMetadata.
        """
        if BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel > 2:
            print( t("loadDBLStyles()") )

        styleFilepath = os.path.join( self.givenFolderName, 'styles.xml' )
        if BibleOrgSysGlobals.verbosityLevel > 2: print( "DBLBible.loading styles from {}...".format( styleFilepath ) )
        self.tree = ElementTree().parse( styleFilepath )
        assert( len ( self.tree ) ) # Fail here if we didn't load anything at all

        def getStyle( element, location ):
            """
            Load the contents information (which is more nested/complex).
            """
            assert( element.tag == 'style' )
            ourDict = self.DBLStyles['styles']
            BibleOrgSysGlobals.checkXMLNoText( element, location )
            BibleOrgSysGlobals.checkXMLNoTail( element, location )

            # Process style attributes first
            styleID = publishable = versetext = None
            for attrib,value in element.items():
                if attrib=='id': styleID = value
                elif attrib=='publishable': publishable = value
                elif attrib=='versetext': versetext = value
                else: logging.warning( _("Unprocessed style {} attribute ({}) in {}").format( attrib, value, location ) )
            #print( "StyleID", styleID )
            assert( styleID not in ourDict )
            ourDict[styleID] = OrderedDict()

            # Now process the style properties
            for subelement in element:
                sublocation = subelement.tag + ' ' + location
                #print( "  Processing {}...".format( sublocation ) )
                BibleOrgSysGlobals.checkXMLNoSubelements( subelement, sublocation )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, sublocation )
                if subelement.tag in ( 'name', 'description' ):
                    BibleOrgSysGlobals.checkXMLNoAttributes( subelement, sublocation )
                    assert( subelement.tag not in ourDict[styleID] )
                    ourDict[styleID][subelement.tag] = subelement.text
                elif subelement.tag == 'property':
                    if 'properties' not in ourDict[styleID]: ourDict[styleID]['properties'] = OrderedDict()
                    BibleOrgSysGlobals.checkXMLNoSubelements( subelement, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( subelement, sublocation )
                    # Collect the property attributes first
                    name = None
                    attribDict = {}
                    for attrib,value in element.items():
                        if attrib=='name': name = value
                        else: attribDict[attrib] = value
                    if name in ( 'font-family', 'font-size' ):
                        ourDict[styleID]['properties'][name] = ( element.text, attribDict )
                else: logging.warning( _("Unprocessed style {} subelement '{}' in {}").format( subelement.tag, subelement.text, sublocation ) )
            #print( "Styles:", self.DBLStyles['styles'] )
        # end of getStyle

        self.DBLStyles = OrderedDict()
        #loadErrors = []

        # Find the main container
        if self.tree.tag=='stylesheet':
            location = "DBL {} file".format( self.tree.tag )
            BibleOrgSysGlobals.checkXMLNoAttributes( self.tree, location )
            BibleOrgSysGlobals.checkXMLNoText( self.tree, location )
            BibleOrgSysGlobals.checkXMLNoTail( self.tree, location )

            # Now process the actual properties and styles
            for element in self.tree:
                sublocation = element.tag + ' ' + location
                #print( "\nProcessing {}...".format( sublocation ) )
                if element.tag == 'property':
                    if 'properties' not in self.DBLStyles: self.DBLStyles['properties'] = OrderedDict()
                    BibleOrgSysGlobals.checkXMLNoSubelements( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )
                    # Collect the property attributes first
                    name = None
                    attribDict = {}
                    for attrib,value in element.items():
                        if attrib=='name': name = value
                        else: attribDict[attrib] = value
                    if name in ( 'font-family', 'font-size' ):
                        self.DBLStyles['properties'][name] = ( element.text, attribDict )
                elif element.tag == 'style':
                    if 'styles' not in self.DBLStyles: self.DBLStyles['styles'] = OrderedDict()
                    getStyle( element, sublocation )
                else:
                    logging.warning( _("Unprocessed {} element in {}").format( element.tag, sublocation ) )
                    #self.addPriorityError( 1, c, v, _("Unprocessed {} element").format( element.tag ) )
        #print( '\n', self.DBLMetadata )
        if BibleOrgSysGlobals.verbosityLevel > 2: print( "  Loaded {} style elements.".format( len(self.DBLStyles['styles']) ) )
    # end of DBLBible.loadDBLStyles


    def loadDBLVersification( self ):
        """
        Load the versification.vrs file and parse it into the ordered dictionary self.DBLVersification.
        """
        if BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel > 2:
            print( t("loadDBLVersification()") )

        versificationFilename = 'versification.vrs'
        versificationFilepath = os.path.join( self.givenFolderName, versificationFilename )
        if BibleOrgSysGlobals.verbosityLevel > 2: print( "DBLBible.loading versification from {}...".format( versificationFilepath ) )

        self.DBLVersification = { 'VerseCounts':{}, 'Mappings':{}, 'Omitted':{} }

        lineCount = 0
        with open( versificationFilepath, 'rt' ) as vFile: # Automatically closes the file when done
            for line in vFile:
                lineCount += 1
                if lineCount==1 and line[0]==chr(65279): #U+FEFF
                    logging.info( "SFMLines: Detected UTF-16 Byte Order Marker in {}".format( versificationFilename ) )
                    line = line[1:] # Remove the UTF-8 Byte Order Marker
                if line[-1]=='\n': line=line[:-1] # Removing trailing newline character
                if not line: continue # Just discard blank lines
                lastLine = line
                if line[0]=='#' and not line.startswith('#!'): continue # Just discard comment lines
                #print( "line", repr(line) )

                if len(line)<7:
                    print( "Why was line #{} so short? {!r}".format( lineCount, line ) )
                    continue

                if line.startswith( '#! -' ): # It's an excluded verse (or passage???)
                    halt
                elif line[0] == '#': # It's a comment line
                    pass # Just ignore it
                elif '=' in line: # it's a verse mapping, e.g.,
                    left, right = line.split( ' = ', 1 )
                    #print( "left", repr(left), 'right', repr(right) )
                    self.DBLVersification['Mappings'][left] = right
                else: # It's a verse count line, e.g., LAM 1:22 2:22 3:66 4:22 5:22
                    assert( line[3] == ' ' )
                    USFMBookCode = line[:3]
                    #if USFMBookCode == 'ODA': USFMBookCode = 'ODE'
                    BBB = BibleOrgSysGlobals.BibleBooksCodes.getBBBFromUSFM( USFMBookCode )
                    self.DBLVersification['VerseCounts'][BBB] = OrderedDict()
                    for CVBit in line[4:].split():
                        #print( "CVBit", repr(CVBit) )
                        assert( ':' in CVBit )
                        C,V = CVBit.split( ':', 1 )
                        #print( "CV", repr(C), repr(V) )
                        self.DBLVersification['VerseCounts'][BBB][C] = V

        #print( '\n', self.DBLMetadata )
        if BibleOrgSysGlobals.verbosityLevel > 2: print( "  Loaded {} versification elements.".format( len(self.DBLVersification) ) )
    # end of DBLBible.loadDBLVersification


    def loadDBLLanguage( self ):
        """
        Load the something.lds file and parse it into the ordered dictionary self.DBLLanguage.
        """
        if BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel > 2:
            print( t("loadDBLLanguage()") )

        languageFilenames = []
        for something in os.listdir( self.givenFolderName ):
            somepath = os.path.join( self.givenFolderName, something )
            if os.path.isfile(somepath) and something.endswith('.lds'): languageFilenames.append( something )
        if len(languageFilenames) > 1:
            logging.error( "Got more than one language file: {}".format( languageFilenames ) )
        languageFilename = languageFilenames[0]
        languageName = languageFilename[:-4] # Remove the .lds

        languageFilepath = os.path.join( self.givenFolderName, languageFilename )
        if BibleOrgSysGlobals.verbosityLevel > 2: print( "DBLBible.loading language from {}...".format( languageFilepath ) )

        self.DBLLanguage = { 'Filename':languageName }

        lineCount = 0
        sectionName = None
        with open( languageFilepath, 'rt' ) as vFile: # Automatically closes the file when done
            for line in vFile:
                lineCount += 1
                if lineCount==1 and line[0]==chr(65279): #U+FEFF
                    logging.info( "SFMLines: Detected UTF-16 Byte Order Marker in {}".format( languageFilename ) )
                    line = line[1:] # Remove the UTF-8 Byte Order Marker
                if line[-1]=='\n': line=line[:-1] # Removing trailing newline character
                if not line: continue # Just discard blank lines
                lastLine = line
                if line[0]=='#': continue # Just discard comment lines
                #print( "line", repr(line) )

                if len(line)<5:
                    print( "Why was line #{} so short? {!r}".format( lineCount, line ) )
                    continue

                if line[0]=='[' and line[-1]==']': # it's a new section name
                    sectionName = line[1:-1]
                    assert( sectionName not in self.DBLLanguage )
                    self.DBLLanguage[sectionName] = {}
                elif '=' in line: # it's a mapping, e.g., UpperCaseLetters=ABCDEFGHIJKLMNOPQRSTUVWXYZ
                    left, right = line.split( '=', 1 )
                    #print( "left", repr(left), 'right', repr(right) )
                    self.DBLLanguage[sectionName][left] = right
                else: print( "What's this language line? {!r}".format( line ) )

        #print( '\n', self.DBLLanguage )
        if BibleOrgSysGlobals.verbosityLevel > 2: print( "  Loaded {} language sections.".format( len(self.DBLLanguage) ) )
    # end of DBLBible.loadDBLLanguage


    def xxxloadDBLBooksNames( self ):
        """
        """
        if BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel > 2:
            print( t("loadDBLBooksNames()") )
        if BibleOrgSysGlobals.verbosityLevel > 1: print( "DBLBible.loading books names from {}...".format( self.givenFolderName ) )
        bnFilepath = os.path.join( self.givenFolderName, "BookNames.xml" )
        self.tree = ElementTree().parse( bnFilepath )
        assert( len ( self.tree ) ) # Fail here if we didn't load anything at all

        self.booksNames = OrderedDict()
        #loadErrors = []

        # Find the main container
        if self.tree.tag=='BookNames':
            location = "DBL {} file".format( self.tree.tag )
            BibleOrgSysGlobals.checkXMLNoAttributes( self.tree, location )
            BibleOrgSysGlobals.checkXMLNoText( self.tree, location )
            BibleOrgSysGlobals.checkXMLNoTail( self.tree, location )

            # Now process the actual book data
            for element in self.tree:
                sublocation = element.tag + ' ' + location
                if element.tag == 'book':
                    BibleOrgSysGlobals.checkXMLNoSubelements( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoText( element, sublocation )
                    BibleOrgSysGlobals.checkXMLNoTail( element, sublocation )

                    bnCode = bnAbbr = bnShort = bnLong = None
                    for attrib,value in element.items():
                        if attrib=='code': bnCode = value
                        elif attrib=='abbr': bnAbbr = value
                        elif attrib=='short': bnShort = value
                        elif attrib=='long': bnLong = value
                        else: logging.warning( _("Unprocessed {} attribute ({}) in {}").format( attrib, value, location ) )
                    #print( bnCode, self.booksNames[bnCode] )
                    assert( len(bnCode)==3 )
                    self.booksNames[bnCode] = (bnAbbr,bnShort,bnLong,)
                else:
                    logging.warning( _("Unprocessed {} element in {}").format( element.tag, sublocation ) )
        #print( '\n', self.booksNames )
        if BibleOrgSysGlobals.verbosityLevel > 2: print( "  Loaded {} books names.".format( len(self.booksNames) ) )
    # end of DBLBible.loadDBLBooksNames


    def loadBooks( self ):
        """
        Load the USX XML Bible text files.
        """
        if BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel > 2:
            print( t("loadBooks()") )
        if BibleOrgSysGlobals.verbosityLevel > 1: print( _("DBLBible: Loading {} books from {}...").format( self.name, self.givenFolderName ) )

        # Do a preliminary check on the contents of our folder
        foundFiles, foundFolders = [], []
        for something in os.listdir( self.givenFolderName ):
            somepath = os.path.join( self.givenFolderName, something )
            if os.path.isdir( somepath ): foundFolders.append( something )
            elif os.path.isfile( somepath ): foundFiles.append( something )
            else: print( "ERROR: Not sure what '{}' is in {}!".format( somepath, self.givenFolderName ) )
        if not foundFolders: # We need a USX folder
            print( "DBLBible.loadBooks: Couldn't find any folders in '{}'".format( self.givenFolderName ) )
            return # No use continuing

        # Determine which is the USX subfolder
        possibilities = []
        haveDefault = False
        for someKey in self.DBLMetadata['contents']:
            if someKey.startswith( 'bookList' ): possibilities.append( someKey )
            if '(default)' in someKey: haveDefault = someKey
        #print( "possibilities", possibilities )
        bookListKey = haveDefault if haveDefault else possibilities[0]
        USXFolderName = 'USX_' + bookListKey[9:10]
        #print( "USXFolderName", USXFolderName )
        self.USXFolderPath = os.path.join( self.givenFolderName, USXFolderName + '/' )

        ## Work out our filenames
        #self.USXFilenamesObject = USXFilenames( self.USXFolderPath )
        #print( "fo", self.USXFilenamesObject )

        # Load the books one by one -- assuming that they have regular Paratext style filenames
        for USFMBookCode in self.DBLMetadata['contents'][bookListKey]:
            #print( USFMBookCode )
            BBB = BibleOrgSysGlobals.BibleBooksCodes.getBBBFromUSFM( USFMBookCode )
            filename = USFMBookCode + '.usx'
            UBB = USXXMLBibleBook( self, BBB )
            UBB.load( filename, self.USXFolderPath, self.encoding )
            UBB.validateMarkers()
            #print( UBB )
            self.books[BBB] = UBB
            # Make up our book name dictionaries while we're at it
            assumedBookNames = UBB.getAssumedBookNames()
            for assumedBookName in assumedBookNames:
                self.BBBToNameDict[BBB] = assumedBookName
                assumedBookNameLower = assumedBookName.lower()
                self.bookNameDict[assumedBookNameLower] = BBB # Store the deduced book name (just lower case)
                self.combinedBookNameDict[assumedBookNameLower] = BBB # Store the deduced book name (just lower case)
                if ' ' in assumedBookNameLower: self.combinedBookNameDict[assumedBookNameLower.replace(' ','')] = BBB # Store the deduced book name (lower case without spaces)

        if not self.books: # Didn't successfully load any regularly named books -- maybe the files have weird names??? -- try to be intelligent here
            if BibleOrgSysGlobals.verbosityLevel > 2:
                print( "DBLBible.load: Didn't find any regularly named USX files in '{}'".format( self.USXFolderPath ) )
            #for thisFilename in foundFiles:
                ## Look for BBB in the ID line (which should be the first line in a USX file)
                #isUSX = False
                #thisPath = os.path.join( self.givenFolderName, thisFilename )
                #with open( thisPath ) as possibleUSXFile: # Automatically closes the file when done
                    #for line in possibleUSXFile:
                        #if line.startswith( '\\id ' ):
                            #USXId = line[4:].strip()[:3] # Take the first three non-blank characters after the space after id
                            #if BibleOrgSysGlobals.verbosityLevel > 2: print( "Have possible USX ID '{}'".format( USXId ) )
                            #BBB = BibleOrgSysGlobals.BibleBooksCodes.getBBBFromUSFM( USXId )
                            #if BibleOrgSysGlobals.verbosityLevel > 2: print( "BBB is '{}'".format( BBB ) )
                            #isUSX = True
                        #break # We only look at the first line
                #if isUSX:
                    #UBB = USXXMLBibleBook( self, BBB )
                    #UBB.load( self.givenFolderName, thisFilename, self.encoding )
                    #UBB.validateMarkers()
                    #print( UBB )
                    #self.books[BBB] = UBB
                    ## Make up our book name dictionaries while we're at it
                    #assumedBookNames = UBB.getAssumedBookNames()
                    #for assumedBookName in assumedBookNames:
                        #self.BBBToNameDict[BBB] = assumedBookName
                        #assumedBookNameLower = assumedBookName.lower()
                        #self.bookNameDict[assumedBookNameLower] = BBB # Store the deduced book name (just lower case)
                        #self.combinedBookNameDict[assumedBookNameLower] = BBB # Store the deduced book name (just lower case)
                        #if ' ' in assumedBookNameLower: self.combinedBookNameDict[assumedBookNameLower.replace(' ','')] = BBB # Store the deduced book name (lower case without spaces)
            #if self.books: print( "DBLBible.load: Found {} irregularly named USX files".format( len(self.books) ) )
        self.doPostLoadProcessing()
    # end of DBLBible.loadBooks
# end of class DBLBible



def demo():
    """
    Demonstrate reading and checking some Bible databases.
    """
    if BibleOrgSysGlobals.verbosityLevel > 0: print( ProgNameVersion )

    testFolder = "Tests/DataFilesForTests/DBLTest/"

    if 1: # demo the file checking code -- first with the whole folder and then with only one folder
        result1 = DBLBibleFileCheck( testFolder )
        if BibleOrgSysGlobals.verbosityLevel > 1: print( "DBL TestA1", result1 )
        result2 = DBLBibleFileCheck( testFolder, autoLoad=True )
        if BibleOrgSysGlobals.verbosityLevel > 1: print( "DBL TestA2", result2 )
        result3 = DBLBibleFileCheck( testFolder, autoLoadBooks=True )
        if BibleOrgSysGlobals.verbosityLevel > 1: print( "DBL TestA3", result3 )

    if 0: # specify testFolder containing a single module
        if BibleOrgSysGlobals.verbosityLevel > 1: print( "\nDBL B/ Trying single module in {}".format( testFolder ) )
        testDBL_B( testFolder )

    if 0: # specified single installed module
        singleModule = 'ASV'
        if BibleOrgSysGlobals.verbosityLevel > 1: print( "\nDBL C/ Trying installed {} module".format( singleModule ) )
        DBL_Bible = testDBL_B( None, singleModule )
        if BibleOrgSysGlobals.debugFlag and debuggingThisModule: # Print the index of a small book
            BBB = 'JN1'
            if BBB in DBL_Bible:
                DBL_Bible.books[BBB].debugPrint()
                for entryKey in DBL_Bible.books[BBB]._CVIndex:
                    print( BBB, entryKey, DBL_Bible.books[BBB]._CVIndex.getEntries( entryKey ) )

    if 0: # specified installed modules
        good = ('KJV','WEB','KJVA','YLT','ASV','LEB','ESV','ISV','NET','OEB',
                'AB','ABP','ACV','AKJV','BBE','BSV','BWE','CPDV','Common','DRC','Darby',
                'EMTV','Etheridge','Geneva1599','Godbey','GodsWord','JPS','KJVPCE','LITV','LO','Leeser',
                'MKJV','Montgomery','Murdock','NETfree','NETtext','NHEB','NHEBJE','NHEBME','Noyes',
                'OEBcth','OrthJBC','RKJNT','RNKJV','RWebster','RecVer','Rotherham',
                'SPE','TS1998','Twenty','Tyndale','UKJV','WEBBE','WEBME','Webster','Weymouth','Worsley',)
        nonEnglish = (  )
        bad = ( )
        for j, testFilename in enumerate( good ): # Choose one of the above: good, nonEnglish, bad
            if BibleOrgSysGlobals.verbosityLevel > 1: print( "\nDBL D{}/ Trying {}".format( j+1, testFilename ) )
            #myTestFolder = os.path.join( testFolder, testFilename+'/' )
            #testFilepath = os.path.join( testFolder, testFilename+'/', testFilename+'_utf8.txt' )
            testDBL_B( testFolder, testFilename )


    if 0: # all discovered modules in the test folder
        foundFolders, foundFiles = [], []
        for something in os.listdir( testFolder ):
            somepath = os.path.join( testFolder, something )
            if os.path.isdir( somepath ): foundFolders.append( something )
            elif os.path.isfile( somepath ): foundFiles.append( something )

        if BibleOrgSysGlobals.maxProcesses > 1: # Get our subprocesses ready and waiting for work
            if BibleOrgSysGlobals.verbosityLevel > 1: print( "\nTrying all {} discovered modules...".format( len(foundFolders) ) )
            parameters = [(testFolder,folderName) for folderName in sorted(foundFolders)]
            with multiprocessing.Pool( processes=BibleOrgSysGlobals.maxProcesses ) as pool: # start worker processes
                results = pool.map( testDBL_B, parameters ) # have the pool do our loads
                assert( len(results) == len(parameters) ) # Results (all None) are actually irrelevant to us here
        else: # Just single threaded
            for j, someFolder in enumerate( sorted( foundFolders ) ):
                if BibleOrgSysGlobals.verbosityLevel > 1: print( "\nDBL E{}/ Trying {}".format( j+1, someFolder ) )
                #myTestFolder = os.path.join( testFolder, someFolder+'/' )
                testDBL_B( testFolder, someFolder )
    if 0:
        testFolders = (
                    "Tests/DataFilesForTests/DBLTest/",
                    ) # You can put your DBL test folder here

        for testFolder in testFolders:
            if os.access( testFolder, os.R_OK ):
                DB = DBLBible( testFolder )
                DB.loadDBLMetadata()
                DB.load()
                if BibleOrgSysGlobals.verbosityLevel > 0: print( DB )
                if BibleOrgSysGlobals.strictCheckingFlag: DB.check()
                #DBErrors = DB.getErrors()
                # print( DBErrors )
                #print( DB.getVersification () )
                #print( DB.getAddedUnits () )
                #for ref in ('GEN','Genesis','GeNeSiS','Gen','MrK','mt','Prv','Xyz',):
                    ##print( "Looking for", ref )
                    #print( "Tried finding '{}' in '{}': got '{}'".format( ref, name, UB.getXRefBBB( ref ) ) )
            else: print( "Sorry, test folder '{}' is not readable on this computer.".format( testFolder ) )

    if 0:
        testFolders = (
                    "Tests/DataFilesForTests/theWordRoundtripTestFiles/acfDBL 2013-02-03",
                    "Tests/DataFilesForTests/theWordRoundtripTestFiles/aucDBL 2013-02-26",
                    ) # You can put your DBL test folder here

        for testFolder in testFolders:
            if os.access( testFolder, os.R_OK ):
                DB = DBLBible( testFolder )
                DB.loadDBLBooksNames()
                #DB.load()
                if BibleOrgSysGlobals.verbosityLevel > 0: print( DB )
                if BibleOrgSysGlobals.strictCheckingFlag: DB.check()
                #DBErrors = DB.getErrors()
                # print( DBErrors )
                #print( DB.getVersification () )
                #print( DB.getAddedUnits () )
                #for ref in ('GEN','Genesis','GeNeSiS','Gen','MrK','mt','Prv','Xyz',):
                    ##print( "Looking for", ref )
                    #print( "Tried finding '{}' in '{}': got '{}'".format( ref, name, UB.getXRefBBB( ref ) ) )
            else: print( "Sorry, test folder '{}' is not readable on this computer.".format( testFolder ) )

    #if BibleOrgSysGlobals.commandLineOptions.export:
    #    if BibleOrgSysGlobals.verbosityLevel > 0: print( "NOTE: This is {} V{} -- i.e., not even alpha quality software!".format( ProgName, ProgVersion ) )
    #       pass

if __name__ == '__main__':
    # Configure basic set-up
    parser = BibleOrgSysGlobals.setup( ProgName, ProgVersion )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    demo()

    BibleOrgSysGlobals.closedown( ProgName, ProgVersion )
# end of DBLBible.py