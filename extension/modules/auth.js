var EXPORTED_SYMBOLS = ['auth'];

const Cc = Components.classes;
const Ci = Components.interfaces;

var loginManager = Cc["@mozilla.org/login-manager;1"]
                     .getService(Ci.nsILoginManager);

var nsLoginInfo = new Components.Constructor("@mozilla.org/login-manager/loginInfo;1",
                                             Ci.nsILoginInfo,
                                             "init");

function getLogins() {
  return loginManager.findLogins({}, 'chrome://firenomics', 'Firenomics Profile', null);
}

var auth = {
  get: function auth_get() {
    var logins = getLogins();
    if (logins.length == 1) {
      return {key: logins[0].username, secret: logins[0].password};
    }
  },
  set: function auth_set(key, secret) {
    var logins = getLogins();

    var newLogin = new nsLoginInfo('chrome://firenomics',
                                   'Firenomics Profile', null,
                                   key, secret, "", "");

    if (logins.length > 0) {
      loginManager.modifyLogin(logins[0], newLogin);
    } else {
      loginManager.addLogin(newLogin);
    }
  },
  clear: function auth_clear() {
    var logins = getLogins();
    logins.forEach(function(login) {
      loginManager.removeLogin(login);
    });
  }
};
