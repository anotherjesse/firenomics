Components.utils.import("resource://firenomics/reporter.js");

var Firenomics = (function() {
  var self = this;

  var load = function() {
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

    if (win.location.href.match(FIRENOMICS_URL + "/profile")) {
      renderProfilePage(win);
      return;
    }
  }

  self.gotoProfilePage = function() {
    openUILinkIn(FIRENOMICS_URL + "/profile/agpmaXJlbm9taWNzcg0LEgdQcm9maWxlGA0M", "tab");
  }

  var renderProfilePage = function(doc) {
    input = doc.getElementById('fnProfileSecret');
    input.value = '1234';
    div = doc.getElementById('fnClaimProfile');
    div.style.visibility = 'visible';
  }

  self.submit = function() {
    FirenomicsReporter.submit();
  }

  load();

  return self;
})();
