FIRENOMICS_URL = "http://firenomics.appspot.com"

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
	
	if (win.location.href.match(FIRENOMICS_URL + "/profile")) {
		fnRenderProfilePage(win);
		return;
	}
}

function fnGotoProfilePage() {
  alert('going to profile page');
  openUILinkIn(FIRENOMICS_URL + "/profile/foo", "tab");
}

function fnRenderProfilePage(win) {
  alert('rendering profile page');
}

fnLoad();
