<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    version="1.0">
    <xsl:output method="xml" indent="yes"/>
    <!--<xsl:template name="test" match="/invoice/header/field">
        hello world
    </xsl:template>
    <xsl:template name="StripWhiteSpace" match="/invoice/header/field[@name='']">
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:template>
    -->
    <xsl:template match="/">
    <!--<xsl:apply-templates></xsl:apply-templates>-->
    <Invoice>
        <Head>
            <DematType>C</DematType>
            <InvoiceType>380</InvoiceType>
            <InstallmentRequest>0</InstallmentRequest>
            <InvoiceTreatment>9</InvoiceTreatment>
            <InvoiceNumber><xsl:value-of select="invoice/header/InvoiceNo"/></InvoiceNumber>
            <InvoiceDate><xsl:value-of select="invoice/header/InvoiceDate"/></InvoiceDate>
            <PaymentMeanCode>42</PaymentMeanCode>
            <PaymentMean>Virement</PaymentMean>
            <PaymentConditions><xsl:value-of select="invoice/header/Terms"/></PaymentConditions>
            <SettlementConditions>Pas d'escompte pour paiement anticipé.</SettlementConditions>
            <PenaltyConditions>En cas de paiement tardif il sera appliqué une majoration pour intéręt de retard d'un taux égal ŕ 3  fois le taux d'intéręt légal.</PenaltyConditions>
            <PONum><xsl:value-of select="invoice/header/CustomerPO"/></PONum>
            <TaxMode>EXO</TaxMode>
            <Currency>USD</Currency>
            <PaymentDueDate><xsl:value-of select="invoice/header/DueDate"/></PaymentDueDate>
            <DeliveryDate><xsl:value-of select="invoice/header/InvoiceDate"/></DeliveryDate>
            <!--<GenText><xsl:value-of select="invoice/header/FixedMessage"/></GenText>-->           
        </Head>
        <Party>
            <PartyType>SU</PartyType>
            <PartyId>52-2281142</PartyId><!--Fiscal Id Number-->
            <PartyName1><xsl:text>INC</xsl:text></PartyName1>
            <PartyAddress1><xsl:text>Standish Place</xsl:text></PartyAddress1>
            <PostalCode>20855</PostalCode>
            <City>Arlington</City>
            <Country>USA</Country>
            <ISOCountryCode>US</ISOCountryCode>
            <Siret></Siret>
            <TVAnum>12-3111142</TVAnum>
            <RCS>RCS STATE OF DELAWARE </RCS><!--Registry State and #-->
            <Status>INC</Status>
            <Capital></Capital>
            <CapitalCur>USD</CapitalCur>
            <InternalDepCode></InternalDepCode>
            <SupplierCode>5025846</SupplierCode><!--ECF:5030073, ECE:5030073, ECD:5025846-->
        </Party>
        <Party>
            <PartyType>BY</PartyType>
            <PartyID></PartyID>
            <PartyName1><xsl:value-of select="invoice/header/SoldTo"/></PartyName1>
            <PartyAddress1><xsl:value-of select="invoice/header/SoldToAttn"/></PartyAddress1>
            <PartyAddress2><xsl:value-of select="invoice/header/SoldToAdd1"/></PartyAddress2>
            <PartyAddress3><xsl:value-of select="invoice/header/SoldToAdd2"/></PartyAddress3>
            <PartyAddress4><xsl:value-of select="invoice/header/SoldToAdd3"/></PartyAddress4>
            <PostalCode><xsl:value-of select="invoice/header/SoldToZip"/></PostalCode>
            <City><xsl:value-of select="invoice/header/SoldToCity"/></City>
            <Country><xsl:value-of select="invoice/header/SoldToCountry"/></Country>
            <ISOCountryCode><xsl:value-of select="invoice/header/SoldToCountryCode"/></ISOCountryCode>
            <TVAnum></TVAnum>
        </Party>
        <Party>
            <PartyType>IV</PartyType>
            <PartyID></PartyID>
            <PartyName1><xsl:value-of select="invoice/header/BillTo"/></PartyName1>
            <PartyAddress1><xsl:value-of select="invoice/header/BillToAttn"/></PartyAddress1>
            <PartyAddress2><xsl:value-of select="invoice/header/BillToAdd1"/></PartyAddress2>
            <PartyAddress3><xsl:value-of select="invoice/header/BillToAdd2"/></PartyAddress3>
            <PartyAddress4><xsl:value-of select="invoice/header/BillToAdd3"/></PartyAddress4>
            <PostalCode><xsl:value-of select="invoice/header/BillToZip"/></PostalCode>
            <City><xsl:value-of select="invoice/header/BillToCity"/></City>
            <Country><xsl:value-of select="invoice/header/BillToCountry"/></Country>
            <ISOCountryCode><xsl:value-of select="invoice/header/BillToCountryCode"/></ISOCountryCode>
            <TVAnum></TVAnum>
        </Party>
        <Party>
            <PartyType>DP</PartyType>
            <PartyID></PartyID>
            <PartyName1><xsl:value-of select="invoice/header/ShipTo"/></PartyName1>
            <PartyAddress1><xsl:value-of select="invoice/header/ShipToAttn"/></PartyAddress1>
            <PartyAddress2><xsl:value-of select="invoice/header/ShipToAdd1"/></PartyAddress2>
            <PartyAddress3><xsl:value-of select="invoice/header/ShipToAdd2"/></PartyAddress3>
            <PartyAddress4><xsl:value-of select="invoice/header/ShipToAdd3"/></PartyAddress4>
            <PostalCode><xsl:value-of select="invoice/header/ShipToZip"/></PostalCode>
            <City><xsl:value-of select="invoice/header/ShipToCity"/></City>
            <Country><xsl:value-of select="invoice/header/ShipToCountry"/></Country>
            <ISOCountryCode><xsl:value-of select="invoice/header/ShipToCountryCode"/></ISOCountryCode>
            <TVAnum></TVAnum>
        </Party>
        <Comh>
            <Desc>COORDONNEES BANCAIRES/BANKING INFORMATION </Desc>
            <Desc>TEST</Desc>
            <Desc> ACCOUNT NUMBER:  </Desc>
            <Desc>ROUTING NUMBER:  </Desc>
            <Desc>BENEFICIARY: </Desc>
            <Desc>These commodities, technology or software were exported from the in accordance with </Desc>
        </Comh>
        <xsl:for-each select="invoice/header/Detail/detail"><!-- Need to change to Details-->
        <Line>
            <LineType>L</LineType>
            <LineNum><xsl:value-of select="Line"/></LineNum>
            <LinePartNumVP></LinePartNumVP>
            <PartDesc><xsl:value-of select="Descr"/></PartDesc>
            <PartDescComp></PartDescComp>
            <PartDescComp2></PartDescComp2>
            <Quantity><xsl:value-of select="QtyOrdered"/></Quantity>
            <UnitOfMeasure><xsl:value-of select="UOM"/></UnitOfMeasure>
            <PackQty></PackQty>
            <PackQtyUoM></PackQtyUoM>
            <LineItemSubTotal><xsl:value-of select="Amount"/></LineItemSubTotal>
            <UnitPrice><xsl:value-of select="UnitPrice"/></UnitPrice>
            <GrossUnitPrice></GrossUnitPrice>
            <POLineNum></POLineNum>
            <TaxPercent></TaxPercent>
            <TaxCategory>E</TaxCategory>
        </Line>
        </xsl:for-each>
        <TaxSummary>
            <TaxableAmount><xsl:value-of select="invoice/header/Subtotal"/></TaxableAmount>
            <TaxPercent></TaxPercent>
            <TaxAmount></TaxAmount>
            <TaxCategory>E</TaxCategory>
        </TaxSummary>
        <Summary>
            <NetValue><xsl:value-of select="invoice/header/Subtotal"/></NetValue>
            <TotalTaxAmount></TotalTaxAmount>
            <GrossAmount><xsl:value-of select="invoice/header/Subtotal"/></GrossAmount>
        </Summary>
    </Invoice>    
        </xsl:template>
</xsl:stylesheet>