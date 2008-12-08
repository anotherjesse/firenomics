const appInfo = Components.classes["@mozilla.org/xre/app-info;1"]
                  .getService(Components.interfaces.nsIXULAppInfo);
const runtime = Components.classes["@mozilla.org/xre/app-info;1"]
                  .getService(Components.interfaces.nsIXULRuntime);
const extMgr  = Components.classes["@mozilla.org/extensions/manager;1"]
                  .getService(Components.interfaces.nsIExtensionManager);
const RDFS    = Components.classes['@mozilla.org/rdf/rdf-service;1']
                  .getService(Components.interfaces.nsIRDFService);

function extensions() {
  var extensions = {};

  var ds = extMgr.datasource;
  ds.QueryInterface(Components.interfaces.nsIRDFDataSource);

  // Get list of incompatibles add-ons
  var incompatibles = {};

  const TYPE_EXTENSION = 2; // this is defined in nsIUpdateItem

  try {
    // Firefox 3
    var results = extMgr.getIncompatibleItemList(null, null, null, TYPE_EXTENSION, true, {});
  }
  catch(e) {
    // Firefox 2 and below
    var results = extMgr.getIncompatibleItemList(null, null, TYPE_EXTENSION, true, {});
  }

  for (var i = 0; i < results.length; i++) {
    incompatibles[results[i].id] = true;
  }

  // get the list of all extensions
  var results = extMgr.getItemList(TYPE_EXTENSION, {});
  for (var i = 0; i < results.length; i++) {

    var item = results[i];
    var skip = false;

    // check if extension is disabled

    var target = ds.GetTarget(RDFS.GetResource("urn:mozilla:item:" + item.id),
                                 RDFS.GetResource("http://www.mozilla.org/2004/em-rdf#isDisabled"),
                                 true);

    if ((target instanceof Components.interfaces.nsIRDFLiteral) &&
        (target.Value == 'true')) {
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
        icon: item.iconURL
      };
    }
  }

  return extensions;
}

function sysInfo() {
  return {
    ID: appInfo.ID,
    vendor: appInfo.vendor,
    name: appInfo.name,
    version: appInfo.version,
    appBuildID: appInfo.appBuildID,
    platformVersion: appInfo.platformVersion,
    platformBuildID: appInfo.platformBuildID,
    OS: runtime.OS
  };
}

function sendExtensionList() {
  const SUBMIT_URL = "http://firenomics.appspot.com/";

  var list = extensions();

  var nsJSON = Components.classes["@mozilla.org/dom/json;1"]
                         .createInstance(Components.interfaces.nsIJSON);
  var json = nsJSON.encode(list);

  var postBody = "data=" + encodeURIComponent(json);

  var req = Components.classes["@mozilla.org/xmlextras/xmlhttprequest;1"]
                      .createInstance(Components.interfaces.nsIXMLHttpRequest);
  req.mozBackgroundRequest = true;
  req.open("POST", SUBMIT_URL);
  req.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  req.send(postBody);
}
