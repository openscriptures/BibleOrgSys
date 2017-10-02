#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# LDML.py
#
# Module handling Unicode LOCALE DATA MARKUP LANGUAGE (XML) files
#
# Copyright (C) 2017 Robert Hunt
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
Module handling / reading Unicode LDML XML files.
    LDML = Locale Data Markup Language (see http://unicode.org/reports/tr35/tr35-4.html)

The XML data file is loaded into a Python dictionary and made available in
    that form.

This module (and most of the Bible Organisational System / BOS modules that
    load XML files) do it quite manually and quite pedantically. Although
    this makes what could be simple code quite long, it does allow us to
    be alerted if/when the file format (which we have no control over) is
    modified or extended.

The module is tested on LDML files from the SIL NRSI Github repository
    at https://github.com/silnrsi
"""

from gettext import gettext as _

LastModifiedDate = '2017-10-02' # by RJH
ShortProgName = "LDML_Handler"
ProgName = "Unicode LOCALE DATA MARKUP LANGUAGE handler"
ProgVersion = '0.05'
ProgNameVersion = '{} v{}'.format( ShortProgName, ProgVersion )
ProgNameVersionDate = '{} {} {}'.format( ProgNameVersion, _("last modified"), LastModifiedDate )

debuggingThisModule = False


import sys, os, logging
from collections import OrderedDict
import multiprocessing
from xml.etree.ElementTree import ElementTree

import BibleOrgSysGlobals



def exp( messageString ):
    """
    Expands the message string in debug mode.
    Prepends the module name to a error or warning message string
        if we are in debug mode.
    Returns the new string.
    """
    try: nameBit, errorBit = messageString.split( ': ', 1 )
    except ValueError: nameBit, errorBit = '', messageString
    if BibleOrgSysGlobals.debugFlag or debuggingThisModule:
        nameBit = '{}{}{}'.format( ShortProgName, '.' if nameBit else '', nameBit )
    return '{}{}'.format( nameBit+': ' if nameBit else '', errorBit )
# end of exp



def getFlagFromAttribute( attributeName, attributeValue ):
    """
    Get a 'true' or 'false' string and convert to True/False.
    """
    if attributeValue == 'true': return True
    if attributeValue == 'false': return False
    logging.error( _("Unexpected {} attribute value of {}").format( attributeName, attributeValue ) )
    return attributeValue
# end of getFlagFromAttribute

def getFlagFromText( subelement ):
    """
    Get a 'true' or 'false' string and convert to True/False.
    """
    if subelement.text == 'true': return True
    if subelement.text == 'false': return False
    logging.error( _("Unexpected {} text value of {}").format( subelement.tag, subelement.text ) )
    return subelement.text
# end of getFlagFromText



class LDMLFile:
    """
    A class to load and validate the XML Unicode LOCALE DATA MARKUP LANGUAGE files.
    """
    def __init__( self, givenFolderName, givenFilename ):
        """
        """
        assert givenFolderName
        assert givenFilename
        assert givenFilename.endswith( '.ldml' ) or givenFilename.endswith( '.xml' )

        self.givenFolderName, self.givenFilename = givenFolderName, givenFilename
        self.filepath = os.path.join( givenFolderName, givenFilename )
        self.languageCode = givenFilename[:-5] # Remove the .ldml
    # end of LDMLFile.__init__


    def load( self ):
        """
        Load the something.ldml file (which is an LDML file) and parse it into the dictionary PTXLanguages.

        LDML = Locale Data Markup Language (see http://unicode.org/reports/tr35/tr35-4.html)
        """
        if BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel > 2:
            print( exp("load()") )

        urnPrefix = '{urn://www.sil.org/ldml/0.1}'
        lenUrnPrefix = len( urnPrefix )
        def removeSILPrefix( someText ):
            """
            Remove the SIL URN which might be prefixed to the element tag.
            """
            if someText and someText.startswith( urnPrefix ): return someText[lenUrnPrefix:]
            return someText
        # end of removeSILPrefix


        def loadIdentity( element, elementLocation, identity ):
            """
            Returns the updated dictionary.
            """
            for subelement in element:
                subelementLocation = subelement.tag + ' in ' + elementLocation
                #if debuggingThisModule: print( "    Processing {}…".format( subelementLocation ) )
                BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                if subelement.tag == 'version':
                    BibleOrgSysGlobals.checkXMLNoSubelements( subelement, subelementLocation )
                    number = None
                    for attrib,value in subelement.items():
                        if attrib=='number': number = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    assert subelement.tag not in identity
                    identity[subelement.tag] = number
                elif subelement.tag == 'generation':
                    BibleOrgSysGlobals.checkXMLNoSubelements( subelement, subelementLocation )
                    date = None
                    for attrib,value in subelement.items():
                        if attrib=='date': date = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    assert subelement.tag not in identity
                    identity[subelement.tag] = date
                elif subelement.tag in ('language','territory'):
                    BibleOrgSysGlobals.checkXMLNoSubelements( subelement, subelementLocation )
                    lgType = None
                    for attrib,value in subelement.items():
                        if attrib=='type': lgType = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    assert subelement.tag not in identity
                    identity[subelement.tag] = lgType
                elif subelement.tag == 'special':
                    BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing {}…".format( sub2elementLocation ) )
                        BibleOrgSysGlobals.checkXMLNoText( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        windowsLCID = draft = source = None
                        for attrib,value in sub2element.items():
                            if attrib=='windowsLCID': windowsLCID = value
                            elif attrib=='draft': draft = value
                            elif attrib=='source': source = value
                            else:
                                logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                        assert subelement.tag not in identity
                        identity[subelement.tag] = {'tag':sub2element.tag,'windowsLCID':windowsLCID,'draft':draft,'source':source}
                else:
                    logging.error( _("Unprocessed {!r} subelement ({}) in {}").format( subelement.tag, subelement.text.strip(), elementLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
            return identity
        # end of loadIdentity


        def loadCharacters( element, elementLocation, characters ):
            """
            Returns the updated dictionary.
            """
            for subelement in element:
                subelementLocation = subelement.tag + ' in ' + elementLocation
                #if debuggingThisModule: print( "    Processing {}…".format( subelementLocation ) )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                if subelement.tag == 'exemplarCharacters':
                    BibleOrgSysGlobals.checkXMLNoSubelements( subelement, subelementLocation )
                    ecType = None
                    for attrib,value in subelement.items():
                        if attrib=='type': ecType = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    if subelement.tag not in characters:
                        characters[subelement.tag] = []
                    characters[subelement.tag].append( (ecType,subelement.text) )
                elif subelement.tag == 'special':
                    BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                    assert subelement.tag not in characters
                    characters[subelement.tag] = {}
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing {}…".format( sub2elementLocation ) )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        secType = None
                        for attrib,value in sub2element.items():
                            if attrib=='type': secType = value
                            else:
                                logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                        if sub2element.tag not in characters[subelement.tag]:
                            characters[subelement.tag][sub2element.tag] = []
                        characters[subelement.tag][sub2element.tag].append( (secType,sub2element.text) )
                else:
                    logging.error( _("Unprocessed {!r} subelement ({}) in {}").format( subelement.tag, subelement.text.strip(), elementLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
            return characters
        # end of loadCharacters


        def loadDelimiters( element, elementLocation, delimiters ):
            """
            Returns the updated dictionary.
            """
            for subelement in element:
                subelementLocation = subelement.tag + ' in ' + elementLocation
                #if debuggingThisModule: print( "    Processing {}…".format( subelementLocation ) )
                BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                if subelement.tag in ('quotationStart','quotationEnd','alternateQuotationStart','alternateQuotationEnd',):
                    BibleOrgSysGlobals.checkXMLNoSubelements( subelement, subelementLocation )
                    assert subelement.tag not in delimiters
                    delimiters[subelement.tag] = subelement.text
                elif subelement.tag == 'special':
                    BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                    assert subelement.tag not in delimiters
                    delimiters[subelement.tag] = OrderedDict()
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        adjusted2Tag = removeSILPrefix( sub2element.tag )
                        #if debuggingThisModule: print( "      Processing {}…".format( sub2elementLocation ) )
                        BibleOrgSysGlobals.checkXMLNoText( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if adjusted2Tag not in delimiters:
                            delimiters[subelement.tag][adjusted2Tag] = {}
                        paraContinueType = None
                        for attrib,value in sub2element.items():
                            #print( "here9", attrib, value )
                            if attrib=='paraContinueType': paraContinueType = value
                            else:
                                logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                        for sub3element in sub2element:
                            sub3elementLocation = sub3element.tag + ' in ' + sub2elementLocation
                            adjusted3Tag = removeSILPrefix( sub3element.tag )
                            #if debuggingThisModule: print( "        Processing {}…".format( sub3elementLocation ) )
                            #BibleOrgSysGlobals.checkXMLNoText( sub3element, sub3elementLocation, "ABC" )
                            BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                            BibleOrgSysGlobals.checkXMLNoSubelements( sub3element, sub3elementLocation )
                            openA = close = level = paraClose = pattern = context = qContinue = qType = None
                            for attrib,value in sub3element.items():
                                #print( attrib, value )
                                if attrib=='open': openA = value
                                elif attrib=='close': close = value
                                elif attrib=='level':
                                    level = value
                                    if debuggingThisModule: assert level in '123'
                                elif attrib=='paraClose':
                                    paraClose = value
                                    if debuggingThisModule: assert paraClose in ('false',)
                                elif attrib=='pattern': pattern = value
                                elif attrib=='context':
                                    context = value
                                    if debuggingThisModule: assert context in ('medial','final',)
                                elif attrib=='continue':
                                    qContinue = value
                                elif attrib=='type':
                                    qType = value
                                else:
                                    logging.error( _("DS Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub3elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            if adjusted3Tag not in delimiters[subelement.tag][adjusted2Tag]:
                                delimiters[subelement.tag][adjusted2Tag][adjusted3Tag] = []
                            delimiters[subelement.tag][adjusted2Tag][adjusted3Tag] \
                                    .append( (openA,close,level,paraClose,pattern,context,paraContinueType,qContinue,qType,sub3element.text) )
                else:
                    logging.error( _("Unprocessed {!r} subelement ({}) in {}").format( subelement.tag, subelement.text.strip(), elementLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
            #print( '\n', element.tag, LDMLData[element.tag] )
            return delimiters
        # end of loadDelimiters


        def loadLayout( element, elementLocation, layout ):
            """
            Returns the updated dictionary.
            """
            for subelement in element:
                subelementLocation = subelement.tag + ' in ' + elementLocation
                #if debuggingThisModule: print( "    Processing {}…".format( subelementLocation ) )
                BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                if subelement.tag == 'orientation':
                    assert subelement.tag not in layout
                    layout[subelement.tag] = {}
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing {}…".format( sub2elementLocation ) )
                        BibleOrgSysGlobals.checkXMLNoAttributes( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        assert sub2element.tag not in layout[subelement.tag]
                        layout[subelement.tag][sub2element.tag] = sub2element.text
                else:
                    logging.error( _("Unprocessed {!r} subelement ({}) in {}").format( subelement.tag, subelement.text.strip(), elementLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
            return layout
        # end of loadLayout


        def loadNumbers( element, elementLocation, numbers ):
            """
            Returns the updated dictionary.
            """
            currencies = {}
            percentFormats = {}
            for subelement in element:
                subelementLocation = subelement.tag + ' in ' + elementLocation
                #if debuggingThisModule: print( "    Processing {}…".format( subelementLocation ) )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                if subelement.tag == 'defaultNumberingSystem':
                    BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                    assert subelement.tag not in numbers
                    numbers[subelement.tag]  = subelement.text
                elif subelement.tag == 'numberingSystem':
                    BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                    nID = digits = nType = None
                    for attrib,value in subelement.items():
                        if attrib=='id': nID = value
                        elif attrib=='digits': digits = value
                        elif attrib=='type': nType = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    assert subelement.tag not in numbers
                    numbers[subelement.tag] = (nID,digits,nType)
                elif subelement.tag == 'symbols':
                    symbols = {}
                    BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                    numberSystem = None
                    for attrib,value in subelement.items():
                        if attrib=='numberSystem': numberSystem = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    if numberSystem not in symbols:
                        symbols[numberSystem] = {}
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing {} ({})…".format( sub2elementLocation, sub2element.tag.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoAttributes( sub2element, sub2elementLocation, "DGD361" )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag not in symbols[numberSystem]:
                            symbols[numberSystem][sub2element.tag] = sub2element.text
                    if symbols:
                        #print( "symbols", symbols )
                        assert subelement.tag not in numbers
                        numbers[subelement.tag] = symbols
                elif subelement.tag == 'currencyFormats':
                    currencyFormats = {}
                    BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                    numberSystem = None
                    for attrib,value in subelement.items():
                        if attrib=='numberSystem': numberSystem = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    if numberSystem not in currencyFormats:
                        currencyFormats[numberSystem] = {}
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing {} ({})…".format( sub2elementLocation, sub2element.tag.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoAttributes( sub2element, sub2elementLocation, "DGD461" )
                        BibleOrgSysGlobals.checkXMLNoText( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        #if sub2element.tag not in currencyFormats[numberSystem]:
                            #currencyFormats[numberSystem][sub2element.tag] = sub2element.text
                        if sub2element.tag == 'currencyFormatLength':
                            for sub3element in sub2element:
                                sub3elementLocation = sub3element.tag + ' in ' + sub2elementLocation
                                #if debuggingThisModule: print( "        Processing {} ({})…".format( sub3elementLocation, sub3element.text.strip() ) )
                                BibleOrgSysGlobals.checkXMLNoText( sub3element, sub3elementLocation )
                                BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                                if sub3element.tag == 'currencyFormat':
                                    draft = cfType = alt = None
                                    for attrib,value in sub3element.items():
                                        #if attrib=='draft': draft = value
                                        if attrib=='type': cfType = value
                                        #elif attrib=='alt': alt = value
                                        else:
                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                    for sub4element in sub3element:
                                        sub4elementLocation = sub4element.tag + ' in ' + sub3elementLocation
                                        #if debuggingThisModule: print( "          ProcessingCF {} ({})…".format( sub4elementLocation, sub4element.text.strip() ) )
                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4elementLocation )
                                        if sub4element.tag == 'pattern':
                                            pDraft = None
                                            for attrib,value in sub4element.items():
                                                if attrib=='draft': pDraft = value
                                                else:
                                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                            pass # Save text XXXXX
                                        else:
                                            logging.error( _("Unprocessed {!r} sub4element ({}) in {}").format( sub4element.tag, sub4element.text.strip(), sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                else:
                                    logging.error( _("Unprocessed {!r} sub3element ({}) in {}").format( sub3element.tag, sub3element.text.strip(), sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                    if currencyFormats:
                        #print( "currencyFormats", currencyFormats )
                        assert subelement.tag not in numbers
                        numbers[subelement.tag] = currencyFormats
                elif subelement.tag == 'currencies':
                    BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoText( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'currency':
                            cuType = None
                            for attrib,value in sub2element.items():
                                #if attrib=='draft': draft = value
                                if attrib=='type': cuType = value
                                #elif attrib=='alt': alt = value
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            assert cuType not in currencies
                            currencies[cuType] = {}
                            for sub3element in sub2element:
                                sub3elementLocation = sub3element.tag + ' in ' + sub2elementLocation
                                #if debuggingThisModule: print( "        Processing {} ({})…".format( sub3elementLocation, sub3element.text.strip() ) )
                                BibleOrgSysGlobals.checkXMLNoSubelements( sub3element, sub3elementLocation )
                                BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                                displayNames = []
                                symbols = []
                                if sub3element.tag == 'displayName':
                                    dnCount = None
                                    for attrib,value in sub3element.items():
                                        #if attrib=='draft': draft = value
                                        if attrib=='count': dnCount = value
                                        #elif attrib=='alt': alt = value
                                        else:
                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                    displayNames.append( (dnCount,sub3element.text) )
                                elif sub3element.tag == 'symbol':
                                    BibleOrgSysGlobals.checkXMLNoAttributes( sub3element, sub3elementLocation )
                                    symbols.append( sub3element.text )
                                elif sub3element.tag == 'pattern':
                                    BibleOrgSysGlobals.checkXMLNoAttributes( sub3element, sub3elementLocation )
                                    symbols.append( sub3element.text )
                                else:
                                    logging.error( _("Unprocessed {!r} sub3element ({}) in {}").format( sub3element.tag, sub3element.text.strip(), sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                            if displayNames:
                                assert 'displayNames' not in currencies[cuType]
                                currencies[cuType]['displayNames']= displayNames
                            if symbols:
                                assert 'symbols' not in currencies[cuType]
                                currencies[cuType]['symbols']= symbols
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                    if currencies:
                        #print( "currencies", currencies )
                        assert subelement.tag not in numbers
                        numbers[subelement.tag] = currencies

                elif subelement.tag == 'percentFormats':
                    BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                    numberSystem = None
                    for attrib,value in subelement.items():
                        #if attrib=='draft': draft = value
                        if attrib=='numberSystem': numberSystem = value
                        #elif attrib=='alt': alt = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoAttributes( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoText( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'percentFormat':
                            for sub3element in sub2element:
                                sub3elementLocation = sub3element.tag + ' in ' + sub2elementLocation
                                #if debuggingThisModule: print( "        Processing {} ({})…".format( sub3elementLocation, sub3element.text.strip() ) )
                                BibleOrgSysGlobals.checkXMLNoSubelements( sub3element, sub3elementLocation )
                                BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                                displayNames = []
                                symbols = []
                                if sub3element.tag == 'displayName':
                                    dnCount = None
                                    for attrib,value in sub3element.items():
                                        #if attrib=='draft': draft = value
                                        if attrib=='count': dnCount = value
                                        #elif attrib=='alt': alt = value
                                        else:
                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                    displayNames.append( (dnCount,sub3element.text) )
                                elif sub3element.tag == 'symbol':
                                    BibleOrgSysGlobals.checkXMLNoAttributes( sub3element, sub3elementLocation )
                                    symbols.append( sub3element.text )
                                else:
                                    logging.error( _("Unprocessed {!r} sub3element ({}) in {}").format( sub3element.tag, sub3element.text.strip(), sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                            if displayNames:
                                assert 'displayNames' not in percentFormats[cuType]
                                percentFormats[cuType]['displayNames']= displayNames
                            if symbols:
                                assert 'symbols' not in percentFormats[cuType]
                                percentFormats[cuType]['symbols']= symbols
                        elif sub2element.tag == 'percentFormatLength':
                            for sub3element in sub2element:
                                sub3elementLocation = sub3element.tag + ' in ' + sub2elementLocation
                                #if debuggingThisModule: print( "        Processing {} ({})…".format( sub3elementLocation, sub3element.text.strip() ) )
                                BibleOrgSysGlobals.checkXMLNoAttributes( sub3element, sub3elementLocation )
                                BibleOrgSysGlobals.checkXMLNoText( sub3element, sub3elementLocation )
                                BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                                if sub3element.tag == 'percentFormat':
                                    for sub4element in sub3element:
                                        sub4elementLocation = sub4element.tag + ' in ' + sub3elementLocation
                                        #if debuggingThisModule: print( "          Processing {} ({})…".format( sub4elementLocation, sub4element.text.strip() ) )
                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4elementLocation )
                                        if sub4element.tag == 'pattern':
                                            pDraft = None
                                            for attrib,value in sub4element.items():
                                                if attrib=='draft': pDraft = value
                                                else:
                                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                            pass # Save text XXXXX
                                        else:
                                            logging.error( _("Unprocessed {!r} sub4element ({}) in {}").format( sub4element.tag, sub4element.text.strip(), sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                else:
                                    logging.error( _("Unprocessed {!r} sub3element ({}) in {}").format( sub3element.tag, sub3element.text.strip(), sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                    if percentFormats:
                        #print( "percentFormats", percentFormats )
                        assert subelement.tag not in numbers
                        numbers[subelement.tag] = percentFormats

                elif subelement.tag == 'minimumGroupingDigits':
                    BibleOrgSysGlobals.checkXMLNoSubelements( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                    mgdDraft = None
                    for attrib,value in subelement.items():
                        if attrib=='draft': mgdDraft = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    pass # save text XXXXXXXXXXXXXXXXXXX

                else:
                    logging.error( _("Unprocessed {!r} subelement ({}) in {}").format( subelement.tag, subelement.text.strip(), elementLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
            return numbers
        # end of loadNumbers


        def loadCollations( element, elementLocation, collations ):
            """
            Returns the updated dictionary.
            """
            for subelement in element:
                subelementLocation = subelement.tag + ' in ' + elementLocation
                #if debuggingThisModule: print( "    Processing {}…".format( subelementLocation ) )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                if subelement.tag == 'defaultCollation':
                    BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoSubelements( subelement, subelementLocation )
                    assert subelement.tag not in collations
                    collations[subelement.tag]  = subelement.text
                elif subelement.tag == 'collation':
                    BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                    assert subelement.tag not in collations
                    collations[subelement.tag] = {}
                    cType = None
                    for attrib,value in subelement.items():
                        if attrib=='type': cType = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    assert cType not in collations[subelement.tag]
                    collations[subelement.tag][cType] = {}
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing {}…".format( sub2elementLocation ) )
                        BibleOrgSysGlobals.checkXMLNoAttributes( sub2element, sub2elementLocation, "DGD561" )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag not in collations[subelement.tag][cType]:
                            collations[subelement.tag][cType][sub2element.tag] = {}
                        for sub3element in sub2element:
                            sub3elementLocation = sub3element.tag + ' in ' + sub2elementLocation
                            #if debuggingThisModule: print( "        Processing {}…".format( sub3elementLocation ) )
                            BibleOrgSysGlobals.checkXMLNoAttributes( sub3element, sub3elementLocation, "DSD354" )
                            BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                            BibleOrgSysGlobals.checkXMLNoSubelements( sub3element, sub3elementLocation )
                            if sub3element.tag not in collations[subelement.tag][cType][sub2element.tag]:
                                collations[subelement.tag][cType][sub2element.tag][sub3element.tag] = []
                            collations[subelement.tag][cType][sub2element.tag][sub3element.tag].append( sub3element.text )
                else:
                    logging.error( _("Unprocessed {!r} subelement ({}) in {}").format( subelement.tag, subelement.text.strip(), elementLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
            return collations
        # end of loadCollations


        def loadLocateDisplayNames( element, elementLocation, localeDisplayNames ):
            """
            Returns the updated dictionary.
            """
            languages = OrderedDict()
            territories = OrderedDict()
            keys = OrderedDict()
            types = OrderedDict()
            scripts = OrderedDict()
            variants = OrderedDict()
            codePatterns = OrderedDict()
            for subelement in element:
                subelementLocation = subelement.tag + ' in ' + elementLocation
                #if debuggingThisModule: print( "    Processing2 {} ({})…".format( subelementLocation, subelement.text.strip() ) )
                BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                if subelement.tag == 'languages':
                    languages = OrderedDict()
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      ProcessingLgs3a {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'language':
                            lDraft = lType = lAlt = None
                            for attrib,value in sub2element.items():
                                #print( "here Lg7", attrib, value )
                                if attrib=='draft': lDraft = value
                                elif attrib=='type': lType = value
                                elif attrib=='alt': lAlt = value; assert lAlt in ('short','long','variant')
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            #assert lType not in languages # XXXXXXXXXXXXXX losing some info here
                            languages[lType] = (lType,sub2element.text,lDraft)
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                    if languages:
                        assert subelement.tag not in localeDisplayNames
                        localeDisplayNames[subelement.tag] = languages
                elif subelement.tag == 'territories':
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing3b {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'territory':
                            tDraft = tType = tAlt = None
                            for attrib,value in sub2element.items():
                                #print( "hereT8", attrib, value )
                                if attrib=='draft': tDraft = value
                                elif attrib=='type': tType = value
                                elif attrib=='alt': tAlt = value; assert tAlt in ('short','variant')
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            #assert tType not in territories # Losing info here XXXXXXXXXXXXXXXXXXXXXXX
                            territories[tType] = (tType,sub2element.text,tDraft,tAlt)
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                elif subelement.tag == 'keys':
                    BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing3k {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'key':
                            draft = tType = alt = None
                            for attrib,value in sub2element.items():
                                #print( "hereK8", attrib, value )
                                #if attrib=='draft': draft = value
                                if attrib=='type': tType = value
                                #elif attrib=='alt': alt = value
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            assert tType not in territories
                            territories[tType] = (tType,sub2element.text,draft,alt)
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                elif subelement.tag == 'types':
                    BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing3t {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'type':
                            tKey = kType = kAlt = None
                            for attrib,value in sub2element.items():
                                #print( "hereT8", attrib, value )
                                #if attrib=='draft': draft = value
                                if attrib=='key': tKey = value # assert tKey in ('colNormalization','cf','numbers','d0','m0','collation','lw','calendar','kr','kv')
                                elif attrib=='type': kType = value
                                elif attrib=='alt': kAlt = value; assert kAlt in ('short',)#'variant','stand-alone')
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            #assert kType not in types # losing data here XXXXXXXXXXXXXXXXXXXXXXX
                            types[kType] = {'type':kType,'key':tKey,'value':sub2element.text}
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                elif subelement.tag == 'scripts':
                    BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing3scr {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'script':
                            key = sType = sAlt = None
                            for attrib,value in sub2element.items():
                                #print( "hereS8", attrib, value )
                                #if attrib=='draft': draft = value
                                if attrib=='type': sType = value
                                elif attrib=='alt': sAlt = value; assert sAlt in ('short','variant','stand-alone')
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            #assert sType not in scripts # XXXXXXXXXXXxx losing some info here
                            scripts[sType] = {'type':sType,'value':sub2element.text}
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                elif subelement.tag == 'variants':
                    BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      ProcessingV3 {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'variant':
                            key = vType = vAlt = None
                            for attrib,value in sub2element.items():
                                #print( "hereV8", attrib, value )
                                #if attrib=='draft': draft = value
                                if attrib=='type': vType = value
                                elif attrib=='alt': vAlt = value; assert vAlt in ('short',)#'variant','stand-alone')
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            assert vType not in variants
                            variants[vType] = {'type':vType,'value':sub2element.text}
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                elif subelement.tag == 'codePatterns':
                    BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                    BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      ProcessingCP6 {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'codePattern':
                            key = cpType = vAlt = None
                            for attrib,value in sub2element.items():
                                #print( "hereCP8", attrib, value )
                                if attrib=='type': cpType = value; assert cpType in ('language','script','territory')
                                #elif attrib=='xalt': vAlt = value; assert vAlt in ('short',)#'variant','stand-alone')
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            assert cpType not in codePatterns
                            codePatterns[cpType] = {'type':cpType,'value':sub2element.text}
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                else:
                    logging.error( _("Unprocessed {!r} subelement ({}) in {}").format( subelement.tag, subelement.text.strip(), elementLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
            if territories:
                assert 'territories' not in localeDisplayNames
                localeDisplayNames['territories'] = territories
            if keys:
                assert 'keys' not in localeDisplayNames
                localeDisplayNames['keys'] = keys
            if types:
                assert 'types' not in localeDisplayNames
                localeDisplayNames['types'] = types
            if scripts:
                assert 'scripts' not in localeDisplayNames
                localeDisplayNames['scripts'] = scripts
            if variants:
                assert 'variants' not in localeDisplayNames
                localeDisplayNames['variants'] = variants
            if codePatterns:
                assert 'codePatterns' not in localeDisplayNames
                localeDisplayNames['codePatterns'] = codePatterns
            return localeDisplayNames
        # end of loadLocateDisplayNames


        def loadDates( element, elementLocation, dates ):
            """
            Returns the updated dictionary.
            """
            dCalendars = OrderedDict()
            fields = OrderedDict()
            timeZoneNames = OrderedDict()
            for subelement in element:
                subelementLocation = subelement.tag + ' in ' + elementLocation
                #if debuggingThisModule: print( "    Processing2 {} ({})…".format( subelementLocation, subelement.text.strip() ) )
                BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                if subelement.tag == 'calendars':
                    dCalendar = OrderedDict()
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing3a {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoText( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'calendar':
                            cType = None
                            for attrib,value in sub2element.items():
                                #print( "here7", attrib, value )
                                #if attrib=='draft': draft = value
                                if attrib=='type': cType = value
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            dateTimeFormats = OrderedDict()
                            dayPeriods = OrderedDict()
                            for sub3element in sub2element:
                                sub3elementLocation = sub3element.tag + ' in ' + sub2elementLocation
                                #if debuggingThisModule: print( "        ProcessingD-C {} ({})…".format( sub3elementLocation, sub3element.text.strip() ) )
                                BibleOrgSysGlobals.checkXMLNoAttributes( sub3element, sub3elementLocation )
                                BibleOrgSysGlobals.checkXMLNoText( sub3element, sub3elementLocation )
                                BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                                if sub3element.tag == 'dateTimeFormats':
                                    for sub4element in sub3element:
                                        sub4elementLocation = sub4element.tag + ' in ' + sub3elementLocation
                                        #if debuggingThisModule: print( "          ProcessingDTF4 {} ({})…".format( sub4elementLocation, sub4element.text.strip() ) )
                                        BibleOrgSysGlobals.checkXMLNoText( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4elementLocation )
                                        if sub4element.tag == 'intervalFormats':
                                            BibleOrgSysGlobals.checkXMLNoAttributes( sub4element, sub4elementLocation )
                                            for sub5element in sub4element:
                                                sub5elementLocation = sub5element.tag + ' in ' + sub4elementLocation
                                                #if debuggingThisModule: print( "            ProcessingD5 {} ({})…".format( sub5elementLocation, sub5element.text.strip() ) )
                                                BibleOrgSysGlobals.checkXMLNoTail( sub5element, sub5elementLocation )
                                                if sub5element.tag == 'intervalFormatFallback':
                                                    BibleOrgSysGlobals.checkXMLNoSubelements( sub5element, sub5elementLocation )
                                                    draft = None
                                                    for attrib,value in sub5element.items():
                                                        #print( "here7", attrib, value )
                                                        if attrib=='draft': draft = value
                                                        #if attrib=='type': cType = value
                                                        else:
                                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                    pass # Save text XXXXXXXXXXXXXXX
                                                    for sub6element in sub5element:
                                                        sub6elementLocation = sub6element.tag + ' in ' + sub5elementLocation
                                                        #if debuggingThisModule: print( "              ProcessingD6 {} ({})…".format( sub6elementLocation, sub6element.text.strip() ) )
                                                        BibleOrgSysGlobals.checkXMLNoAttributes( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoText( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoTail( sub6element, sub6elementLocation )
                                                        if 1: pass
                                                        else:
                                                            logging.error( _("Unprocessed {!r} sub6element in {}").format( sub6element.tag, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                                elif sub5element.tag == 'intervalFormatItem':
                                                    BibleOrgSysGlobals.checkXMLNoText( sub5element, sub5elementLocation )
                                                    ifiID = None
                                                    for attrib,value in sub5element.items():
                                                        #print( "here7", attrib, value )
                                                        if attrib=='id': ifiID = value
                                                        #if attrib=='type': cType = value
                                                        else:
                                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                    pass # Save text XXXXXXXXXXXXXXX
                                                    for sub6element in sub5element:
                                                        sub6elementLocation = sub6element.tag + ' in ' + sub5elementLocation
                                                        #if debuggingThisModule: print( "              ProcessingD6 {} ({})…".format( sub6elementLocation, sub6element.text.strip() ) )
                                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoTail( sub6element, sub6elementLocation )
                                                        if 1: pass
                                                        else:
                                                            logging.error( _("Unprocessed {!r} sub6element in {}").format( sub6element.tag, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                                else:
                                                    logging.error( _("Unprocessed {!r} sub5element in {}").format( sub5element.tag, sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                            dateTimeFormats[sub4element.tag] = sub4element.text
                                        elif sub4element.tag == 'availableFormats':
                                            BibleOrgSysGlobals.checkXMLNoAttributes( sub4element, sub4elementLocation )
                                            for sub5element in sub4element:
                                                sub5elementLocation = sub5element.tag + ' in ' + sub4elementLocation
                                                #if debuggingThisModule: print( "            ProcessingAF5 {} ({})…".format( sub5elementLocation, sub5element.text.strip() ) )
                                                BibleOrgSysGlobals.checkXMLNoTail( sub5element, sub5elementLocation )
                                                if sub5element.tag == 'dateFormatItem':
                                                    BibleOrgSysGlobals.checkXMLNoSubelements( sub5element, sub5elementLocation )
                                                    dfiID = dfiDraft = None
                                                    for attrib,value in sub5element.items():
                                                        #print( "here7", attrib, value )
                                                        if attrib=='id': dfiID = value
                                                        elif attrib=='draft': dfiDraft = value
                                                        else:
                                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                    pass # Save text XXXXXXXXXXXXXXX
                                                else:
                                                    logging.error( _("Unprocessed {!r} sub5element in {}").format( sub5element.tag, sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                        elif sub4element.tag == 'dateTimeFormatLength':
                                            dtflType = dtflDraft = None
                                            for attrib,value in sub4element.items():
                                                #print( "here7", attrib, value )
                                                if attrib=='type': dtflType = value
                                                elif attrib=='draft': dtflDraft = value
                                                else:
                                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                        else:
                                            logging.error( _("Unprocessed {!r} sub4element ({}) in {}").format( sub4element.tag, sub4element.text.strip(), sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                elif sub3element.tag == 'dateFormats':
                                    for sub4element in sub3element:
                                        sub4elementLocation = sub4element.tag + ' in ' + sub3elementLocation
                                        #if debuggingThisModule: print( "          ProcessingDF4 {} ({})…".format( sub4elementLocation, sub4element.text.strip() ) )
                                        BibleOrgSysGlobals.checkXMLNoText( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4elementLocation )
                                        if sub4element.tag == 'intervalFormats':
                                            for sub5element in sub4element:
                                                sub5elementLocation = sub5element.tag + ' in ' + sub4elementLocation
                                                #if debuggingThisModule: print( "            ProcessingD5 {} ({})…".format( sub5elementLocation, sub5element.text.strip() ) )
                                                BibleOrgSysGlobals.checkXMLNoTail( sub5element, sub5elementLocation )
                                                if sub5element.tag == 'intervalFormatFallback':
                                                    BibleOrgSysGlobals.checkXMLNoSubelements( sub5element, sub5elementLocation )
                                                    draft = None
                                                    for attrib,value in sub5element.items():
                                                        #print( "here7", attrib, value )
                                                        if attrib=='draft': draft = value
                                                        #if attrib=='type': cType = value
                                                        else:
                                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                    pass # Save text XXXXXXXXXXXXXXX
                                                    for sub6element in sub5element:
                                                        sub6elementLocation = sub6element.tag + ' in ' + sub5elementLocation
                                                        #if debuggingThisModule: print( "              ProcessingD6 {} ({})…".format( sub6elementLocation, sub6element.text.strip() ) )
                                                        BibleOrgSysGlobals.checkXMLNoAttributes( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoText( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoTail( sub6element, sub6elementLocation )
                                                        if 1: pass
                                                        else:
                                                            logging.error( _("Unprocessed {!r} sub6element in {}").format( sub6element.tag, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                                elif sub5element.tag == 'intervalFormatItem':
                                                    BibleOrgSysGlobals.checkXMLNoText( sub5element, sub5elementLocation )
                                                    ifiID = None
                                                    for attrib,value in sub5element.items():
                                                        #print( "here7", attrib, value )
                                                        if attrib=='id': ifiID = value
                                                        #if attrib=='type': cType = value
                                                        else:
                                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                    pass # Save text XXXXXXXXXXXXXXX
                                                    for sub6element in sub5element:
                                                        sub6elementLocation = sub6element.tag + ' in ' + sub5elementLocation
                                                        #if debuggingThisModule: print( "              ProcessingD6 {} ({})…".format( sub6elementLocation, sub6element.text.strip() ) )
                                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoTail( sub6element, sub6elementLocation )
                                                        if 1: pass
                                                        else:
                                                            logging.error( _("Unprocessed {!r} sub6element in {}").format( sub6element.tag, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                                else:
                                                    logging.error( _("Unprocessed {!r} sub5element in {}").format( sub5element.tag, sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                            dateTimeFormats[sub4element.tag] = sub4element.text
                                        elif sub4element.tag == 'dateFormatLength':
                                            BibleOrgSysGlobals.checkXMLNoText( sub4element, sub4elementLocation )
                                            BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4elementLocation )
                                            dflType = None
                                            for attrib,value in sub4element.items():
                                                #print( "here7", attrib, value )
                                                #if attrib=='id': ifiID = value
                                                if attrib=='type': dflType = value
                                                else:
                                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                            for sub5element in sub4element:
                                                sub5elementLocation = sub5element.tag + ' in ' + sub4elementLocation
                                                #if debuggingThisModule: print( "            ProcessingD5 {} ({})…".format( sub5elementLocation, sub5element.text.strip() ) )
                                                BibleOrgSysGlobals.checkXMLNoAttributes( sub5element, sub5elementLocation )
                                                BibleOrgSysGlobals.checkXMLNoText( sub5element, sub5elementLocation )
                                                BibleOrgSysGlobals.checkXMLNoTail( sub5element, sub5elementLocation )
                                                if sub5element.tag == 'dateFormat':
                                                    for sub6element in sub5element:
                                                        sub6elementLocation = sub6element.tag + ' in ' + sub5elementLocation
                                                        #if debuggingThisModule: print( "              ProcessingD6 {} ({})…".format( sub6elementLocation, sub6element.text.strip() ) )
                                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoTail( sub6element, sub6elementLocation )
                                                        if sub6element.tag == 'pattern':
                                                            pDraft = None
                                                            for attrib,value in sub6element.items():
                                                                #print( "here7", attrib, value )
                                                                if attrib=='draft': pDraft = value; assert pDraft in ('unconfirmed',)
                                                                else:
                                                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub6elementLocation ) )
                                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                            pass # Save text xxxxxxxxxxxxxxx
                                                        else:
                                                            logging.error( _("Unprocessed {!r} sub6element in {}").format( sub6element.tag, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                                else:
                                                    logging.error( _("Unprocessed {!r} sub5element in {}").format( sub5element.tag, sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                        else:
                                            logging.error( _("Unprocessed {!r} sub4element in {}").format( sub4element.tag, sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                elif sub3element.tag == 'dayPeriods':
                                    for sub4element in sub3element:
                                        sub4elementLocation = sub4element.tag + ' in ' + sub3elementLocation
                                        #if debuggingThisModule: print( "          ProcessingDP1 {} ({})…".format( sub4elementLocation, sub4element.text.strip() ) )
                                        BibleOrgSysGlobals.checkXMLNoText( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4elementLocation )
                                        if sub4element.tag == 'dayPeriodContext':
                                            for sub5element in sub4element:
                                                sub5elementLocation = sub5element.tag + ' in ' + sub4elementLocation
                                                #if debuggingThisModule: print( "            ProcessingD5 {} ({})…".format( sub5elementLocation, sub5element.text.strip() ) )
                                                BibleOrgSysGlobals.checkXMLNoTail( sub5element, sub5elementLocation )
                                                if sub5element.tag == 'dayPeriodWidth':
                                                    dpwType = None
                                                    for attrib,value in sub5element.items():
                                                        #print( "here7", attrib, value )
                                                        #if attrib=='draft': draft = value
                                                        if attrib=='type': dpwType = value
                                                        else:
                                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                    pass # Save text XXXXXXXXXXXXXXX
                                                    for sub6element in sub5element:
                                                        sub6elementLocation = sub6element.tag + ' in ' + sub5elementLocation
                                                        #if debuggingThisModule: print( "              ProcessingD6 {} ({})…".format( sub6elementLocation, sub6element.text.strip() ) )
                                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoTail( sub6element, sub6elementLocation )
                                                        dpType = dpDraft = None
                                                        for attrib,value in sub6element.items():
                                                            #print( "here7", attrib, value )
                                                            if attrib=='type': dpType = value
                                                            elif attrib=='draft': dpDraft = value
                                                            else:
                                                                logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub6elementLocation ) )
                                                                if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                        pass # Save text field XXXXXXXXXXXXXX
                                                        if 1: pass
                                                        else:
                                                            logging.error( _("Unprocessed {!r} sub6element ({}) in {}").format( sub6element.tag, sub6element.text.strip(), sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                                elif sub5element.tag == 'intervalFormatItem':
                                                    BibleOrgSysGlobals.checkXMLNoText( sub5element, sub5elementLocation )
                                                    ifiID = None
                                                    for attrib,value in sub5element.items():
                                                        #print( "here7", attrib, value )
                                                        if attrib=='id': ifiID = value
                                                        #if attrib=='type': cType = value
                                                        else:
                                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                    pass # Save text XXXXXXXXXXXXXXX
                                                    for sub6element in sub5element:
                                                        sub6elementLocation = sub6element.tag + ' in ' + sub5elementLocation
                                                        #if debuggingThisModule: print( "              ProcessingD6 {} ({})…".format( sub6elementLocation, sub6element.text.strip() ) )
                                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoTail( sub6element, sub6elementLocation )
                                                        if 1: pass
                                                        else:
                                                            logging.error( _("Unprocessed {!r} sub6element in {}").format( sub6element.tag, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                                else:
                                                    logging.error( _("Unprocessed {!r} sub5element ({}) in {}").format( sub5element.tag, sub5element.text.strip(), sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                            dayPeriods[sub4element.tag] = sub4element.text
                                        else:
                                            logging.error( _("Unprocessed {!r} sub4element ({}) in {}").format( sub4element.tag, sub4element.text.strip(), sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                elif sub3element.tag == 'months':
                                    for sub4element in sub3element:
                                        sub4elementLocation = sub4element.tag + ' in ' + sub3elementLocation
                                        #if debuggingThisModule: print( "          ProcessingDP1 {} ({})…".format( sub4elementLocation, sub4element.text.strip() ) )
                                        BibleOrgSysGlobals.checkXMLNoText( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4elementLocation )
                                        if sub4element.tag == 'monthContext':
                                            mcType = None
                                            for attrib,value in sub4element.items():
                                                #print( "here7", attrib, value )
                                                #if attrib=='draft': draft = value
                                                if attrib=='type': mcType = value
                                                else:
                                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                            for sub5element in sub4element:
                                                sub5elementLocation = sub5element.tag + ' in ' + sub4elementLocation
                                                #if debuggingThisModule: print( "            ProcessingD5 {} ({})…".format( sub5elementLocation, sub5element.text.strip() ) )
                                                BibleOrgSysGlobals.checkXMLNoText( sub5element, sub5elementLocation )
                                                BibleOrgSysGlobals.checkXMLNoTail( sub5element, sub5elementLocation )
                                                if sub5element.tag == 'monthWidth':
                                                    mwType = None
                                                    for attrib,value in sub5element.items():
                                                        #print( "here7", attrib, value )
                                                        #if attrib=='draft': draft = value
                                                        if attrib=='type': mwType = value
                                                        else:
                                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                    for sub6element in sub5element:
                                                        sub6elementLocation = sub6element.tag + ' in ' + sub5elementLocation
                                                        #if debuggingThisModule: print( "              ProcessingD6 {} ({})…".format( sub6elementLocation, sub6element.text.strip() ) )
                                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoTail( sub6element, sub6elementLocation )
                                                        if sub6element.tag == 'month':
                                                            mType = mDraft = None
                                                            for attrib,value in sub6element.items():
                                                                #print( "here7", attrib, value )
                                                                if attrib=='type': mType = value
                                                                elif attrib=='draft': mDraft = value
                                                                else:
                                                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub6elementLocation ) )
                                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                            pass # Save text field XXXXXXXXXXXXXX
                                                        else:
                                                            logging.error( _("Unprocessed {!r} sub6element ({}) in {}").format( sub6element.tag, sub6element.text.strip(), sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                                else:
                                                    logging.error( _("Unprocessed {!r} sub5element ({}) in {}").format( sub5element.tag, sub5element.text.strip(), sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                        else:
                                            logging.error( _("Unprocessed {!r} sub4element ({}) in {}").format( sub4element.tag, sub4element.text.strip(), sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                elif sub3element.tag == 'days':
                                    for sub4element in sub3element:
                                        sub4elementLocation = sub4element.tag + ' in ' + sub3elementLocation
                                        #if debuggingThisModule: print( "          ProcessingDP1 {} ({})…".format( sub4elementLocation, sub4element.text.strip() ) )
                                        BibleOrgSysGlobals.checkXMLNoText( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4elementLocation )
                                        if sub4element.tag == 'dayContext':
                                            dcType = None
                                            for attrib,value in sub4element.items():
                                                #print( "here7", attrib, value )
                                                #if attrib=='draft': draft = value
                                                if attrib=='type': dcType = value
                                                else:
                                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                            for sub5element in sub4element:
                                                sub5elementLocation = sub5element.tag + ' in ' + sub4elementLocation
                                                #if debuggingThisModule: print( "            ProcessingD5 {} ({})…".format( sub5elementLocation, sub5element.text.strip() ) )
                                                BibleOrgSysGlobals.checkXMLNoText( sub5element, sub5elementLocation )
                                                BibleOrgSysGlobals.checkXMLNoTail( sub5element, sub5elementLocation )
                                                if sub5element.tag == 'dayWidth':
                                                    dwType = None
                                                    for attrib,value in sub5element.items():
                                                        #print( "here7", attrib, value )
                                                        #if attrib=='draft': draft = value
                                                        if attrib=='type': dwType = value
                                                        else:
                                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                    for sub6element in sub5element:
                                                        sub6elementLocation = sub6element.tag + ' in ' + sub5elementLocation
                                                        #if debuggingThisModule: print( "              ProcessingD6 {} ({})…".format( sub6elementLocation, sub6element.text.strip() ) )
                                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoTail( sub6element, sub6elementLocation )
                                                        if sub6element.tag == 'day':
                                                            mType = mDraft = None
                                                            for attrib,value in sub6element.items():
                                                                #print( "here7", attrib, value )
                                                                if attrib=='type': mType = value
                                                                elif attrib=='draft': mDraft = value
                                                                else:
                                                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub6elementLocation ) )
                                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                            pass # Save text field XXXXXXXXXXXXXX
                                                        else:
                                                            logging.error( _("Unprocessed {!r} sub6element ({}) in {}").format( sub6element.tag, sub6element.text.strip(), sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                                else:
                                                    logging.error( _("Unprocessed {!r} sub5element ({}) in {}").format( sub5element.tag, sub5element.text.strip(), sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                        else:
                                            logging.error( _("Unprocessed {!r} sub4element ({}) in {}").format( sub4element.tag, sub4element.text.strip(), sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                elif sub3element.tag == 'timeFormats':
                                    for sub4element in sub3element:
                                        sub4elementLocation = sub4element.tag + ' in ' + sub3elementLocation
                                        #if debuggingThisModule: print( "          ProcessingDP1 {} ({})…".format( sub4elementLocation, sub4element.text.strip() ) )
                                        BibleOrgSysGlobals.checkXMLNoText( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4elementLocation )
                                        if sub4element.tag == 'timeFormatLength':
                                            tflType = None
                                            for attrib,value in sub4element.items():
                                                #print( "here7", attrib, value )
                                                #if attrib=='draft': draft = value
                                                if attrib=='type': tflType = value
                                                else:
                                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                            for sub5element in sub4element:
                                                sub5elementLocation = sub5element.tag + ' in ' + sub4elementLocation
                                                #if debuggingThisModule: print( "            ProcessingD5 {} ({})…".format( sub5elementLocation, sub5element.text.strip() ) )
                                                BibleOrgSysGlobals.checkXMLNoAttributes( sub5element, sub5elementLocation )
                                                BibleOrgSysGlobals.checkXMLNoText( sub5element, sub5elementLocation )
                                                BibleOrgSysGlobals.checkXMLNoTail( sub5element, sub5elementLocation )
                                                if sub5element.tag == 'timeFormat':
                                                    for sub6element in sub5element:
                                                        sub6elementLocation = sub6element.tag + ' in ' + sub5elementLocation
                                                        #if debuggingThisModule: print( "              ProcessingD6 {} ({})…".format( sub6elementLocation, sub6element.text.strip() ) )
                                                        BibleOrgSysGlobals.checkXMLNoAttributes( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoTail( sub6element, sub6elementLocation )
                                                        if sub6element.tag == 'pattern':
                                                            pass # Save text field XXXXXXXXXXXXXX
                                                        else:
                                                            logging.error( _("Unprocessed {!r} sub6element ({}) in {}").format( sub6element.tag, sub6element.text.strip(), sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                                else:
                                                    logging.error( _("Unprocessed {!r} sub5element ({}) in {}").format( sub5element.tag, sub5element.text.strip(), sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                        else:
                                            logging.error( _("Unprocessed {!r} sub4element ({}) in {}").format( sub4element.tag, sub4element.text.strip(), sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                elif sub3element.tag == 'cyclicNameSets':
                                    for sub4element in sub3element:
                                        sub4elementLocation = sub4element.tag + ' in ' + sub3elementLocation
                                        if debuggingThisModule: print( "          ProcessingDP1 {} ({})…".format( sub4elementLocation, sub4element.text.strip() ) )
                                        BibleOrgSysGlobals.checkXMLNoText( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4elementLocation )
                                        if sub4element.tag == 'cyclicNameSet':
                                            cnsType = None
                                            for attrib,value in sub4element.items():
                                                #print( "here7", attrib, value )
                                                #if attrib=='draft': draft = value
                                                if attrib=='type': cnsType = value; assert cnsType in ('zodiacs',)
                                                else:
                                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                            for sub5element in sub4element:
                                                sub5elementLocation = sub5element.tag + ' in ' + sub4elementLocation
                                                #if debuggingThisModule: print( "            ProcessingD5 {} ({})…".format( sub5elementLocation, sub5element.text.strip() ) )
                                                BibleOrgSysGlobals.checkXMLNoText( sub5element, sub5elementLocation )
                                                BibleOrgSysGlobals.checkXMLNoTail( sub5element, sub5elementLocation )
                                                if sub5element.tag == 'cyclicNameContext':
                                                    cncType = None
                                                    for attrib,value in sub5element.items():
                                                        #print( "here7", attrib, value )
                                                        #if attrib=='draft': draft = value
                                                        if attrib=='type': cncType = value; assert cncType in ('format',)
                                                        else:
                                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                    for sub6element in sub5element:
                                                        sub6elementLocation = sub6element.tag + ' in ' + sub5elementLocation
                                                        #if debuggingThisModule: print( "              ProcessingD6 {} ({})…".format( sub6elementLocation, sub6element.text.strip() ) )
                                                        BibleOrgSysGlobals.checkXMLNoText( sub6element, sub6elementLocation )
                                                        BibleOrgSysGlobals.checkXMLNoTail( sub6element, sub6elementLocation )
                                                        if sub6element.tag == 'cyclicNameWidth':
                                                            cnwType = None
                                                            for attrib,value in sub6element.items():
                                                                #print( "here7", attrib, value )
                                                                #if attrib=='draft': draft = value
                                                                if attrib=='type': cnwType = value; assert cnwType in ('abbreviated',)
                                                                else:
                                                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub6elementLocation ) )
                                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                            for sub7element in sub6element:
                                                                sub7elementLocation = sub7element.tag + ' in ' + sub6elementLocation
                                                                #if debuggingThisModule: print( "              ProcessingD6 {} ({})…".format( sub6elementLocation, sub6element.text.strip() ) )
                                                                BibleOrgSysGlobals.checkXMLNoSubelements( sub7element, sub7elementLocation )
                                                                BibleOrgSysGlobals.checkXMLNoTail( sub7element, sub7elementLocation )
                                                                if sub7element.tag == 'cyclicName':
                                                                    cnType = None
                                                                    for attrib,value in sub6element.items():
                                                                        #print( "hereCN7", attrib, value )
                                                                        #if attrib=='draft': draft = value
                                                                        if attrib=='type': cnType = value; assert cnType in ('1','abbreviated')
                                                                        else:
                                                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub6elementLocation ) )
                                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                                                    pass # Save text field XXXXXXXXXXXXXX
                                                                else:
                                                                    logging.error( _("Unprocessed {!r} sub7element ({}) in {}").format( sub7element.tag, sub7element.text.strip(), sub6elementLocation ) )
                                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                                        else:
                                                            logging.error( _("Unprocessed {!r} sub6element ({}) in {}").format( sub6element.tag, sub6element.text.strip(), sub5elementLocation ) )
                                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                                else:
                                                    logging.error( _("Unprocessed {!r} sub5element ({}) in {}").format( sub5element.tag, sub5element.text.strip(), sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                        else:
                                            logging.error( _("Unprocessed {!r} sub4element ({}) in {}").format( sub4element.tag, sub4element.text.strip(), sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                else:
                                    logging.error( _("Unprocessed {!r} sub3element ({}) in {}").format( sub3element.tag, sub3element.text.strip(), sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                    if dateTimeFormats:
                        assert 'dateTimeFormats' not in dCalendar
                        dCalendar['dateTimeFormats'] = dateTimeFormats
                    if dayPeriods:
                        assert 'dayPeriods' not in dCalendar
                        dCalendar['dayPeriods'] = dayPeriods
                    assert cType not in dCalendars
                    dCalendars[cType] = dCalendar
                    if dCalendars:
                        assert subelement.tag not in dates
                        dates[subelement.tag] = dCalendars
                elif subelement.tag == 'fields':
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing3b {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoText( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'field':
                            draft = fType = alt = None
                            for attrib,value in sub2element.items():
                                #print( "hereF8", attrib, value )
                                #if attrib=='draft': draft = value
                                if attrib=='type': fType = value # assert fType in ('day','day-narrow','day-short','dayperiod','era','fri','fri-narrow','fri-short','hour',...)
                                #elif attrib=='alt': alt = value
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            for sub3element in sub2element:
                                sub3elementLocation = sub3element.tag + ' in ' + sub2elementLocation
                                #if debuggingThisModule: print( "        Processing {}…".format( sub3elementLocation ) )
                                BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                                if sub3element.tag == 'displayName':
                                    BibleOrgSysGlobals.checkXMLNoSubelements( sub3element, sub3elementLocation )
                                    draft = dnType = alt = None
                                    for attrib,value in sub3element.items():
                                        if attrib=='draft': draft = value
                                        #elif attrib=='type': dnType = value
                                        #elif attrib=='alt': alt = value
                                        else:
                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                elif sub3element.tag == 'relativeTime':
                                    BibleOrgSysGlobals.checkXMLNoText( sub3element, sub3elementLocation )
                                    BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                                    rtType = alt = None
                                    for attrib,value in sub3element.items():
                                        #if attrib=='draft': draft = value
                                        if attrib=='type': rtType = value
                                        #elif attrib=='alt': alt = value
                                        else:
                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                    for sub4element in sub3element:
                                        sub4elementLocation = sub4element.tag + ' in ' + sub3elementLocation
                                        #if debuggingThisModule: print( "          ProcessingRT4 {} ({})…".format( sub4elementLocation, sub4element.text.strip() ) )
                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4elementLocation )
                                        if sub4element.tag == 'relativeTimePattern':
                                            rtpCount = rtpDraft = None
                                            for attrib,value in sub4element.items():
                                                if attrib=='count': rtpCount = value
                                                elif attrib=='draft': rtpDraft = value
                                                else:
                                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub4elementLocation ) )
                                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                            pass # save Text XXXXXXXXXXXXXXXXXXX
                                elif sub3element.tag == 'alias':
                                    BibleOrgSysGlobals.checkXMLNoText( sub3element, sub3elementLocation )
                                    BibleOrgSysGlobals.checkXMLNoSubelements( sub3element, sub3elementLocation )
                                    BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                                    aPath = aSource = None
                                    for attrib,value in sub3element.items():
                                        #if attrib=='draft': draft = value
                                        if attrib=='path': aPath = value
                                        elif attrib=='source': aSource = value
                                        else:
                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                elif sub3element.tag == 'relative':
                                    BibleOrgSysGlobals.checkXMLNoSubelements( sub3element, sub3elementLocation )
                                    BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                                    rType = rDraft = None
                                    for attrib,value in sub3element.items():
                                        if attrib=='type': rType = value
                                        elif attrib=='draft': rDraft = value
                                        else:
                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                    pass # save Text XXXXXXXXXXXXXXXXXXX
                                else:
                                    logging.error( _("Unprocessed {!r} sub3element ({}) in {}").format( sub3element.tag, sub3element.text.strip(), sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                            if fType in fields: logging.critical( "Losing data here for {} field".format( fType ) )
                            fields[fType] = (fType,sub2element.text,draft,alt)
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                    if fields:
                        assert subelement.tag not in dates
                        dates[subelement.tag] = fields
                elif subelement.tag == 'timeZoneNames':
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing3g {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoText( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        metazones = {}
                        if sub2element.tag == 'metazone':
                            mzType = None
                            for attrib,value in sub2element.items():
                                #print( "here58", attrib, value )
                                if attrib=='type': mzType = value
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            metazone = {}
                            for sub3element in sub2element:
                                sub3elementLocation = sub3element.tag + ' in ' + sub2elementLocation
                                #if debuggingThisModule: print( "        Processing8 {} ({})…".format( sub3elementLocation, sub3element.text.strip() ) )
                                BibleOrgSysGlobals.checkXMLNoAttributes( sub3element, sub3elementLocation )
                                BibleOrgSysGlobals.checkXMLNoText( sub3element, sub3elementLocation )
                                BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                                if sub3element.tag == 'short':
                                    if sub3element.tag not in metazone:
                                        metazone[sub3element.tag] = {}
                                    for sub4element in sub3element:
                                        sub4elementLocation = sub4element.tag + ' in ' + sub3elementLocation
                                        #if debuggingThisModule: print( "          Processing9 {} ({})…".format( sub4elementLocation, sub4element.text.strip() ) )
                                        BibleOrgSysGlobals.checkXMLNoAttributes( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4elementLocation )
                                        if sub4element.tag in ('generic','standard','daylight'):
                                            metazone[sub3element.tag][sub4element.tag] = sub4element.text
                                        else:
                                            logging.error( _("Unprocessed {!r} sub4element in {}").format( sub4element.tag, sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                else:
                                    logging.error( _("Unprocessed {!r} sub3element ({}) in {}").format( sub3element.tag, sub3element.text.strip(), sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                            if metazone:
                                assert mzType not in metazones
                                metazones[mzType] = metazone
                        elif sub2element.tag == 'zone':
                            zType = None
                            for attrib,value in sub2element.items():
                                #print( "here58", attrib, value )
                                if attrib=='type': zType = value
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            zone = {}
                            for sub3element in sub2element:
                                sub3elementLocation = sub3element.tag + ' in ' + sub2elementLocation
                                #if debuggingThisModule: print( "        Processing8 {} ({})…".format( sub3elementLocation, sub3element.text.strip() ) )
                                BibleOrgSysGlobals.checkXMLNoAttributes( sub3element, sub3elementLocation )
                                BibleOrgSysGlobals.checkXMLNoText( sub3element, sub3elementLocation )
                                BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                                if sub3element.tag == 'short':
                                    if sub3element.tag not in zone:
                                        zone[sub3element.tag] = {}
                                    for sub4element in sub3element:
                                        sub4elementLocation = sub4element.tag + ' in ' + sub3elementLocation
                                        #if debuggingThisModule: print( "          Processing9 {} ({})…".format( sub4elementLocation, sub4element.text.strip() ) )
                                        BibleOrgSysGlobals.checkXMLNoAttributes( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoSubelements( sub4element, sub4elementLocation )
                                        BibleOrgSysGlobals.checkXMLNoTail( sub4element, sub4elementLocation )
                                        if sub4element.tag in ('generic','standard','daylight'):
                                            zone[sub3element.tag][sub4element.tag] = sub4element.text
                                        #elif sub4element.tag == 'standard':
                                            #zone[sub3element.tag][sub4element.tag] = sub4element.text
                                        #elif sub4element.tag == 'daylight':
                                            #zone[sub3element.tag][sub4element.tag] = sub4element.text
                                        else:
                                            logging.error( _("Unprocessed {!r} sub4element in {}").format( sub4element.tag, sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                                else:
                                    logging.error( _("Unprocessed {!r} sub3element ({}) in {}").format( sub3element.tag, sub3element.text.strip(), sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                    if timeZoneNames:
                        assert subelement.tag not in dates
                        dates[subelement.tag] = timeZoneNames
                else:
                    logging.error( _("Unprocessed {!r} subelement ({}) in {}").format( subelement.tag, subelement.text.strip(), elementLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
            return dates
        # end of loadDates


        def loadUnits( element, elementLocation, units ):
            """
            Returns the updated dictionary.
            """
            for subelement in element:
                subelementLocation = subelement.tag + ' in ' + elementLocation
                #if debuggingThisModule: print( "    Processing {}…".format( subelementLocation ) )
                BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                if subelement.tag == 'unitLength':
                    ulLong = ulType = None
                    for attrib,value in subelement.items():
                        if attrib=='long': ulLong = value
                        #elif attrib=='digits': digits = value
                        elif attrib=='type': ulType = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoText( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'unit':
                            uType = None
                            for attrib,value in subelement.items():
                                #if attrib=='long': ulLong = value
                                #elif attrib=='digits': digits = value
                                if attrib=='type': uType = value
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            for sub3element in sub2element:
                                sub3elementLocation = sub3element.tag + ' in ' + sub2elementLocation
                                #if debuggingThisModule: print( "        Processing {} ({})…".format( sub3elementLocation, sub3element.text.strip() ) )
                                BibleOrgSysGlobals.checkXMLNoSubelements( sub3element, sub3elementLocation )
                                BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                                if sub3element.tag == 'displayName':
                                    dnDraft = None
                                    for attrib,value in sub3element.items():
                                        #if attrib=='draft': draft = value
                                        if attrib=='draft': dnDraft = value
                                        #elif attrib=='alt': alt = value
                                        else:
                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                    pass # Save text XXXXXXXXXXXXX
                                elif sub3element.tag == 'unitPattern':
                                    upCount = upDraft = None
                                    for attrib,value in sub3element.items():
                                        if attrib=='count': upCount = value
                                        elif attrib=='draft': upDraft = value
                                        else:
                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                    pass # Save text XXXXXXXXXXXXX
                                elif sub3element.tag == 'perUnitPattern':
                                    pupDraft = None
                                    for attrib,value in sub3element.items():
                                        #if attrib=='draft': draft = value
                                        if attrib=='draft': pupDraft = value
                                        #elif attrib=='alt': alt = value
                                        else:
                                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub3elementLocation ) )
                                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                                    pass # Save text XXXXXXXXXXXXX
                                else:
                                    logging.error( _("Unprocessed {!r} sub3element ({}) in {}").format( sub3element.tag, sub3element.text.strip(), sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                    #assert subelement.tag not in units
                    #units[subelement.tag] = (nID,digits,nType)
                else:
                    logging.error( _("Unprocessed {!r} subelement ({}) in {}").format( subelement.tag, subelement.text.strip(), elementLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
            return units
        # end of loadUnits


        def loadCharacterLabels( element, elementLocation, characterLabels ):
            """
            Returns the updated dictionary.
            """
            for subelement in element:
                subelementLocation = subelement.tag + ' in ' + elementLocation
                #if debuggingThisModule: print( "    Processing {}…".format( subelementLocation ) )
                BibleOrgSysGlobals.checkXMLNoSubelements( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                if subelement.tag == 'characterLabel':
                    clType = None
                    for attrib,value in subelement.items():
                        #if attrib=='long': ulLong = value
                        #elif attrib=='digits': digits = value
                        if attrib=='type': clType = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    assert clType not in characterLabels
                    characterLabels[clType] = subelement.text
                else:
                    logging.error( _("Unprocessed {!r} subelement ({}) in {}").format( subelement.tag, subelement.text.strip(), elementLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
            return characterLabels
        # end of loadCharacterLabels


        def loadListPatterns( element, elementLocation, listPatterns ):
            """
            Returns the updated dictionary.
            """
            for subelement in element:
                subelementLocation = subelement.tag + ' in ' + elementLocation
                #if debuggingThisModule: print( "    Processing {}…".format( subelementLocation ) )
                BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                if subelement.tag == 'listPattern':
                    lpType = None
                    for attrib,value in subelement.items():
                        #if attrib=='long': ulLong = value
                        #elif attrib=='digits': digits = value
                        if attrib=='type': lpType = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'listPatternPart':
                            lppDraft = lppType = None
                            for attrib,value in sub2element.items():
                                if attrib=='draft': lppDraft = value
                                elif attrib=='type': lppType = value
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            pass # Save Text XXXXX
                            #for sub3element in sub2element:
                                #sub3elementLocation = sub3element.tag + ' in ' + sub2elementLocation
                                ##if debuggingThisModule: print( "        Processing {} ({})…".format( sub3elementLocation, sub3element.text.strip() ) )
                                #BibleOrgSysGlobals.checkXMLNoAttributes( sub3element, sub3elementLocation )
                                #BibleOrgSysGlobals.checkXMLNoText( sub3element, sub3elementLocation )
                                #BibleOrgSysGlobals.checkXMLNoSubelements( sub3element, sub3elementLocation )
                                #BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                    assert lpType not in listPatterns
                    listPatterns[lpType] = subelement.text
                else:
                    logging.error( _("Unprocessed {!r} subelement ({}) in {}").format( subelement.tag, subelement.text.strip(), elementLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
            return listPatterns
        # end of loadListPatterns


        def loadContextTransforms( element, elementLocation, contextTransforms ):
            """
            Returns the updated dictionary.
            """
            for subelement in element:
                subelementLocation = subelement.tag + ' in ' + elementLocation
                #if debuggingThisModule: print( "    Processing {}…".format( subelementLocation ) )
                BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                if subelement.tag == 'contextTransformUsage':
                    ctuType = None
                    for attrib,value in subelement.items():
                        #if attrib=='long': ulLong = value
                        #elif attrib=='digits': digits = value
                        if attrib=='type': ctuType = value
                        else:
                            logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing {} ({})…".format( sub2elementLocation, sub2element.text.strip() ) )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        if sub2element.tag == 'contextTransform':
                            lppDraft = ctType = None
                            for attrib,value in sub2element.items():
                                if attrib=='xdraft': lppDraft = value
                                elif attrib=='type': ctType = value
                                else:
                                    logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                            pass # Save Text XXXXX
                            #for sub3element in sub2element:
                                #sub3elementLocation = sub3element.tag + ' in ' + sub2elementLocation
                                ##if debuggingThisModule: print( "        Processing {} ({})…".format( sub3elementLocation, sub3element.text.strip() ) )
                                #BibleOrgSysGlobals.checkXMLNoAttributes( sub3element, sub3elementLocation )
                                #BibleOrgSysGlobals.checkXMLNoText( sub3element, sub3elementLocation )
                                #BibleOrgSysGlobals.checkXMLNoSubelements( sub3element, sub3elementLocation )
                                #BibleOrgSysGlobals.checkXMLNoTail( sub3element, sub3elementLocation )
                        else:
                            logging.error( _("Unprocessed {!r} sub2element ({}) in {}").format( sub2element.tag, sub2element.text.strip(), subelementLocation ) )
                            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
                    assert ctuType not in contextTransforms
                    contextTransforms[ctuType] = subelement.text
                else:
                    logging.error( _("Unprocessed {!r} subelement ({}) in {}").format( subelement.tag, subelement.text.strip(), elementLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
            return contextTransforms
        # end of loadContextTransforms


        def loadSpecial( element, elementLocation, special ):
            """
            Returns the updated dictionary.
            """
            for subelement in element:
                subelementLocation = subelement.tag + ' in ' + elementLocation
                #if debuggingThisModule: print( "    Processing {}…".format( subelementLocation ) )
                BibleOrgSysGlobals.checkXMLNoAttributes( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoText( subelement, subelementLocation )
                BibleOrgSysGlobals.checkXMLNoTail( subelement, subelementLocation )
                assert subelement.tag not in special
                if subelement.tag.endswith( 'external-resources' ):
                    adjustedTag = removeSILPrefix( subelement.tag )
                    special[adjustedTag] = {}
                    for sub2element in subelement:
                        sub2elementLocation = sub2element.tag + ' in ' + subelementLocation
                        #if debuggingThisModule: print( "      Processing {}…".format( sub2elementLocation ) )
                        BibleOrgSysGlobals.checkXMLNoText( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoSubelements( sub2element, sub2elementLocation )
                        BibleOrgSysGlobals.checkXMLNoTail( sub2element, sub2elementLocation )
                        erName = erSize = erType = None
                        for attrib,value in sub2element.items():
                            #print( "hereLS7", attrib, value )
                            if attrib=='name': erName = value
                            elif attrib=='size': erSize = value
                            elif attrib=='type': erType = value # assert erType in ('default','hunspell')
                            else:
                                logging.error( _("Unprocessed {!r} attribute ({}) in {}").format( attrib, value, sub2elementLocation ) )
                                if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag and BibleOrgSysGlobals.haltOnXMLWarning: halt
                        #assert erName
                        if sub2element.tag not in special[adjustedTag]:
                            special[adjustedTag][sub2element.tag] = []
                        special[adjustedTag][sub2element.tag].append( (erType,erName,erSize) )
                else:
                    logging.error( _("Unprocessed {!r} subelement ({}) in {}").format( subelement.tag, subelement.text.strip(), elementLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
            return special
        # end of loadSpecial


        # Main code for LDMLFile.load()
        if BibleOrgSysGlobals.verbosityLevel > 0:
            print( "    Loading LOCALE DATA MARKUP LANGUAGE (LDML) file from {}…".format( self.filepath ) )

        LDMLData = OrderedDict()

        languageTree = ElementTree().parse( self.filepath )
        assert len( languageTree ) # Fail here if we didn't load anything at all

        # Find the main container
        if languageTree.tag=='ldml':
            treeLocation = "PTX8 {} file for {}".format( languageTree.tag, self.languageCode )
            BibleOrgSysGlobals.checkXMLNoAttributes( languageTree, treeLocation )
            BibleOrgSysGlobals.checkXMLNoText( languageTree, treeLocation )
            BibleOrgSysGlobals.checkXMLNoTail( languageTree, treeLocation )

            identity = OrderedDict()
            characters = OrderedDict()
            delimiters = OrderedDict()
            layout = OrderedDict()
            numbers = OrderedDict()
            collations = OrderedDict()
            localeDisplayNames = OrderedDict()
            dates = OrderedDict()
            units = OrderedDict()
            characterLabels = OrderedDict()
            listPatterns = OrderedDict()
            contextTransforms = OrderedDict()
            special = OrderedDict()

            # Now process the actual entries
            for element in languageTree:
                elementLocation = element.tag + ' in ' + treeLocation
                #if debuggingThisModule: print( "  Processing1 {} ({})…".format( elementLocation, element.text.strip() ) )
                BibleOrgSysGlobals.checkXMLNoAttributes( element, elementLocation )
                BibleOrgSysGlobals.checkXMLNoText( element, elementLocation )
                BibleOrgSysGlobals.checkXMLNoTail( element, elementLocation )
                assert element.tag not in LDMLData # Each one can only occur onces

                if element.tag == 'identity':
                    identity = loadIdentity( element, elementLocation, identity )
                    if identity:
                        #print( "identity", identity )
                        LDMLData[element.tag] = identity
                elif element.tag == 'characters':
                    characters = loadCharacters( element, elementLocation, characters )
                    if characters:
                        #print( "characters", characters )
                        LDMLData[element.tag] = characters
                elif element.tag == 'delimiters':
                    delimiters = loadDelimiters( element, elementLocation, delimiters )
                    if delimiters:
                        #print( "delimiters", delimiters )
                        LDMLData[element.tag] = delimiters
                elif element.tag == 'layout':
                    layout = loadLayout( element, elementLocation, layout )
                    if layout:
                        #print( "layout", layout )
                        LDMLData[element.tag] = layout
                elif element.tag == 'numbers':
                    numbers = loadNumbers( element, elementLocation, numbers )
                    if numbers:
                        #print( "numbers", numbers )
                        LDMLData[element.tag] = numbers
                elif element.tag == 'collations':
                    collations = loadCollations( element, elementLocation, collations )
                    if collations:
                        #print( "collations", collations )
                        LDMLData[element.tag] = collations
                elif element.tag == 'localeDisplayNames':
                    localeDisplayNames = loadLocateDisplayNames( element, elementLocation, localeDisplayNames )
                    if localeDisplayNames:
                        #print( "localeDisplayNames", localeDisplayNames )
                        LDMLData[element.tag] = localeDisplayNames
                elif element.tag == 'dates':
                    dates = loadDates( element, elementLocation, dates )
                    if dates:
                        #print( "dates", dates )
                        LDMLData[element.tag] = dates
                elif element.tag == 'units':
                    units = loadUnits( element, elementLocation, units )
                    if units:
                        #print( "units", units )
                        LDMLData[element.tag] = units
                elif element.tag == 'characterLabels':
                    characterLabels = loadCharacterLabels( element, elementLocation, characterLabels )
                    if characterLabels:
                        #print( "characterLabels", characterLabels )
                        LDMLData[element.tag] = characterLabels
                elif element.tag == 'listPatterns':
                    listPatterns = loadListPatterns( element, elementLocation, listPatterns )
                    if listPatterns:
                        #print( "listPatterns", listPatterns )
                        LDMLData[element.tag] = listPatterns
                elif element.tag == 'contextTransforms':
                    contextTransforms = loadContextTransforms( element, elementLocation, contextTransforms )
                    if contextTransforms:
                        #print( "contextTransforms", contextTransforms )
                        LDMLData[element.tag] = contextTransforms
                elif element.tag == 'special':
                    special = loadSpecial( element, elementLocation, special )
                    if special:
                        #print( "special", special )
                        LDMLData[element.tag] = special
                else:
                    logging.error( _("Unprocessed {} element ({}) in {}").format( element.tag, element.text.strip(), treeLocation ) )
                    if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt
        else:
            logging.critical( _("Unrecognised PTX8 {} language settings tag: {}").format( self.languageCode, languageTree.tag ) )
            if BibleOrgSysGlobals.strictCheckingFlag or BibleOrgSysGlobals.debugFlag: halt

        if BibleOrgSysGlobals.verbosityLevel > 2:
            print( "\n\nLDML data for {} ({}):".format( self.languageCode, len(LDMLData) ) )
            for key in LDMLData:
                #print( "\n      {}: ({}) {}".format( key, len(LDMLData[key]), LDMLData[key] ) )
                print( "\n      {} ({}):".format( key, len(LDMLData[key]) ) )
                for key2 in LDMLData[key]:
                    print( "        {} ({}): {!r}".format( key2, len(LDMLData[key][key2]), LDMLData[key][key2] ) )
        elif debuggingThisModule: print( '\nLDMLData for {} ({}): {}'.format( self.languageCode, len(LDMLData), LDMLData ) )
        return LDMLData
    # end of LDML.load
# end of class LDMLFile



def demo():
    """
    Demonstrate reading and checking some LDML files.
    """
    if BibleOrgSysGlobals.verbosityLevel > 0: print( ProgNameVersion )

    mainTestFolder = '../../../ExternalPrograms/SIL_NRSI/sldr/sldr/'
    if 1: # test load all SIL LDML files (cloned from GitHub)
        for something in sorted( os.listdir( mainTestFolder ) ):
            somepath = os.path.join( mainTestFolder, something )
            if os.path.isdir( somepath ):
                if BibleOrgSysGlobals.verbosityLevel > 0:
                    print( "\n\nA: Looking for files in folder: {}".format( somepath ) )

                for something2 in sorted( os.listdir( somepath ) ):
                    if something2 == 'aeb_Latn.xml':
                        print( "Skipping {}".format( something2 ) )
                        continue # bad XML
                    somepath2 = os.path.join( somepath, something2 )
                    if os.path.isfile( somepath2 ):
                        if BibleOrgSysGlobals.verbosityLevel > 0:
                            print( "  Found {}".format( somepath2 ) )

                        if os.access( somepath2, os.R_OK ):
                            thisLDMLfile = LDMLFile( somepath, something2 )
                            LDMLdict = thisLDMLfile.load()
                            if BibleOrgSysGlobals.verbosityLevel > 1: print( "\nLoaded {} and got:\n  {}".format( something2, LDMLdict ) )
                            #if BibleOrgSysGlobals.strictCheckingFlag: thisLDMLfile.check()
                        else: print( "Sorry, test file '{}' is not readable on this computer.".format( somepath2 ) )
        #if BibleOrgSysGlobals.verbosityLevel > 1: print( "\nPTX8 B/ Trying single module in {}".format( testFolder ) )
        #thisLDMLfile = LDMLFile( testFolder )
        #thisLDMLfile.load()
        #if BibleOrgSysGlobals.verbosityLevel > 0: print( "thisLDMLfile )


if __name__ == '__main__':
    # Configure basic set-up
    parser = BibleOrgSysGlobals.setup( ProgName, ProgVersion )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    demo()

    BibleOrgSysGlobals.closedown( ProgName, ProgVersion )
# end of LDML.py