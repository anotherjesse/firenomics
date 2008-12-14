Components.utils.import("resource://firenomics/reporter.js");

function fnLoad() {
  var appcontent = window.document.getElementById("appcontent");
  if (appcontent) {
    if (!appcontent.firenomicsInited) {
      appcontent.firenomicsInited = true;
      appcontent.addEventListener("DOMContentLoaded", function(event) { fnInit(event); }, false);
    }
  }
}

function fnInit(event) {
  var win = new XPCNativeWrapper(event.originalTarget, "top");

  if (win.location.href.match(FFirenomicsReporter.FIRENOMICS_URL + "/profile")) {
    fnRenderProfilePage(win);
    return;
  }
}

function fnGotoProfilePage() {
  openUILinkIn(FirenomicsReporter.FIRENOMICS_URL + "/profile/1234", "tab");
}

function fnRenderProfilePage(doc) {
  alert('rendering profile page');
  input = doc.getElementById('fnProfileSecret');
  input.value = '1234';
  div = doc.getElementById('fnClaimProfile');
  div.style.visibility = 'visible';
}

function fnSubmit() {
  alert('submitting stuffs');
  FirenomicsReporter.submit();
}

fnLoad();
