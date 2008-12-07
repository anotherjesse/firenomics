from vendor import web
from google.appengine.api import users

def analytics():
    if users.is_current_user_admin():
        return ''
    html = "<script src='http://www.google-analytics.com/ga.js' type='text/javascript'></script>\n"
    html += "<script type='text/javascript'>\n"
    html += "  var pageTracker = _gat._getTracker('UA-50927-3');\n"
    html += "  pageTracker._initData();\n"
    if web.ctx.status.find('404') == 0:
        html += "  pageTracker._trackPageview('404?'+document.location.pathname);\n"
    else:
        html += "  pageTracker._trackPageview();\n"
    html += "</script>"
    return html

