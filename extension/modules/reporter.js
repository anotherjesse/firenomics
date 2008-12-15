const Cc = Components.classes;
const Ci = Components.interfaces;
const Cr = Components.results;
const Cu = Components.utils;

Cu.import("resource://gre/modules/XPCOMUtils.jsm");

var EXPORTED_SYMBOLS = ["FirenomicsReporter", "FIRENOMICS_URL"];

//const FIRENOMICS_URL = "http://firenomics.appspot.com";
const FIRENOMICS_URL = "http://localhost:8080";

const appInfo = Cc["@mozilla.org/xre/app-info;1"]
  .getService(Ci.nsIXULAppInfo);
const runtime = Cc["@mozilla.org/xre/app-info;1"]
  .getService(Ci.nsIXULRuntime);
const extMgr = Cc["@mozilla.org/extensions/manager;1"]
  .getService(Ci.nsIExtensionManager);
const RDFS = Cc['@mozilla.org/rdf/rdf-service;1']
  .getService(Ci.nsIRDFService);

const isDisabledRes =
  RDFS.GetResource("http://www.mozilla.org/2004/em-rdf#isDisabled");
const hiddenRes =
  RDFS.GetResource("http://www.mozilla.org/2004/em-rdf#hidden");

const sysInfo = {
  ID: appInfo.ID,
  vendor: appInfo.vendor,
  name: appInfo.name,
  version: appInfo.version,
  appBuildID: appInfo.appBuildID,
  platformVersion: appInfo.platformVersion,
  platformBuildID: appInfo.platformBuildID,
  OS: runtime.OS
};

var FirenomicsReporter = {
  _extensions: function FR__extensions() {
    var extensions = {};

    var ds = extMgr.datasource;
    ds.QueryInterface(Ci.nsIRDFDataSource);

    // Get list of incompatible add-ons
    var incompatibles = {};

    var results =
      extMgr.getIncompatibleItemList(null, null, null,
                                     Ci.nsIUpdateItem.TYPE_EXTENSION,
                                     true, {});

    for (var i = 0; i < results.length; i++) {
      incompatibles[results[i].id] = true;
    }

    // get the list of all extensions
    var results = extMgr.getItemList(Ci.nsIUpdateItem.TYPE_EXTENSION, {});
    for (var i = 0; i < results.length; i++) {
      var item = results[i];
      var skip = false;

      // check if extension is disabled or hidden
      var res = RDFS.GetResource("urn:mozilla:item:" + item.id);

      function trueValue(prop) {
        var target = ds.GetTarget(res, prop, true);
        return (target instanceof Ci.nsIRDFLiteral) &&
               (target.Value == 'true');
      }

      if (trueValue(isDisabledRes) || trueValue(hiddenRes)) {
        skip = true;
      }

      // check if extension is incompatible
      if (incompatibles[item.id]) {
        skip = true;
      }

      if (!skip) {
        extensions[item.id] = {
          name: item.name,
          version: item.version,
          icon: item.iconURL,
          updateRDF: item.updateRDF ? item.updateRDF : null
        };
      }
    }

    return extensions;
  },

  submit: function FR_submit() {
    var nsJSON = Cc["@mozilla.org/dom/json;1"].createInstance(Ci.nsIJSON);
    var json = nsJSON.encode({ extensions: this._extensions(),
                               system: sysInfo });

    var postBody = "data=" + encodeURIComponent(json);

    var req = Cc["@mozilla.org/xmlextras/xmlhttprequest;1"]
      .createInstance(Ci.nsIXMLHttpRequest);
    req.mozBackgroundRequest = true;

    req.onload = function FRS_onload(aEvent) {
      if (req.status == 200) {
        if (getLogins().length < 1) {
          var user = nsJSON.decode(req.responseText);
          auth.set(user.profile, user.secret);
        }
        openUILinkIn('http://firenomics.appspot.com/home', 'tab');
      }
    };

    req.open("POST", FIRENOMICS_URL + "/update");
    req.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    req.send(postBody);
  }
}

function getIcon(iconURL, callback) {
  var ios = Cc['@mozilla.org/network/io-service;1']
            .getService(Ci.nsIIOService);
  var chan = ios.newChannel(iconURL, null, null);
  var listener = new IconLoadListener(iconURL, chan, callback);
  chan.notificationCallbacks = listener;
  chan.asyncOpen(listener, null);
}

function IconLoadListener(iconURL, channel, callback) {
  this._iconURL = iconURL;
  this._channel = channel;
  this._callback = callback;
  this._bytes = [];
  this._bytesRead = 0;
}

IconLoadListener.prototype = {
  QueryInterface: XPCOMUtils.generateQI([Ci.nsIInterfaceRequestor,
                                         Ci.nsIRequestObserver,
                                         Ci.nsIChannelEventSink,
                                         Ci.nsIProgressEventSink,
                                         Ci.nsIStreamListener]),

  // nsIInterfaceRequestor
  getInterface: function (iid) {
    try {
      return this.QueryInterface(iid);
    } catch (e) {
      throw Cr.NS_NOINTERFACE;
    }
  },

  // nsIRequestObserver
  onStartRequest: function (aRequest, aContext) {
    this._stream = Cc['@mozilla.org/binaryinputstream;1']
                   .createInstance(Ci.nsIBinaryInputStream);
  },

  onStopRequest: function (aRequest, aContext, aStatusCode) {
    if (Components.isSuccessCode(aStatusCode) && this._bytesRead > 0) {
      var dataURL;

      var mimeType = null;

      var catMgr = Cc["@mozilla.org/categorymanager;1"]
                   .getService(Ci.nsICategoryManager);
      var sniffers = catMgr.enumerateCategory("content-sniffing-services");
      while (mimeType == null && sniffers.hasMoreElements()) {
        var snifferCID = sniffers.getNext().QueryInterface(Ci.nsISupportsCString).toString();
        var sniffer = Cc[snifferCID].getService(Ci.nsIContentSniffer);

        try {
          mimeType = sniffer.getMIMETypeFromContent(aRequest, this._bytes, this._bytesRead);
        } catch (ex) {
          mimeType = null;
          // ignore
        }
      }

      if (this._bytes && this._bytesRead > 0 && mimeType != null) {
        var data = 'data:';
        data += mimeType;
        data += ';base64,';

        var iconData = String.fromCharCode.apply(null, this._bytes);
        data += btoa(iconData);

        this._callback.result(this._iconURL, data);
      }
    }

    this._channel = null;
  },

  onDataAvailable: function (aRequest, aContext, aInputStream, aOffset, aCount) {
    // we could get a different aInputStream, so we don't save this;
    // it's unlikely we'll get more than one onDataAvailable for a
    // favicon anyway
    this._stream.setInputStream(aInputStream);

    var chunk = this._stream.readByteArray(aCount);
    this._bytes = this._bytes.concat(chunk);
    this._bytesRead += aCount;
  },

  // nsIChannelEventSink
  onChannelRedirect: function (aOldChannel, aNewChannel, aFlags) {
    this._channel = aNewChannel;
  },

  onProgress: function (aRequest, aContext, aProgress, aProgressMax) { },
  onStatus: function (aRequest, aContext, aStatus, aStatusArg) { }
};



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

FirenomicsReporter.auth = auth;
