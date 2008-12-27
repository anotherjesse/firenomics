var Firenomics = (function() {
  var reporter = Cc['@oy/firenomics;1'].getService(Ci.oyIFirenomics);
  Cu.import("resource://firenomics/crypto.js");

  var self = this;

  var load = function() {
    // TODO: get rid of this!!!
    //reporter.clearAuth();
    var appcontent = window.document.getElementById("appcontent");
    if (appcontent) {
      if (!appcontent.firenomicsInited) {
        appcontent.firenomicsInited = true;
        appcontent.addEventListener("DOMContentLoaded", init, true);
      }
    }
  }

  var init = function(event) {
    var win = new XPCNativeWrapper(event.originalTarget, "top");

    if (win.location.href.match(reporter.FIRENOMICS_URL + "/profile")) {
      renderProfilePage(win);
    }
  }

  self.gotoProfilePage = function() {
    user = reporter.getUser();
    openUILinkIn(reporter.FIRENOMICS_URL + "/profile/" + user.key, "tab");
  }

  var renderProfilePage = function(doc) {
    var user = reporter.getUser();
    if (doc.location.href.match(user.key)) {
      input = doc.getElementById('fnProfileNonce');
      response = doc.getElementById('fnProfileResponse');
      response.value = CryptoHash.md5Sign(input.value, user.secret);
      div = doc.getElementById('fnClaimProfile');
      div.style.visibility = 'visible';
    }
  }

  self.submit = function() {
    reporter.submit();
  }

  load();

  return self;
})();
