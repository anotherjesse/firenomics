var Firenomics = (function() {
  var reporter = Cc['@oy/firenomics;1'].getService(Ci.oyIFirenomics);

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
      response.value = sign(input.value, user.secret);
      div = doc.getElementById('fnClaimProfile');
      div.style.visibility = 'visible';
    }
  }
  
  var sign = function(str, key) {
    return FlockCryptoHash.md5(str + key);
  }

  self.submit = function() {
    reporter.submit();
  }

  const CC = Components.classes;
  const CI = Components.interfaces;
  const CR = Components.results;

  var EXPORTED_SYMBOLS = ["FlockCryptoHash"];

  var FlockCryptoHash = {
    hashStream: function FlockCryptoHash_hashStream(aStream, aAlgorithm) {
      var hasher = CC["@mozilla.org/security/hash;1"]
        .createInstance(CI.nsICryptoHash);
      hasher.init(aAlgorithm);

      hasher.updateFromStream(aStream, aStream.available());
      var hash = hasher.finish(false);

      var ret = "";
      for (var i = 0; i < hash.length; ++i) {
        var hexChar = hash.charCodeAt(i).toString(16);
        if (hexChar.length == 1) {
          ret += "0";
        }
        ret += hexChar;
      }

      return ret;
    },
    hash: function FlockCryptoHash_hash(aString, aAlgorithm) {
      var stream = CC["@mozilla.org/io/string-input-stream;1"]
        .createInstance(CI.nsIStringInputStream);
      stream.setData(aString, aString.length);
      return this.hashStream(stream, aAlgorithm);
    },
    md5Stream: function FlockCryptoHash_md5Stream(aStream) {
      return this.hashStream(aStream, CI.nsICryptoHash.MD5);
    },
    md5: function FlockCryptoHash_md5(aString) {
      return this.hash(aString, CI.nsICryptoHash.MD5);
    },

    hexSHA1FromStream: function FlockCryptoHash_hexSHA1FromStream(aStream) {
      return this.hashStream(aStream, CI.nsICryptoHash.SHA1);
    },
    sha1: function FlockCryptoHash_sha1(aString) {
      return this.hash(aString, CI.nsICryptoHash.SHA1);
    }
  };

  load();

  return self;
})();
