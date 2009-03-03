import re
from vendor.BeautifulSoup import BeautifulSoup, Comment

absolute_url_matcher = re.compile("^https?://")
valid_tags = 'i strong b u a em img pre code p br blockquote cite'.split()
valid_attrs = 'href src'.split()

BeautifulSoup.QUOTE_TAGS['pre'] = None  # don't parse inside of PRE tags

def url(URI):
    if absolute_url_matcher.match(URI):
        return URI

def html(value):
    value = value.replace("\r\n","\n")
    soup = BeautifulSoup(value)

    # remove HTML comments
    for comment in soup.findAll(
            text=lambda text: isinstance(text, Comment)):
        comment.extract()

    # limit tags and attributes, 'nofollow' links, escape <pre> contents
    for tag in soup.findAll(True):
        if tag.name not in valid_tags:
            tag.hidden = True
        tag.attrs = [(attr, val) for attr, val in tag.attrs
                     if attr in valid_attrs and url(val)]
        if tag.name == 'a':
            tag.attrs.append(['rel', 'nofollow'])
        if tag.name == 'pre':
            # convert < into &lt; AND \n\n -> \n&nbsp;\n so that we don't add <br>s in the linebreaking step
            tag.replaceWith('<pre>%s</pre>' % tag.contents[0].replace('<', '&lt;').replace('\n', '\r'))

    # add a linebreak whenever there are two returns
    html = soup.renderContents().decode('utf8')
    html = html.replace("\n", "<br />\n")
    html = html.replace('\r', '\n')

    return html

if __name__ == '__main__':
    assert html('some words') == 'some words'
    assert html('no<!-- comments -->') == "no"
    assert html('<a href="http://del.icio.us">me</a>') == '<a href="http://del.icio.us" rel="nofollow">me</a>'
    assert html('one\ntwo') == "one<br />\ntwo"
    assert html('one\n\ntwo') == "one<br />\n<br />\ntwo"
    assert html('<pre>123\n456</pre>') == "<pre>123\n456</pre>"
    assert html('here is <b>my</b> code:\n<pre>hello(world)</pre>') == "here is <b>my</b> code:<br />\n<pre>hello(world)</pre>"
    assert html('<pre>if 1 <2:\n\n  print <script type="text/javascript">alert(1)</script>') == \
      '<pre>if 1 &lt;2:\n\n  print &lt;script type="text/javascript">alert(1)&lt;/script></pre>'
    print "tests passed!"
