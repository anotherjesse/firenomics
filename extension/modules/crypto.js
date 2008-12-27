// FIXME: copyright flock

var EXPORTED_SYMBOLS = ['CryptoHash'];

const Cc = Components.classes;
const Ci = Components.interfaces;

var CryptoHash = {
  hashStream: function CryptoHash_hashStream(aStream, aAlgorithm) {
    var hasher = Cc["@mozilla.org/security/hash;1"]
      .createInstance(Ci.nsICryptoHash);
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
  hash: function CryptoHash_hash(aString, aAlgorithm) {
    var stream = Cc["@mozilla.org/io/string-input-stream;1"]
      .createInstance(Ci.nsIStringInputStream);
    stream.setData(aString, aString.length);
    return this.hashStream(stream, aAlgorithm);
  },
  md5Stream: function CryptoHash_md5Stream(aStream) {
    return this.hashStream(aStream, Ci.nsICryptoHash.MD5);
  },
  md5: function CryptoHash_md5(aString) {
    return this.hash(aString, Ci.nsICryptoHash.MD5);
  },
  hexSHA1FromStream: function CryptoHash_hexSHA1FromStream(aStream) {
    return this.hashStream(aStream, Ci.nsICryptoHash.SHA1);
  },
  sha1: function CryptoHash_sha1(aString) {
    return this.hash(aString, Ci.nsICryptoHash.SHA1);
  }
};
