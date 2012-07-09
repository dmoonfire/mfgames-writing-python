<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:d="http://docbook.org/ns/docbook"
    xmlns="http://www.w3.org/1999/xhtml"
    version="2.0">
  <!-- This doesn't use the standard DocBook stylesheets. Instead, it
       is just a simple conversion of a DocBook document into HTML for
       use with `kindlegen`.

       This doesn't generate a table of contents (see kindletoc for
       that) and it only generates ID fields for those elements that
       have one. -->
  <xsl:output
	  method="xml" 
	  doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-
transitional.dtd" 
	  doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN"
	  indent="yes"/>

  <xsl:template match="/">
	<!-- We need an outer DIV tag to make it a valid XML. -->
	<div>
	  <xsl:apply-templates/>
	</div>
  </xsl:template>

  <!-- Book -->

  <!-- Article -->
  <xsl:template match="d:article">
	<!-- Include the contents of the article. -->
	<xsl:apply-templates select="d:para|d:simpara"/>

	<xsl:apply-templates select="d:section">
	  <xsl:with-param name="depth">2</xsl:with-param>
	</xsl:apply-templates>
  </xsl:template>

  <!-- Sections with Titles -->
  <xsl:template match="d:section[d:info/d:title]">
	<xsl:param name="depth"/>

	<!-- Give the section a heading title based on the level. -->
	<xsl:element name="h{$depth}">
	  <xsl:apply-templates select="d:info/d:title"/>
	</xsl:element>

	<!-- Include the contents of the section. -->
	<xsl:apply-templates select="d:para|d:simpara"/>
  </xsl:template>

  <!-- Structural Catches -->
  <xsl:template match="*" mode="title" priority="-1"/>

  <!-- Paragraphs -->
  <xsl:template match="d:para|d:simpara">
	<p>
	  <xsl:apply-templates />
	</p>
  </xsl:template>

  <!-- Info -->
  <xsl:template match="d:title">
	<xsl:apply-templates/>
  </xsl:template>
</xsl:stylesheet>
