function reload_iframe() {
    setTimeout(function(){
        document.getElementById('frame').contentWindow.location.reload();
    }, 500)
}
